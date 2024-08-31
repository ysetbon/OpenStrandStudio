from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QPushButton, QInputDialog, QVBoxLayout, QWidget, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QDrag, QDragEnterEvent, QDropEvent
from PyQt5.QtCore import QMimeData, QPoint

class GroupedLayerTree(QTreeWidget):
    layer_selected = pyqtSignal(int)
    group_created = pyqtSignal(str)
    layer_moved = pyqtSignal(int, str)  # layer index, group name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QTreeWidget.SingleSelection)
        self.itemClicked.connect(self.on_item_clicked)

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

class GroupPanel(QWidget):
    group_operation = pyqtSignal(str, str, list)  # operation, group_name, layer_indices

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.groups = {}
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat("application/x-strand-data"):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        data = eval(event.mimeData().data("application/x-strand-data").decode())
        strand_id = data['strand_id']
        
        group_name, ok = QInputDialog.getText(self, "Add to Group", "Enter group name:")
        if ok and group_name:
            self.add_layer_to_group(strand_id, group_name)

    def add_layer_to_group(self, strand_id, group_name):
        if group_name not in self.groups:
            self.create_group(group_name)
        
        if "layers" not in self.groups[group_name]:
            self.groups[group_name]["layers"] = []
        
        self.groups[group_name]["layers"].append(strand_id)
        self.update_group_display(group_name)

    def create_group(self, group_name):
        group_widget = QWidget()
        group_layout = QVBoxLayout(group_widget)
        group_label = QLabel(group_name)
        group_layout.addWidget(group_label)
        self.layout.addWidget(group_widget)
        self.groups[group_name] = {"widget": group_widget, "label": group_label, "layers": []}

    def update_group_display(self, group_name):
        if group_name in self.groups:
            group_info = self.groups[group_name]
            strand_count = len(group_info["layers"])
            group_info["label"].setText(f"{group_name} ({strand_count})")
            
            # Clear existing layer labels
            for i in reversed(range(group_info["widget"].layout().count())):
                if i > 0:  # Keep the group label
                    group_info["widget"].layout().itemAt(i).widget().setParent(None)
            
            # Add layer labels
            for layer in group_info["layers"]:
                layer_label = QLabel(layer)
                group_info["widget"].layout().addWidget(layer_label)

class GroupLayerManager:
    def __init__(self, layer_panel):
        self.layer_panel = layer_panel
        self.canvas = layer_panel.canvas
        self.tree = GroupedLayerTree(layer_panel)
        self.layer_panel.layout.insertWidget(1, self.tree)  # Insert after the splitter handle

        self.group_panel = GroupPanel(layer_panel)
        self.layer_panel.layout.addWidget(self.group_panel)

        self.create_group_button = QPushButton("Create Group")
        self.create_group_button.clicked.connect(self.create_group)
        self.layer_panel.layout.insertWidget(2, self.create_group_button)

        self.tree.layer_selected.connect(self.layer_panel.select_layer)
        self.tree.group_created.connect(self.on_group_created)
        self.tree.layer_moved.connect(self.on_layer_moved)
        self.groups = {}  # Dictionary to store groups and their strands

        self.group_panel.group_operation.connect(self.on_group_operation)
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
            self.tree.add_group(group_name)
            self.group_panel.create_group(group_name)

    def on_group_created(self, group_name):
        # You can add any additional logic here when a group is created
        pass

    def on_layer_moved(self, layer_index, group_name):
        layer_name = self.layer_panel.layer_buttons[layer_index].text()
        self.group_panel.add_layer_to_group(layer_index, group_name)

    def on_group_operation(self, operation, group_name, layer_indices):
        if operation == "rotate":
            self.rotate_group(group_name, layer_indices)
        elif operation == "move":
            self.move_group(group_name, layer_indices)

    def rotate_group(self, group_name, layer_indices):
        # Calculate the center point of all strands in the group
        center_x = sum(self.canvas.strands[i].start_point.x() + self.canvas.strands[i].end_point.x() for i in layer_indices) / (2 * len(layer_indices))
        center_y = sum(self.canvas.strands[i].start_point.y() + self.canvas.strands[i].end_point.y() for i in layer_indices) / (2 * len(layer_indices))
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

    def add_layer(self, layer_name, color):
        return self.tree.add_layer(layer_name, color)

    def clear(self):
        self.tree.clear()
        self.group_panel.groups.clear()
        for i in reversed(range(self.group_panel.layout.count())): 
            self.group_panel.layout.itemAt(i).widget().setParent(None)

    def update_layer_color(self, index, color):
        item = self.tree.topLevelItem(index)
        if item:
            item.setData(1, Qt.UserRole, color)

    def select_layer(self, index):
        item = self.tree.topLevelItem(index)
        if item:
            self.tree.setCurrentItem(item)

    def refresh(self):
        self.clear()
        for i, button in enumerate(self.layer_panel.layer_buttons):
            self.add_layer(button.text(), button.color)

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
