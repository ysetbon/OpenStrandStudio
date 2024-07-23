from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QScrollArea, QHBoxLayout, QMenu, QAction, QColorDialog, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPen
from functools import partial

class SplitterHandle(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(20)
        self.setCursor(Qt.SplitHCursor)
        if parent:
            parent.resizeEvent = self.parentResizeEvent

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(200, 200, 200))  # Light gray color

    def updateSize(self):
        if self.parent():
            self.setFixedWidth(self.parent().width())
            self.move(0, 0)  # Ensure the handle is at the top-left corner
            self.update()  # Force a repaint

    def parentResizeEvent(self, event):
        self.updateSize()
        # Call the original resizeEvent of the parent if it exists
        original_resize = getattr(type(self.parent()), 'resizeEvent', None)
        if original_resize:
            original_resize(self.parent(), event)

    def resizeEvent(self, event):
        self.updateSize()
        super().resizeEvent(event)

class NumberedLayerButton(QPushButton):
    color_changed = pyqtSignal(int, QColor)

    def __init__(self, text, count, color=QColor('purple'), parent=None):
        super().__init__(parent)
        self.setText(text)
        self.count = count
        self.setFixedSize(100, 30)  # Increased width to accommodate longer names
        self.setCheckable(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.color = color
        self.border_color = None
        self.set_color(color)

    def set_color(self, color):
        self.color = color
        self.update_style()

    def set_border_color(self, color):
        self.border_color = color
        self.update_style()

    def update_style(self):
        style = f"""
            QPushButton {{
                background-color: {self.color.name()};
                color: white;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.color.lighter().name()};
            }}
            QPushButton:checked {{
                background-color: {self.color.darker().name()};
            }}
        """
        if self.border_color:
            style += f"""
                QPushButton {{
                    border: 2px solid {self.border_color.name()};
                }}
            """
        self.setStyleSheet(style)

    def darken_color(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color.darker().name()};
                color: white;
                font-weight: bold;
            }}
        """)

    def restore_original_style(self):
        self.update_style()

    def show_context_menu(self, pos):
        context_menu = QMenu(self)
        change_color_action = QAction("Change Color", self)
        change_color_action.triggered.connect(self.change_color)
        context_menu.addAction(change_color_action)
        context_menu.exec_(self.mapToGlobal(pos))

    def change_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.set_color(color)
            self.color_changed.emit(int(self.text().split('_')[0]), color)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.border_color:
            painter = QPainter(self)
            painter.setPen(QPen(self.border_color, 2))
            painter.drawRect(self.rect().adjusted(1, 1, -1, -1))

class LayerPanel(QWidget):
    new_strand_requested = pyqtSignal(int, QColor)
    strand_selected = pyqtSignal(int)
    deselect_all_requested = pyqtSignal()
    color_changed = pyqtSignal(int, QColor)
    masked_layer_created = pyqtSignal(int, int)
    draw_names_requested = pyqtSignal(bool)  # Emit with the toggle state
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.handle = SplitterHandle(self)
        self.layout.addWidget(self.handle)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        self.scroll_area.setWidget(self.scroll_content)
        
        button_layout = QHBoxLayout()
        self.add_new_strand_button = QPushButton("Add New Strand")
        self.add_new_strand_button.setStyleSheet("background-color: lightgreen;")
        self.add_new_strand_button.clicked.connect(self.request_new_strand)
        
        self.deselect_all_button = QPushButton("Deselect All")
        self.deselect_all_button.setStyleSheet("background-color: lightyellow;")
        self.deselect_all_button.clicked.connect(self.deselect_all)

        self.draw_names_button = QPushButton("Draw Names")
        self.draw_names_button.clicked.connect(self.request_draw_names)
        self.should_draw_names = False  # Track the toggle state

        button_layout.addWidget(self.draw_names_button)               
        button_layout.addWidget(self.add_new_strand_button)
        button_layout.addWidget(self.deselect_all_button)
        
        self.layout.addWidget(self.scroll_area)
        self.layout.addLayout(button_layout)
        
        self.layer_buttons = []
        self.current_set = 1
        self.set_counts = {1: 0}
        self.set_colors = {1: QColor('purple')}
      


        self.masked_mode = False
        self.first_masked_layer = None
        self.notification_label = QLabel()
        self.notification_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.notification_label)

    def request_draw_names(self):
        self.should_draw_names = not self.should_draw_names
        self.draw_names_requested.emit(self.should_draw_names)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.enter_masked_mode()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.exit_masked_mode()

    def enter_masked_mode(self):
        self.masked_mode = True
        self.first_masked_layer = None
        for button in self.layer_buttons:
            button.setStyleSheet(f"background-color: gray; color: white;")

    def exit_masked_mode(self):
        self.masked_mode = False
        self.first_masked_layer = None
        for button in self.layer_buttons:
            button.restore_original_style()
        self.notification_label.clear()

    def select_layer(self, index, emit_signal=True):
        if self.masked_mode:
            self.handle_masked_layer_selection(index)
        else:
            for i, button in enumerate(self.layer_buttons):
                button.setChecked(i == index)
            if emit_signal:
                self.strand_selected.emit(index)

    def handle_masked_layer_selection(self, index):
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
        masked_layer_name = f"{self.layer_buttons[layer1].text()}_{self.layer_buttons[layer2].text()}"
        if any(button.text() == masked_layer_name for button in self.layer_buttons):
            self.notification_label.setText(f"Masked layer {masked_layer_name} already exists")
            return

        self.masked_layer_created.emit(layer1, layer2)
        self.notification_label.setText(f"Created new masked layer: {masked_layer_name}")

    def add_masked_layer_button(self, layer1, layer2):
        button = NumberedLayerButton(f"{self.layer_buttons[layer1].text()}_{self.layer_buttons[layer2].text()}", 0)
        button.set_color(self.layer_buttons[layer1].color)
        button.set_border_color(self.layer_buttons[layer2].color)
        button.clicked.connect(partial(self.select_layer, len(self.layer_buttons)))
        button.color_changed.connect(self.on_color_changed)
        self.scroll_layout.insertWidget(0, button)
        self.layer_buttons.append(button)
        return button

    def request_new_strand(self):
        self.start_new_set()
        new_color = QColor('purple')
        new_strand_number = self.current_set
        new_strand_index = self.set_counts[self.current_set] + 1
        new_strand_name = f"{new_strand_number}_{new_strand_index}"
        self.new_strand_requested.emit(new_strand_number, new_color)
        
  

    def add_layer_button(self, set_number=None):
        if set_number is None:
            set_number = self.current_set
        
        if set_number not in self.set_counts:
            self.set_counts[set_number] = 0
        
        self.set_counts[set_number] += 1
        count = self.set_counts[set_number]
        
        color = self.set_colors.get(set_number, QColor('purple'))
        button = NumberedLayerButton(f"{set_number}_{count}", count, color)
        button.clicked.connect(partial(self.select_layer, len(self.layer_buttons)))
        button.color_changed.connect(self.on_color_changed)
        
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setAlignment(Qt.AlignHCenter)
        button_layout.addWidget(button)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_layout.insertWidget(0, button_container)
        self.layer_buttons.append(button)
        self.select_layer(len(self.layer_buttons) - 1)
        
        if set_number > self.current_set:
            self.current_set = set_number

    def start_new_set(self):
        self.current_set = max(self.set_counts.keys(), default=0) + 1
        self.set_counts[self.current_set] = 0
        new_color = QColor('purple')
        self.set_colors[self.current_set] = new_color

    def clear_selection(self):
        for button in self.layer_buttons:
            button.setChecked(False)

    def get_selected_layer(self):
        for i, button in enumerate(self.layer_buttons):
            if button.isChecked():
                return i
        return None

    def deselect_all(self):
        self.clear_selection()
        self.deselect_all_requested.emit()

    def on_color_changed(self, set_number, color):
        self.set_colors[set_number] = color
        self.update_colors_for_set(set_number, color)
        self.color_changed.emit(set_number, color)

    def update_colors_for_set(self, set_number, color):
        for button in self.layer_buttons:
            if isinstance(button, NumberedLayerButton):
                if button.text().startswith(f"{set_number}_") or button.text().split('_')[0] == str(set_number):
                    button.set_color(color)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.handle.updateSize()