import os
import sys
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QHBoxLayout, QVBoxLayout,
    QSplitter, QFileDialog
)
from PyQt5.QtCore import Qt, QSize, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QImage, QPainter, QColor
from PyQt5.QtWidgets import QApplication

from strand_drawing_canvas import StrandDrawingCanvas
from layer_panel import LayerPanel
from strand import Strand, AttachedStrand, MaskedStrand
from save_load_manager import save_strands, load_strands, apply_loaded_strands
from mask_mode import MaskMode
from group_layers import GroupLayerManager, StrandAngleEditDialog
from settings_dialog import SettingsDialog
from translations import translations

# main_window.py

class MainWindow(QMainWindow):
    language_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.language_code = 'en'  # Default language

        logging.info("Initializing MainWindow")

        # Determine the base path to resources
        if getattr(sys, 'frozen', False):
            # If the application is frozen (running as an executable)
            base_path = sys._MEIPASS
        else:
            # If running from source
            base_path = os.path.dirname(os.path.abspath(__file__))

        # Load the icon
        icon_path = os.path.join(base_path, 'box_stitch.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            logging.info(f"Window icon set from: {icon_path}")
        else:
            logging.warning(f"Icon not found at {icon_path}")

        # Initialize components
        self.canvas = StrandDrawingCanvas(parent=self)
        self.layer_panel = LayerPanel(self.canvas, parent=self)  # Pass self as parent

        # Use the GroupLayerManager from layer_panel
        self.group_layer_manager = self.layer_panel.group_layer_manager

        # Set the group_layer_manager in the canvas
        self.canvas.group_layer_manager = self.group_layer_manager

        logging.info(f"Canvas set in MainWindow: {self.canvas}")

        # Create settings dialog
        self.settings_dialog = SettingsDialog(parent=self, canvas=self.canvas)

        # Verify that group_layer_manager is properly initialized
        if self.group_layer_manager is None:
            logging.error("group_layer_manager is None")
        else:
            logging.info("group_layer_manager is initialized")

        # Ensure that on_theme_changed method exists
        if hasattr(self.group_layer_manager, 'on_theme_changed'):
            logging.info("group_layer_manager.on_theme_changed exists")
        else:
            logging.error("group_layer_manager.on_theme_changed does not exist")
        self.group_layer_manager = self.layer_panel.group_layer_manager


        # Proceed with the rest of your setup
        self.setup_ui()
        self.setup_connections()
        self.current_mode = None
        self.previous_mode = None
        self.set_attach_mode()
        self.selected_strand = None


    def setup_ui(self):
        logging.info("Entered setup_ui")

        # Set the window icon if available
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'box_stitch.ico'))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            logging.info(f"Window icon set from: {icon_path}")
        else:
            logging.warning(f"Window icon not found at: {icon_path}")

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Create the horizontal layout for buttons
        button_layout = QHBoxLayout()
        self.attach_button = QPushButton("Attach Mode")
        self.move_button = QPushButton("Move Mode")
        self.rotate_button = QPushButton("Rotate Mode")
        self.toggle_grid_button = QPushButton("Toggle Grid")
        self.angle_adjust_button = QPushButton("Angle Adjust Mode")
        self.save_button = QPushButton("Save")
        self.load_button = QPushButton("Load")
        self.save_image_button = QPushButton("Save as Image")
        self.select_strand_button = QPushButton("Select Strand")
        self.mask_button = QPushButton("Mask Mode")

        # Create the settings button
        self.settings_button = QPushButton()
        self.settings_button.setFixedSize(32, 32)
        self.settings_button.setObjectName("settingsButton")  # Assign an object name for stylesheet targeting

        # Set the gear icon or fallback to Unicode character if the image is not found
        gear_icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'settings_icon.png'))
        logging.info(f"Searching for gear icon at: {gear_icon_path}")

        if os.path.exists(gear_icon_path):
            logging.info("Settings icon found. Setting icon for settings_button.")
            self.settings_button.setIcon(QIcon(gear_icon_path))
            self.settings_button.setIconSize(QSize(24, 24))
        else:
            logging.warning("Settings icon not found. Using Unicode '⚙' character.")
            self.settings_button.setText('⚙')
            self.settings_button.setFont(QFont('Segoe UI Symbol', 16))  # Adjust font if necessary

        # Style the settings button to have a transparent background
        self.settings_button.setStyleSheet("""
            QPushButton#settingsButton {
                background-color: rgba(150, 150, 150, 255);
                border: none;
                border-radius: 18px;
            }
            QPushButton#settingsButton:hover {
                background-color: rgba(200, 200, 200, 50); /* Light transparent hover effect */
            }
        """)

        # Add buttons to the button layout
        button_layout.addWidget(self.mask_button)
        button_layout.addWidget(self.select_strand_button)
        button_layout.addWidget(self.attach_button)
        button_layout.addWidget(self.move_button)
        button_layout.addWidget(self.rotate_button)
        button_layout.addWidget(self.toggle_grid_button)
        button_layout.addWidget(self.angle_adjust_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.save_image_button)
        button_layout.addWidget(self.settings_button)

        # Change the angle_adjust_button to be non-checkable
        self.angle_adjust_button.setCheckable(False)

        # Set up the splitter and layouts
        self.splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addLayout(button_layout)
        left_layout.addWidget(self.canvas)
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(self.layer_panel)

        # Configure splitter and main layout
        self.splitter.setHandleWidth(0)
        main_layout.addWidget(self.splitter)

        # Set minimum widths
        left_widget.setMinimumWidth(200)
        self.layer_panel.setMinimumWidth(100)

        # Apply button styles
        self.setup_button_styles()

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
        self.rotate_button.clicked.connect(self.set_rotate_mode)
        self.toggle_grid_button.clicked.connect(self.canvas.toggle_grid)
        self.angle_adjust_button.clicked.connect(self.handle_angle_adjust_click)
        self.save_button.clicked.connect(self.save_project)
        self.load_button.clicked.connect(self.load_project)
        self.save_image_button.clicked.connect(self.save_canvas_as_image)
        self.select_strand_button.clicked.connect(self.set_select_mode)
        self.mask_button.clicked.connect(self.set_mask_mode)
        self.rotate_button.clicked.connect(self.set_rotate_mode)
        self.settings_button.clicked.connect(self.open_settings_dialog)

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

        # Add this new connection
        self.canvas.angle_adjust_completed.connect(self.deselect_angle_adjust_button)

        # Connect attachable_changed signal for each layer button
        for button in self.layer_panel.layer_buttons:
            button.attachable_changed.connect(self.update_strand_attachable)

    def open_settings_dialog(self):
        settings_dialog = SettingsDialog(parent=self, canvas=self.canvas)
        settings_dialog.theme_changed.connect(self.apply_theme)  # Connect the signal
        settings_dialog.exec_()

    def apply_theme(self, theme_name):
        if theme_name == "dark":
            style_sheet = """
                QWidget {
                    background-color: #2C2C2C;
                    color: white;
                }
                /* Apply styles to all QPushButtons except the settings button */
                QPushButton:not(#settingsButton) {
                    background-color: #3C3C3C;
                    color: white;
                }
                /* Add styles for other widgets as needed */
            """
        elif theme_name == "light":
            style_sheet = """
                QWidget {
                    background-color: #FFFFFF;
                    color: black;
                }
                /* Apply styles to all QPushButtons except the settings button */
                QPushButton:not(#settingsButton) {
                    background-color: #F0F0F0;
                    color: black;
                }
                /* Add styles for other widgets as needed */
            """
        elif theme_name == "default":
            # Clear the style sheet to use the default theme
            style_sheet = ""
        else:
            # If an unknown theme is selected, default to using no stylesheet
            style_sheet = ""

        # Apply the style sheet to the application
        QApplication.instance().setStyleSheet(style_sheet)

        # Update the canvas theme if needed
        self.canvas.set_theme(theme_name)
        self.canvas.update()

        # Update the layer panel theme
        if hasattr(self.layer_panel, 'set_theme'):
            self.layer_panel.set_theme(theme_name)

    def update_strand_attachable(self, set_number, attachable):
        for strand in self.canvas.strands:
            if strand.set_number == set_number:
                strand.set_attachable(attachable)
        self.canvas.update()  # Redraw the canvas to show the changes

    def handle_angle_adjust_click(self):
        if self.canvas.selected_strand:
            if isinstance(self.canvas.selected_strand, MaskedStrand):
                print("Angle adjustment is not available for masked layers.")
                return
            
            self.previous_mode = self.current_mode  # Store the current mode


    def setup_button_styles(self):
        button_style = """
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                font-weight: bold;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
            }}
            QPushButton:checked {{
                background-color: {checked_color};
            }}
        """
        buttons = [
            (self.attach_button, "#436A7C", "white", "#AFBDC3", "#34383A", "#133D4D"),
            (self.move_button, "#AD8D3C", "white", "#B8B35C", "#856A2B", "#856A2B"),
            (self.rotate_button, "#8D3CAD", "white", "#B35CB8", "#6A2B85", "#6A2B85"),
            (self.toggle_grid_button, "#DDA0DD", "black", "#DA70D6", "#BA55D3", "#BA55D3"),
            (self.angle_adjust_button, "#DBAA93", "black", "#C69C6D", "#B38B5D", "#B38B5D"),
            (self.save_button, "#20B2AA", "white", "#48D1CC", "#008B8B", "#008B8B"),
            (self.load_button, "#FF69B4", "white", "#FF1493", "#C71585", "#C71585"),
            (self.save_image_button, "#4CAF50", "white", "#45a049", "#3e8e41", "#3e8e41"),
            (self.select_strand_button, "#FFA500", "white", "#FFEBC7", "#FF8C00", "#FF8C00"),
            (self.mask_button, "#800080", "white", "#9932CC", "#4B0082", "#4B0082"),
        ]
        for button, bg_color, text_color, hover_color, pressed_color, checked_color in buttons:
            # Avoid applying styles to the settings button
            if button != self.settings_button:
                button.setStyleSheet(button_style.format(
                    bg_color=bg_color,
                    text_color=text_color,
                    hover_color=hover_color,
                    pressed_color=pressed_color,
                    checked_color=checked_color
                ))
                button.setCheckable(True)

        # Style specific buttons that don't follow the generic pattern
        self.layer_panel.lock_layers_button.setStyleSheet("""
            QPushButton {
                background-color: orange;
                color: white;
                font-weight: bold;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
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
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
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
                color: black;                                           
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #6EB56E;
            }
            QPushButton:pressed {
                background-color: #4D804D;
            }
        """)

        self.layer_panel.deselect_all_button.setStyleSheet("""
            QPushButton {
                background-color: lightyellow;
                font-weight: bold;
                color: black;                                                                                      
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #D7D9A3;
            }
            QPushButton:pressed {
                background-color: #C0C286;
            }
        """)

    def update_button_states(self, active_mode):
        buttons = {
            "attach": self.attach_button,
            "move": self.move_button,
            "rotate": self.rotate_button,
            "select": self.select_strand_button,
            "mask": self.mask_button
        }

        for mode, button in buttons.items():
            button.setChecked(mode == active_mode)


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
        self.rotate_button.clicked.connect(self.set_rotate_mode)
        self.toggle_grid_button.clicked.connect(self.canvas.toggle_grid)
        self.angle_adjust_button.clicked.connect(self.handle_angle_adjust_click)
        self.save_button.clicked.connect(self.save_project)
        self.load_button.clicked.connect(self.load_project)
        self.save_image_button.clicked.connect(self.save_canvas_as_image)
        self.select_strand_button.clicked.connect(self.set_select_mode)
        self.mask_button.clicked.connect(self.set_mask_mode)
        self.rotate_button.clicked.connect(self.set_rotate_mode)
        self.settings_button.clicked.connect(self.open_settings_dialog)

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

        # Add this new connection
        self.canvas.angle_adjust_completed.connect(self.deselect_angle_adjust_button)

        # Connect attachable_changed signal for each layer button
        for button in self.layer_panel.layer_buttons:
            button.attachable_changed.connect(self.update_strand_attachable)
    def open_settings_dialog(self):
        settings_dialog = SettingsDialog(parent=self, canvas=self.canvas)
        settings_dialog.theme_changed.connect(self.apply_theme)
        settings_dialog.exec_()
    def update_strand_attachable(self, set_number, attachable):
        for strand in self.canvas.strands:
            if strand.set_number == set_number:
                strand.set_attachable(attachable)
        self.canvas.update()  # Redraw the canvas to show the changes

    # Add this new method
    def handle_angle_adjust_click(self):
        if self.canvas.selected_strand:
            if isinstance(self.canvas.selected_strand, MaskedStrand):
                print("Angle adjustment is not available for masked layers.")
                return
            
            self.previous_mode = self.current_mode  # Store the current mode
            self.canvas.toggle_angle_adjust_mode(self.canvas.selected_strand)
            self.update_mode("angle_adjust")
        else:
            print("No strand selected. Please select a strand before adjusting its angle.")
            logging.warning("Attempted to enter angle adjust mode with no strand selected.")

    def set_angle_adjust_mode(self):
        if self.canvas.selected_strand:
            if isinstance(self.canvas.selected_strand, MaskedStrand):
                print("Angle adjustment is not available for masked layers.")
                return
            
            self.previous_mode = self.current_mode  # Store the current mode
            self.canvas.toggle_angle_adjust_mode(self.canvas.selected_strand)
            self.update_mode("angle_adjust")
        else:
            print("No strand selected. Please select a strand before adjusting its angle.")
            logging.warning("Attempted to enter angle adjust mode with no strand selected.")

    def toggle_angle_adjust_mode(self):
        if self.canvas.selected_strand:
            if isinstance(self.canvas.selected_strand, MaskedStrand):
                print("Angle adjustment is not available for masked layers.")
                return
            
            if self.canvas.is_angle_adjusting:
                # Exit angle adjust mode
                self.canvas.angle_adjust_mode.confirm_adjustment()
                self.update_mode(self.previous_mode)  # Return to previous mode
            else:
                # Enter angle adjust mode
                self.previous_mode = self.current_mode  # Store the current mode
                self.canvas.toggle_angle_adjust_mode(self.canvas.selected_strand)
                self.update_mode("angle_adjust")
        else:
            print("No strand selected. Please select a strand before adjusting its angle.")
            logging.warning("Attempted to enter angle adjust mode with no strand selected.")

    def deselect_angle_adjust_button(self):
        self.angle_adjust_button.setChecked(False)
        self.update_mode(self.previous_mode)  # Return to the previous mode

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
        if self.current_mode == "angle_adjust" and mode != "angle_adjust":
            # If we're leaving angle adjust mode, confirm the adjustment
            self.canvas.angle_adjust_mode.confirm_adjustment()
        
        self.current_mode = mode
        self.canvas.set_mode(mode)
        self.update_button_states(mode)

        if mode == "select":
            self.attach_button.setEnabled(True)
            self.move_button.setEnabled(True)
            self.angle_adjust_button.setEnabled(True)
            self.select_strand_button.setEnabled(False)
            self.mask_button.setEnabled(True)
            self.rotate_button.setEnabled(True)
        elif mode == "attach":
            self.attach_button.setEnabled(False)
            self.move_button.setEnabled(True)
            self.angle_adjust_button.setEnabled(True)
            self.select_strand_button.setEnabled(True)
            self.mask_button.setEnabled(True)
            self.rotate_button.setEnabled(True)
        elif mode == "move":
            self.attach_button.setEnabled(True)
            self.move_button.setEnabled(False)
            self.angle_adjust_button.setEnabled(True)
            self.select_strand_button.setEnabled(True)
            self.mask_button.setEnabled(True)
            self.rotate_button.setEnabled(True)
        elif mode == "angle_adjust":
            self.attach_button.setEnabled(True)
            self.move_button.setEnabled(True)
            self.angle_adjust_button.setEnabled(False)  # Keep it enabled
            self.select_strand_button.setEnabled(True)
            self.mask_button.setEnabled(True)
            self.rotate_button.setEnabled(True)
        elif mode == "mask":
            self.attach_button.setEnabled(True)
            self.move_button.setEnabled(True)
            self.angle_adjust_button.setEnabled(True)
            self.select_strand_button.setEnabled(True)
            self.mask_button.setEnabled(False)
            self.rotate_button.setEnabled(True)
        elif mode == "new_strand":
            self.attach_button.setEnabled(True)
            self.move_button.setEnabled(True)
            self.angle_adjust_button.setEnabled(True)
            self.select_strand_button.setEnabled(True)
            self.mask_button.setEnabled(False)
            self.rotate_button.setEnabled(True)
        elif mode == "rotate":
            self.attach_button.setEnabled(True)
            self.move_button.setEnabled(True)
            self.angle_adjust_button.setEnabled(True)
            self.select_strand_button.setEnabled(True)
            self.mask_button.setEnabled(True)
            self.rotate_button.setEnabled(False)

        if self.canvas.selected_strand_index is not None:
            self.canvas.highlight_selected_strand(self.canvas.selected_strand_index)

    def deselect_angle_adjust_button(self):
        # This method is no longer needed, but we'll keep it empty for compatibility
        pass


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


    def create_new_strand(self):
        if self.canvas.is_angle_adjusting:
            self.canvas.toggle_angle_adjust_mode(self.canvas.selected_strand)
        
        set_number = max(self.canvas.strand_colors.keys(), default=0) + 1
        
        if set_number not in self.canvas.strand_colors:
            self.canvas.strand_colors[set_number] = QColor('purple')
        
        self.canvas.start_new_strand_mode(set_number)
        
        logging.info(f"Ready to create new main strand for set: {set_number}")
    def toggle_angle_adjust_mode(self):
        if self.canvas.selected_strand:
            if isinstance(self.canvas.selected_strand, MaskedStrand):
                print("Angle adjustment is not available for masked layers.")
                return
            
            if self.canvas.is_angle_adjusting:
                # Exit angle adjust mode
                self.canvas.angle_adjust_mode.confirm_adjustment()
                self.update_mode(self.previous_mode)  # Return to previous mode
            else:
                # Enter angle adjust mode
                self.previous_mode = self.current_mode  # Store the current mode
                self.canvas.toggle_angle_adjust_mode(self.canvas.selected_strand)
                self.update_mode("angle_adjust")
        else:
            print("No strand selected. Please select a strand before adjusting its angle.")
            logging.warning("Attempted to enter angle adjust mode with no strand selected.")

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
            # Retrieve the group data from the correct instance
            groups = self.group_layer_manager.get_group_data()
            logging.debug(f"Group data before saving: {groups}")  # Add this line
            # Save the strands and groups
            save_strands(self.canvas.strands, groups, filename)
            logging.info(f"Project saved to {filename}")
    def load_project(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "JSON Files (*.json)")
        if filename:
            strands, groups = load_strands(filename, self.canvas)
            apply_loaded_strands(self.canvas, strands, groups)
            logging.info(f"Project loaded from {filename}")
    def edit_group_angles(self, group_name):
        if group_name in self.canvas.groups:
            group_data = self.canvas.groups[group_name]
            dialog = StrandAngleEditDialog(group_name, group_data, self.canvas)
            dialog.angle_changed.connect(self.canvas.update_strand_angle)
            dialog.exec_()

    def set_rotate_mode(self):
        self.update_mode("rotate")
        self.canvas.set_mode("rotate")
    def set_language(self, language_code):
        """Set the application language and update all UI elements."""
        self.language_code = language_code

        # Update the language code in all components
        self.canvas.language_code = language_code
        self.layer_panel.language_code = language_code
        if self.settings_dialog:
            self.settings_dialog.language_code = language_code

        # Update translations in UI elements
        self.translate_ui()
        self.canvas.update_translations()
        self.layer_panel.translate_ui()
        if self.settings_dialog.isVisible():
            self.settings_dialog.update_translations()
        if self.canvas:
            self.canvas.language_code = language_code

    def translate_ui(self):
        """Update the UI texts to the selected language."""
        _ = translations[self.language_code]

        # Update window title
        self.setWindowTitle(_['main_window_title'])

        # Update button texts
        self.attach_button.setText(_['attach_mode'])
        self.move_button.setText(_['move_mode'])
        self.rotate_button.setText(_['rotate_mode'])
        self.toggle_grid_button.setText(_['toggle_grid'])
        self.angle_adjust_button.setText(_['angle_adjust_mode'])
        self.select_strand_button.setText(_['select_mode'])
        self.mask_button.setText(_['mask_mode'])
        self.save_button.setText(_['save'])
        self.load_button.setText(_['open'])
        self.save_image_button.setText(_['save_image'])

        # Update settings button tooltip or text
        self.settings_button.setToolTip(_['settings'])

        # Update any other UI elements as needed
        # ...

        # Apply translations to other UI components
        if hasattr(self.layer_panel, 'translate_ui'):
            self.layer_panel.translate_ui()
        if hasattr(self.canvas, 'update_translations'):
            self.canvas.update_translations()