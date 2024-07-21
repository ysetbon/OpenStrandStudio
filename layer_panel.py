from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QScrollArea, QHBoxLayout, QMenu, QAction, QColorDialog
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter
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

    def __init__(self, set_number, count, color=QColor('purple'), parent=None):
        super().__init__(parent)
        self.set_number = set_number
        self.count = count
        self.setFixedSize(40, 30)
        self.setText(f"{set_number}_{count}")
        self.setCheckable(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.set_color(color)

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
            self.color_changed.emit(self.set_number, color)

    def set_color(self, color):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color.name()};
                border: 1px solid black;
                font-weight: bold;
                color: white;
            }}
            QPushButton:hover {{
                background-color: {color.lighter().name()};
            }}
            QPushButton:checked {{
                background-color: {color.darker().name()};
            }}
        """)

class LayerPanel(QWidget):
    new_strand_requested = pyqtSignal(int, QColor)  # Emit set number and color
    strand_selected = pyqtSignal(int)
    deselect_all_requested = pyqtSignal()
    color_changed = pyqtSignal(int, QColor)

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
        self.scroll_layout.setAlignment(Qt.AlignBottom)
        self.scroll_area.setWidget(self.scroll_content)
        
        button_layout = QHBoxLayout()
        self.add_new_strand_button = QPushButton("Add New Strand")
        self.add_new_strand_button.setStyleSheet("background-color: lightgreen;")
        self.add_new_strand_button.clicked.connect(self.request_new_strand)
        
        self.deselect_all_button = QPushButton("Deselect All")
        self.deselect_all_button.setStyleSheet("background-color: lightyellow;")
        self.deselect_all_button.clicked.connect(self.deselect_all)
        
        button_layout.addWidget(self.add_new_strand_button)
        button_layout.addWidget(self.deselect_all_button)
        
        self.layout.addWidget(self.scroll_area)
        self.layout.addLayout(button_layout)
        
        self.layer_buttons = []
        self.current_set = 1
        self.set_counts = {1: 0}
        self.set_colors = {1: QColor('purple')}

    def request_new_strand(self):
        self.start_new_set()
        new_color = QColor('purple')
        self.new_strand_requested.emit(self.current_set, new_color)

    def add_layer_button(self, set_number=None):
        if set_number is None:
            set_number = self.current_set
        
        if set_number not in self.set_counts:
            self.set_counts[set_number] = 0
        
        self.set_counts[set_number] += 1
        count = self.set_counts[set_number]
        
        color = self.set_colors.get(set_number, QColor('purple'))
        button = NumberedLayerButton(set_number, count, color)
        button.clicked.connect(partial(self.select_layer, len(self.layer_buttons)))
        button.color_changed.connect(self.on_color_changed)
        self.scroll_layout.insertWidget(0, button)
        self.layer_buttons.append(button)
        self.select_layer(len(self.layer_buttons) - 1)
        
        # Update the current_set if a higher set number is encountered
        if set_number > self.current_set:
            self.current_set = set_number

    def select_layer(self, index, emit_signal=True):
        for i, button in enumerate(self.layer_buttons):
            button.setChecked(i == index)
        if emit_signal:
            self.strand_selected.emit(index)

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
        for button in self.layer_buttons:
            if button.set_number == set_number:
                button.set_color(color)
        self.color_changed.emit(set_number, color)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.handle.updateSize()