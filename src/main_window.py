from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QSplitter, QFileDialog
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QIcon, QColor, QImage, QPainter
import os

from strand_drawing_canvas import StrandDrawingCanvas
from layer_panel import LayerPanel
from strand import Strand, AttachedStrand, MaskedStrand
from save_load_manager import save_strands, load_strands, apply_loaded_strands
from mask_mode import MaskMode
import logging
from group_layers import GroupLayerManager, StrandAngleEditDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenStrand Studio")
        self.setMinimumSize(900, 900)
        self.canvas = StrandDrawingCanvas()
        self.layer_panel = LayerPanel(self.canvas)
        # The GroupLayerManager is now initialized inside LayerPanel, so we don't need to do it here
        self.setup_ui()
        self.setup_connections()
        self.current_mode = "attach"
        self.set_attach_mode()
        self.selected_strand = None

        self.group_layer_manager = GroupLayerManager(self.layer_panel, self.canvas)
        self.layer_panel.group_layer_manager.set_canvas(self.canvas)
        self.canvas.set_group_layer_manager(self.layer_panel.group_layer_manager)
        logging.info(f"Canvas set in MainWindow: {self.canvas}")

        # Connect group operation signal
        self.layer_panel.group_layer_manager.group_panel.group_operation.connect(
            self.layer_panel.group_layer_manager.on_group_operation
        )
    def setup_ui(self):
        icon_path = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\box_stitch.ico"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        button_layout = QHBoxLayout()
        self.attach_button = QPushButton("Attach Mode")
        self.move_button = QPushButton("Move Mode")
        self.toggle_grid_button = QPushButton("Toggle Grid")
        self.angle_adjust_button = QPushButton("Angle Adjust Mode")
        self.save_button = QPushButton("Save")
        self.load_button = QPushButton("Load")
        self.save_image_button = QPushButton("Save as Image")  # New button
        self.select_strand_button = QPushButton("Select Strand")
        self.mask_button = QPushButton("Mask Mode")
        button_layout.addWidget(self.mask_button)
        button_layout.addWidget(self.select_strand_button)
        button_layout.addWidget(self.attach_button)
        button_layout.addWidget(self.move_button)
        button_layout.addWidget(self.toggle_grid_button)
        button_layout.addWidget(self.angle_adjust_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.save_image_button)  # Add new button to layout

        self.canvas = StrandDrawingCanvas()
        self.layer_panel = LayerPanel(self.canvas)
        
        self.setup_button_styles()

        self.splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addLayout(button_layout)
        left_layout.addWidget(self.canvas)
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(self.layer_panel)

        self.splitter.setHandleWidth(0)
        main_layout.addWidget(self.splitter)

        left_widget.setMinimumWidth(200)
        self.layer_panel.setMinimumWidth(100)


        # Connect group operation signal
        self.layer_panel.group_layer_manager.group_panel.group_operation.connect(
            self.layer_panel.group_layer_manager.on_group_operation
        )

    def setup_button_styles(self):
        self.layer_panel.lock_layers_button.setStyleSheet("""
            QPushButton {
                background-color: orange;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: darkorange;
            }
            QPushButton:pressed {
                background-color: #FF8C00;
            }
        """)

        self.layer_panel.draw_names_button.setStyleSheet("""
            QPushButton {
                background-color: #E6E6FA;
                color: black;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D8BFD8;
            }
            QPushButton:pressed {
                background-color: #DDA0DD;
            }
        """)

        self.layer_panel.add_new_strand_button.setStyleSheet("""
            QPushButton {
                background-color: lightgreen;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #90EE90;
            }
            QPushButton:pressed {
                background-color: #32CD32;
            }
        """)

        self.layer_panel.deselect_all_button.setStyleSheet("""
            QPushButton {
                background-color: lightyellow;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFFFE0;
            }
            QPushButton:pressed {
                background-color: #FAFAD2;
            }
        """)

        # Add style for the new save image button
        self.save_image_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
        """)

    def setup_connections(self):
        # Layer panel handle connections
        self.layer_panel.handle.mousePressEvent = self.start_resize
        self.layer_panel.handle.mouseMoveEvent = self.do_resize
        self.layer_panel.handle.mouseReleaseEvent = self.stop_resize

        # Set layer panel for canvas
        self.canvas.set_layer_panel(self.layer_panel)

        # Layer panel connections
        self.layer_panel.new_strand_requested.connect(self.create_new_strand)
        self.layer_panel.strand_selected.connect(lambda idx: self.select_strand(idx, emit_signal=False))
        self.layer_panel.deselect_all_requested.connect(self.canvas.deselect_all_strands)
        self.layer_panel.color_changed.connect(self.handle_color_change)
        self.layer_panel.masked_layer_created.connect(self.create_masked_layer)
        self.layer_panel.masked_mode_entered.connect(self.canvas.deselect_all_strands)
        self.layer_panel.masked_mode_exited.connect(self.restore_selection)
        self.layer_panel.lock_layers_changed.connect(self.update_locked_layers)
        self.layer_panel.strand_deleted.connect(self.delete_strand)

        # Button connections
        self.attach_button.clicked.connect(self.set_attach_mode)
        self.move_button.clicked.connect(self.set_move_mode)
        self.toggle_grid_button.clicked.connect(self.canvas.toggle_grid)
        self.angle_adjust_button.clicked.connect(self.toggle_angle_adjust_mode)
        self.save_button.clicked.connect(self.save_project)
        self.load_button.clicked.connect(self.load_project)
        self.save_image_button.clicked.connect(self.save_canvas_as_image)
        self.select_strand_button.clicked.connect(self.set_select_mode)
        self.mask_button.clicked.connect(self.set_mask_mode)

        # Canvas connections
        self.canvas.strand_selected.connect(self.handle_canvas_strand_selection)

        # Disconnect any existing connections for mask_created
        try:
            self.canvas.mask_created.disconnect(self.handle_mask_created)
        except TypeError:
            # This exception will be raised if there was no connection, which is fine
            pass

        # Reconnect mask_created signal
        self.canvas.mask_created.connect(self.handle_mask_created)

        # Connect the canvas to the group layer manager
        self.layer_panel.group_layer_manager.canvas = self.canvas

        # Connect group operation signal
        self.layer_panel.group_layer_manager.group_panel.group_operation.connect(
            self.layer_panel.group_layer_manager.on_group_operation
        )

    def set_mask_mode(self):
        self.update_mode("mask")
        self.canvas.set_mode("mask")

    def handle_mask_created(self, strand1, strand2):
        logging.info(f"Received mask_created signal for {strand1.layer_name} and {strand2.layer_name}")

        # Verify that both strands exist in the canvas
        if strand1 not in self.canvas.strands or strand2 not in self.canvas.strands:
            logging.error("One or both strands are not in the canvas. Cannot create mask.")
            return

        # Check if a mask already exists for these strands
        if self.canvas.mask_exists(strand1, strand2):
            logging.info(f"Mask already exists for {strand1.layer_name} and {strand2.layer_name}. Skipping creation.")
            return

        # Create the masked layer
        masked_strand = MaskedStrand(strand1, strand2)
        self.canvas.add_strand(masked_strand)

        # Update the groups
        self.layer_panel.group_layer_manager.update_groups_with_new_mask(masked_strand)

        # Update UI or perform any other necessary actions
        self.update_mode(self.current_mode)  # Refresh the current mode
        
        # Update the layer panel
        if self.layer_panel:
            self.layer_panel.refresh()

        logging.info(f"Processed mask creation for {strand1.layer_name} and {strand2.layer_name}")

        # Note: The actual creation of the masked strand is now handled in the StrandDrawingCanvas class


    def save_canvas_as_image(self):
            """Save the entire canvas as a PNG image with transparent background, including all layers and masks."""
            filename, _ = QFileDialog.getSaveFileName(self, "Save Canvas as Image", "", "PNG Files (*.png)")
            if filename:
                # Ensure the filename ends with .png
                if not filename.lower().endswith('.png'):
                    filename += '.png'
                
                # Get the size of the canvas
                canvas_size = self.canvas.size()
                
                # Create a transparent image of the canvas size
                image = QImage(canvas_size, QImage.Format_ARGB32)
                image.fill(Qt.transparent)
                
                # Create a painter for the image
                painter = QPainter(image)
                painter.setRenderHint(QPainter.Antialiasing)
                
                # Custom painting method to draw all strands and masks
                def paint_canvas(painter):
                    # Draw the grid if it's visible
                    if self.canvas.show_grid:
                        self.canvas.draw_grid(painter)
                    
                    # Draw all strands in their current order
                    for strand in self.canvas.strands:
                        if strand == self.canvas.selected_strand:
                            self.canvas.draw_highlighted_strand(painter, strand)
                        else:
                            strand.draw(painter)
                    
                    # Draw the current strand if it exists
                    if self.canvas.current_strand:
                        self.canvas.current_strand.draw(painter)
                    
                    # Draw strand names if enabled
                    if self.canvas.should_draw_names:
                        for strand in self.canvas.strands:
                            self.canvas.draw_strand_label(painter, strand)
                
                # Perform the custom painting
                paint_canvas(painter)
                
                # End painting
                painter.end()
                
                # Save the image
                image.save(filename)
                logging.info(f"Full canvas saved as image: {filename}")

    def handle_color_change(self, set_number, color):
        self.canvas.update_color_for_set(set_number, color)
        self.layer_panel.update_colors_for_set(set_number, color)

    def create_masked_layer(self, layer1_index, layer2_index):
        logging.info(f"Creating masked layer for layers at indices {layer1_index} and {layer2_index}")
        layer1 = self.canvas.strands[layer1_index]
        layer2 = self.canvas.strands[layer2_index]
        
        masked_strand = MaskedStrand(layer1, layer2)
        self.canvas.add_strand(masked_strand)
        
        button = self.layer_panel.add_masked_layer_button(layer1_index, layer2_index)
        button.color_changed.connect(self.handle_color_change)
        
        logging.info(f"Created masked layer: {masked_strand.layer_name}")
        
        # Update the groups with the new masked strand
        logging.info("Updating groups with new masked strand")
        self.layer_panel.group_layer_manager.update_groups_with_new_mask(masked_strand)
        
        self.canvas.update()
        self.update_mode(self.current_mode)

        logging.info("Finished creating masked layer and updating groups")

    def restore_selection(self):
        if self.layer_panel.last_selected_index is not None:
            self.select_strand(self.layer_panel.last_selected_index)

    def set_select_mode(self):
        self.update_mode("select")
        self.canvas.set_mode("select")
        
    def update_mode(self, mode):
        if self.current_mode == "select" and mode != "select":
            self.canvas.exit_select_mode()
        
        self.current_mode = mode
        self.canvas.set_mode(mode)
        
        if mode == "select":
            self.attach_button.setEnabled(True)
            self.move_button.setEnabled(True)
            self.angle_adjust_button.setEnabled(True)
            self.angle_adjust_button.setChecked(False)
            self.select_strand_button.setEnabled(False)
            self.mask_button.setEnabled(True)
        elif mode == "attach":
            self.attach_button.setEnabled(False)
            self.move_button.setEnabled(True)
            self.angle_adjust_button.setEnabled(True)
            self.angle_adjust_button.setChecked(False)
            self.select_strand_button.setEnabled(True)
            self.mask_button.setEnabled(True)
        elif mode == "move":
            self.attach_button.setEnabled(True)
            self.move_button.setEnabled(False)
            self.angle_adjust_button.setEnabled(True)
            self.angle_adjust_button.setChecked(False)
            self.select_strand_button.setEnabled(True)
            self.mask_button.setEnabled(True)
        elif mode == "angle_adjust":
            self.attach_button.setEnabled(True)
            self.move_button.setEnabled(True)
            self.angle_adjust_button.setEnabled(True)
            self.angle_adjust_button.setChecked(self.canvas.is_angle_adjusting)
            self.select_strand_button.setEnabled(True)
            self.mask_button.setEnabled(True)
        elif mode == "mask":
            self.attach_button.setEnabled(True)
            self.move_button.setEnabled(True)
            self.angle_adjust_button.setEnabled(True)
            self.angle_adjust_button.setChecked(False)
            self.select_strand_button.setEnabled(True)
            self.mask_button.setEnabled(False)
        elif mode == "new_strand":
            self.attach_button.setEnabled(True)
            self.move_button.setEnabled(True)
            self.angle_adjust_button.setEnabled(False)
            self.select_strand_button.setEnabled(True)
            self.mask_button.setEnabled(False)

        if self.canvas.selected_strand_index is not None:
            self.canvas.highlight_selected_strand(self.canvas.selected_strand_index)
    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        self.layer_panel.keyPressEvent(event)
        if event.key() == Qt.Key_A and event.modifiers() == Qt.ControlModifier:
            if self.canvas.selected_strand and not isinstance(self.canvas.selected_strand, MaskedStrand):
                self.toggle_angle_adjust_mode()
            elif self.canvas.selected_strand and isinstance(self.canvas.selected_strand, MaskedStrand):
                print("Angle adjustment is not available for masked layers.")
        elif self.canvas.is_angle_adjusting:
            self.canvas.angle_adjust_mode.handle_key_press(event)
        elif event.key() == Qt.Key_M and event.modifiers() == Qt.ControlModifier:
            self.set_mask_mode()

    def keyReleaseEvent(self, event):
        super().keyReleaseEvent(event)
        self.layer_panel.keyReleaseEvent(event)

    def set_attach_mode(self):
        self.update_mode("attach")
        if self.canvas.last_selected_strand_index is not None:
            self.select_strand(self.canvas.last_selected_strand_index)

    def set_move_mode(self):
        self.update_mode("move")
        self.canvas.last_selected_strand_index = self.canvas.selected_strand_index
        self.canvas.selected_strand = None
        self.canvas.selected_strand_index = None
        self.canvas.update()

    def toggle_angle_adjust_mode(self):
        if self.canvas.selected_strand:
            if isinstance(self.canvas.selected_strand, MaskedStrand):
                print("Angle adjustment is not available for masked layers.")
                return
            
            if self.canvas.is_angle_adjusting:
                # Exit angle adjust mode
                self.canvas.angle_adjust_mode.confirm_adjustment()
                # The strand should still be selected at this point
                self.update_mode(self.current_mode)
            else:
                # Enter angle adjust mode
                self.canvas.toggle_angle_adjust_mode(self.canvas.selected_strand)
                self.update_mode("angle_adjust")
            self.angle_adjust_button.setChecked(self.canvas.is_angle_adjusting)
        else:
            print("No strand selected. Please select a strand before adjusting its angle.")
            logging.warning("Attempted to enter angle adjust mode with no strand selected.")

    def create_new_strand(self):
        if self.canvas.is_angle_adjusting:
            self.canvas.toggle_angle_adjust_mode(self.canvas.selected_strand)
        
        set_number = max(self.canvas.strand_colors.keys(), default=0) + 1
        
        if set_number not in self.canvas.strand_colors:
            self.canvas.strand_colors[set_number] = QColor('purple')
        
        self.canvas.start_new_strand_mode(set_number)
        
        logging.info(f"Ready to create new main strand for set: {set_number}")

    def select_strand(self, index, emit_signal=True):
        if self.canvas.is_angle_adjusting:
            self.canvas.toggle_angle_adjust_mode(self.canvas.selected_strand)
        
        if index is None or index == -1:
            self.canvas.clear_selection()
            if emit_signal:
                self.layer_panel.clear_selection()
        elif self.canvas.selected_strand_index != index:
            self.canvas.select_strand(index)
            if emit_signal:
                self.layer_panel.select_layer(index, emit_signal=False)
        
        self.canvas.is_first_strand = False
        # Don't call update_mode here to avoid recursion

    def handle_canvas_strand_selection(self, index):
        self.select_strand(index, emit_signal=True)
        # Update the mode after selection, if necessary
        if self.current_mode == "select":
            self.update_mode("attach")  # or any other appropriate mode


    def delete_strand(self, index):
            if 0 <= index < len(self.canvas.strands):
                strand_to_delete = self.canvas.strands[index]
                strand_name = strand_to_delete.layer_name
                logging.info(f"Attempting to delete strand: {strand_name}")

                # Find the correct strand in the canvas based on the layer name
                strand_index = next((i for i, s in enumerate(self.canvas.strands) if s.layer_name == strand_name), None)
                
                if strand_index is not None:
                    strand = self.canvas.strands[strand_index]
                    logging.info(f"Deleting strand: {strand.layer_name}")

                    set_number = strand.set_number
                    is_main_strand = strand.layer_name.split('_')[1] == '1'
                    is_attached_strand = isinstance(strand, AttachedStrand)

                    strands_to_remove = [strand]
                    if is_main_strand:
                        strands_to_remove.extend([s for s in self.canvas.strands if s.set_number == set_number and s != strand])

                    # Delete masks that are directly related to the deleted strand
                    masks_to_delete = []
                    for s in self.canvas.strands:
                        if isinstance(s, MaskedStrand):
                            if strand.layer_name in s.layer_name.split('_'):
                                masks_to_delete.append(s)
                                logging.info(f"Marking mask for deletion: {s.layer_name}")

                    # Remove the strands and masks
                    for s in strands_to_remove + masks_to_delete:
                        self.canvas.remove_strand(s)
                        logging.info(f"Removed strand/mask: {s.layer_name}")

                    # Collect indices of removed strands and masks
                    removed_indices = [i for i, s in enumerate(self.canvas.strands) if s in strands_to_remove + masks_to_delete]

                    # Update the layer panel without renumbering
                    self.layer_panel.update_after_deletion(set_number, removed_indices, is_main_strand, renumber=False)

                    # Ensure correct state of the canvas
                    self.canvas.force_redraw()

                    # Clear any selection
                    self.canvas.clear_selection()

                    # Update the mode to maintain consistency
                    self.update_mode(self.current_mode)

                    logging.info("Finished deleting strand and updating UI")
                else:
                    logging.warning(f"Strand {strand_name} not found in canvas strands")
            else:
                logging.warning(f"Invalid strand index: {index}")

    def start_resize(self, event):
        self.resize_start = event.pos()

    def do_resize(self, event):
        if hasattr(self, 'resize_start'):
            delta = event.pos().x() - self.resize_start.x()
            sizes = self.splitter.sizes()
            sizes[0] += delta
            sizes[1] -= delta
            self.splitter.setSizes(sizes)

    def stop_resize(self, event):
        if hasattr(self, 'resize_start'):
            del self.resize_start

    def update_locked_layers(self, locked_layers, lock_mode_active):
        self.canvas.move_mode.set_locked_layers(locked_layers, lock_mode_active)

    def save_project(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "JSON Files (*.json)")
        if filename:
            save_strands(self.canvas.strands, filename)
            logging.info(f"Project saved to {filename}")

    def load_project(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Project", "", "JSON Files (*.json)")
        if filename:
            loaded_strands = load_strands(filename, self.canvas)
            apply_loaded_strands(self.canvas, loaded_strands)
            logging.info(f"Project loaded from {filename}")
    def edit_group_angles(self, group_name):
        if group_name in self.canvas.groups:
            group_data = self.canvas.groups[group_name]
            dialog = StrandAngleEditDialog(group_name, group_data, self.canvas)
            dialog.angle_changed.connect(self.canvas.update_strand_angle)
            dialog.exec_()