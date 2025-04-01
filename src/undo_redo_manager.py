import os
import json
import logging
import datetime
import shutil
from PyQt5.QtWidgets import QPushButton, QStyle, QStyleOption
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtGui import QPainter, QPainterPath, QPen, QFontMetrics, QColor
from save_load_manager import save_strands, load_strands, apply_loaded_strands

# StrokeTextButton class incorporated directly into this file
class StrokeTextButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(40, 40)
        self.current_theme = "default"  # Default theme
        self.setup_theme_colors()
        self.updateStyleSheet()
        # Ensure the button accepts paint events
        self.setAttribute(Qt.WA_StyledBackground, True)
        # Enable mouse tracking for better hover detection
        self.setMouseTracking(True)
    
    def setup_theme_colors(self):
        """Set up color schemes for different themes"""
        # Theme-specific colors dictionary
        self.theme_colors = {
            "default": {
                "bg_normal": "#4d9958",           # Normal background 
                "bg_hover": "#286335",            # Significantly darker hover
                "bg_pressed": "#102513",          # Almost black when pressed
                "border_normal": "#3c7745",       # Normal border
                "border_hover": "#1d4121",        # Darker border on hover
                "border_pressed": "#ffffff",      # White border when pressed
                "stroke_normal": "#e6fae9",       # Normal stroke
                "stroke_hover": "#ffffff",        # Hover stroke (bright white)
                "stroke_pressed": "#b8ffc2",      # Brighter stroke when pressed
                "fill": "#000000",                # Icon fill color
                "bg_disabled": "#8a8a8a",         # Disabled background (gray)
                "border_disabled": "#696969",     # Disabled border (darker gray)
                "stroke_disabled": "#d0d0d0"      # Disabled stroke (light gray)
            },
            "dark": {
                "bg_normal": "#3d7846",           # Darker background for dark theme
                "bg_hover": "#4e9854",            # Hover background for dark theme
                "bg_pressed": "#081f0d",          # Almost black when pressed
                "border_normal": "#2c5833",       # Normal border for dark theme
                "border_hover": "#c8edcc",        # Hover border for dark theme
                "border_pressed": "#7dff8e",      # Bright border when pressed
                "stroke_normal": "#c8edcc",       # Normal stroke for dark theme
                "stroke_hover": "#ffffff",        # Hover stroke for dark theme
                "stroke_pressed": "#daffe0",      # Brighter stroke for dark theme
                "fill": "#000000",                # Icon fill color
                "bg_disabled": "#4a4a4a",         # Disabled background (dark gray)
                "border_disabled": "#3d3d3d",     # Disabled border (darker gray)
                "stroke_disabled": "#888888"      # Disabled stroke (medium gray)
            },
            "light": {
                "bg_normal": "#4d9958",           # Normal background for light theme
                "bg_hover": "#286335",            # Significantly darker hover
                "bg_pressed": "#102513",          # Almost black when pressed
                "border_normal": "#3c7745",       # Normal border for light theme
                "border_hover": "#1d4121",        # Darker border on hover
                "border_pressed": "#ffffff",      # White border when pressed
                "stroke_normal": "#e6fae9",       # Normal stroke for light theme
                "stroke_hover": "#ffffff",        # Hover stroke for light theme
                "stroke_pressed": "#b8ffc2",      # Brighter stroke for light theme
                "fill": "#000000",                # Icon fill color
                "bg_disabled": "#acacac",         # Disabled background (light gray)
                "border_disabled": "#9c9c9c",     # Disabled border (medium gray)
                "stroke_disabled": "#e0e0e0"      # Disabled stroke (very light gray)
            }
        }
    
    def set_theme(self, theme_name):
        """Update button appearance based on theme"""
        if theme_name in self.theme_colors:
            self.current_theme = theme_name
        else:
            self.current_theme = "default"  # Fallback to default for unknown themes
        
        self.updateStyleSheet()
        self.update()  # Force repaint

    def updateStyleSheet(self):
        # Get colors for current theme
        colors = self.theme_colors.get(self.current_theme, self.theme_colors["default"])
        
        self.setStyleSheet(f"""
            QPushButton {{
                font-weight: bold;
                font-size: 30px;
                color: transparent;  /* Make default text transparent */
                background-color: {colors["bg_normal"]};
                border: 1px solid {colors["border_normal"]};  /* Subtle border in normal state */
                padding: 0px;
                border-radius: 20px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {colors["bg_hover"]};  /* Brighter green on hover */
                border: 2px solid {colors["border_hover"]};  /* Light border on hover */
            }}
            QPushButton:pressed {{
                background-color: {colors["bg_pressed"]};  /* Darker green when pressed */
                border: 2px solid {colors["border_pressed"]};  /* Darker border when pressed */
            }}
            QPushButton:disabled {{
                background-color: {colors["bg_disabled"]};  /* Gray when disabled */
                border: 1px solid {colors["border_disabled"]};  /* Darker gray border when disabled */
            }}
        """)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw the background (if not handled by stylesheet)
        option = QStyleOption()
        option.initFrom(self)
        self.style().drawPrimitive(QStyle.PE_Widget, option, painter, self)

        # Draw the text with stroke
        font = self.font()
        font.setBold(True)
        font.setPixelSize(30)  # Explicit font size
        painter.setFont(font)

        text = self.text()
        text_rect = self.rect()
        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(text)
        text_height = fm.height()
        x = (text_rect.width() - text_width) / 2
        y = (text_rect.height() + text_height) / 2 - fm.descent()

        # Create and draw the text path
        path = QPainterPath()
        path.addText(x, y-2, font, text)

        # Get colors for current theme
        colors = self.theme_colors.get(self.current_theme, self.theme_colors["default"])

        # Determine stroke color and width based on button state and theme
        if not self.isEnabled():
            # Disabled state
            stroke_color = QColor(colors["stroke_disabled"])
            stroke_width = 2.5  # Thinner stroke for disabled state
            fill_color = QColor(150, 150, 150, 180)  # Gray with transparency for disabled
        elif self.isDown():
            stroke_color = QColor(colors["stroke_pressed"])
            stroke_width = 5.0
            fill_color = QColor(colors["fill"])
        elif self.underMouse():
            stroke_color = QColor(colors["stroke_hover"])
            if self.current_theme == "dark":
                stroke_width = 3.5
            else:
                stroke_width = 4.0
            fill_color = QColor(colors["fill"])
        else:
            stroke_color = QColor(colors["stroke_normal"])
            stroke_width = 3.0
            fill_color = QColor(colors["fill"])

        # Draw stroke with appropriate color and width
        pen = QPen(stroke_color, stroke_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.strokePath(path, pen)
        
        # Fill with color based on button state
        painter.fillPath(path, fill_color)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateStyleSheet()

# Removing the import of StrokeTextButton from external file
# from stroke_text_button import StrokeTextButton

class UndoRedoManager(QObject):
    """
    Manages undo and redo operations by saving/loading temporary state files.
    Each state represents a snapshot after a mouse release in move mode.
    """
    undo_performed = pyqtSignal()
    redo_performed = pyqtSignal()
    state_saved = pyqtSignal(int)  # Emits current step number when a new state is saved

    def __init__(self, canvas, layer_panel):
        super().__init__()
        self.canvas = canvas
        self.layer_panel = layer_panel
        self.current_step = 0  # Start at step 0 (no steps saved yet)
        self.max_step = 0      # Start with no steps saved
        self.temp_dir = self._create_temp_dir()
        self.session_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.undo_button = None
        self.redo_button = None
        
        # Connect signals
        self.undo_performed.connect(self._update_button_states)
        self.redo_performed.connect(self._update_button_states)
        self.state_saved.connect(self._update_button_states)
        
        # Do not save initial state here - this will be done when connecting to move_mode
        # This way, we won't have a "blank" initial state
        
        # Update button states initially (both should be disabled)
        self._update_button_states()

    def _create_temp_dir(self):
        """Create a temporary directory for state files if it doesn't exist."""
        temp_dir = os.path.join(os.path.dirname(__file__), "temp_states")
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    def _get_state_filename(self, step):
        """Generate a filename for the specified step."""
        return os.path.join(self.temp_dir, f"{self.session_id}_{step}.json")

    def save_state(self):
        """Save the current state of the canvas, handling history correctly."""
        # Check if there's a previous state to compare with
        if self.current_step > 0:
            # Get previous state filename
            prev_filename = self._get_state_filename(self.current_step)
            
            # Create a temporary file to save current state for comparison
            temp_filename = os.path.join(self.temp_dir, f"{self.session_id}_temp.json")
            
            try:
                # Save current state to temp file
                save_strands(self.canvas.strands, 
                            self.canvas.groups if hasattr(self.canvas, 'groups') else {},
                            temp_filename,
                            self.canvas)
                
                # Check if files are identical
                if os.path.exists(prev_filename):
                    with open(prev_filename, 'r') as prev_file, open(temp_filename, 'r') as temp_file:
                        prev_content = prev_file.read()
                        temp_content = temp_file.read()
                        
                        if prev_content == temp_content:
                            # States are identical, clean up temp file and exit
                            logging.info(f"New state is identical to previous state, skipping save")
                            try:
                                os.remove(temp_filename)
                            except:
                                pass
                            return
                
                # Clean up temp file
                try:
                    os.remove(temp_filename)
                except:
                    pass
            except Exception as e:
                logging.error(f"Error during state comparison: {e}")
                # Continue with normal save process if comparison fails
                try:
                    if os.path.exists(temp_filename):
                        os.remove(temp_filename)
                except:
                    pass
        
        # Increment step before saving
        next_step = self.current_step + 1
        
        # If we're not at the end of the history, clear future states
        if next_step <= self.max_step:
            logging.info(f"Overwriting future history from step {next_step} onwards.")
            for step in range(next_step, self.max_step + 1):
                filename = self._get_state_filename(step)
                try:
                    if os.path.exists(filename):
                        os.remove(filename)
                        logging.debug(f"Removed future state file: {filename}")
                except OSError as e:
                    logging.error(f"Error removing future state file {filename}: {e}")
            # Update max_step since future states are now invalid
            self.max_step = self.current_step 

        # Update step counters
        self.current_step += 1
        self.max_step = self.current_step
        
        filename = self._get_state_filename(self.current_step)
        logging.info(f"Saving state to {filename} (current_step={self.current_step}, max_step={self.max_step})")
        
        try:
            save_strands(self.canvas.strands, 
                         self.canvas.groups if hasattr(self.canvas, 'groups') else {},
                         filename,
                         self.canvas)
            self.state_saved.emit(self.current_step)
            logging.info(f"State saved successfully at step {self.current_step}")
        except Exception as e:
            logging.error(f"Error saving state: {e}")

    def undo(self):
        """Load the previous state if available."""
        if self.current_step > 1:
            self.current_step -= 1
            self._load_state(self.current_step)
            self.undo_performed.emit()
            logging.info(f"Undo performed, now at step {self.current_step}")
            
            # Make sure buttons are properly updated
            self._update_button_states()

            # Ensure the canvas is fully refreshed after undo
            self.canvas.update()
            
            # Call refresh_layers to simulate clicking the green refresh button
            if hasattr(self.layer_panel, 'refresh_layers'):
                self.layer_panel.refresh_layers()
            elif hasattr(self.layer_panel, 'refresh'):
                self.layer_panel.refresh()
        else:
            logging.info("Cannot undo: already at oldest state")

    def redo(self):
        """Load the next state if available."""
        if self.current_step < self.max_step:
            self.current_step += 1
            self._load_state(self.current_step)
            self.redo_performed.emit()
            logging.info(f"Redo performed, now at step {self.current_step}")
            
            # Make sure buttons are properly updated
            self._update_button_states()

            # Ensure the canvas is fully refreshed after redo
            self.canvas.update()
            
            # Call refresh_layers to simulate clicking the green refresh button
            if hasattr(self.layer_panel, 'refresh_layers'):
                self.layer_panel.refresh_layers()
            elif hasattr(self.layer_panel, 'refresh'):
                self.layer_panel.refresh()
        else:
            logging.info("Cannot redo: already at newest state")

    def _load_state(self, step):
        """Load the state for the specified step and apply it."""
        filename = self._get_state_filename(step)
        
        logging.info(f"Attempting to load state from step {step}: {filename}")
        
        if os.path.exists(filename):
            logging.info(f"File exists: {filename}")
            try:
                # First load the strands from the file
                logging.info(f"Loading strands from file: {filename}")
                strands, groups = load_strands(filename, self.canvas)
                logging.info(f"Loaded {len(strands)} strands and {len(groups)} groups")
                
                # Then set the loaded strands on the canvas
                self.canvas.strands = strands
                if hasattr(self.canvas, 'groups'):
                    self.canvas.groups = groups
                logging.info("Applied strands and groups to canvas")
                
                # Refresh the UI
                if hasattr(self.layer_panel, 'refresh'):
                    logging.info("Refreshing layer panel")
                    self.layer_panel.refresh()
                else:
                    logging.warning("Layer panel has no refresh method")
                
                # Update the canvas
                logging.info("Updating canvas")
                self.canvas.update()
                
                logging.info(f"State loaded and applied successfully from step {step}")
            except Exception as e:
                # Log the full traceback for detailed debugging
                logging.exception(f"Error loading and applying state from {filename}: {e}")
        else:
            logging.error(f"State file not found: {filename}")

    def _update_button_states(self):
        """Update the enabled state of undo/redo buttons."""
        if self.undo_button:
            can_undo = self.current_step > 1
            self.undo_button.setEnabled(can_undo)
            logging.debug(f"Undo button {'enabled' if can_undo else 'disabled'} (current_step={self.current_step})")
        else:
            logging.debug("Undo button not initialized yet")
            
        if self.redo_button:
            can_redo = self.current_step < self.max_step
            self.redo_button.setEnabled(can_redo)
            logging.debug(f"Redo button {'enabled' if can_redo else 'disabled'} (current_step={self.current_step}, max_step={self.max_step})")
        else:
            logging.debug("Redo button not initialized yet")

    def setup_buttons(self, top_layout):
        """Create and add undo/redo buttons to the specified layout."""
        # Create buttons using StrokeTextButton for consistent styling
        self.undo_button = StrokeTextButton("↶")  # Unicode left arrow for undo
        self.redo_button = StrokeTextButton("↷")  # Unicode right arrow for redo
        
        # Apply theme to match the refresh button
        # Colors will be shades of blue instead of green to differentiate them
        self.undo_button.theme_colors = {
            "default": {
                "bg_normal": "#4387c2",           # Blueish normal background 
                "bg_hover": "#2c5c8a",            # Darker hover
                "bg_pressed": "#10253a",          # Almost black when pressed
                "border_normal": "#3c77a5",       # Normal border
                "border_hover": "#1d4168",        # Darker border on hover
                "border_pressed": "#ffffff",      # White border when pressed
                "stroke_normal": "#e0ecfa",       # Normal stroke
                "stroke_hover": "#ffffff",        # Hover stroke (bright white)
                "stroke_pressed": "#b8d6ff",      # Brighter stroke when pressed
                "fill": "#000000",                # Icon fill color
                "bg_disabled": "#8a8a8a",         # Disabled background (gray)
                "border_disabled": "#696969",     # Disabled border (darker gray)
                "stroke_disabled": "#d0d0d0"      # Disabled stroke (light gray)
            },
            "dark": {
                "bg_normal": "#3d5d78",           # Darker background for dark theme
                "bg_hover": "#4e7898",            # Hover background for dark theme
                "bg_pressed": "#081a2f",          # Almost black when pressed
                "border_normal": "#2c4e69",       # Normal border for dark theme
                "border_hover": "#c8deec",        # Hover border for dark theme
                "border_pressed": "#7dbdff",      # Bright border when pressed
                "stroke_normal": "#c8deec",       # Normal stroke for dark theme
                "stroke_hover": "#ffffff",        # Hover stroke for dark theme
                "stroke_pressed": "#dae9ff",      # Brighter stroke for dark theme
                "fill": "#000000",                # Icon fill color 
                "bg_disabled": "#4a4a4a",         # Disabled background (dark gray)
                "border_disabled": "#3d3d3d",     # Disabled border (darker gray)
                "stroke_disabled": "#888888"      # Disabled stroke (medium gray)
            },
            "light": {
                "bg_normal": "#4387c2",           # Normal background for light theme
                "bg_hover": "#2c5c8a",            # Significantly darker hover
                "bg_pressed": "#10253a",          # Almost black when pressed
                "border_normal": "#3c77a5",       # Normal border for light theme
                "border_hover": "#1d4168",        # Darker border on hover
                "border_pressed": "#ffffff",      # White border when pressed
                "stroke_normal": "#e0ecfa",       # Normal stroke for light theme
                "stroke_hover": "#ffffff",        # Hover stroke for light theme
                "stroke_pressed": "#b8d6ff",      # Brighter stroke for light theme
                "fill": "#000000",                # Icon fill color
                "bg_disabled": "#acacac",         # Disabled background (light gray)
                "border_disabled": "#9c9c9c",     # Disabled border (medium gray)
                "stroke_disabled": "#e0e0e0"      # Disabled stroke (very light gray)
            }
        }
        
        # Apply same colors to redo button
        self.redo_button.theme_colors = self.undo_button.theme_colors.copy()
        
        # Update the styles
        self.undo_button.updateStyleSheet()
        self.redo_button.updateStyleSheet()
        
        # Set fixed size to match the refresh button
        self.undo_button.setFixedSize(40, 40)
        self.redo_button.setFixedSize(40, 40)
        
        # Set tooltips
        self.undo_button.setToolTip("Undo last action")
        self.redo_button.setToolTip("Redo last undone action")
        
        # Connect button clicks
        self.undo_button.clicked.connect(self.undo)
        self.redo_button.clicked.connect(self.redo)
        
        # Initially disable both buttons until there are states to navigate
        self.undo_button.setEnabled(False)
        self.redo_button.setEnabled(False)
        
        # Add buttons to layout
        top_layout.addWidget(self.undo_button)
        top_layout.addWidget(self.redo_button)
        
        # Update button states based on current history
        self._update_button_states()
        
        logging.info("Undo/redo buttons initialized and added to layout")
        
        return self.undo_button, self.redo_button

    def clear_history(self):
        """Clear all saved states and reset the history."""
        for step in range(1, self.max_step + 1):
            try:
                os.remove(self._get_state_filename(step))
            except:
                pass
        
        self.current_step = 0
        self.max_step = 0
        
        # Save current state as the initial state
        self.save_state()
        logging.info("History cleared and current state saved as initial state")

    def cleanup(self):
        """Clean up temporary files when the application closes."""
        try:
            shutil.rmtree(self.temp_dir)
            logging.info(f"Removed temporary directory: {self.temp_dir}")
        except Exception as e:
            logging.error(f"Error cleaning up temporary files: {e}")


def connect_to_move_mode(canvas, undo_redo_manager):
    """
    Connect the move mode's mouse release event to save state, but only if a move occurred.
    
    Args:
        canvas: The canvas object with the move_mode
        undo_redo_manager: The UndoRedoManager instance
    """
    if hasattr(canvas, 'move_mode') and canvas.move_mode:
        # Store the original mouseReleaseEvent function
        original_mouse_release = canvas.move_mode.mouseReleaseEvent
        
        # Create a new function that calls the original and then saves state
        def enhanced_mouse_release(event):
            # Check if a move was actually in progress *before* calling the original release event
            was_moving = getattr(canvas.move_mode, 'is_moving', False)
            
            # Call the original function first to finalize the move and reset flags
            original_mouse_release(event)
            
            # Now, save state only if a move actually happened during the drag
            if was_moving:
                logging.info("Move detected, saving state for undo/redo.")
                undo_redo_manager.save_state()
            else:
                logging.info("Mouse released, but no move detected. Not saving state.")
        
        # Replace the original function with our enhanced version
        canvas.move_mode.mouseReleaseEvent = enhanced_mouse_release
        logging.info("Connected UndoRedoManager to move_mode mouse release events")
        
        # Save initial state to ensure we have something to undo to
        undo_redo_manager.save_state()
        logging.info("Saved initial canvas state for undo/redo")
    else:
        logging.warning("Could not connect to move_mode: move_mode not found on canvas")


def connect_to_attach_mode(canvas, undo_redo_manager):
    """
    Connect the attach mode's mouse release event to save state when a strand is attached.
    
    Args:
        canvas: The canvas object with the attach_mode
        undo_redo_manager: The UndoRedoManager instance
    """
    if hasattr(canvas, 'attach_mode') and canvas.attach_mode:
        # We won't save state on every strand_attached signal
        # Instead, we'll let the mouseReleaseEvent handle this
        
        # Store the original mouseReleaseEvent function
        original_mouse_release = canvas.attach_mode.mouseReleaseEvent
        
        # Create a new function that calls the original and then saves state
        def enhanced_mouse_release(event):
            # Store initial states to check if something happened
            initial_is_attaching = canvas.attach_mode.is_attaching
            initial_is_first_strand = getattr(canvas, 'is_first_strand', False)
            initial_strand = canvas.current_strand
            
            # Call the original function first
            original_mouse_release(event)
            
            # Check if a strand was actually created or modified during this action
            if ((initial_is_attaching and initial_strand) or                  # Attached a new strand
                (initial_is_first_strand and initial_strand and               # First strand created
                 initial_strand.start != initial_strand.end)):                # And it's not a zero-length strand
                logging.info("Strand created or attached, saving state for undo/redo.")
                undo_redo_manager.save_state()
                
        # Replace the original function with our enhanced version
        canvas.attach_mode.mouseReleaseEvent = enhanced_mouse_release
        logging.info("Connected UndoRedoManager to attach_mode mouse release events")
    else:
        logging.warning("Could not connect to attach_mode: attach_mode not found on canvas")


def setup_undo_redo(canvas, layer_panel):
    """
    Set up undo/redo functionality for the application.
    
    Args:
        canvas: The canvas object
        layer_panel: The layer panel to add buttons to
    
    Returns:
        UndoRedoManager: The created manager instance
    """
    # Create the manager
    manager = UndoRedoManager(canvas, layer_panel)
    
    # Add buttons to the top layout (next to refresh button)
    if hasattr(layer_panel, 'top_panel') and layer_panel.top_panel:
        top_layout = layer_panel.top_panel.layout()
        if top_layout:
            manager.setup_buttons(top_layout)
            logging.info("Added undo/redo buttons to layer panel")
        else:
            logging.warning("Could not find top_layout in layer_panel")
    else:
        logging.warning("Could not find top_panel in layer_panel")
    
    # Connect to move mode mouse release
    connect_to_move_mode(canvas, manager)
    
    # Connect to attach mode as well
    connect_to_attach_mode(canvas, manager)
    
    return manager 