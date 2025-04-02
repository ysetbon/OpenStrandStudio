import os
import json
import glob
import time  # Add time module for timestamp comparison
import logging
import shutil
from datetime import datetime
from PyQt5.QtWidgets import QPushButton, QStyle, QStyleOption, QDialog
from PyQt5.QtCore import QObject, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QPainter, QPainterPath, QPen, QFontMetrics, QColor, QBrush, QLinearGradient, QPalette
from save_load_manager import save_strands, load_strands, apply_loaded_strands
# Import QTimer here to avoid UnboundLocalError
from PyQt5.QtCore import QTimer
from group_layers import CollapsibleGroupWidget # Import at the top level to ensure availability
# Note: We don't import GroupPanel here, as it can cause issues with Qt objects
# We'll work with instances that are already created

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
        self.current_step = 0  # Start at step 0 (empty state, no steps saved yet)
        self.max_step = 0      # Start with no steps saved
        self.temp_dir = self._create_temp_dir()
        self.session_id = datetime.now().strftime("%Y%m%d%H%M%S")
        self.undo_button = None
        self.redo_button = None
        
        # Connect signals
        self.undo_performed.connect(self._update_button_states)
        self.redo_performed.connect(self._update_button_states)
        self.state_saved.connect(self._update_button_states)
        
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
        """Save the current state of strands and groups for undo/redo."""
        # Skip save if flagged to avoid saving states
        if getattr(self, '_skip_save', False):
            logging.info("Skipping state save due to _skip_save flag")
            return
            
        # Ensure the canvas exists
        if not self.canvas:
            logging.warning("Cannot save state: Canvas is not available")
            return
            
        # Check if there is content to save
        if not self.canvas.strands and not hasattr(self.canvas, 'groups'):
            logging.info("No content (strands or groups) to save, skipping state save")
            return
            
        # Only save if content actually exists
        if not self.canvas.strands and not (hasattr(self.canvas, 'groups') and self.canvas.groups):
            logging.info("Empty canvas (no strands or groups), skipping state save")
            return
            
        # Record the timestamp of this save
        current_time = time.time()
        last_save_time = getattr(self, '_last_save_time', 0)
        
        # If we've saved very recently (<300ms), check if we should skip this save
        if (current_time - last_save_time < 0.3) and self.current_step > 0:
            # Check if the current state would be identical to the previous state
            if self._would_be_identical_save():
                logging.info("Skipping identical state save that would occur too soon after previous save")
                return
        
        self._last_save_time = current_time
            
        # Ensure groups are properly saved when needed
        self._ensure_groups_are_saved()
        
        # Process incremental saving
        if self.current_step < self.max_step:
            # Clear away any existing future states
            self._clear_future_states()
            
        # Increment step counter
        self.current_step += 1
        self.max_step = self.current_step
        
        # Save the state file
        filename = self._save_state_file(self.current_step)
        
        if filename:
            # Signal that a state was saved
            logging.info(f"State saved successfully at step {self.current_step}")
            self.state_saved.emit(self.current_step)
            
            # Update button states
            self._update_button_states()
        else:
            # If save failed, revert step counter
            self.current_step -= 1
            if self.max_step > self.current_step:
                self.max_step = self.current_step
            logging.error(f"Failed to save state at step {self.current_step + 1}")

    def _would_be_identical_save(self):
        """Check if the current state would be identical to the previous saved state."""
        if self.current_step <= 0:
            return False
            
        try:
            # Get previous state file path
            prev_filename = self._get_state_filename(self.current_step)
            
            # Basic check: compare strand count and layer names
            if os.path.exists(prev_filename):
                with open(prev_filename, 'r') as f:
                    prev_data = json.load(f)
                    
                # Compare strand count
                current_strand_count = len(self.canvas.strands)
                prev_strand_count = len(prev_data.get('strands', []))
                
                if current_strand_count != prev_strand_count:
                    return False
                    
                # Compare layer names
                current_layer_names = {s.layer_name for s in self.canvas.strands if hasattr(s, 'layer_name')}
                prev_layer_names = {s.get('layer_name') for s in prev_data.get('strands', []) if 'layer_name' in s}
                
                if current_layer_names != prev_layer_names:
                    return False
                    
                # Compare groups - this is a critical check
                current_groups = getattr(self.canvas, 'groups', {})
                prev_groups = prev_data.get('groups', {})
                
                # Compare group count
                current_group_count = len(current_groups)
                prev_group_count = len(prev_groups)
                
                if current_group_count != prev_group_count:
                    return False
                
                # Compare group names to ensure they're the same
                current_group_names = set(current_groups.keys())
                prev_group_names = set(prev_groups.keys())
                
                if current_group_names != prev_group_names:
                    return False
                
                # Compare group contents - even if the same groups exist, their contents might differ
                for group_name in current_group_names:
                    if group_name not in prev_groups:
                        return False
                        
                    # Compare strands in the group
                    current_group_strands = set()
                    prev_group_strands = set()
                    
                    # Extract strand names from current group
                    if 'strands' in current_groups[group_name]:
                        for strand in current_groups[group_name]['strands']:
                            if isinstance(strand, str):
                                current_group_strands.add(strand)
                            elif hasattr(strand, 'layer_name'):
                                current_group_strands.add(strand.layer_name)
                    
                    # Extract strand names from previous group
                    if 'strands' in prev_groups[group_name]:
                        for strand in prev_groups[group_name]['strands']:
                            if isinstance(strand, str):
                                prev_group_strands.add(strand)
                            elif hasattr(strand, 'layer_name'):
                                prev_group_strands.add(strand.layer_name)
                    
                    # If the strands in the group are different, consider it a different state
                    if current_group_strands != prev_group_strands:
                        return False
                
                # If strand count and layer names match, also compare strand positions
                # to detect angle changes and movements
                for i, current_strand in enumerate(self.canvas.strands):
                    if i >= prev_strand_count:
                        return False
                        
                    # Find the corresponding strand in previous data
                    prev_strand = None
                    for s in prev_data.get('strands', []):
                        if s.get('layer_name') == current_strand.layer_name:
                            prev_strand = s
                            break
                            
                    if not prev_strand:
                        return False
                        
                    # Compare positions with some tolerance for floating point differences
                    if (hasattr(current_strand, 'start') and 'start' in prev_strand and
                        hasattr(current_strand, 'end') and 'end' in prev_strand):
                        
                        # If positions differ by more than 0.1 pixels, not identical
                        if (abs(current_strand.start.x() - prev_strand['start']['x']) > 0.1 or
                            abs(current_strand.start.y() - prev_strand['start']['y']) > 0.1 or
                            abs(current_strand.end.x() - prev_strand['end']['x']) > 0.1 or
                            abs(current_strand.end.y() - prev_strand['end']['y']) > 0.1):
                            return False
                    
                # If we made it here, states are identical
                return True
                
        except Exception as e:
            logging.error(f"Error in _would_be_identical_save: {e}")
            
        # Default to allowing the save if anything goes wrong
        return False

    def _clear_future_states(self):
        """Remove any state files from current_step + 1 to max_step."""
        logging.info(f"Clearing future states from step {self.current_step + 1} to {self.max_step}")
        for step in range(self.current_step + 1, self.max_step + 1):
            filename = self._get_state_filename(step)
            try:
                if os.path.exists(filename):
                    os.remove(filename)
                    logging.debug(f"Removed future state file: {filename}")
            except OSError as e:
                logging.warning(f"Could not remove future state file {filename}: {e}")
        
        # Reset max_step to current_step
        self.max_step = self.current_step
        logging.info(f"Reset max_step to current_step: {self.current_step}")

    def _ensure_groups_are_saved(self):
        """Ensure that all groups are properly captured in the next save."""
        if not hasattr(self.canvas, 'group_layer_manager') or not self.canvas.group_layer_manager:
            return
            
        group_manager = self.canvas.group_layer_manager
        
        # If canvas.groups doesn't exist, create it
        if not hasattr(self.canvas, 'groups'):
            self.canvas.groups = {}
            
        # Make sure all groups in the panel are in canvas.groups
        if hasattr(group_manager, 'group_panel') and hasattr(group_manager.group_panel, 'groups'):
            panel_groups = group_manager.group_panel.groups
            
            # Loop through panel groups and ensure they're in canvas.groups
            for group_name, strand_ids in panel_groups.items():
                if group_name not in self.canvas.groups:
                    logging.info(f"Adding missing group {group_name} to canvas.groups for saving")
                    self.canvas.groups[group_name] = strand_ids
                    
            # Log the groups that will be saved
            if self.canvas.groups:
                logging.info(f"Canvas has {len(self.canvas.groups)} groups to save: {list(self.canvas.groups.keys())}")
            else:
                logging.info("No groups to save")

    def _save_state_file(self, step):
        """Save the current state of the canvas to a file."""
        filename = self._get_state_filename(step)
        
        logging.info(f"Saving state to {filename} (current_step={step}, max_step={self.max_step})")
        
        try:
            save_strands(self.canvas.strands, 
                         self.canvas.groups if hasattr(self.canvas, 'groups') else {},
                         filename,
                         self.canvas)
            self.state_saved.emit(step)
            logging.info(f"State saved successfully to {filename}")
            return True
        except Exception as e:
            logging.exception(f"Error saving state to {filename}: {str(e)}")
            return False

    def undo(self):
        """Load the previous state if available."""
        if self.current_step > 0:
            # Store the current strands for comparison
            original_strands = self.canvas.strands.copy() if hasattr(self.canvas, 'strands') else []
            original_strands_count = len(original_strands)
            original_layer_names = {s.layer_name for s in original_strands if hasattr(s, 'layer_name')}
            
            # Store original groups for comparison
            original_groups = {}
            if hasattr(self.canvas, 'groups'):
                original_groups = self.canvas.groups.copy()
            
            # Store original group names and contents for detailed comparison
            original_group_names = set(original_groups.keys())
            original_group_contents = {}
            for group_name, group_data in original_groups.items():
                if 'strands' in group_data:
                    strand_names = set()
                    for strand in group_data['strands']:
                        if isinstance(strand, str):
                            strand_names.add(strand)
                        elif hasattr(strand, 'layer_name'):
                            strand_names.add(strand.layer_name)
                    original_group_contents[group_name] = strand_names
            
            self.current_step -= 1
            
            # Special case: If undoing to step 0 (empty state)
            if self.current_step == 0:
                logging.info("Undoing to initial empty state")
                # Clear the canvas by removing all strands and groups
                self.canvas.strands = []
                if hasattr(self.canvas, 'groups'):
                    self.canvas.groups = {}
                
                # Refresh the UI
                if hasattr(self.layer_panel, 'refresh'):
                    self.layer_panel.refresh()
                if hasattr(self.layer_panel, 'refresh_layers'):
                    self.layer_panel.refresh_layers()
                if hasattr(self.canvas, 'group_layer_manager'):
                    self._refresh_group_panel(False)  # No groups in empty state
                self.canvas.update()
            else:
                # Normal undo to a saved state
                self._load_state(self.current_step)
                
                # Check if the state we just loaded is visually identical to the previous state
                # If yes, continue undoing to the next state
                new_strands = self.canvas.strands
                new_strands_count = len(new_strands)
                new_layer_names = {s.layer_name for s in new_strands if hasattr(s, 'layer_name')}
                
                # Get new groups for comparison
                new_groups = {}
                if hasattr(self.canvas, 'groups'):
                    new_groups = self.canvas.groups.copy()
                
                # Get new group names and contents for detailed comparison
                new_group_names = set(new_groups.keys())
                new_group_contents = {}
                for group_name, group_data in new_groups.items():
                    if 'strands' in group_data:
                        strand_names = set()
                        for strand in group_data['strands']:
                            if isinstance(strand, str):
                                strand_names.add(strand)
                            elif hasattr(strand, 'layer_name'):
                                strand_names.add(strand.layer_name)
                        new_group_contents[group_name] = strand_names
                
                # Check if groups have changed (either names or contents)
                groups_changed = (original_group_names != new_group_names)
                
                # If group names are the same, check if contents have changed
                if not groups_changed:
                    for group_name in original_group_names:
                        if group_name in original_group_contents and group_name in new_group_contents:
                            if original_group_contents[group_name] != new_group_contents[group_name]:
                                groups_changed = True
                                break
                
                # If strand count is the same and layer names are the same,
                # check if key properties (like positions) are identical
                if (new_strands_count == original_strands_count and 
                    new_layer_names == original_layer_names and
                    not groups_changed and
                    self.current_step > 1):
                    
                    logging.info("Detected potentially identical state after undo, checking for visual differences...")
                    
                    # Check for meaningful visual differences between states
                    has_visual_difference = False
                    
                    # Check positions and other visual properties
                    for i, new_strand in enumerate(new_strands):
                        if i >= len(original_strands):
                            has_visual_difference = True
                            break
                            
                        original_strand = original_strands[i]
                        
                        # Check start and end positions
                        if (hasattr(new_strand, 'start') and hasattr(original_strand, 'start') and
                            hasattr(new_strand, 'end') and hasattr(original_strand, 'end')):
                            
                            # If positions differ by more than 0.1 pixels, consider it visually different
                            if (abs(new_strand.start.x() - original_strand.start.x()) > 0.1 or
                                abs(new_strand.start.y() - original_strand.start.y()) > 0.1 or
                                abs(new_strand.end.x() - original_strand.end.x()) > 0.1 or
                                abs(new_strand.end.y() - original_strand.end.y()) > 0.1):
                                has_visual_difference = True
                                break
                        
                        # Check colors (if one is visibly different)
                        if (hasattr(new_strand, 'color') and hasattr(original_strand, 'color')):
                            # Only consider color difference significant if it's visible
                            if (abs(new_strand.color.red() - original_strand.color.red()) > 5 or
                                abs(new_strand.color.green() - original_strand.color.green()) > 5 or
                                abs(new_strand.color.blue() - original_strand.color.blue()) > 5 or
                                abs(new_strand.color.alpha() - original_strand.color.alpha()) > 5):
                                has_visual_difference = True
                                break
                    
                    # If no visual difference found, skip this state and continue undoing
                    if not has_visual_difference:
                        logging.info("States are visually identical, skipping to previous state...")
                        # Recursively call undo to get to the next state
                        return self.undo()
                
            self.undo_performed.emit()
            logging.info(f"Undo performed, now at step {self.current_step}")
            
            # Make sure buttons are properly updated
            self._update_button_states()

            # Additional logging to track what's being refreshed
            logging.info("Refreshing UI after undo operation")
            
            # Try to simulate a refresh button click (preferred method)
            if hasattr(self.layer_panel, 'simulate_refresh_button_click'):
                logging.info("Simulating refresh button click after undo")
                self.layer_panel.simulate_refresh_button_click()
            # Fallback to direct method call if simulate method not available
            elif hasattr(self.layer_panel, 'refresh_layers'):
                logging.info("Explicitly refreshing layer panel")
                self.layer_panel.refresh_layers()
                
            # Final update of the canvas
            self.canvas.update()
        else:
            logging.info("Cannot undo: already at oldest state")

    def redo(self):
        """Load the next state if available."""
        if self.current_step < self.max_step:
            # Store the current strands for comparison
            original_strands = self.canvas.strands.copy() if hasattr(self.canvas, 'strands') else []
            original_strands_count = len(original_strands)
            original_layer_names = {s.layer_name for s in original_strands if hasattr(s, 'layer_name')}
            
            # Store original groups for comparison
            original_groups = {}
            if hasattr(self.canvas, 'groups'):
                original_groups = self.canvas.groups.copy()
            
            # Store original group names and contents for detailed comparison
            original_group_names = set(original_groups.keys())
            original_group_contents = {}
            for group_name, group_data in original_groups.items():
                if 'strands' in group_data:
                    strand_names = set()
                    for strand in group_data['strands']:
                        if isinstance(strand, str):
                            strand_names.add(strand)
                        elif hasattr(strand, 'layer_name'):
                            strand_names.add(strand.layer_name)
                    original_group_contents[group_name] = strand_names
            
            # Special case: If redoing from step 0 (empty state)
            if self.current_step == 0:
                logging.info("Redoing from initial empty state to step 1")
            
            # Increment the step counter
            self.current_step += 1
            
            # Load the state
            result = self._load_state(self.current_step)

            if result:
                # Check if the state we just loaded is visually identical to the previous state
                # If yes, continue redoing to the next state
                new_strands = self.canvas.strands
                new_strands_count = len(new_strands)
                new_layer_names = {s.layer_name for s in new_strands if hasattr(s, 'layer_name')}
                
                # Get new groups for comparison
                new_groups = {}
                if hasattr(self.canvas, 'groups'):
                    new_groups = self.canvas.groups.copy()
                
                # Get new group names and contents for detailed comparison
                new_group_names = set(new_groups.keys())
                new_group_contents = {}
                for group_name, group_data in new_groups.items():
                    if 'strands' in group_data:
                        strand_names = set()
                        for strand in group_data['strands']:
                            if isinstance(strand, str):
                                strand_names.add(strand)
                            elif hasattr(strand, 'layer_name'):
                                strand_names.add(strand.layer_name)
                        new_group_contents[group_name] = strand_names
                
                # Check if groups have changed (either names or contents)
                groups_changed = (original_group_names != new_group_names)
                
                # If group names are the same, check if contents have changed
                if not groups_changed:
                    for group_name in original_group_names:
                        if group_name in original_group_contents and group_name in new_group_contents:
                            if original_group_contents[group_name] != new_group_contents[group_name]:
                                groups_changed = True
                                break
                
                # If strand count is the same and layer names are the same,
                # check if key properties (like positions) are identical
                if (new_strands_count == original_strands_count and 
                    new_layer_names == original_layer_names and
                    not groups_changed and
                    self.current_step < self.max_step):
                    
                    logging.info("Detected potentially identical state after redo, checking for visual differences...")
                    
                    # Check for meaningful visual differences between states
                    has_visual_difference = False
                    
                    # Check positions and other visual properties
                    for i, new_strand in enumerate(new_strands):
                        if i >= len(original_strands):
                            has_visual_difference = True
                            break
                            
                        original_strand = original_strands[i]
                        
                        # Check start and end positions
                        if (hasattr(new_strand, 'start') and hasattr(original_strand, 'start') and
                            hasattr(new_strand, 'end') and hasattr(original_strand, 'end')):
                            
                            # If positions differ by more than 0.1 pixels, consider it visually different
                            if (abs(new_strand.start.x() - original_strand.start.x()) > 0.1 or
                                abs(new_strand.start.y() - original_strand.start.y()) > 0.1 or
                                abs(new_strand.end.x() - original_strand.end.x()) > 0.1 or
                                abs(new_strand.end.y() - original_strand.end.y()) > 0.1):
                                has_visual_difference = True
                                break
                        
                        # Check colors (if one is visibly different)
                        if (hasattr(new_strand, 'color') and hasattr(original_strand, 'color')):
                            # Only consider color difference significant if it's visible
                            if (abs(new_strand.color.red() - original_strand.color.red()) > 5 or
                                abs(new_strand.color.green() - original_strand.color.green()) > 5 or
                                abs(new_strand.color.blue() - original_strand.color.blue()) > 5 or
                                abs(new_strand.color.alpha() - original_strand.color.alpha()) > 5):
                                has_visual_difference = True
                                break
                    
                    # If no visual difference found, skip this state and continue redoing
                    if not has_visual_difference:
                        logging.info("States are visually identical, skipping to next state...")
                        # Recursively call redo to get to the next state
                        return self.redo()
                
                self.redo_performed.emit()
                logging.info(f"Redo performed, now at step {self.current_step}")
            else:
                # Rollback if loading failed
                self.current_step -= 1
                logging.error(f"Redo failed: Could not load state for step {self.current_step + 1}")
                return False # Indicate failure

            # Make sure buttons are properly updated
            self._update_button_states()

            # Try to simulate a refresh button click (preferred method)
            if hasattr(self.layer_panel, 'simulate_refresh_button_click'):
                logging.info("Simulating refresh button click after redo")
                self.layer_panel.simulate_refresh_button_click()
            # Fallback to direct method call if simulate method not available
            elif hasattr(self.layer_panel, 'refresh_layers'):
                logging.info("Explicitly refreshing layer panel")
                self.layer_panel.refresh_layers()

            # Ensure the canvas is fully refreshed after redo
            self.canvas.update()
            
            logging.info("UI updated after redo operation")
            return result
        else:
            logging.info("Cannot redo: already at newest state")
            return False # Indicate failure or no action

    def _clear_group_panel_ui(self, group_panel):
        """Helper method to reliably clear all widgets from the group panel's scroll layout."""
        if not group_panel or not hasattr(group_panel, 'scroll_layout'):
            logging.warning("_clear_group_panel_ui: Group panel or scroll layout not found.")
            return

        layout = group_panel.scroll_layout
        # Remove all widgets from the layout
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                widget = child.widget()
                logging.debug(f"Removing widget from group panel: {widget.objectName() if hasattr(widget, 'objectName') else type(widget)}")
                widget.setParent(None) # Necessary for Qt to schedule deletion
                widget.deleteLater()
            # Clean up the layout item itself if it wasn't holding a widget
            elif child.layout():
                 # Handle nested layouts if necessary, though not expected here
                 pass # Or implement recursive clearing if needed

        # Clear internal tracking in the panel if it exists
        if hasattr(group_panel, 'groups'):
             group_panel.groups.clear()
             logging.debug("Cleared group_panel.groups dictionary.")

        logging.info("Cleared all widgets from group panel UI.")


    def _recreate_group_widgets_from_canvas(self, group_panel):
        """Helper method to recreate group widgets based on self.canvas.groups."""
        if not group_panel or not hasattr(group_panel, 'scroll_layout'):
            logging.error("_recreate_group_widgets_from_canvas: Group panel or scroll layout not found.")
            return
            
        # Debug: Print the canvas.groups content to diagnose issues
        if not hasattr(self.canvas, 'groups') or not self.canvas.groups:
            logging.error("canvas.groups is empty or missing - nothing to recreate")
            return
            
        logging.info(f"Canvas has {len(self.canvas.groups)} groups to recreate: {list(self.canvas.groups.keys())}")
        
        # First clear any existing widgets
        self._clear_group_panel_ui(group_panel)
        logging.info("Cleared existing group panel UI successfully")
        
        # Get the scroll_layout to add widgets to
        scroll_layout = group_panel.scroll_layout
        
        # Setup counters for debugging
        processed = 0
        created = 0
        
        # Iterate through a copy of canvas.groups in case we modify it
        for group_name, group_data in dict(self.canvas.groups).items():
            processed += 1
            logging.info(f"Processing group '{group_name}' from canvas.groups")
            
            # Debug: Print structure of this group's data
            if isinstance(group_data, dict):
                logging.info(f"Group data keys: {list(group_data.keys())}")
                if 'strands' in group_data:
                    strand_count = len(group_data['strands'])
                    logging.info(f"Group has {strand_count} strands")
                    
                    # Check if strands are strings or objects
                    strand_types = []
                    for s in group_data['strands'][:3]:  # Check first few for logging
                        strand_types.append(type(s).__name__)
                    logging.info(f"Strand types: {strand_types}")
            elif isinstance(group_data, list):
                logging.info(f"Group data is a list with {len(group_data)} items")
            else:
                logging.info(f"Group data is type: {type(group_data).__name__}")
            
            try:
                # Create a new widget for this group
                logging.info(f"Creating CollapsibleGroupWidget for group '{group_name}'")
                group_widget = CollapsibleGroupWidget(group_name=group_name, group_panel=group_panel)
                
                # We'll count successful strand additions for this widget
                strand_count = 0
                
                # Convert any string IDs to actual strand objects in the groups data
                # This is crucial for functions like move/rotate that require actual strand objects
                if isinstance(group_data, dict) and 'strands' in group_data:
                    # Create a new list to store the updated strands
                    updated_strands = []
                    for strand in group_data['strands']:
                        if isinstance(strand, str):
                            # It's a layer ID string, find the actual strand object
                            strand_obj = None
                            if hasattr(self.canvas, 'find_strand_by_name'):
                                strand_obj = self.canvas.find_strand_by_name(strand)
                            else:
                                # Fallback: search through strands list
                                for s in self.canvas.strands:
                                    if hasattr(s, 'layer_name') and s.layer_name == strand:
                                        strand_obj = s
                                        break
                            
                            if strand_obj:
                                updated_strands.append(strand_obj)
                                logging.info(f"Converted strand ID '{strand}' to actual strand object")
                            else:
                                # Keep the string if we can't find the object
                                updated_strands.append(strand)
                                logging.warning(f"Could not find strand object for ID '{strand}'")
                        else:
                            # It's already a strand object (or something else), keep it as is
                            updated_strands.append(strand)
                    
                    # Replace the old strands list with the updated one
                    group_data['strands'] = updated_strands
                    # Update the canvas.groups entry
                    self.canvas.groups[group_name] = group_data
                    logging.info(f"Updated strands in group data for '{group_name}' with actual strand objects")
                
                # Determine what strands to process
                if 'strands' in group_data:
                    strands_to_process = group_data['strands']
                elif isinstance(group_data, list):
                    strands_to_process = group_data
                else:
                    logging.warning(f"Cannot determine strands for group '{group_name}'")
                    strands_to_process = []
                
                logging.info(f"Found {len(strands_to_process)} strands to process for group '{group_name}'")
                
                for strand in strands_to_process:
                    # Handle both strand objects and layer names
                    if hasattr(strand, 'layer_name'):
                        layer_id = strand.layer_name
                        color = strand.color if hasattr(strand, 'color') else None
                        is_masked = hasattr(strand, 'is_masked') and strand.is_masked
                    else:
                        # We have a layer ID, try to find the actual strand
                        layer_id = strand
                        # Try to find the strand object in canvas
                        strand_obj = None
                        if hasattr(self.canvas, 'find_strand_by_name'):
                            strand_obj = self.canvas.find_strand_by_name(layer_id)
                        else:
                            logging.warning(f"Canvas lacks find_strand_by_name method - using fallback")
                            # Fallback: search through strands list
                            for s in self.canvas.strands:
                                if hasattr(s, 'layer_name') and s.layer_name == layer_id:
                                    strand_obj = s
                                    break
                                    
                        if strand_obj:
                            color = strand_obj.color if hasattr(strand_obj, 'color') else None
                            is_masked = hasattr(strand_obj, 'is_masked') and strand_obj.is_masked
                        else:
                            # Use defaults if we can't find the strand
                            color = None
                            is_masked = False
                    
                    # Add the layer/strand to the widget
                    # Try multiple approaches to ensure it gets added
                    added = False
                    
                    # Approach 1: Add strand object directly if it has a layer_name
                    try:
                        if hasattr(strand, 'layer_name'):
                            group_widget.add_layer(strand.layer_name, strand.color, is_masked)
                            strand_count += 1
                            added = True
                            logging.info(f"Added layer '{layer_id}' to group widget '{group_name}' using strand object")
                    except Exception as e1:
                        logging.warning(f"Error adding strand object directly: {e1}")
                        
                    # Approach 2: Add using specific attributes    
                    if not added:
                        try:
                            group_widget.add_layer(layer_id, color, is_masked)
                            strand_count += 1
                            added = True
                            logging.info(f"Added layer '{layer_id}' to group widget '{group_name}' using layer ID")
                        except Exception as e2:
                            logging.warning(f"Error adding layer with specific attributes: {e2}")
                    
                    # Approach 3: Add just the ID as a fallback
                    if not added:
                        try:
                            group_widget.add_layer(layer_id)
                            strand_count += 1
                            added = True
                            logging.info(f"Added layer '{layer_id}' to group widget '{group_name}' using ID only")
                        except Exception as e3:
                            logging.error(f"All attempts to add layer '{layer_id}' failed: {e3}")
                
                # Check if any strands were added before proceeding
                if strand_count == 0:
                    logging.warning(f"No strands were added to group '{group_name}' - skipping widget")
                    continue
                
                # Add the widget to the scroll layout
                logging.info(f"Adding group widget to scroll layout with {strand_count} layers")
                scroll_layout.addWidget(group_widget)
                
                # Store the group data in the panel's groups dictionary
                try:
                    # IMPORTANT: Ensure we use the updated group_data with actual strand objects
                    # and properly reference the same strands as in canvas.groups
                    group_panel.groups[group_name] = {
                        'strands': self.canvas.groups[group_name].get('strands', []),
                        'layers': [s.layer_name if hasattr(s, 'layer_name') else s 
                                   for s in self.canvas.groups[group_name].get('strands', [])],
                        'widget': group_widget
                    }
                    
                    # Preserve main_strands if available, converting to objects if needed
                    if 'main_strands' in group_data:
                        main_strands_list = []
                        for ms in group_data['main_strands']:
                            if hasattr(ms, 'layer_name'):
                                # Already a strand object
                                main_strands_list.append(ms)
                            else:
                                # Try to find the strand object
                                found = False
                                for s in self.canvas.strands:
                                    if hasattr(s, 'layer_name') and s.layer_name == ms:
                                        main_strands_list.append(s)
                                        found = True
                                        break
                                if not found:
                                    # Add the string ID as fallback
                                    main_strands_list.append(ms)
                        
                        group_panel.groups[group_name]['main_strands'] = main_strands_list
                    
                    # Preserve control_points if available
                    if 'control_points' in group_data:
                        group_panel.groups[group_name]['control_points'] = group_data['control_points']
                        
                    logging.info(f"Group '{group_name}' added to panel.groups with {len(group_panel.groups[group_name]['strands'])} strands")
                except Exception as e:
                    logging.error(f"Error adding group to panel.groups: {e}")
                
                # If this widget should have collapsed state, set it
                if hasattr(group_widget, 'toggle_collapse') and 'collapsed' in group_data and group_data['collapsed']:
                    try:
                        group_widget.toggle_collapse()
                        logging.info(f"Set collapsed state for group '{group_name}'")
                    except Exception as e:
                        logging.warning(f"Error setting collapsed state: {e}")

                # Fix/Reconnect the move and rotate signals with correct parameter capture
                try:
                    # We need to ensure the group_name is correctly captured in the lambda
                    # by creating a proper closure with default parameter values
                    
                    # For the move function
                    if hasattr(group_widget, 'move_button') and hasattr(group_widget.move_button, 'clicked'):
                        try:
                            # Disconnect any existing connections
                            group_widget.move_button.clicked.disconnect()
                        except (TypeError, RuntimeError):
                            # Expected if no connections exist yet
                            pass
                            
                        # Create a proper function with correct parameter capture
                        def create_move_handler(name):
                            return lambda checked=False: group_panel.start_group_move(name)
                            
                        # Connect the handler with the specific group name
                        move_handler = create_move_handler(group_name)
                        group_widget.move_button.clicked.connect(move_handler)
                        logging.info(f"Reconnected move signal for group '{group_name}'")
                    
                    # For the rotate function
                    if hasattr(group_widget, 'rotate_button') and hasattr(group_widget.rotate_button, 'clicked'):
                        try:
                            # Disconnect any existing connections
                            group_widget.rotate_button.clicked.disconnect()
                        except (TypeError, RuntimeError):
                            # Expected if no connections exist yet
                            pass
                            
                        # Create a proper function with correct parameter capture
                        def create_rotate_handler(name):
                            return lambda checked=False: group_panel.start_group_rotation(name)
                            
                        # Connect the handler with the specific group name
                        rotate_handler = create_rotate_handler(group_name)
                        group_widget.rotate_button.clicked.connect(rotate_handler)
                        logging.info(f"Reconnected rotate signal for group '{group_name}'")
                except Exception as e:
                    logging.error(f"Error connecting signals: {e}")
                
                created += 1

            except Exception as e:
                logging.error(f"Error creating widget for group '{group_name}': {str(e)}", exc_info=True)
        
        # Force update
        try:
            # Update scrollbar and layout
            if hasattr(group_panel, 'scroll_area') and group_panel.scroll_area:
                group_panel.scroll_area.verticalScrollBar().setValue(0)
                
            # Make sure the panel gets properly refreshed
            scroll_layout.activate()
            group_panel.updateGeometry()
            group_panel.update()
            
            logging.info(f"Forced UI update on group panel")
        except Exception as e:
            logging.error(f"Error during final UI update: {e}")
            
        logging.info(f"Finished recreating group panel UI. Processed: {processed}, Created: {created}, Layout has {scroll_layout.count()} widgets.")
        
        # Output the final result of the groups stored in the panel
        if hasattr(group_panel, 'groups'):
            logging.info(f"FINAL RESULT: Group panel now has {len(group_panel.groups)} groups: {list(group_panel.groups.keys())}")
            
        # Return success/failure status
        return created > 0

    def _refresh_group_panel(self, has_loaded_groups):
        """
        Refreshes the group panel UI based on the loaded state.
        Always clears the UI first, then rebuilds from self.canvas.groups if necessary.
        """
        logging.info(f"Refreshing group panel. State has groups: {has_loaded_groups}")

        group_manager = getattr(self.canvas, 'group_layer_manager', None)
        if not group_manager:
            logging.warning("Cannot refresh group panel: No group_layer_manager found on canvas.")
            return

        group_panel = getattr(group_manager, 'group_panel', None)
        if not group_panel:
            logging.warning("Cannot refresh group panel: No group_panel found on group_layer_manager.")
            return

        # --- Step 1: Always Clear the UI ---
        logging.info("Clearing existing group panel UI before refresh...")
        self._clear_group_panel_ui(group_panel)

        # --- Step 2: Recreate UI if state has groups ---
        if has_loaded_groups:
            logging.info("State has groups. Recreating group panel UI from canvas.groups...")
            if hasattr(self.canvas, 'groups') and self.canvas.groups:
                 self._recreate_group_widgets_from_canvas(group_panel)
            else:
                 logging.warning("State reported having groups, but self.canvas.groups is empty or missing.")
        else:
            logging.info("State has no groups. Group panel UI remains clear.")

        # --- Step 3: Final UI Update ---
        # Force an update on the panel to ensure layout changes are visible
        try:
            group_panel.update()
            if hasattr(group_panel, 'scroll_area') and group_panel.scroll_area:
                 group_panel.scroll_area.update()
            logging.info("Updated group panel and scroll area after refresh.")
        except Exception as e:
            logging.error(f"Error updating group panel UI components: {str(e)}")

        logging.info(f"Group panel refresh complete. Final widget count in layout: {group_panel.scroll_layout.count()}")

    def _load_state(self, step):
        """Load the state for the specified step and apply it."""
        filename = self._get_state_filename(step)
        logging.info(f"Attempting to load state from step {step}: {filename}")

        if not os.path.exists(filename):
            logging.warning(f"State file does not exist: {filename}")
            return False

        try:
            # --- Step 1: Load data from file and inspect its structure --- 
            logging.info(f"Loading strands and groups data from file: {filename}")
            
            # First inspect the raw JSON to understand the structure
            with open(filename, 'r') as f:
                raw_data = json.load(f)
                
            # Log information about the raw data structure
            has_groups_in_file = 'groups' in raw_data and bool(raw_data.get('groups', {}))
            logging.info(f"File contains group data: {has_groups_in_file}")
            if has_groups_in_file:
                group_count = len(raw_data.get('groups', {}))
                group_names = list(raw_data.get('groups', {}).keys())
                logging.info(f"Found {group_count} groups in file: {group_names}")
            
            # Load the data using the normal method
            loaded_strands, loaded_groups_data = load_strands(filename, self.canvas)
            state_has_groups = bool(loaded_groups_data)
            logging.info(f"Loaded {len(loaded_strands)} strands and {len(loaded_groups_data)} groups")
            logging.info(f"State has groups according to loaded_groups_data: {state_has_groups}")
            
            # Check if we lost groups during loading
            if has_groups_in_file and not state_has_groups:
                logging.warning("Groups found in file but not returned by load_strands - attempting recovery")
                
                # Try to manually extract group data from the file
                if 'groups' in raw_data:
                    loaded_groups_data = raw_data['groups']
                    state_has_groups = bool(loaded_groups_data)
                    logging.info(f"Manually recovered {len(loaded_groups_data)} groups from file")

            # --- Step 2: Replace canvas data --- 
            # Completely replace the existing strands and groups with the loaded data
            self.canvas.strands = loaded_strands
            
            # Ensure self.canvas.groups exists
            if not hasattr(self.canvas, 'groups'):
                self.canvas.groups = {}
                
            # Set the groups data on the canvas
            if state_has_groups:
                self.canvas.groups = loaded_groups_data
                logging.info(f"Set canvas.groups with {len(loaded_groups_data)} groups: {list(loaded_groups_data.keys())}")
            else:
                # Clear any existing groups if the state has none
                self.canvas.groups = {}
                logging.info("Cleared canvas.groups (state has no groups)")
                
            logging.info("Replaced canvas strands and groups with loaded data")
            
            # Update strand properties (like canvas reference) after loading
            for strand in self.canvas.strands:
                 if hasattr(strand, 'set_canvas'):
                      strand.set_canvas(self.canvas)
                 # Add any other necessary post-load initialization for strands here
                 
            # --- Step 3: Refresh UI Panels --- 
            # Refresh layer panel based on the new self.canvas.strands
            logging.info("Refreshing Layer Panel UI...")
            self._refresh_layer_panel() 

            # Try to simulate a refresh button click (preferred method)
            if hasattr(self.layer_panel, 'simulate_refresh_button_click'):
                logging.info("Simulating refresh button click after loading state")
                self.layer_panel.simulate_refresh_button_click()
            # Fallback to direct method call if simulate method not available
            elif hasattr(self.layer_panel, 'refresh_layers'):
                logging.info("Explicitly refreshing layer panel UI...")
                self.layer_panel.refresh_layers()

            # Refresh group panel based on the new self.canvas.groups
            logging.info("Refreshing Group Panel UI...")
            success = self._refresh_group_panel(state_has_groups) # Pass the flag indicating if groups exist
            
            if state_has_groups and not success:
                logging.warning("Group panel refresh unsuccessful - performing additional recovery steps")
                
                # Additional recovery steps for groups
                if hasattr(self.canvas, 'group_layer_manager') and self.canvas.group_layer_manager:
                    try:
                        group_manager = self.canvas.group_layer_manager
                        if hasattr(group_manager, 'refresh'):
                            logging.info("Calling group_layer_manager.refresh() as additional recovery")
                            group_manager.refresh()
                    except Exception as e:
                        logging.error(f"Error during group recovery: {e}")

            # --- Step 4: Final Canvas Update --- 
            logging.info("Updating canvas display...")
            self.canvas.update()
            
            # Optional: Update selection state if needed (e.g., clear selection)
            if hasattr(self.canvas, 'deselect_strand'):
                 self.canvas.deselect_strand()
                 logging.debug("Deselected strand after loading state.")

            logging.info(f"State loaded and applied successfully from step {step}")
            return True # Indicate success
            
        except Exception as e:
            logging.exception(f"CRITICAL Error loading state from step {step} ({filename}): {str(e)}")
            # Consider rolling back or handling the error state more gracefully here if needed
            return False # Indicate failure
    
    def _refresh_layer_panel(self):
        """Refresh the layer panel UI to match loaded state."""
        if hasattr(self.layer_panel, 'refresh'):
            logging.info("Refreshing layer panel via _refresh_layer_panel")
            self.layer_panel.refresh()
        else:
            logging.warning("Layer panel has no refresh method")
        
        # Also refresh/update the layer state manager if available
        if hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
            if hasattr(self.canvas.layer_state_manager, 'update_layer_order'):
                layer_names = [strand.layer_name for strand in self.canvas.strands if hasattr(strand, 'layer_name')]
                self.canvas.layer_state_manager.update_layer_order(layer_names)
                logging.info(f"Updated layer state manager order with {len(layer_names)} layers")

    def _force_clear_all_groups(self):
        """Force a complete removal of all groups from both canvas and UI."""
        logging.info("Beginning force clear of all groups")
        
        # First try to clear the group manager through canvas
        try:
            if hasattr(self.canvas, 'group_layer_manager'):
                group_manager = self.canvas.group_layer_manager
                
                # Try using clear method if it exists
                if hasattr(group_manager, 'clear'):
                    group_manager.clear()
                # Or clear method on tree if it exists
                elif hasattr(group_manager, 'tree') and hasattr(group_manager.tree, 'clear'):
                    group_manager.tree.clear()
        except Exception as e:
            logging.error(f"Error clearing group_manager: {str(e)}")
            
        # Then clear the groups from the panel itself
        if hasattr(self.canvas, 'group_layer_manager') and hasattr(self.canvas.group_layer_manager, 'group_panel'):
            group_panel = self.canvas.group_layer_manager.group_panel
            
            # Get all groups from the panel and delete them one by one
            groups_to_delete = []
            if hasattr(group_panel, 'groups'):
                groups_to_delete = list(group_panel.groups.keys())
                
            logging.info(f"Found {len(groups_to_delete)} groups to clear from panel: {groups_to_delete}")
                
            for group_name in groups_to_delete:
                try:
                    # Check if group exists in canvas
                    if not hasattr(self.canvas, 'groups') or group_name not in self.canvas.groups:
                        logging.warning(f"Group '{group_name}' not found in canvas.")
                    
                    # Try to use the delete_group method
                    if hasattr(group_panel, 'delete_group'):
                        logging.info(f"Group operation: delete on group {group_name} with layers {group_panel.groups.get(group_name, [])}")
                        group_panel.delete_group(group_name)
                        logging.info(f"Group '{group_name}' deleted.")
                except Exception as e:
                    logging.error(f"Error deleting group '{group_name}': {str(e)}")
                    
            # Force reset the groups dictionary to be empty
            if hasattr(group_panel, 'groups'):
                group_panel.groups = {}
                logging.info("Forcibly reset panel.groups to empty dict")
                
            # Remove any remaining widgets from the scroll layout
            if hasattr(group_panel, 'scroll_layout'):
                # Find all widgets in the scroll layout
                widget_count = group_panel.scroll_layout.count()
                logging.info(f"Found {widget_count} widgets in scroll_layout")
                
                # Remove all widgets
                for i in range(widget_count - 1, -1, -1):  # Remove in reverse order
                    try:
                        widget = group_panel.scroll_layout.itemAt(i).widget()
                        if widget:
                            widget.setParent(None)
                            widget.deleteLater()
                    except Exception as e:
                        logging.error(f"Error removing widget at index {i}: {str(e)}")
                        
                logging.info(f"Removed all {widget_count} widgets from scroll_layout")
                
        # Ensure canvas.groups is empty
        if hasattr(self.canvas, 'groups'):
            self.canvas.groups = {}
            
        logging.info("Completed force clear of all groups")
    
    def _ensure_all_groups_exist_in_panel(self, group_manager):
        """Ensure all groups in canvas.groups exist in the panel."""
        logging.info("Ensuring all groups exist in panel")
        if not hasattr(group_manager, 'group_panel') or not group_manager.group_panel:
            return
            
        group_panel = group_manager.group_panel
        
        # Get all groups in the panel
        panel_groups = set(group_panel.groups.keys()) if hasattr(group_panel, 'groups') else set()
        
        # Get all groups in the canvas
        canvas_groups = set(self.canvas.groups.keys()) if hasattr(self.canvas, 'groups') else set()
        
        # Find missing groups
        missing_groups = canvas_groups - panel_groups
        
        if missing_groups:
            logging.info(f"Found {len(missing_groups)} groups missing from panel: {missing_groups}")
            
            # Create each missing group
            for group_name in missing_groups:
                if group_name in self.canvas.groups and 'strands' in self.canvas.groups[group_name]:
                    strands = self.canvas.groups[group_name]['strands']
                    if strands and hasattr(group_panel, 'create_group'):
                        try:
                            logging.info(f"Creating missing group '{group_name}' with {len(strands)} strands")
                            group_panel.create_group(group_name, strands)
                        except Exception as e:
                            logging.error(f"Error creating missing group '{group_name}': {e}")
        else:
            logging.info("All groups already exist in panel")
    
    def _create_all_groups_in_panel(self, group_panel):
        """Create all groups from canvas.groups in the panel."""
        logging.info(f"Creating all groups from canvas.groups in panel")
        
        # Loop through the available groups in canvas.groups
        for group_name, group_data in self.canvas.groups.items():
            if 'strands' in group_data and group_data['strands']:
                # If panel has create_group method, use it
                if hasattr(group_panel, 'create_group'):
                    logging.info(f"Creating group '{group_name}' with {len(group_data['strands'])} strands")
                    try:
                        # Create group with strands
                        group_panel.create_group(group_name, group_data['strands'])
                        logging.info(f"Successfully created group '{group_name}' in panel")
                    except Exception as e:
                        logging.error(f"Error creating group '{group_name}': {e}")
        
        logging.info("Finished creating all groups in panel")

    def load_specific_state(self, filepath):
        """Loads a specific state file, applies it, and preserves the entire history of the loaded session."""
        logging.info(f"Attempting to load specific state from file: {filepath}")
        if os.path.exists(filepath):
            try:
                # Extract the session ID and step from the filepath
                # Filepath format is: /path/to/temp_dir/YYYYMMDDHHMMSS_step.json
                filename = os.path.basename(filepath)
                logging.info(f"Processing filename: {filename}")
                
                # Store the original session ID for cleanup
                original_session_id = self.session_id
                logging.info(f"Original session ID before loading: {original_session_id}")
                
                # Parse the session ID and step from the filename
                parts = filename.split('_')
                if len(parts) >= 2:
                    # Extract the session ID (timestamp part before the underscore)
                    loaded_session_id = parts[0]
                    
                    # Extract the step number from the filename (part after underscore, before .json)
                    loaded_step = int(parts[1].split('.')[0])
                    
                    logging.info(f"Extracted session ID: {loaded_session_id}, step: {loaded_step}")
                    
                    # Update the current session ID to continue with the loaded session
                    self.session_id = loaded_session_id
                    logging.info(f"Set current session ID to: {self.session_id}")
                else:
                    logging.warning(f"Could not parse session ID from filename: {filename}, keeping original session ID")
                    return False
                
                # Find all available states for this session
                available_steps = []
                max_step = 0
                
                try:
                    for file in os.listdir(self.temp_dir):
                        if file.startswith(f"{loaded_session_id}_") and file.endswith(".json"):
                            try:
                                step = int(file.split('_')[1].split('.')[0])
                                available_steps.append(step)
                                max_step = max(max_step, step)
                            except (ValueError, IndexError):
                                continue
                    
                    available_steps.sort()
                    logging.info(f"Found {len(available_steps)} steps for session {loaded_session_id}: {available_steps}")
                    logging.info(f"Maximum step found: {max_step}")
                except Exception as e:
                    logging.error(f"Error scanning for available steps: {e}")
                    return False
                
                # Clean up any files from the current session before switching
                try:
                    for file in os.listdir(self.temp_dir):
                        if file.startswith(f"{original_session_id}_") and file.endswith(".json"):
                            try:
                                os.remove(os.path.join(self.temp_dir, file))
                                logging.debug(f"Removed file from original session: {file}")
                            except:
                                logging.warning(f"Failed to remove file: {file}")
                except Exception as e:
                    logging.error(f"Error cleaning up original session files: {e}")
                
                # Load strands and groups from the specified file
                strands, groups = load_strands(filepath, self.canvas)
                logging.info(f"Loaded {len(strands)} strands and {len(groups)} groups from {filepath}")
                
                # First inspect the raw JSON directly to ensure we didn't miss anything
                with open(filepath, 'r') as f:
                    raw_data = json.load(f)
                    has_groups_in_file = 'groups' in raw_data and bool(raw_data.get('groups', {}))
                    if has_groups_in_file:
                        group_count = len(raw_data.get('groups', {}))
                        group_names = list(raw_data.get('groups', {}).keys())
                        logging.info(f"Raw file contains {group_count} groups: {group_names}")
                        
                        # Ensure the groups data is properly loaded
                        if not groups and has_groups_in_file:
                            groups = raw_data.get('groups', {})
                            logging.info(f"Recovered groups directly from raw file data: {list(groups.keys())}")

                # Apply the loaded state to the canvas
                self.canvas.strands = strands
                if hasattr(self.canvas, 'groups'):
                    self.canvas.groups = groups
                    logging.info(f"Applied loaded state to canvas with {len(groups)} groups: {list(groups.keys())}")
                else:
                    self.canvas.groups = {}
                    logging.warning("Canvas had no groups attribute, created empty one")

                # Set the step pointers to match the loaded state
                self.current_step = loaded_step
                self.max_step = max_step
                logging.info(f"Set current_step to {self.current_step} and max_step to {self.max_step}")

                # Refresh UI
                if hasattr(self.layer_panel, 'refresh'):
                    self.layer_panel.refresh()
                    logging.info("Layer panel refreshed via its refresh method")
                
                # Now handle the group panel update
                state_has_groups = bool(self.canvas.groups)
                logging.info(f"State has groups: {state_has_groups}")
                
                # --- Perform comprehensive group panel refresh ---
                if state_has_groups and hasattr(self.canvas, 'group_layer_manager') and self.canvas.group_layer_manager:
                    group_manager = self.canvas.group_layer_manager
                    group_panel = getattr(group_manager, 'group_panel', None)
                    
                    if group_panel:
                        # First clear the current group panel UI
                        logging.info("Clearing group panel UI before rebuilding it")
                        self._clear_group_panel_ui(group_panel)
                        
                        # Rebuild the group panel UI from scratch
                        success = self._recreate_group_widgets_from_canvas(group_panel)
                        logging.info(f"Recreated group widgets from canvas.groups: success={success}")
                        
                        # If that didn't work, try group_layer_manager's refresh method
                        if not success and hasattr(group_manager, 'refresh'):
                            logging.info("Calling group_layer_manager.refresh() as a fallback")
                            group_manager.refresh()
                            
                        # Final approach: recreate each group manually
                        if hasattr(group_panel, 'create_group') and not success:
                            logging.info("Final approach: Manually creating each group")
                            for group_name, group_data in self.canvas.groups.items():
                                if 'strands' in group_data and group_data['strands']:
                                    try:
                                        logging.info(f"Manually creating group '{group_name}' with {len(group_data['strands'])} strands")
                                        group_panel.create_group(group_name, group_data['strands'])
                                    except Exception as e:
                                        logging.error(f"Error creating group '{group_name}': {e}")
                            
                        # Force UI update
                        group_panel.update()
                        if hasattr(group_panel, 'scroll_area') and group_panel.scroll_area:
                            group_panel.scroll_area.update()
                        
                        logging.info(f"Final group count in panel: {len(group_panel.groups) if hasattr(group_panel, 'groups') else 'Unknown'}")
                
                self.canvas.update()
                self.state_saved.emit(self.current_step) # Emit signal to update buttons

                # Verify the session ID is still set correctly after all operations
                logging.info(f"Final session ID after all operations: {self.session_id}")
                test_filename = self._get_state_filename(self.current_step + 1)  # Get what the next state filename would be
                logging.info(f"Next state would be saved as: {test_filename}")

                logging.info(f"Successfully loaded state from {filepath} with full history preservation.")
                return True
            except Exception as e:
                logging.exception(f"Error loading specific state from {filepath}: {e}")
                return False
        else:
            logging.error(f"Specific state file not found: {filepath}")
            return False

    def _update_button_states(self):
        """Update the enabled state of undo/redo buttons."""
        if self.undo_button:
            # Enable undo if we have a current step greater than 0
            # This allows undoing from step 1 to the empty state
            can_undo = self.current_step > 0
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
                "border_hover": "#1d4121",        # Darker border on hover
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

    def clear_history(self, save_current=True):
        """Clear all saved states for the current session and reset the history."""
        logging.info(f"Clearing history for session {self.session_id}. Save current state: {save_current}")
        for step in range(1, self.max_step + 1):
            filename = self._get_state_filename(step)
            try:
                if os.path.exists(filename):
                    os.remove(filename)
                    logging.debug(f"Removed state file: {filename}")
            except OSError as e:
                logging.warning(f"Could not remove state file {filename}: {e}")

        self.current_step = 0
        self.max_step = 0

        if save_current:
            # Save current state as the initial state (step 1)
            self.save_state() # This increments current_step to 1 and saves
            logging.info("History cleared and current state saved as initial state.")
        else:
            # If not saving current, just reset steps and update buttons
            self._update_button_states()
            logging.info("History cleared without saving current state.")
            
    def clear_all_past_history(self):
        """Deletes all *.json state files from the temp_states directory, 
           excluding the files belonging to the current session."""
        logging.info(f"Clearing all past history. Current session ID: {self.session_id}")
        cleared_count = 0
        error_count = 0
        current_session_prefix = f"{self.session_id}_"

        try:
            for filename in os.listdir(self.temp_dir):
                # Check if it's a state file and NOT from the current session
                if filename.endswith(".json") and not filename.startswith(current_session_prefix):
                    filepath = os.path.join(self.temp_dir, filename)
                    try:
                        os.remove(filepath)
                        logging.info(f"Deleted past history file: {filepath}")
                        cleared_count += 1
                    except OSError as e:
                        logging.error(f"Could not delete past history file {filepath}: {e}")
                        error_count += 1
            logging.info(f"Finished clearing past history. Deleted: {cleared_count}, Errors: {error_count}")
        except Exception as e:
            logging.error(f"Error listing directory {self.temp_dir} for history clearing: {e}")
            
        # Note: This function only deletes files, it doesn't affect the current session's history management

    def cleanup(self):
        """Clean up temporary files when the application closes."""
        try:
            shutil.rmtree(self.temp_dir)
            logging.info(f"Removed temporary directory: {self.temp_dir}")
        except Exception as e:
            logging.error(f"Error cleaning up temporary files: {e}")

    def get_temp_dir(self):
        """Returns the path to the temporary directory."""
        return self.temp_dir

    def get_session_id(self):
        """Returns the current session ID."""
        return self.session_id

    def _create_group_in_panel(self, group_name, group_data):
        """Directly create a group in the panel from loaded data."""
        logging.info(f"Directly creating group in panel: {group_name}")
        
        if not hasattr(self.canvas, 'group_layer_manager') or not self.canvas.group_layer_manager:
            logging.warning("Cannot create group in panel: group_layer_manager not found")
            return False
            
        if not hasattr(self.canvas.group_layer_manager, 'group_panel'):
            logging.warning("Cannot create group in panel: group_panel not found")
            return False
            
        group_panel = self.canvas.group_layer_manager.group_panel
        
        # Skip if group already exists in panel
        if hasattr(group_panel, 'groups') and group_name in group_panel.groups:
            logging.info(f"Group {group_name} already exists in panel")
            return True
        
        # Extract strand IDs from the group data, which can be in different formats
        strand_ids = []
        
        if isinstance(group_data, list):
            # If group_data is a list, it's a list of strand IDs
            strand_ids = group_data
        elif isinstance(group_data, dict):
            # If group_data is a dict, check several possible keys for strand data
            if 'strands' in group_data:
                strand_list = group_data['strands']
                for strand in strand_list:
                    if isinstance(strand, str):
                        # It's already a string ID
                        strand_ids.append(strand)
                    elif hasattr(strand, 'layer_name'):
                        # It's a strand object
                        strand_ids.append(strand.layer_name)
            elif 'layers' in group_data:
                # Layers are typically string IDs
                strand_ids = group_data['layers']
        
        logging.info(f"Extracted {len(strand_ids)} strand IDs for group {group_name}")
        
        # Now convert those IDs to actual strand objects
        existing_strands = []
        for strand_id in strand_ids:
            # Find the matching strand object in the canvas
            for strand in self.canvas.strands:
                if hasattr(strand, 'layer_name') and strand.layer_name == strand_id:
                    existing_strands.append(strand)
                    logging.info(f"Found strand object for ID '{strand_id}'")
                    break
        
        if not existing_strands:
            logging.warning(f"No existing strands found for group {group_name}")
            return False
            
        logging.info(f"Creating group {group_name} with {len(existing_strands)} strands")
        
        # Try several approaches to create the group
        try:
            # First approach: Use the standard create_group method
            group_panel.create_group(group_name, existing_strands)
            logging.info(f"Created group {group_name} using standard method")
            return True
        except Exception as e:
            logging.warning(f"Error using standard create_group method: {str(e)}")
            
            # Second approach: Try to use the CollapsibleGroupWidget directly
            try:
                # Create a new widget
                widget = CollapsibleGroupWidget(group_name=group_name, group_panel=group_panel)
                
                # Add strands to it
                for strand in existing_strands:
                    widget.add_layer(
                        layer_name=strand.layer_name,
                        color=strand.color if hasattr(strand, 'color') else None,
                        is_masked=hasattr(strand, 'is_masked') and strand.is_masked
                    )
                
                # Add to the scroll layout
                if hasattr(group_panel, 'scroll_layout'):
                    group_panel.scroll_layout.addWidget(widget)
                    
                    # Store in groups dictionary
                    group_panel.groups[group_name] = {
                        'strands': existing_strands,
                        'layers': [s.layer_name for s in existing_strands],
                        'widget': widget
                    }
                    logging.info(f"Created group {group_name} using direct widget creation")
                    return True
            except Exception as e:
                logging.warning(f"Error creating group widget directly: {str(e)}")
        
        # If all approaches failed, log an error
        logging.error(f"All approaches to create group {group_name} failed")
        return False

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
        
        # Do NOT save initial state automatically - only save when user actions create content
        # undo_redo_manager.save_state() - REMOVED
        logging.info("Initial empty state will not be saved for undo/redo until user creates content")
    else:
        logging.warning("Could not connect to move_mode: move_mode not found on canvas")


