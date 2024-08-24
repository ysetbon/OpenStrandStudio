from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QScrollArea, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from functools import partial
import logging
from splitter_handle import SplitterHandle
from numbered_layer_button import NumberedLayerButton
from strand import MaskedStrand

class LayerPanel(QWidget):
    # Custom signals for various events
    new_strand_requested = pyqtSignal(int, QColor)  # Signal when a new strand is requested (set number, color)
    strand_selected = pyqtSignal(int)  # Signal when a strand is selected (index)
    deselect_all_requested = pyqtSignal()  # Signal to deselect all strands
    color_changed = pyqtSignal(int, QColor)  # Signal when a strand's color is changed (set number, new color)
    masked_layer_created = pyqtSignal(int, int)  # Signal when a masked layer is created (layer1 index, layer2 index)
    draw_names_requested = pyqtSignal(bool)  # Signal to toggle drawing of strand names
    masked_mode_entered = pyqtSignal()  # Signal when masked mode is entered
    masked_mode_exited = pyqtSignal()  # Signal when masked mode is exited
    lock_layers_changed = pyqtSignal(set, bool)  # Signal when locked layers change (locked layers set, lock mode state)
    strand_deleted = pyqtSignal(int)  # New signal for strand deletion

    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.last_selected_index = None  # Stores the index of the last selected layer
        
        # Create and add the splitter handle
        self.handle = SplitterHandle(self)
        self.layout.addWidget(self.handle)

        # Create scrollable area for layer buttons
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        self.scroll_area.setWidget(self.scroll_content)
        
        # Create bottom panel for control buttons
        bottom_panel = QWidget()
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(5, 5, 5, 5)
        
        self.draw_names_button = QPushButton("Draw Names")
        self.draw_names_button.setStyleSheet("font-weight: bold; background-color: #E6E6FA;")
        self.draw_names_button.clicked.connect(self.request_draw_names)

        self.lock_layers_button = QPushButton("Lock Layers")
        self.lock_layers_button.setStyleSheet("font-weight: bold; background-color: orange;")
        self.lock_layers_button.setCheckable(True)
        self.lock_layers_button.clicked.connect(self.toggle_lock_mode)

        self.add_new_strand_button = QPushButton("Add New Strand")
        self.add_new_strand_button.setStyleSheet("font-weight: bold; background-color: lightgreen;")
        self.add_new_strand_button.clicked.connect(self.request_new_strand)

        self.delete_strand_button = QPushButton("Delete Strand (beta)")
        self.delete_strand_button.setStyleSheet("font-weight: bold; background-color: #FF6B6B;")
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
        
        # Add scroll area and bottom panel to main layout
        self.layout.addWidget(self.scroll_area)
        self.layout.addWidget(bottom_panel)
        
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
        self.layout.addWidget(self.notification_label)

        # Initialize lock mode variables
        self.lock_mode = False
        self.locked_layers = set()
        self.previously_locked_layers = set()

        # Initialize should_draw_names attribute
        self.should_draw_names = False

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
        if self.masked_mode:
            self.handle_masked_layer_selection(index)
        elif self.lock_mode:
            if self.canvas.current_mode == self.canvas.attach_mode:
                # If in attach mode, check if the strand has a free side
                strand = self.canvas.strands[index]
                if any(not circle for circle in strand.has_circles):
                    for i, button in enumerate(self.layer_buttons):
                        button.setChecked(i == index)
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
            if emit_signal:
                self.strand_selected.emit(index)
            self.last_selected_index = index
        self.update_layer_button_states()

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

    def request_new_strand(self):
        """Request the creation of a new strand."""
        self.start_new_set()
        new_color = QColor('purple')
        new_strand_number = self.current_set
        new_strand_index = self.set_counts[self.current_set] + 1
        new_strand_name = f"{new_strand_number}_{new_strand_index}"
        self.new_strand_requested.emit(new_strand_number, new_color)

    def request_delete_strand(self):
        """Request the deletion of the selected strand."""
        selected_button = next((button for button in self.layer_buttons if button.isChecked()), None)
        if selected_button:
            strand_name = selected_button.text()
            logging.info(f"Selected strand for deletion: {strand_name}")
            
            # Find the corresponding strand in the canvas
            strand_index = next((i for i, s in enumerate(self.canvas.strands) if s.layer_name == strand_name), None)
            
            if strand_index is not None:
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

            # Update the current set to the highest remaining set number
            if self.set_counts:
                self.current_set = max(self.set_counts.keys())
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

    def add_layer_button(self, set_number, count=None):
        logging.info(f"Starting add_layer_button: set_number={set_number}, count={count}")
        # Ensure set_number is an integer
        set_number = int(set_number) if isinstance(set_number, str) else set_number
        
        if set_number not in self.set_counts:
            self.set_counts[set_number] = 0
            logging.info(f"Initialized set count for set {set_number}")
        
        if count is None:
            self.set_counts[set_number] += 1
            count = self.set_counts[set_number]
            logging.info(f"Incremented set count for set {set_number} to {count}")
        else:
            self.set_counts[set_number] = max(self.set_counts[set_number], count)
            logging.info(f"Updated set count for set {set_number} to {self.set_counts[set_number]}")
        
        color = self.set_colors.get(set_number, QColor('purple'))
        button = NumberedLayerButton(f"{set_number}_{count}", count, color)
        button.clicked.connect(partial(self.select_layer, len(self.layer_buttons)))
        button.color_changed.connect(self.on_color_changed)
        logging.info(f"Created new button: {button.text()}")
        
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setAlignment(Qt.AlignHCenter)
        button_layout.addWidget(button)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_layout.insertWidget(0, button_container)
        self.layer_buttons.append(button)
        self.select_layer(len(self.layer_buttons) - 1)
        logging.info(f"Added button to layer_buttons, total buttons: {len(self.layer_buttons)}")
        
        if set_number > self.current_set:
            self.current_set = set_number
            logging.info(f"Updated current_set to {self.current_set}")

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

    def start_new_set(self):
        """Start a new set of strands."""
        self.current_set = max(self.set_counts.keys(), default=0) + 1
        self.set_counts[self.current_set] = 0
        self.set_colors[self.current_set] = QColor('purple')

    def delete_strand(self, index):
        """
        Delete a strand and update the canvas and layer panel.

        Args:
            index (int): The index of the strand to delete.
        """
        if 0 <= index < len(self.canvas.strands):
            strand = self.canvas.strands[index]
            self.canvas.remove_strand(strand)
            self.canvas.update()

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
        for button in self.layer_buttons:
            button.setChecked(False)
            button.update()  # Force a repaint of the button
        if self.lock_mode:
            self.locked_layers.clear()
            self.update_layer_buttons_lock_state()
            self.lock_layers_changed.emit(self.locked_layers, self.lock_mode)
        self.deselect_all_requested.emit()
        self.update()  # Force a repaint of the entire panel

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
                # A strand is attachable if it has any free end (not connected to another strand)
                is_attachable = not all(strand.has_circles)
                button.set_attachable(is_attachable)
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

# End of LayerPanel class