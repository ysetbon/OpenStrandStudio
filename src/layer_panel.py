# src/layer_panel.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea, QLabel,
    QInputDialog, QDialog, QListWidget, QListWidgetItem, QDialogButtonBox,
    QSplitter 
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
import logging
from functools import partial
from splitter_handle import SplitterHandle
from numbered_layer_button import NumberedLayerButton
from strand import MaskedStrand
from group_layers import GroupPanel, GroupLayerManager
from PyQt5.QtWidgets import QWidget, QPushButton  # Example widget imports
from PyQt5.QtGui import QPalette, QColor  # Added QPalette and QColor imports
from PyQt5.QtCore import Qt
from translations import translations
class LayerSelectionDialog(QDialog):
    def __init__(self, layers, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Layers for Group")
        self.layout = QVBoxLayout(self)
        
        self.layer_list = QListWidget()
        for layer in layers:
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


class LayerPanel(QWidget):
    # Custom signals for various events
    new_strand_requested = pyqtSignal(int, QColor)  # Signal when a new strand is requested
    strand_selected = pyqtSignal(int)  # Signal when a strand is selected
    deselect_all_requested = pyqtSignal()  # Signal to deselect all strands
    color_changed = pyqtSignal(int, QColor)  # Signal when a strand's color is changed
    masked_layer_created = pyqtSignal(int, int)  # Signal when a masked layer is created
    draw_names_requested = pyqtSignal(bool)  # Signal to toggle drawing of strand names
    masked_mode_entered = pyqtSignal()  # Signal when masked mode is entered
    masked_mode_exited = pyqtSignal()  # Signal when masked mode is exited
    lock_layers_changed = pyqtSignal(set, bool)  # Signal when locked layers change
    strand_deleted = pyqtSignal(int)  # Signal for strand deletion

    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.parent_window = parent
        self.language_code = parent.language_code if parent else 'en'
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.last_selected_index = None
        self.group_layer_manager = GroupLayerManager(parent=parent, layer_panel=self, canvas=self.canvas)

        # Create left panel (existing layer panel)
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)

        # **Add the splitter handle at the top of the left layout**
        self.handle = SplitterHandle(self)
        self.left_layout.addWidget(self.handle)

        # **Add the refresh button below the splitter handle**
        # Create top panel for the refresh button
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(5, 5, 5, 5)
        top_layout.setAlignment(Qt.AlignLeft)

        # Create the refresh button
        self.refresh_button = StrokeTextButton("⟳")
        self.refresh_button.clicked.connect(self.refresh_layers)

        # Add the refresh button to the top layout
        top_layout.addWidget(self.refresh_button)

        # Add top_panel to left_layout below the splitter handle
        self.left_layout.addWidget(top_panel)

        # Create scrollable area for layer buttons
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        self.scroll_area.setWidget(self.scroll_content)

        # Add the scroll area to the left layout
        self.left_layout.addWidget(self.scroll_area)

        # Create bottom panel for control buttons
        bottom_panel = QWidget()
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(5, 5, 5, 5)

        self.draw_names_button = QPushButton("Draw Names")
        self.draw_names_button.setStyleSheet("font-weight: bold; background-color: #E6E6FA;")
        self.draw_names_button.clicked.connect(self.request_draw_names)

        self.lock_layers_button = QPushButton("Lock Layers")
        self.lock_layers_button.setStyleSheet("font-weight: bold; color: black; background-color: orange;")
        self.lock_layers_button.setCheckable(True)
        self.lock_layers_button.clicked.connect(self.toggle_lock_mode)

        self.add_new_strand_button = QPushButton("Add New Strand")
        self.add_new_strand_button.setStyleSheet("font-weight: bold; background-color: lightgreen;")
        ### Inside LayerPanel __init__ method ###

        self.add_new_strand_button.clicked.connect(self.request_new_strand)

        self.delete_strand_button = QPushButton("Delete Strand (beta)")
        self.delete_strand_button.setStyleSheet("font-weight: bold; color: black; background-color: #FF6B6B;")
        self.delete_strand_button.clicked.connect(self.request_delete_strand)
        self.delete_strand_button.setEnabled(False)

        self.deselect_all_button = QPushButton("Deselect All")
        self.deselect_all_button.setStyleSheet("font-weight: bold; background-color: lightyellow;")
        self.deselect_all_button.clicked.connect(self.deselect_all)

        # Add buttons to bottom panel in the desired order
        bottom_layout.addWidget(self.draw_names_button)
        bottom_layout.addWidget(self.lock_layers_button)
        bottom_layout.addWidget(self.add_new_strand_button)
        bottom_layout.addWidget(self.delete_strand_button)
        bottom_layout.addWidget(self.deselect_all_button)

        # Add scroll area and bottom panel to left layout
        self.left_layout.addWidget(self.scroll_area)
        self.left_layout.addWidget(bottom_panel)

        # Create right panel (group panel)
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)

        # Create GroupLayerManager
        # In layer_panel.py, inside LayerPanel.__init__
        self.group_layer_manager = GroupLayerManager(parent=self, layer_panel=self, canvas=self.canvas)

        # Add the create_group_button and group_panel to right layout
        self.right_layout.addWidget(self.group_layer_manager.create_group_button)
        self.right_layout.addWidget(self.group_layer_manager.group_panel)

        # Create a splitter to allow resizing between left and right panels
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)

        # Add splitter to main layout
        self.layout.addWidget(self.splitter)

        # Initialize variables for managing layers
        self.layer_buttons = []  # List to store layer buttons
        self.current_set = 1  # Current set number
        self.set_counts = {1: 0}  # Dictionary to keep track of counts for each set
        self.set_colors = {1: QColor('purple')}  # Dictionary to store colors for each set

        # Initialize masked mode variables
        self.masked_mode = False
        self.first_masked_layer = None

        # Create notification label
        self.notification_label = QLabel()
        self.notification_label.setAlignment(Qt.AlignCenter)
        self.left_layout.addWidget(self.notification_label)

        # Initialize lock mode variables
        self.lock_mode = False
        self.locked_layers = set()
        self.previously_locked_layers = set()

        # Initialize should_draw_names attribute
        self.should_draw_names = False

        # Initialize groups
        self.groups = {}

        logging.info("LayerPanel initialized")

    def refresh_layers(self):
        """Refresh the drawing of the layers."""
        logging.info("Starting refresh of layer panel")
        # Clear all layer buttons from the layout without deleting them
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                # Remove the widget from the layout but do not set parent to None or delete it
                widget.hide()  # Optionally hide the widget
            else:
                # Handle nested layouts if any
                pass
        
        # Re-add the layer buttons in the original order
        for button in reversed(self.layer_buttons):
            button_container = QWidget()
            button_layout = QHBoxLayout(button_container)
            button_layout.setAlignment(Qt.AlignHCenter)
            button_layout.addWidget(button)
            button_layout.setContentsMargins(0, 0, 0, 0)
            self.scroll_layout.addWidget(button_container)
            button.show()  # Ensure the button is visible
            button_container.show()
        
        logging.info(f"Finished refreshing layer panel. Total buttons: {len(self.layer_buttons)}")
    def translate_ui(self):
        """Update the UI texts to the selected language."""
        _ = translations[self.language_code]
        # Update any UI elements with new translations
        self.draw_names_button.setText(_['draw_names'])
        self.lock_layers_button.setText(_['lock_layers'])
        self.add_new_strand_button.setText(_['add_new_strand'])
        self.delete_strand_button.setText(_['delete_strand'])
        self.deselect_all_button.setText(_['deselect_all'])
        # Update other text elements as needed

        # Update the GroupLayerManager
        if self.group_layer_manager:
            self.group_layer_manager.language_code = self.language_code
            self.group_layer_manager.update_translations()
    def set_theme(self, theme_name):
        """Set the theme of the layer panel without altering child widget styles."""
        if theme_name == "dark":
            palette = self.palette()
            palette.setColor(QPalette.Window, QColor("#2C2C2C"))
            palette.setColor(QPalette.WindowText, QColor("white"))
            self.setPalette(palette)
            self.setAutoFillBackground(True)

            # Update button styles for dark theme
            self.delete_strand_button.setStyleSheet("""
                QPushButton {
                    font-weight: bold;
                    color: black;
                    background-color: #FF6B6B;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #FF4C4C; /* Lighter red on hover */
                }
                QPushButton:pressed {
                    background-color: #FF0000; /* Darker red on click */
                }
            """)

            # Similarly update other buttons if necessary

        elif theme_name == "light":
            palette = self.palette()
            palette.setColor(QPalette.Window, QColor("#FFFFFF"))
            palette.setColor(QPalette.WindowText, QColor("black"))
            self.setPalette(palette)
            self.setAutoFillBackground(True)

            # Update button styles for light theme
            self.delete_strand_button.setStyleSheet("""
                QPushButton {
                    font-weight: bold;
                    color: black;
                    background-color: #FF6B6B;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #FF4C4C; /* Lighter red on hover */
                }
                QPushButton:pressed {
                    background-color: #FF0000; /* Darker red on click */
                }
            """)

            # Similarly update other buttons if necessary

        elif theme_name == "default":
            # Clear any custom palettes to use the default theme
            self.setPalette(self.style().standardPalette())
            self.setAutoFillBackground(False)

            # Reset button styles to default
            self.delete_strand_button.setStyleSheet("""
                QPushButton {
                    font-weight: bold;
                    color: black;
                    background-color: #FF6B6B;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #FF4C4C; /* Lighter red on hover */
                }
                QPushButton:pressed {
                    background-color: #FF0000; /* Darker red on click */
                }
            """)

            # Similarly reset other buttons if necessary

        else:
            # Handle unknown themes by reverting to default
            self.setPalette(self.style().standardPalette())
            self.setAutoFillBackground(False)

            # Reset button styles to default
            self.delete_strand_button.setStyleSheet("""
                QPushButton {
                    font-weight: bold;
                    color: black;
                    background-color: #FF6B6B;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #FF4C4C; /* Lighter red on hover */
                }
                QPushButton:pressed {
                    background-color: #FF0000; /* Darker red on click */
                }
            """)

            # Similarly reset other buttons if necessary

    def update_translations(self):
        _ = translations[self.parent().language_code]

        # Update window title if applicable
        self.setWindowTitle(_['layer_panel_title'])

        # Update button texts
        self.draw_names_button.setText(_['draw_names'])
        self.lock_layers_button.setText(_['lock_layers'])
        self.add_new_strand_button.setText(_['add_new_strand'])
        self.delete_strand_button.setText(_['delete_strand'])
        self.deselect_all_button.setText(_['deselect_all'])

        # Update any labels or UI elements with text
        if self.notification_label.text():
            self.notification_label.setText(_['notification_message'])

        # Update tooltips or other text properties if any
        # Example:
        # self.draw_names_button.setToolTip(_['draw_names_tooltip'])
        # Similarly update other tooltips or accessible descriptions


    def request_draw_names(self):
        self.should_draw_names = not self.should_draw_names
        self.draw_names_requested.emit(self.should_draw_names)


    def create_group(self):
        group_name, ok = QInputDialog.getText(self, "Create Group", "Enter group name:")
        if ok and group_name:
            # Filter out masked layers
            layers = [button.text() for button in self.layer_buttons if not self.is_masked_layer(button)]
            dialog = LayerSelectionDialog(layers, self)
            if dialog.exec_():
                selected_layers = dialog.get_selected_layers()
                for layer in selected_layers:
                    self.group_layer_manager.group_panel.add_layer_to_group(layer, group_name)

    def is_masked_layer(self, button):
        # Check if the button text follows the masked layer naming convention
        index = self.layer_buttons.index(button)
        return isinstance(self.canvas.strands[index], MaskedStrand)


    def add_group(self, group_name, layers):
        group_widget = QWidget()
        group_layout = QVBoxLayout(group_widget)
        group_label = QLabel(group_name)
        group_layout.addWidget(group_label)
        
        for layer in layers:
            layer_label = QLabel(layer)
            group_layout.addWidget(layer_label)
        
        self.group_scroll_layout.addWidget(group_widget)
        self.groups[group_name] = layers
        
        # Update the group display
        self.update_group_display(group_name)

    def update_group_display(self, group_name):
        if group_name in self.groups:
            group_widget = self.group_scroll_layout.itemAt(list(self.groups.keys()).index(group_name)).widget()
            group_layout = group_widget.layout()
            
            # Update the group label
            group_label = group_layout.itemAt(0).widget()
            group_label.setText(f"{group_name} ({len(self.groups[group_name])})")
            
            # Clear existing layer labels
            for i in reversed(range(group_layout.count())):
                if i > 0:  # Keep the group label
                    group_layout.itemAt(i).widget().setParent(None)
            
            # Add updated layer labels
            for layer in self.groups[group_name]:
                layer_label = QLabel(layer)
                group_layout.addWidget(layer_label)

    def request_draw_names(self):
        """Toggle the drawing of strand names and emit the corresponding signal."""
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
        """Enter masked mode, update UI, and emit relevant signal."""
        self.masked_mode = True
        self.first_masked_layer = None
        self.last_selected_index = self.get_selected_layer()
        for button in self.layer_buttons:
            button.set_masked_mode(True)
            button.setChecked(False)
        self.masked_mode_entered.emit()

    def exit_masked_mode(self):
        """Exit masked mode, update UI, and emit relevant signal."""
        self.masked_mode = False
        self.first_masked_layer = None
        for button in self.layer_buttons:
            button.set_masked_mode(False)
        self.masked_mode_exited.emit()
        self.notification_label.clear()

    def toggle_lock_mode(self):
        """Toggle lock mode on/off and update UI accordingly."""
        self.lock_mode = self.lock_layers_button.isChecked()
        if self.lock_mode:
            self.lock_layers_button.setText("Exit Lock Mode")
            self.notification_label.setText("Select layers to lock/unlock")
            self.locked_layers = self.previously_locked_layers.copy()
            self.deselect_all_button.setText("Clear All Locks")
        else:
            self.lock_layers_button.setText("Lock Layers")
            self.notification_label.setText("Exited lock mode")
            self.previously_locked_layers = self.locked_layers.copy()
            self.locked_layers.clear()
            self.deselect_all_button.setText("Deselect All")

        self.update_layer_buttons_lock_state()
        self.lock_layers_changed.emit(self.locked_layers, self.lock_mode)

    def update_layer_buttons_lock_state(self):
        """Update the lock state and attachability of all layer buttons."""
        for i, button in enumerate(self.layer_buttons):
            if isinstance(button, NumberedLayerButton):
                button.set_locked(i in self.locked_layers)
                button.set_selectable(self.lock_mode)
                
                # Set attachability based on whether the strand has free sides
                if i < len(self.canvas.strands):
                    strand = self.canvas.strands[i]
                    button.set_attachable(any(not circle for circle in strand.has_circles))
                else:
                    button.set_attachable(False)

    def select_layer(self, index, emit_signal=True):
        """
        Handle layer selection based on current mode (normal, masked, or lock).
        
        Args:
            index (int): The index of the layer to select.
            emit_signal (bool): Whether to emit the selection signal.
        """
        # Deselect all strands first
        for strand in self.canvas.strands:
            strand.is_selected = False

        if self.masked_mode:
            self.handle_masked_layer_selection(index)
        elif self.lock_mode:
            if self.canvas.current_mode == self.canvas.attach_mode:
                # If in attach mode, check if the strand has a free side
                strand = self.canvas.strands[index]
                if any(not circle for circle in strand.has_circles):
                    for i, button in enumerate(self.layer_buttons):
                        button.setChecked(i == index)
                    # Set the selected strand's is_selected to True
                    strand.is_selected = True
                    if emit_signal:
                        self.strand_selected.emit(index)
                    self.last_selected_index = index
            else:
                # Toggle lock state only if not in attach mode
                if index in self.locked_layers:
                    self.locked_layers.remove(index)
                else:
                    self.locked_layers.add(index)
                self.update_layer_buttons_lock_state()
                self.lock_layers_changed.emit(self.locked_layers, self.lock_mode)
        else:
            for i, button in enumerate(self.layer_buttons):
                button.setChecked(i == index)
            # Set the selected strand's is_selected to True
            if 0 <= index < len(self.canvas.strands):
                selected_strand = self.canvas.strands[index]
                selected_strand.is_selected = True
            if emit_signal:
                self.strand_selected.emit(index)
            self.last_selected_index = index

        # Ensure the selected strand is updated in the canvas
        if 0 <= index < len(self.canvas.strands):
            self.canvas.selected_strand = self.canvas.strands[index]
            self.canvas.selected_strand_index = index
        else:
            self.canvas.selected_strand = None
            self.canvas.selected_strand_index = None

        # Update layer button states and redraw the canvas
        self.update_layer_button_states()
        self.canvas.update()

        if not self.masked_mode and not self.lock_mode:
            for i, button in enumerate(self.layer_buttons):
                button.setChecked(i == index)
            # Set the selected strand's is_selected to True
            if 0 <= index < len(self.canvas.strands):
                selected_strand = self.canvas.strands[index]
                selected_strand.is_selected = True
            if emit_signal:
                self.strand_selected.emit(index)
            self.last_selected_index = index

            # Switch to attach mode
            if self.parent_window:
                self.parent_window.set_attach_mode()

    def handle_masked_layer_selection(self, index):
        """Handle the selection of layers in masked mode."""
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
        """Create a new masked layer from two selected layers."""
        masked_layer_name = f"{self.layer_buttons[layer1].text()}_{self.layer_buttons[layer2].text()}"
        if any(button.text() == masked_layer_name for button in self.layer_buttons):
            self.notification_label.setText(f"Masked layer {masked_layer_name} already exists")
            return

        self.masked_layer_created.emit(layer1, layer2)
        self.notification_label.setText(f"Created new masked layer: {masked_layer_name}")

    def add_masked_layer_button(self, layer1, layer2):
        """Add a new button for a masked layer."""
        button = NumberedLayerButton(f"{self.layer_buttons[layer1].text()}_{self.layer_buttons[layer2].text()}", 0)
        button.set_color(self.layer_buttons[layer1].color)
        button.set_border_color(self.layer_buttons[layer2].color)
        button.clicked.connect(partial(self.select_layer, len(self.layer_buttons)))
        button.color_changed.connect(self.on_color_changed)
        self.scroll_layout.insertWidget(0, button)
        self.layer_buttons.append(button)
        return button

    ### Inside LayerPanel class ###

    def request_new_strand(self):
        logging.info("Add New Strand button clicked.")
        # Start a new set or use an existing one
        self.start_new_set()
        # Call the canvas method to start drawing a new strand
        self.canvas.start_new_strand_mode(self.current_set)
        logging.info(f"Requested new strand for set {self.current_set}")

    def request_delete_strand(self):
        """Request the deletion of the selected strand."""
        selected_button = next((button for button in self.layer_buttons if button.isChecked()), None)
        if selected_button:
            strand_name = selected_button.text()
            logging.info(f"Selected strand for deletion: {strand_name}")
            
            # Find the corresponding strand in the canvas
            strand_index = next((i for i, s in enumerate(self.canvas.strands) if s.layer_name == strand_name), None)
            
            if strand_index is not None:
                strand = self.canvas.strands[strand_index]
                if isinstance(strand, MaskedStrand):
                    # Delete masked layer
                    if self.canvas.delete_masked_layer(strand):
                        self.remove_layer_button(strand_index)
                else:
                    # Delete regular strand
                    self.strand_deleted.emit(strand_index)
            else:
                logging.warning(f"Strand {strand_name} not found in canvas strands")
        else:
            logging.warning("No strand selected for deletion")

    def remove_layer_button(self, index):
        """Remove a layer button at the specified index."""
        if 0 <= index < len(self.layer_buttons):
            button = self.layer_buttons.pop(index)
            button.setParent(None)
            button.deleteLater()
            self.scroll_layout.removeWidget(button)

    def update_masked_layers(self, deleted_set_number, strands_removed):
        logging.info(f"Updating masked layers for set {deleted_set_number}")
        buttons_to_remove = []
        for i, button in enumerate(self.layer_buttons):
            button_text = button.text()
            parts = button_text.split('_')
            if len(parts) == 4:  # This is a masked layer
                should_remove = False
                # Check if the mask involves the deleted set number
                if str(deleted_set_number) in [parts[0], parts[2]]:
                    should_remove = True
                # Check if the mask involves any of the removed strands
                for strand_index in strands_removed:
                    if strand_index < len(self.canvas.strands):
                        removed_strand = self.canvas.strands[strand_index]
                        removed_strand_name = removed_strand.layer_name
                        # Check if the removed strand is at the start or end of the mask name
                        if button_text.startswith(removed_strand_name) or button_text.endswith(removed_strand_name):
                            should_remove = True
                            break
                if should_remove:
                    buttons_to_remove.append(i)
                    logging.info(f"Marking masked layer for removal: {button_text}")

        # Remove the marked buttons
        for index in sorted(buttons_to_remove, reverse=True):
            button = self.layer_buttons.pop(index)
            button.setParent(None)
            button.deleteLater()
            self.scroll_layout.removeWidget(button)
            logging.info(f"Removed masked layer button: {button.text()}")

        logging.info("Finished updating masked layers")

    def update_after_deletion(self, deleted_set_number, strands_removed, is_main_strand, renumber=False):
        logging.info(f"Starting update_after_deletion: deleted_set_number={deleted_set_number}, strands_removed={strands_removed}, is_main_strand={is_main_strand}, renumber={renumber}")

        # Remove the corresponding buttons
        for index in sorted(strands_removed, reverse=True):
            if 0 <= index < len(self.layer_buttons):
                button = self.layer_buttons.pop(index)
                button.setParent(None)
                button.deleteLater()
                self.scroll_layout.removeWidget(button)
                logging.info(f"Removed button at index {index}")

        if is_main_strand:
            # Update set counts and colors
            if deleted_set_number in self.set_counts:
                del self.set_counts[deleted_set_number]
                logging.info(f"Deleted set count for set {deleted_set_number}")
            if deleted_set_number in self.set_colors:
                del self.set_colors[deleted_set_number]
                logging.info(f"Deleted set color for set {deleted_set_number}")

            # Update the current set to the highest remaining set number among main strands
            existing_sets = set(
                strand.set_number
                for strand in self.canvas.strands
                if hasattr(strand, 'set_number') and not isinstance(strand, MaskedStrand)
            )
            if existing_sets:
                self.current_set = max(existing_sets)
            else:
                self.current_set = 0
            logging.info(f"Updated current_set to {self.current_set}")


        # Update masked layers
        self.update_masked_layers(deleted_set_number, strands_removed)

        # Clear selection if the deleted strand was selected
        selected_layer = self.get_selected_layer()
        if selected_layer is not None and selected_layer in strands_removed:
            self.clear_selection()
            logging.info("Cleared selection due to deleted strand")

        self.update_layer_button_states()
        self.update_attachable_states()
        
        # Refresh the entire panel to ensure consistency
        self.refresh()
        
        logging.info("Finished update_after_deletion")

    def renumber_sets(self):
        new_set_numbers = {}
        new_count = 1
        for button in self.layer_buttons:
            old_set_number = int(button.text().split('_')[0])
            if old_set_number not in new_set_numbers:
                new_set_numbers[old_set_number] = new_count
                new_count += 1
            new_set_number = new_set_numbers[old_set_number]
            button.setText(f"{new_set_number}_{button.text().split('_')[1]}")
        
        # Update set_counts and set_colors
        self.set_counts = {new_set_numbers[k]: v for k, v in self.set_counts.items() if k in new_set_numbers}
        self.set_colors = {new_set_numbers[k]: v for k, v in self.set_colors.items() if k in new_set_numbers}
        
        logging.info(f"Renumbered sets: {new_set_numbers}")


    def update_button_numbering_for_set(self, set_number):
        logging.info(f"Starting update_button_numbering_for_set: set_number={set_number}")
        for button in self.layer_buttons:
            button_text = button.text()
            parts = button_text.split('_')
            if parts[0] == str(set_number):
                if len(parts) == 2:  # Regular strand
                    # Keep the original number, don't increment
                    new_text = button_text
                    logging.info(f"Kept original button text: {new_text}")
                else:  # Masked layer
                    logging.info(f"Skipping renumbering for masked layer: {button_text}")
        logging.info("Finished update_button_numbering_for_set")
    

    def update_layer_buttons_after_deletion(self, deleted_set_number, indices_to_remove):
        # Remove buttons for deleted strands
        for index in sorted(indices_to_remove, reverse=True):
            if 0 <= index < len(self.layer_buttons):
                button = self.layer_buttons.pop(index)
                button.setParent(None)
                button.deleteLater()
                self.scroll_layout.removeWidget(button)

        # Update remaining buttons
        for i, button in enumerate(self.layer_buttons):
            parts = button.text().split('_')
            set_number = int(parts[0])
            
            if set_number == deleted_set_number:
                # Update the numbering for the affected set
                new_number = i + 1 - sum(1 for b in self.layer_buttons[:i] if int(b.text().split('_')[0]) != deleted_set_number)
                new_text = f"{set_number}_{new_number}"
                button.setText(new_text)
            elif set_number > deleted_set_number:
                # Decrement set numbers greater than the deleted set
                new_set_number = set_number - 1
                new_text = f"{new_set_number}_{parts[1]}"
                button.setText(new_text)
                button.set_color(self.set_colors.get(new_set_number, QColor('purple')))

        self.update_layer_button_states()

    def get_next_available_set_number(self):
        existing_set_numbers = set(
            strand.set_number
            for strand in self.canvas.strands
            if hasattr(strand, 'set_number') and not isinstance(strand, MaskedStrand)
        )
        max_set_number = max(existing_set_numbers, default=0)
        return max_set_number + 1

    def add_layer_button(self, set_number, count=None):
        """Add a new button for a layer."""
        logging.info(f"Starting add_layer_button: set_number={set_number}, count={count}")

        # Ensure set_number is an integer
        if not isinstance(set_number, int):
            try:
                set_number_int = int(set_number)
            except ValueError:
                logging.warning(f"Invalid set_number '{set_number}' provided. Using next available integer.")
                set_number_int = self.get_next_available_set_number()
        else:
            set_number_int = set_number

        # Initialize or update set count
        if set_number_int not in self.set_counts:
            self.set_counts[set_number_int] = 0
            logging.info(f"Initialized set count for set {set_number_int}")

        if count is None:
            self.set_counts[set_number_int] += 1
            count = self.set_counts[set_number_int]
            logging.info(f"Incremented set count for set {set_number_int} to {count}")
        else:
            self.set_counts[set_number_int] = max(self.set_counts[set_number_int], count)
            logging.info(f"Updated set count for set {set_number_int} to {self.set_counts[set_number_int]}")

        # Get the color for the set
        color = self.set_colors.get(set_number_int, QColor('purple'))

        # Create the layer name using set_number_int and count
        layer_name = f"{set_number_int}_{count}"

        # Create the new layer button
        button = NumberedLayerButton(layer_name, count, color)
        button.clicked.connect(partial(self.select_layer, len(self.layer_buttons)))
        button.color_changed.connect(self.on_color_changed)
        logging.info(f"Created new button: {button.text()}")

        # Set up the layout for the button
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setAlignment(Qt.AlignHCenter)
        button_layout.addWidget(button)
        button_layout.setContentsMargins(0, 0, 0, 0)

        # Insert the button at the top of the scroll area
        self.scroll_layout.insertWidget(0, button_container)
        self.layer_buttons.append(button)
        
        # Select the newly created layer and ensure it's selected in the canvas
        new_index = len(self.layer_buttons) - 1
        self.select_layer(new_index, emit_signal=True)
        
        # Ensure the canvas also knows about the selection
        if new_index < len(self.canvas.strands):
            self.canvas.selected_strand = self.canvas.strands[new_index]
            self.canvas.selected_strand_index = new_index
            self.canvas.update()
        
        logging.info(f"Added and selected new button at index {new_index}")

        # Update attachable states after adding a new button
        self.update_layer_button_states()
        logging.info("Finished add_layer_button")

    def update_layer_button_states(self):
        """Update the states of all layer buttons."""
        for i, button in enumerate(self.layer_buttons):
            if i < len(self.canvas.strands):
                strand = self.canvas.strands[i]
                # A strand is attachable if it's a main strand (x_1) or has any free end
                is_main_strand = strand.layer_name.split('_')[1] == '1'
                is_attachable = is_main_strand or any(not circle for circle in strand.has_circles)
                button.set_attachable(is_attachable)
            else:
                button.set_attachable(False)
        
        selected_index = self.get_selected_layer()
        if selected_index is not None and selected_index < len(self.layer_buttons):
            selected_strand = self.canvas.strands[selected_index]
            is_main_strand = selected_strand.layer_name.split('_')[1] == '1'
            self.delete_strand_button.setEnabled(is_main_strand or self.layer_buttons[selected_index].attachable)
        else:
            self.delete_strand_button.setEnabled(False)

    def on_strand_attached(self):
        """Called when a strand is attached to another strand."""
        self.update_layer_button_states()

    ### Inside LayerPanel class ###

    def start_new_set(self):
        """Start a new set of strands."""
        # Get all existing set numbers from the canvas strands, excluding masked strands
        existing_sets = set(
            strand.set_number
            for strand in self.canvas.strands
            if hasattr(strand, 'set_number') and not isinstance(strand, MaskedStrand)
        )
        logging.info(f"Existing sets: {existing_sets}")
        # Determine the next available set number
        self.current_set = max(existing_sets, default=0) + 1
        # Initialize count and color for the new set
        self.set_counts[self.current_set] = 0
        self.set_colors[self.current_set] = QColor('purple')
        logging.info(f"Starting new set. Assigned set number: {self.current_set}")

    def delete_strand(self, index):
        """
        Delete a strand and update the canvas and layer panel.

        Args:
            index (int): The index of the strand to delete.
        """
        if 0 <= index < len(self.canvas.strands):
            strand = self.canvas.strands[index]
            set_number = strand.set_number
            is_main_strand = strand.layer_name.split('_')[1] == '1'

            # Remove the strand from the canvas
            self.canvas.remove_strand(strand)
            self.canvas.update()

            # Remove the corresponding layer button
            if index < len(self.layer_buttons):
                button = self.layer_buttons.pop(index)
                button.setParent(None)
                button.deleteLater()
                logging.info(f"Removed layer button for strand: {strand.layer_name}")

            # Update set_counts
            if set_number in self.set_counts:
                self.set_counts[set_number] -= 1
                if self.set_counts[set_number] <= 0:
                    del self.set_counts[set_number]
                    logging.info(f"Removed set_count entry for set {set_number}")

            # Remove set color if no strands are left in the set
            if not any(s.set_number == set_number for s in self.canvas.strands):
                if set_number in self.set_colors:
                    del self.set_colors[set_number]
                    logging.info(f"Removed set_color entry for set {set_number}")

            # Update current_set to the lowest available set number
            existing_sets = set(
                strand.set_number for strand in self.canvas.strands if hasattr(strand, 'set_number')
            )
            if existing_sets:
                self.current_set = min(existing_sets)
            else:
                self.current_set = 1
            logging.info(f"Updated current_set to {self.current_set}")

            # Update layer button states
            self.update_layer_button_states()
        else:
            logging.warning(f"Invalid index for deleting strand: {index}")

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
        """Deselect all layers and strands."""
        # Deselect all layer buttons
        for button in self.layer_buttons:
            button.setChecked(False)

        # Deselect all strands in the canvas
        for strand in self.canvas.strands:
            strand.is_selected = False

        # Update the canvas to reflect changes
        self.canvas.selected_strand = None
        self.canvas.selected_strand_index = None
        self.canvas.update()

    def on_color_changed(self, set_number, color):
        """Handle color change for a set of strands."""
        logging.info(f"Color change requested for set {set_number}")
        self.set_colors[set_number] = color
        self.canvas.update_color_for_set(set_number, color)
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

    def on_strand_created(self, strand):
        """Handle the creation of a new strand."""
        self.add_layer_button(strand.set_number)
        self.update_layer_button_states()

    def on_strands_deleted(self, indices):
        """Handle the deletion of multiple strands from the canvas."""
        for index in sorted(indices, reverse=True):
            self.remove_layer_button(index)
        self.update_layer_button_states()
    def update_layer_names(self, affected_set_number=None):
        logging.info(f"Starting update_layer_names: affected_set_number={affected_set_number}")
        for i, button in enumerate(self.layer_buttons):
            if i < len(self.canvas.strands):
                strand = self.canvas.strands[i]
                if affected_set_number is None or strand.set_number == affected_set_number:
                    # Keep the original layer name
                    button.setText(strand.layer_name)
                    logging.info(f"Kept original layer name for strand {i}: {button.text()}")
        self.update_layer_button_states()
        logging.info("Finished update_layer_names")

    def refresh(self):
        logging.info("Starting refresh of layer panel")
        
        # Remove all existing buttons
        for button in self.layer_buttons:
            button.setParent(None)
            button.deleteLater()
        self.layer_buttons.clear()
        
        # Reset set counts
        self.set_counts = {}
        
        # Add buttons for all current strands
        for i, strand in enumerate(self.canvas.strands):
            set_number = strand.set_number
            
            if set_number not in self.set_counts:
                self.set_counts[set_number] = 0
            self.set_counts[set_number] += 1
            
            # Use the strand's actual color
            strand_color = strand.color if hasattr(strand, 'color') else self.canvas.strand_colors.get(set_number, QColor('purple'))
            
            button = NumberedLayerButton(strand.layer_name, self.set_counts[set_number], strand_color)
            button.clicked.connect(partial(self.select_layer, len(self.layer_buttons)))
            button.color_changed.connect(self.on_color_changed)
            
            if isinstance(strand, MaskedStrand):
                button.set_border_color(strand.second_selected_strand.color)
                # Ensure masked strand color is correct
                if strand.first_selected_strand:
                    button.set_color(strand.first_selected_strand.color)
            
            self.scroll_layout.insertWidget(0, button)
            self.layer_buttons.append(button)
            
            logging.info(f"Added button for strand: {strand.layer_name} with color {strand_color.name()}")
        
        # Update button states
        self.update_layer_button_states()
        
        # Ensure the correct button is selected
        if self.canvas.selected_strand_index is not None and self.canvas.selected_strand_index < len(self.layer_buttons):
            self.select_layer(self.canvas.selected_strand_index, emit_signal=False)
        else:
            self.clear_selection()
        
        # Update the current set
        self.current_set = max(self.set_counts.keys(), default=0)
        
        # Refresh the GroupLayerManager
        self.group_layer_manager.refresh()
        
        logging.info(f"Finished refreshing layer panel. Total buttons: {len(self.layer_buttons)}")

    def update_masked_strand_color(self, layer_name, color):
        for button in self.layer_buttons:
            if button.text() == layer_name:
                button.set_color(color)
                logging.info(f"Updated color for masked strand button: {layer_name} to {color.name()}")
                break    
    def get_layer_button(self, index):
        """Get the layer button at the specified index."""
        if 0 <= index < len(self.layer_buttons):
            return self.layer_buttons[index]
        return None

    def set_canvas(self, canvas):
        """Set the canvas associated with this layer panel."""
        self.canvas = canvas
        self.refresh()

    def on_layer_order_changed(self, new_order):
        """Handle changes in the order of layers."""
        reordered_buttons = [self.layer_buttons[i] for i in new_order]
        self.layer_buttons = reordered_buttons
        
        for i, button in enumerate(self.layer_buttons):
            self.scroll_layout.insertWidget(i, button)
        
        self.update_layer_button_states()

    def update_attachable_states(self):
        """Update the attachable state of all layer buttons based on strand connections."""
        for i, button in enumerate(self.layer_buttons):
            if i < len(self.canvas.strands):
                strand = self.canvas.strands[i]
                strand.update_attachable()  # Update the strand's attachable property
                button.set_attachable(strand.attachable)
            else:
                button.set_attachable(False)

    def update_layer_button_states(self):
        """Update the states of all layer buttons."""
        for i, button in enumerate(self.layer_buttons):
            is_attachable = i < len(self.canvas.strands) and any(not circle for circle in self.canvas.strands[i].has_circles)
            button.set_attachable(is_attachable)
        
        selected_index = self.get_selected_layer()
        if selected_index is not None and selected_index < len(self.layer_buttons):
            self.delete_strand_button.setEnabled(self.layer_buttons[selected_index].attachable)
        else:
            self.delete_strand_button.setEnabled(False)


           # Update tooltips or other text properties if any
           # Example:
           # self.draw_names_button.setToolTip(_['draw_names_tooltip'])
           # Similarly update other tooltips or accessible descriptions
        # Update any other UI elements as needed