def connect_to_attach_mode(canvas, undo_redo_manager):
    """
    Connect the attach mode's mouse release event to save state when a strand is attached.
    Prevents duplicate saves for a single attach action.
    
    Args:
        canvas: The canvas object with the attach_mode
        undo_redo_manager: The UndoRedoManager instance
    """
    if hasattr(canvas, 'attach_mode') and canvas.attach_mode:
        original_mouse_release = canvas.attach_mode.mouseReleaseEvent
        
        def enhanced_mouse_release(event):
            # Store initial state for comparison
            initial_strand_count = len(canvas.strands)
            initial_strand_names = {s.layer_name for s in canvas.strands if hasattr(s, 'layer_name')}
            
            # Store initial groups for comparison
            initial_groups = {}
            if hasattr(canvas, 'groups'):
                initial_groups = canvas.groups.copy()
            
            # Call the original function first to perform the attach/creation
            original_mouse_release(event)
            
            # Get current state after the action
            current_strand_count = len(canvas.strands)
            current_strand_names = {s.layer_name for s in canvas.strands if hasattr(s, 'layer_name')}
            
            # Get current groups after the action
            current_groups = {}
            if hasattr(canvas, 'groups'):
                current_groups = canvas.groups.copy()

            # Check if a new strand was *actually* added during this specific event
            strand_added = (current_strand_count > initial_strand_count) or \
                           bool(current_strand_names - initial_strand_names) # Check if new names appeared
            
            # Check if groups changed
            groups_changed = initial_groups != current_groups

            # Check if the current state is now non-empty (has content worth saving)
            has_content = current_strand_count > 0 or (hasattr(canvas, 'groups') and bool(canvas.groups))

            if (strand_added or groups_changed) and has_content:
                logging.info(f"Attach mode release: Strand added (count {initial_strand_count} -> {current_strand_count}) or groups changed. Checking if save needed.")
                
                # Check if the state was recently saved by another operation (like group creation)
                if hasattr(undo_redo_manager, 'current_step') and undo_redo_manager.current_step > 0:
                    # Get the timestamp of the last save
                    last_save_time = getattr(undo_redo_manager, '_last_save_time', 0)
                    current_time = time.time()
                    
                    # If the last save was less than 1 second ago, and the step has already been incremented,
                    # don't save again to prevent duplicate states
                    if (current_time - last_save_time < 1.0) and getattr(undo_redo_manager, '_saving_state_now', False):
                        logging.info("--> Recently saved by another operation (likely group update). Skipping duplicate save.")
                        return
                
                # Use a flag to prevent immediate double saves within the same manager instance
                if not getattr(undo_redo_manager, '_saving_state_now', False):
                    logging.info("--> Saving state.")
                    undo_redo_manager._saving_state_now = True
                    try:
                        # Record the save time
                        undo_redo_manager._last_save_time = time.time()
                        # Perform the actual save
                        undo_redo_manager.save_state()
                    finally:
                        # Reset flag after a short delay to allow subsequent saves for different actions
                        # Using lambda to capture the current manager instance
                        QTimer.singleShot(300, lambda mgr=undo_redo_manager: setattr(mgr, '_saving_state_now', False))
                else:
                    logging.info("--> Already saving state recently, skipping duplicate save.")
            else:
                logging.info(f"Attach mode release: No new strand detected or empty state (count {initial_strand_count} -> {current_strand_count}). Not saving state.")

        # Replace the original function with our enhanced version
        canvas.attach_mode.mouseReleaseEvent = enhanced_mouse_release
        logging.info("Connected UndoRedoManager to attach_mode mouse release events (with duplicate save prevention)")
    else:
        logging.warning("Could not connect to attach_mode: attach_mode not found on canvas")


