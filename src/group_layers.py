from PyQt5.QtWidgets import (QTreeWidget, QTreeWidgetItem, QPushButton, QInputDialog, QVBoxLayout, QWidget, QLabel, 
                             QHBoxLayout, QDialog, QListWidget, QListWidgetItem, QDialogButtonBox, QFrame, QScrollArea, QMenu, QAction)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QDrag, QDragEnterEvent, QDropEvent, QIcon
from PyQt5.QtCore import QMimeData, QPoint
from PyQt5.QtCore import QPointF
from strand_drawing_canvas import StrandDrawingCanvas   
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
        
        action = context_menu.exec_(self.group_button.mapToGlobal(position))

        if action == move_strands_action:
            self.group_panel.start_group_move(self.group_name)
        elif action == rotate_strands_action:
            self.group_panel.start_group_rotation(self.group_name)

    def toggle_collapse(self):
        self.is_collapsed = not self.is_collapsed
        self.content.setVisible(not self.is_collapsed)
        self.update_size()

    def add_layer(self, layer_name):
        if layer_name not in self.layers:
            self.layers.append(layer_name)
            item = QListWidgetItem(layer_name)
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
        self.group_button.setText(f"{self.group_name} ({len(self.layers)})")

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
        self.groups[group_name] = {'widget': group_widget, 'layers': [], 'strands': []}
        logging.info(f"Group '{group_name}' created with layers: {layers_data}")
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

    def update_group_display(self, group_name):
        if group_name in self.groups:
            group_widget = self.groups[group_name]['widget']
            group_widget.update_group_display()

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

    def update_groups_with_new_strand(self, new_strand):
        logging.info(f"Updating groups with new strand: {new_strand.layer_name}")
        main_layer = new_strand.layer_name.split('_')[0]
        for group_name, group_data in self.group_panel.groups.items():
            logging.info(f"Checking group: {group_name}")
            if any(layer.startswith(f"{main_layer}_") for layer in group_data['layers']):
                logging.info(f"Adding strand {new_strand.layer_name} to group {group_name}")
                self.add_strand_to_group(group_name, new_strand)

    def add_strand_to_group(self, group_name, strand):
        if group_name in self.group_panel.groups:
            group_data = self.group_panel.groups[group_name]
            if strand.layer_name not in group_data['layers']:
                group_data['layers'].append(strand.layer_name)
                strand_data = {
                    'start': QPointF(strand.start),
                    'end': QPointF(strand.end)
                }
                group_data['strands'].append(strand_data)
                
                # Update the group panel
                self.group_panel.update_group_display(group_name)
                
                # Update the CollapsibleGroupWidget
                group_widget = self.group_panel.groups[group_name]['widget']
                group_widget.add_layer(strand.layer_name)
                group_widget.update_group_display()
                
                logging.info(f"Added strand {strand.layer_name} to group {group_name}")
                
                # Force a refresh of the group panel
                self.group_panel.update()

                # Update canvas groups
                if self.canvas and group_name in self.canvas.groups:
                    self.canvas.groups[group_name]['strands'].append(strand)
                    self.canvas.groups[group_name]['layers'].append(strand.layer_name)
            else:
                logging.info(f"Strand {strand.layer_name} already in group {group_name}")
        else:
            logging.warning(f"Attempted to add strand to non-existent group: {group_name}")

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
                                'start': QPointF(strand.start),
                                'end': QPointF(strand.end)
                            }
                            layers_data.append((sub_layer, strand_data))
                
                self.group_panel.create_group(group_name, layers_data)
                
                # Initialize the group in canvas.groups
                self.canvas.groups[group_name] = {'strands': [], 'layers': []}
                for sub_layer, _ in layers_data:
                    strand = self.canvas.find_strand_by_name(sub_layer)
                    if strand:
                        self.canvas.groups[group_name]['strands'].append(strand)
                        self.canvas.groups[group_name]['layers'].append(sub_layer)

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
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal

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
        self.angle_slider.valueChanged.connect(self.update_angle)
        angle_layout.addWidget(self.angle_slider)
        self.angle_value = QLabel("0°")
        angle_layout.addWidget(self.angle_value)
        layout.addLayout(angle_layout)

        # OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.on_ok_clicked)
        layout.addWidget(ok_button)

    def update_angle(self):
        self.angle = self.angle_slider.value()
        self.angle_value.setText(f"{self.angle}°")
        self.rotation_updated.emit(self.group_name, self.angle)

    def on_ok_clicked(self):
        self.rotation_finished.emit(self.group_name)
        self.accept()