# End of LayerPanel class
from PyQt5.QtGui import QPainter, QPainterPath, QPen, QFontMetrics
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt

class StrokeTextButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(40, 40)
        self.updateStyleSheet()

    def updateStyleSheet(self):
         self.setStyleSheet(f"""
            QPushButton {{
                font-weight: bold;
                font-size: 30px;
                color: black;
                background-color: #4d9958;
                border: none;
                padding: 0px;
                padding-top: -8px;  /* Move text up by 2 pixels */
                border-radius: 20px;
                text-align: center;
                line-height: 38px;  /* Adjust line height to compensate for padding */
            }}
            QPushButton:hover {{
                background-color: #67c975;
            }}
            QPushButton:pressed {{
                background-color: #2a522f;
            }}
        """)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        font = self.font()
        font.setBold(True)
        painter.setFont(font)

        text = self.text()
        text_rect = self.rect()
        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(text)
        text_height = fm.height()
        x = (text_rect.width() - text_width) / 2
        y = (text_rect.height() + text_height) / 2 - fm.descent()

        path = QPainterPath()
        path.addText(x, y-2, font, text)

        pen = QPen(QColor('#e6fae9'), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.strokePath(path, pen)
        painter.fillPath(path, QColor('black'))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateStyleSheet()

    def on_canvas_strand_selected(self, index):
        """Update layer selection based on canvas strand selection."""
        # Deselect all layer buttons
        for button in self.layer_buttons:
            button.setChecked(False)

        # Select the corresponding layer button
        if 0 <= index < len(self.layer_buttons):
            self.layer_buttons[index].setChecked(True)
        # Update the last selected index
        self.last_selected_index = index
        # Update the layer button states
        self.update_layer_button_states()