def connect_to_mask_mode(canvas, undo_redo_manager):
    """
    Connect the mask mode's mask_created signal to save state when a mask is created.
    
    Args:
        canvas: The canvas object with the mask_mode
        undo_redo_manager: The UndoRedoManager instance
    """
    if hasattr(canvas, 'mask_mode') and canvas.mask_mode:
        # Connect the mask_created signal to save state
        def on_mask_created(strand1, strand2):
            logging.info("Mask created, saving state for undo/redo.")
            undo_redo_manager.save_state()
            
        # Connect the signal to our handler
        canvas.mask_mode.mask_created.connect(on_mask_created)
        logging.info("Connected UndoRedoManager to mask_mode mask_created signal")
    else:
        logging.warning("Could not connect to mask_mode: mask_mode not found on canvas")


def connect_to_group_operations(canvas, undo_redo_manager):
    """Connect to group operations to trigger state saves"""
    if not hasattr(canvas, 'group_layer_manager'):
        logging.warning("Could not connect to group operations: group_layer_manager not found on canvas")
        return
        
    group_manager = canvas.group_layer_manager
    
    # First try to connect to group_operation signal if available
    if hasattr(group_manager, 'group_operation'):
        try:
            # Define a handler for group operations
            def on_group_operation(operation, group_name, layers):
                logging.info(f"Group operation detected: {operation} on {group_name}")
                # For operations that have completion functions, we'll save state at completion
                # For other operations, save state immediately
                if operation not in ["move", "rotate", "edit_angles"]:
                    undo_redo_manager.save_state()
                
            # Connect the signal
            group_manager.group_operation.connect(on_group_operation)
            logging.info("Connected to group_operation signal")
        except Exception as e:
            logging.warning(f"Error connecting to group_operation signal: {str(e)}")
    
    # Also connect directly to canvas operations if they exist
    if hasattr(canvas, 'finish_group_move'):
        original_canvas_finish_move = canvas.finish_group_move
        def enhanced_canvas_finish_move(*args, **kwargs):
            result = original_canvas_finish_move(*args, **kwargs)
            logging.info("Canvas group move finished, saving state")
            undo_redo_manager.save_state()
            return result
        canvas.finish_group_move = enhanced_canvas_finish_move
        
    if hasattr(canvas, 'finish_group_rotation'):
        original_canvas_finish_rotation = canvas.finish_group_rotation
        def enhanced_canvas_finish_rotation(*args, **kwargs):
            result = original_canvas_finish_rotation(*args, **kwargs)
            logging.info("Canvas group rotation finished, saving state")
            undo_redo_manager.save_state()
            return result
        canvas.finish_group_rotation = enhanced_canvas_finish_rotation
    
    # Also connect directly to group_panel if available
    if hasattr(group_manager, 'group_panel') and group_manager.group_panel:
        connect_group_panel_directly(group_manager.group_panel, undo_redo_manager)
        
    # Mark the connection as established
    canvas._group_ops_connected = True
    
    logging.info("Successfully connected to group operations")
    return True


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
            # Explicitly ensure buttons are disabled at startup
            if manager.undo_button:
                manager.undo_button.setEnabled(False)
            if manager.redo_button:
                manager.redo_button.setEnabled(False)
            logging.info("Added undo/redo buttons to layer panel (initially disabled)")
        else:
            logging.warning("Could not find top_layout in layer_panel")
    else:
        logging.warning("Could not find top_panel in layer_panel")
    
    # Connect to move mode mouse release
    connect_to_move_mode(canvas, manager)
    
    # Connect to attach mode as well
    connect_to_attach_mode(canvas, manager)
    
    # Connect to mask mode
    connect_to_mask_mode(canvas, manager)
    
    # Connect to group operations if group_layer_manager exists
    if hasattr(canvas, 'group_layer_manager') and canvas.group_layer_manager:
        connect_to_group_operations(canvas, manager)
    else:
        # Setup a function to connect when group_layer_manager becomes available
        def check_and_connect_group_operations():
            if hasattr(canvas, 'group_layer_manager') and canvas.group_layer_manager:
                logging.info("Delayed connection: Group layer manager now available, connecting to group operations")
                connect_to_group_operations(canvas, manager)
                return True
            return False
        
        # Try connecting after 500ms
        QTimer.singleShot(500, check_and_connect_group_operations)
        
        # Schedule multiple retries
        for delay in [1000, 2000, 5000]:
            QTimer.singleShot(delay, lambda: check_and_connect_group_operations() if not hasattr(canvas, '_group_ops_connected') else None)
    
    return manager

