from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QSplitter, QFileDialog
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QIcon, QColor
import os

from strand_drawing_canvas import StrandDrawingCanvas
from layer_panel import LayerPanel
from strand import Strand, AttachedStrand, MaskedStrand
from save_load_manager import save_strands, load_strands, apply_loaded_strands

import logging

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenStrand Studio")
        self.setMinimumSize(900, 900)
        self.setup_ui()
        self.setup_connections()
        self.current_mode = "attach"
        self.set_attach_mode()

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
        button_layout.addWidget(self.attach_button)
        button_layout.addWidget(self.move_button)
        button_layout.addWidget(self.toggle_grid_button)
        button_layout.addWidget(self.angle_adjust_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.load_button)

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

    def setup_connections(self):
        self.layer_panel.handle.mousePressEvent = self.start_resize
        self.layer_panel.handle.mouseMoveEvent = self.do_resize
        self.layer_panel.handle.mouseReleaseEvent = self.stop_resize

        self.canvas.set_layer_panel(self.layer_panel)
        self.layer_panel.new_strand_requested.connect(self.create_new_strand)
        self.layer_panel.strand_selected.connect(lambda idx: self.select_strand(idx, emit_signal=False))
        self.layer_panel.deselect_all_requested.connect(self.canvas.deselect_all_strands)

        self.attach_button.clicked.connect(self.set_attach_mode)
        self.move_button.clicked.connect(self.set_move_mode)
        self.toggle_grid_button.clicked.connect(self.canvas.toggle_grid)
        self.angle_adjust_button.clicked.connect(self.toggle_angle_adjust_mode)

        self.layer_panel.color_changed.connect(self.handle_color_change)
        self.layer_panel.masked_layer_created.connect(self.create_masked_layer)
        self.layer_panel.masked_mode_entered.connect(self.canvas.deselect_all_strands)
        self.layer_panel.masked_mode_exited.connect(self.restore_selection)
        self.layer_panel.lock_layers_changed.connect(self.update_locked_layers)
        self.layer_panel.strand_deleted.connect(self.delete_strand)

        self.save_button.clicked.connect(self.save_project)
        self.load_button.clicked.connect(self.load_project)

    def handle_color_change(self, set_number, color):
        self.canvas.update_color_for_set(set_number, color)
        self.layer_panel.update_colors_for_set(set_number, color)

    def create_masked_layer(self, layer1_index, layer2_index):
        layer1 = self.canvas.strands[layer1_index]
        layer2 = self.canvas.strands[layer2_index]
        
        masked_strand = MaskedStrand(layer1, layer2)
        self.canvas.add_strand(masked_strand)
        
        button = self.layer_panel.add_masked_layer_button(layer1_index, layer2_index)
        button.color_changed.connect(self.handle_color_change)
        
        logging.info(f"Created masked layer: {masked_strand.set_number}")
        
        self.canvas.update()
        self.update_mode(self.current_mode)

    def restore_selection(self):
        if self.layer_panel.last_selected_index is not None:
            self.select_strand(self.layer_panel.last_selected_index)

    def update_mode(self, mode):
        self.current_mode = mode
        self.canvas.set_mode(mode)
        if mode == "attach":
            self.attach_button.setEnabled(False)
            self.move_button.setEnabled(True)
            self.angle_adjust_button.setEnabled(True)
            self.angle_adjust_button.setChecked(False)
        elif mode == "move":
            self.attach_button.setEnabled(True)
            self.move_button.setEnabled(False)
            self.angle_adjust_button.setEnabled(True)
            self.angle_adjust_button.setChecked(False)
        elif mode == "angle_adjust":
            self.attach_button.setEnabled(True)
            self.move_button.setEnabled(True)
            self.angle_adjust_button.setEnabled(True)
            self.angle_adjust_button.setChecked(self.canvas.is_angle_adjusting)

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
                self.update_mode(self.current_mode)
            else:
                # Enter angle adjust mode
                self.canvas.toggle_angle_adjust_mode(self.canvas.selected_strand)
                self.update_mode("angle_adjust")
            self.angle_adjust_button.setChecked(self.canvas.is_angle_adjusting)

    def create_new_strand(self):
        if self.canvas.is_angle_adjusting:
            self.canvas.toggle_angle_adjust_mode(self.canvas.selected_strand)
        new_strand = Strand(QPointF(100, 100), QPointF(200, 200), self.canvas.strand_width)
        new_strand.is_first_strand = True
        new_strand.is_start_side = True
        
        set_number = max(self.canvas.strand_colors.keys(), default=0) + 1
        
        new_strand.set_number = set_number
        
        if set_number not in self.canvas.strand_colors:
            self.canvas.strand_colors[set_number] = QColor('purple')
        new_strand.set_color(self.canvas.strand_colors[set_number])
        
        new_strand.layer_name = f"{set_number}_1"
        
        self.canvas.add_strand(new_strand)
        self.canvas.newest_strand = new_strand
        self.layer_panel.add_layer_button(set_number)
        self.select_strand(len(self.canvas.strands) - 1)
        
        self.update_mode(self.current_mode)

    def select_strand(self, index, emit_signal=True):
        if self.canvas.is_angle_adjusting:
            self.canvas.toggle_angle_adjust_mode(self.canvas.selected_strand)
        if self.canvas.selected_strand_index != index:
            self.canvas.select_strand(index)
            if emit_signal:
                self.layer_panel.select_layer(index, emit_signal=False)
        self.canvas.is_first_strand = False
        
        self.update_mode(self.current_mode)

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