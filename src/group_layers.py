from PyQt5.QtWidgets import (QTreeWidget, QTreeWidgetItem, QPushButton, QInputDialog, QVBoxLayout, QWidget, QLabel, 
                             QHBoxLayout, QDialog, QListWidget, QListWidgetItem, QDialogButtonBox, QFrame, QScrollArea, QMenu, QAction)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QDrag, QDragEnterEvent, QDropEvent, QIcon
from PyQt5.QtCore import QMimeData, QPoint
from PyQt5.QtCore import QPointF
class GroupedLayerTree(QTreeWidget):
    layer_selected = pyqtSignal(int)
    group_created = pyqtSignal(str)
    layer_moved = pyqtSignal(int, str)  # layer index, group name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)
        self.groups = {}
        self.setAcceptDrops(True)

    def update_layer(self, index, layer_name, color):
        # Check if the layer is in any group
        for group_name, group_info in self.groups.items():
            if layer_name in group_info['layers']:
                # Update the layer in the group
                group_widget = self.findChild(CollapsibleGroupWidget, group_name)
                if group_widget:
                    group_widget.update_layer(layer_name, color)
                return
        
        # If the layer is not in any group, it might be a new layer
        # You can decide how to handle new layers here, for example:
        # self.add_layer_to_default_group(layer_name, color)

    def add_layer(self, layer_name, color):
        item = QTreeWidgetItem(self, [layer_name])
        item.setData(0, Qt.UserRole, "layer")
        item.setData(1, Qt.UserRole, color)
        self.addTopLevelItem(item)
        return item

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
        self.layout.setSpacing(2)

        # Header (group name button)
        self.group_button = QPushButton(self.group_name)
        self.group_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 5px;
                text-align: left;
            }
        """)
        self.group_button.clicked.connect(self.toggle_collapse)
        self.group_button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.group_button.customContextMenuRequested.connect(self.show_context_menu)
        self.layout.addWidget(self.group_button)

        # Content (layer buttons)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(5, 0, 0, 0)
        self.content_layout.setSpacing(2)
        self.layout.addWidget(self.content)

    def show_context_menu(self, position):
        context_menu = QMenu(self)
        move_action = context_menu.addAction("Move Group")
        move_strands_action = context_menu.addAction("Move Group Strands")
        delete_action = context_menu.addAction("Delete Group")
        
        action = context_menu.exec_(self.group_button.mapToGlobal(position))
        if action == move_action:
            self.group_panel.start_move_mode(self.group_name)
        elif action == move_strands_action:
            self.group_panel.start_group_move(self.group_name)
        elif action == delete_action:
            self.group_panel.delete_group(self.group_name)


    def toggle_collapse(self):
        self.is_collapsed = not self.is_collapsed
        self.content.setVisible(not self.is_collapsed)

    def add_layer(self, layer_name):
        if layer_name not in self.layers:
            self.layers.append(layer_name)
            layer_button = QPushButton(layer_name)
            layer_button.setStyleSheet("""
                QPushButton {
                    background-color: #e0e0e0;
                    border: 1px solid #c0c0c0;
                    border-radius: 3px;
                    padding: 3px;
                    text-align: left;
                }
            """)
            self.content_layout.addWidget(layer_button)

    def update_group_display(self):
        self.group_button.setText(f"{self.group_name} ({len(self.layers)})")

    def update_layer(self, index, layer_name, color):
        # Check if the layer is in any group
        for group_name, group_info in self.groups.items():
            if layer_name in group_info['layers']:
                # Update the layer in the group
                group_widget = self.findChild(CollapsibleGroupWidget, group_name)
                if group_widget:
                    group_widget.update_layer(layer_name, color)
                return
        
        # If the layer is not in any group, it might be a new layer
        # You can decide how to handle new layers here, for example:
        # self.add_layer_to_default_group(layer_name, color)
        
        # If the layer is not in any group, it might be a new layer
        # You can decide how to handle new layers here, for example:
        # self.add_layer_to_default_group(layer_name, color)

import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QInputDialog
from PyQt5.QtCore import pyqtSignal, Qt, QPointF
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

class GroupPanel(QWidget):
    group_operation = pyqtSignal(str, str, list)  # operation, group_name, layer_indices
    move_group_started = pyqtSignal(str, list)  # New signal

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: white;")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)
        self.groups = {}
        self.setAcceptDrops(True)

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
        self.groups[group_name] = {'widget': group_widget, 'layers': [], 'strands': []}

        logging.info(f"Creating group: {group_name}")
        logging.info("Strands in the group:")

        for layer_name, strand_data in layers_data:
            self.add_layer_to_group(layer_name, group_name, strand_data)
            
            start = strand_data['start']
            end = strand_data['end']
            logging.info(f"  Layer: {layer_name}")
            logging.info(f"    Start: ({start.x():.2f}, {start.y():.2f})")
            logging.info(f"    End: ({end.x():.2f}, {end.y():.2f})")

        logging.info(f"Group {group_name} created with {len(layers_data)} strands.")

    def add_layer_to_group(self, layer_name, group_name, strand_data):
        if group_name not in self.groups:
            return  # Group doesn't exist, can't add layer

        self.groups[group_name]['layers'].append(layer_name)
        self.groups[group_name]['strands'].append(strand_data)
        self.groups[group_name]['widget'].add_layer(layer_name)
        self.groups[group_name]['widget'].update_group_display()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat("application/x-strand-data"):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        data = eval(event.mimeData().data("application/x-strand-data").decode())
        strand_id = data['strand_id']
        
        group_name, ok = QInputDialog.getText(self, "Add to Group", "Enter group name:")
        if ok and group_name:
            self.add_layer_to_group(strand_id, group_name)

    def start_group_move(self, group_name):
        if group_name in self.groups:
            layers = self.groups[group_name]['layers']
            dialog = GroupMoveDialog(self)
            dialog.move_updated.connect(lambda dx, dy: self.update_group_move(group_name, layers, dx, dy))
            dialog.exec_()
        else:
            logging.warning(f"Attempted to move non-existent group: {group_name}")

    def update_group_move(self, group_name, layers, dx, dy):
        self.move_group_started.emit(group_name, layers)
        if hasattr(self, 'canvas'):
            self.canvas.move_group(dx, dy)

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal

class GroupMoveDialog(QDialog):
    move_updated = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Move Group Strands")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # dx slider
        dx_layout = QHBoxLayout()
        dx_layout.addWidget(QLabel("dx:"))
        self.dx_slider = QSlider(Qt.Horizontal)
        self.dx_slider.setRange(-100, 100)
        self.dx_slider.setValue(0)
        self.dx_slider.valueChanged.connect(self.update_move)
        dx_layout.addWidget(self.dx_slider)
        self.dx_value = QLabel("0")
        dx_layout.addWidget(self.dx_value)
        layout.addLayout(dx_layout)

        # dy slider
        dy_layout = QHBoxLayout()
        dy_layout.addWidget(QLabel("dy:"))
        self.dy_slider = QSlider(Qt.Horizontal)
        self.dy_slider.setRange(-100, 100)
        self.dy_slider.setValue(0)
        self.dy_slider.valueChanged.connect(self.update_move)
        dy_layout.addWidget(self.dy_slider)
        self.dy_value = QLabel("0")
        dy_layout.addWidget(self.dy_value)
        layout.addLayout(dy_layout)

        # OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)

    def update_move(self):
        dx = self.dx_slider.value()
        dy = self.dy_slider.value()
        self.dx_value.setText(str(dx))
        self.dy_value.setText(str(dy))
        self.move_updated.emit(dx, dy)

def create_group(self, group_name, layers_data):
    group_widget = CollapsibleGroupWidget(group_name, self)
    self.scroll_layout.addWidget(group_widget)
    self.groups[group_name] = {'widget': group_widget, 'layers': [], 'strands': []}

    for layer_name, strand_data in layers_data:
        self.add_layer_to_group(layer_name, group_name, strand_data)

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
    def __init__(self, layer_panel):
        self.layer_panel = layer_panel
        self.canvas = None
        
        # Create the tree but don't add it to any layout
        self.tree = GroupedLayerTree(layer_panel)
        self.tree.hide()  # Hide the tree completely

        self.group_panel = GroupPanel()
        
        self.create_group_button = QPushButton("Create Group")
        self.create_group_button.clicked.connect(self.create_group)

        # Remove all references to adding the tree to any layout
        # The tree will still exist but won't be visible or take up any space

        # ... (rest of the code)

    def add_strand_to_group(self, group_name, strand_id):
        if group_name not in self.groups:
            self.groups[group_name] = []
        self.groups[group_name].append(strand_id)
        print(f"Added strand {strand_id} to group {group_name}")
        
        # Update the group panel
        self.group_panel.add_layer_to_group(strand_id, group_name)

    def create_group(self):
        group_name, ok = QInputDialog.getText(self.layer_panel, "Create Group", "Enter group name:")
        if ok and group_name:
            layers = [button.text() for button in self.layer_panel.layer_buttons]
            dialog = LayerSelectionDialog(layers, self.layer_panel)
            if dialog.exec_():
                selected_layers = dialog.get_selected_layers()
                self.tree.add_group(group_name)
                
                layers_data = []
                for layer in selected_layers:
                    layer_index = self.layer_panel.layer_buttons.index(next(button for button in self.layer_panel.layer_buttons if button.text() == layer))
                    if layer_index < len(self.canvas.strands):
                        strand = self.canvas.strands[layer_index]
                        strand_data = {
                            'start': QPointF(strand.start),
                            'end': QPointF(strand.end)
                        }
                        layers_data.append((layer, strand_data))
                
                self.group_panel.create_group(group_name, layers_data)

    def on_group_created(self, group_name):
        # You can add any additional logic here when a group is created
        pass

    def on_layer_moved(self, layer_index, group_name):
        layer_name = self.layer_panel.layer_buttons[layer_index].text()
        self.group_panel.add_layer_to_group(layer_name, group_name)

    def on_group_operation(self, operation, group_name, layer_indices):
        if operation == "rotate":
            self.rotate_group(group_name, layer_indices)
        elif operation == "move":
            self.move_group(group_name, layer_indices)
        elif operation == "delete":
            self.delete_group(group_name, layer_indices)

    def rotate_group(self, group_name, layer_indices):
        # Calculate the center point of all strands in the group
        center_x = sum(self.canvas.strands[i].start.x() + self.canvas.strands[i].end.x() for i in layer_indices) / (2 * len(layer_indices))
        center_y = sum(self.canvas.strands[i].start.y() + self.canvas.strands[i].end.y() for i in layer_indices) / (2 * len(layer_indices))
        center = QPoint(center_x, center_y)

        # Rotate all strands in the group
        angle = 45  # You can adjust this or make it user-input
        for i in layer_indices:
            strand = self.canvas.strands[i]
            strand.rotate(angle, center)

        self.canvas.update()

    def move_group(self, group_name, layer_indices):
        # Move all strands in the group
        offset = QPoint(50, 50)  # You can adjust this or make it user-input
        for i in layer_indices:
            strand = self.canvas.strands[i]
            strand.move(offset)

        self.canvas.update()

    def delete_group(self, group_name, layer_indices):
        # Remove layers from the group
        for layer_index in layer_indices:
            self.layer_panel.delete_layer(layer_index)
        
        # Remove the group from the tree
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            if root.child(i).text(0) == group_name:
                root.removeChild(root.child(i))
                break

        # Update the canvas
        self.canvas.update()

    def add_layer(self, layer_name, color):
        return self.tree.add_layer(layer_name, color)

    def clear(self):
        self.tree.clear()
        self.group_panel.groups.clear()
        for i in reversed(range(self.group_panel.scroll_layout.count())): 
            self.group_panel.scroll_layout.itemAt(i).widget().setParent(None)

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
                strand_data['start'] += QPointF(dx, dy)
                strand_data['end'] += QPointF(dx, dy)
                
                layer_name = group_data['layers'][i]
                layer_index = self.layer_panel.layer_buttons.index(next(button for button in self.layer_panel.layer_buttons if button.text() == layer_name))
                strand = self.canvas.strands[layer_index]
                strand.start = strand_data['start']
                strand.end = strand_data['end']
                updated_strands.append(strand)
            
            # Update the canvas with the modified strands
            self.canvas.update_strands(updated_strands)

    def start_group_move(self, group_name):
        if self.canvas:
            self.canvas.start_group_move(group_name, self.move_group_strands)