# Add a new method to directly connect a group_panel to save state on group operations
def connect_group_panel_directly(group_panel, undo_redo_manager):
    """Connect a specific group panel's signals to save state."""
    if not group_panel:
        return False
        
    logging.info("Directly connecting group panel to undo/redo manager")
    
    # Connect to group creation more directly
    original_create_group = group_panel.create_group
    def enhanced_create_group(*args, **kwargs):
        result = original_create_group(*args, **kwargs)
        logging.info("Group created, saving state")
        
        # Record the timestamp before saving state
        current_time = time.time()
        last_save_time = getattr(undo_redo_manager, '_last_save_time', 0)
        
        # Check if a state was saved very recently (within 1 second)
        if current_time - last_save_time < 1.0:
            logging.info("Group creation: Recently saved state detected. Setting flag to enable next save.")
            # Set flag to allow the next save (typically from attach mode) by resetting the prevention flag
            undo_redo_manager._saving_state_now = False
            
            # Force a save anyway to ensure group creation is recorded as a separate step
            # This ensures that strand creation and group creation are treated as separate operations
            logging.info("Group creation: Forcing a save to ensure it's recorded as a separate step")
            undo_redo_manager.save_state()
        else:
            # Normal save if no recent save
            undo_redo_manager.save_state()
            # Record the timestamp
            undo_redo_manager._last_save_time = time.time()
            # Mark that we're in a saving state
            undo_redo_manager._saving_state_now = True
            # Reset after a delay
            QTimer.singleShot(300, lambda mgr=undo_redo_manager: setattr(mgr, '_saving_state_now', False))
            
        return result
    group_panel.create_group = enhanced_create_group
    
    # Connect to group deletion
    original_delete_group = group_panel.delete_group
    def enhanced_delete_group(*args, **kwargs):
        result = original_delete_group(*args, **kwargs)
        logging.info("Group deleted, saving state")
        undo_redo_manager.save_state()
        return result
    group_panel.delete_group = enhanced_delete_group
    
    # Connect to move operation completion
    original_finish_group_move = group_panel.finish_group_move
    def enhanced_finish_group_move(*args, **kwargs):
        result = original_finish_group_move(*args, **kwargs)
        logging.info("Group move finished, saving state")
        undo_redo_manager.save_state()
        return result
    group_panel.finish_group_move = enhanced_finish_group_move
    
    # Connect to rotation operation completion
    original_finish_group_rotation = group_panel.finish_group_rotation
    def enhanced_finish_group_rotation(*args, **kwargs):
        result = original_finish_group_rotation(*args, **kwargs)
        logging.info("Group rotation finished, saving state")
        undo_redo_manager.save_state()
        return result
    group_panel.finish_group_rotation = enhanced_finish_group_rotation
    
    # Connect to angle edit completion
    original_update_group_after_angle_edit = getattr(group_panel, 'update_group_after_angle_edit', None)
    if original_update_group_after_angle_edit:
        def enhanced_update_group_after_angle_edit(*args, **kwargs):
            result = original_update_group_after_angle_edit(*args, **kwargs)
            logging.info("Group angle edit finished, saving state")
            undo_redo_manager.save_state()
            return result
        group_panel.update_group_after_angle_edit = enhanced_update_group_after_angle_edit
    
    # Connect to group operation signal
    def on_group_operation(operation, group_name, layers):
        logging.info(f"Group operation detected: {operation} on {group_name}")
        # For operations that have completion functions, we'll save state at completion
        # For other operations, save state immediately
        if operation not in ["move", "rotate", "edit_angles"]:
            undo_redo_manager.save_state()
    
    group_panel.group_operation.connect(on_group_operation)
    
    logging.info("Successfully connected group panel signals to undo/redo manager")
    return True 