from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QScrollArea, QHBoxLayout
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
    def __init__(self, set_number, count, parent=None):
        super().__init__(parent)
        self.set_number = set_number
        self.count = count
        self.setFixedSize(40, 30)
        self.setText(f"{set_number}_{count}")
        self.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid black;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:checked {
                background-color: lightblue;
            }
        """)
        self.setCheckable(True)

class LayerPanel(QWidget):
    new_strand_requested = pyqtSignal()
    strand_selected = pyqtSignal(int)
    deselect_all_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.handle = SplitterHandle(self)
        self.layout.addWidget(self.handle)

        # Create scrollable area for layer buttons
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignBottom)
        self.scroll_area.setWidget(self.scroll_content)
        
        # Add buttons at the bottom
        button_layout = QHBoxLayout()
        self.add_new_strand_button = QPushButton("Add New Strand")
        self.add_new_strand_button.setStyleSheet("background-color: lightgreen;")
        self.add_new_strand_button.clicked.connect(self.new_strand_requested.emit)
        
        self.deselect_all_button = QPushButton("Deselect All")
        self.deselect_all_button.setStyleSheet("background-color: lightyellow;")
        self.deselect_all_button.clicked.connect(self.deselect_all)
        
        button_layout.addWidget(self.add_new_strand_button)
        button_layout.addWidget(self.deselect_all_button)
        
        # Assemble the layout
        self.layout.addWidget(self.scroll_area)
        self.layout.addLayout(button_layout)
        
        self.layer_buttons = []
        self.current_set = 1
        self.current_count = 0

    def add_layer_button(self):
        self.current_count += 1
        index = len(self.layer_buttons)
        button = NumberedLayerButton(self.current_set, self.current_count)
        button.clicked.connect(partial(self.select_layer, index))
        self.scroll_layout.insertWidget(0, button)
        self.layer_buttons.append(button)
        self.select_layer(index)

    def select_layer(self, index):
        for i, button in enumerate(self.layer_buttons):
            button.setChecked(i == index)
        print(f"Layer {index} selected")
        self.strand_selected.emit(index)

    def start_new_set(self):
        self.current_set += 1
        self.current_count = 0

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
        self.deselect_all_requested.emit()  # Emit signal to notify of deselection

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.handle.updateSize()  # Ensure the handle updates its size