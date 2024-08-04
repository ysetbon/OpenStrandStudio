# Import necessary modules from PyQt5
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QScrollArea, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from functools import partial

# Import custom widgets
from splitter_handle import SplitterHandle
from numbered_layer_button import NumberedLayerButton

class LayerPanel(QWidget):
    # Define custom signals for various events
    new_strand_requested = pyqtSignal(int, QColor)  # Signal emitted when a new strand is requested
    strand_selected = pyqtSignal(int)  # Signal emitted when a strand is selected
    deselect_all_requested = pyqtSignal()  # Signal emitted when deselection of all strands is requested
    color_changed = pyqtSignal(int, QColor)  # Signal emitted when a strand's color is changed
    masked_layer_created = pyqtSignal(int, int)  # Signal emitted when a masked layer is created
    draw_names_requested = pyqtSignal(bool)  # Signal emitted when drawing of names is requested
    masked_mode_entered = pyqtSignal()  # Signal emitted when masked mode is entered
    masked_mode_exited = pyqtSignal()  # Signal emitted when masked mode is exited

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.last_selected_index = None  # Store the index of the last selected layer
       
        # Create and add the splitter handle
        self.handle = SplitterHandle(self)
        self.layout.addWidget(self.handle)

        # Create a scrollable area for layer buttons
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        self.scroll_area.setWidget(self.scroll_content)
        
        # Create a layout for control buttons
        button_layout = QHBoxLayout()
        
        # Create "Add New Strand" button
        self.add_new_strand_button = QPushButton("Add New Strand")
        self.add_new_strand_button.setStyleSheet("background-color: lightgreen;")
        self.add_new_strand_button.clicked.connect(self.request_new_strand)
        
        # Create "Deselect All" button
        self.deselect_all_button = QPushButton("Deselect All")
        self.deselect_all_button.setStyleSheet("background-color: lightyellow;")
        self.deselect_all_button.clicked.connect(self.deselect_all)

        # Create "Draw Names" button
        self.draw_names_button = QPushButton("Draw Names")
        self.draw_names_button.clicked.connect(self.request_draw_names)
        self.should_draw_names = False

        # Add buttons to the button layout
        button_layout.addWidget(self.draw_names_button)               
        button_layout.addWidget(self.add_new_strand_button)
        button_layout.addWidget(self.deselect_all_button)
        
        # Add scroll area and button layout to the main layout
        self.layout.addWidget(self.scroll_area)
        self.layout.addLayout(button_layout)
        
        # Initialize variables for managing layers
        self.layer_buttons = []  # List to store layer buttons
        self.current_set = 1  # Current set number
        self.set_counts = {1: 0}  # Dictionary to keep track of counts for each set
        self.set_colors = {1: QColor('purple')}  # Dictionary to store colors for each set
      
        # Initialize masked mode variables
        self.masked_mode = False
        self.first_masked_layer = None
        
        # Create a label for notifications
        self.notification_label = QLabel()
        self.notification_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.notification_label)

    def request_draw_names(self):
        """Toggle the drawing of names and emit the corresponding signal."""
        self.should_draw_names = not self.should_draw_names
        self.draw_names_requested.emit(self.should_draw_names)

    def keyPressEvent(self, event):
        """Handle key press events, specifically for entering masked mode."""
        if event.key() == Qt.Key_Control:
            self.enter_masked_mode()

    def keyReleaseEvent(self, event):
        """Handle key release events, specifically for exiting masked mode."""
        if event.key() == Qt.Key_Control:
            self.exit_masked_mode()

    def enter_masked_mode(self):
        """Enter masked mode, updating UI and emitting relevant signal."""
        self.masked_mode = True
        self.first_masked_layer = None
        self.last_selected_index = self.get_selected_layer()
        for button in self.layer_buttons:
            button.set_masked_mode(True)
            button.setChecked(False)
        self.masked_mode_entered.emit()

    def exit_masked_mode(self):
        """Exit masked mode, updating UI and emitting relevant signal."""
        self.masked_mode = False
        self.first_masked_layer = None
        for button in self.layer_buttons:
            button.set_masked_mode(False)
        self.masked_mode_exited.emit()
        self.notification_label.clear()

    def select_layer(self, index, emit_signal=True):
        """
        Select a layer by index.
        
        If in masked mode, handle masked layer selection.
        Otherwise, update button states and emit selection signal.
        """
        if self.masked_mode:
            self.handle_masked_layer_selection(index)
        else:
            for i, button in enumerate(self.layer_buttons):
                button.setChecked(i == index)
            if emit_signal:
                self.strand_selected.emit(index)
            self.last_selected_index = index

    def handle_masked_layer_selection(self, index):
        """
        Handle the selection of layers in masked mode.
        
        If it's the first selection, mark it.
        If it's the second selection, create a masked layer.
        """
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
        """
        Create a masked layer from two selected layers.
        
        Check if the masked layer already exists, if not, create it and emit signal.
        """
        masked_layer_name = f"{self.layer_buttons[layer1].text()}_{self.layer_buttons[layer2].text()}"
        if any(button.text() == masked_layer_name for button in self.layer_buttons):
            self.notification_label.setText(f"Masked layer {masked_layer_name} already exists")
            return

        self.masked_layer_created.emit(layer1, layer2)
        self.notification_label.setText(f"Created new masked layer: {masked_layer_name}")

    def add_masked_layer_button(self, layer1, layer2):
        """
        Add a button for a newly created masked layer.
        
        Return the created button.
        """
        button = NumberedLayerButton(f"{self.layer_buttons[layer1].text()}_{self.layer_buttons[layer2].text()}", 0)
        button.set_color(self.layer_buttons[layer1].color)
        button.set_border_color(self.layer_buttons[layer2].color)
        button.clicked.connect(partial(self.select_layer, len(self.layer_buttons)))
        button.color_changed.connect(self.on_color_changed)
        self.scroll_layout.insertWidget(0, button)
        self.layer_buttons.append(button)
        return button

    def request_new_strand(self):
        """
        Request the creation of a new strand.
        
        Start a new set and emit signal with new strand details.
        """
        self.start_new_set()
        new_color = QColor('purple')
        new_strand_number = self.current_set
        new_strand_index = self.set_counts[self.current_set] + 1
        new_strand_name = f"{new_strand_number}_{new_strand_index}"
        self.new_strand_requested.emit(new_strand_number, new_color)

    def add_layer_button(self, set_number=None):
        """
        Add a new layer button for the given set number.
        
        If no set number is provided, use the current set.
        """
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
        """Start a new set by incrementing the current set number."""
        self.current_set = max(self.set_counts.keys(), default=0) + 1
        self.set_counts[self.current_set] = 0
        self.set_colors[self.current_set] = QColor('purple')

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
        """Deselect all layers and emit the deselect_all_requested signal."""
        self.clear_selection()
        self.deselect_all_requested.emit()

    def on_color_changed(self, set_number, color):
        """
        Handle color change for a set.
        
        Update the color in set_colors, update UI, and emit color_changed signal.
        """
        self.set_colors[set_number] = color
        self.update_colors_for_set(set_number, color)
        self.color_changed.emit(set_number, color)

    def update_colors_for_set(self, set_number, color):
        """Update the color of all buttons belonging to a specific set."""
        for button in self.layer_buttons:
            if isinstance(button, NumberedLayerButton):
                if button.text().startswith(f"{set_number}_") or button.text().split('_')[0] == str(set_number):
                    button.set_color(color)

    def resizeEvent(self, event):
        """Handle resize events by updating the size of the splitter handle."""
        super().resizeEvent(event)
        self.handle.updateSize()