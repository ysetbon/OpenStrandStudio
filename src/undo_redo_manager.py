import os
import sys
import json
import glob
import time  # Add time module for timestamp comparison
import shutil
from datetime import datetime
from PyQt5.QtWidgets import QPushButton, QStyle, QStyleOption, QDialog
from PyQt5.QtCore import QObject, pyqtSignal, Qt, QTimer, QPoint, QEvent
from PyQt5.QtGui import QPainter, QPainterPath, QPen, QFontMetrics, QColor, QBrush, QLinearGradient, QPalette
from render_utils import RenderUtils
from save_load_manager import save_strands, load_strands, apply_loaded_strands
# Import QTimer here to avoid UnboundLocalError
from PyQt5.QtCore import QTimer
from group_layers import CollapsibleGroupWidget # Import at the top level to ensure availability
# Note: We don't import GroupPanel here, as it can cause issues with Qt objects
# We'll work with instances that are already created
from masked_strand import MaskedStrand
from attached_strand import AttachedStrand

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
        # For right-click tooltip functionality
        self.custom_tooltip = ""
        # Disable default tooltip behavior
        self.setToolTip("")
    
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
                "bg_normal": "#4387c2",           # Normal background for light theme (blue)
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
        RenderUtils.setup_ui_painter(painter)

        # Draw the background (if not handled by stylesheet)
        option = QStyleOption()
        option.initFrom(self)
        self.style().drawPrimitive(QStyle.PE_Widget, option, painter, self)

        # Draw the text with stroke
        font = self.font()
        font.setBold(True)
        # Adjust font size based on button size
        if self.width() == 32:  # For refresh button
            font.setPixelSize(24)  # Smaller font for refresh button
        else:  # For undo/redo buttons
            font.setPixelSize(30)  # Original size for undo/redo
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
        
        # Ensure painter is properly ended
        painter.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateStyleSheet()
    
    def set_custom_tooltip(self, text):
        """Set the custom tooltip text"""
        self.custom_tooltip = text
        # Make sure default tooltip is disabled
        self.setToolTip("")
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.RightButton:
            
            if self.custom_tooltip:
                # Import CustomTooltip here to avoid circular imports
                from layer_panel import CustomTooltip
                
                # Find the LayerPanel to get the panel's position and size
                layer_panel = None
                parent = self.parent()
                while parent:
                    if parent.__class__.__name__ == 'LayerPanel':
                        layer_panel = parent
                        break
                    parent = parent.parent()
                
                if layer_panel:
                    # Get the LayerPanel's position and size
                    panel_global_pos = layer_panel.mapToGlobal(QPoint(0, 0))
                    panel_size = layer_panel.size()
                    
                    # Simple 4th row calculation: 3 rows down from panel top
                    fourth_row_y = panel_global_pos.y() + 190  # 3 rows * 40px + 3 gaps * 5px
                    
                    # Find the center X based on hide button and refresh button positions
                    # Get the hide button (multi_select_button) and refresh button positions
                    hide_button = getattr(layer_panel, 'multi_select_button', None)
                    refresh_button = getattr(layer_panel, 'refresh_button', None)
                    
                    if hide_button and refresh_button:
                        # Get the global positions of both buttons
                        hide_global_pos = hide_button.mapToGlobal(QPoint(0, 0))
                        refresh_global_pos = refresh_button.mapToGlobal(QPoint(0, 0))

                        # Calculate the center between these two buttons
                        # Get the actual content area of buttons, excluding any extra spacing
                        hide_left = hide_global_pos.x()
                        hide_right = hide_global_pos.x() + hide_button.width()
                        refresh_left = refresh_global_pos.x()
                        refresh_right = refresh_global_pos.x() + refresh_button.width()
                        
                        # Calculate center point between the two button regions
                        center_x = (hide_right + refresh_left) // 2

                        # Create and show custom tooltip at exact position
                        # Always recreate the tooltip to ensure consistent styling
                        if hasattr(self, '_custom_tooltip_widget'):
                            self._custom_tooltip_widget.hide()
                            self._custom_tooltip_widget.deleteLater()
                        
                        self._custom_tooltip_widget = CustomTooltip("", self)
                        self._custom_tooltip_widget.setText(self.custom_tooltip)
                        # Force theme update to ensure proper styling
                        self._custom_tooltip_widget.updateTheme()
                        self._custom_tooltip_widget.adjustSize()
                        
                        # Position tooltip so its center aligns exactly with center_x
                        tooltip_width = self._custom_tooltip_widget.width()
                        tooltip_pos = QPoint(
                            center_x - tooltip_width // 2,
                            fourth_row_y
                        )
                        
                        self._custom_tooltip_widget.showAt(tooltip_pos, timeout=0)  # No auto-hide
                    
            event.accept()
            return
        
        # For left-click or other buttons, process normally
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.RightButton:
            # Hide tooltip immediately when right-click is released
            if hasattr(self, '_custom_tooltip_widget'):
                self._custom_tooltip_widget.hide()
            event.accept()
            return
        
        # For left-click or other buttons, process normally
        super().mouseReleaseEvent(event)
    
    def event(self, event):
        """Override event to disable hover tooltips and allow mouse events on disabled button"""
        if event.type() == QEvent.ToolTip:
            # Ignore tooltip events
            return True
        
        # Allow mouse press/release events even when disabled
        if not self.isEnabled() and event.type() in [QEvent.MouseButtonPress, QEvent.MouseButtonRelease]:
            # Process mouse events directly for disabled buttons
            if event.type() == QEvent.MouseButtonPress:
                self.mousePressEvent(event)
                return True
            elif event.type() == QEvent.MouseButtonRelease:
                self.mouseReleaseEvent(event)
                return True
        
        return super().event(event)

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

    def __init__(self, canvas, layer_panel, base_path):
        super().__init__()
        self.canvas = canvas
        self.layer_panel = layer_panel
        self.current_step = 0  # Start at step 0 (empty state, no steps saved yet)
        self.max_step = 0      # Start with no steps saved
        # Use the provided base_path to determine the temp_dir
        self.base_path = base_path
        self.temp_dir = self._create_temp_dir(base_path)
        self.session_id = datetime.now().strftime("%Y%m%d%H%M%S")
        self.undo_button = None
        self.redo_button = None
        
        # Connect signals
        self.undo_performed.connect(self._update_button_states)
        self.redo_performed.connect(self._update_button_states)
        self.state_saved.connect(self._update_button_states)
        
        # Update button states initially (both should be disabled)
        self._update_button_states()

    def _create_temp_dir(self, base_path):
        """Create a temporary directory for state files if it doesn't exist, relative to the base_path."""
        # Use the provided base_path instead of __file__
        temp_dir = os.path.join(base_path, "temp_states")
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    def _get_state_filename(self, step):
        """Generate a filename for the specified step."""
        return os.path.join(self.temp_dir, f"{self.session_id}_{step}.json")

    def save_state(self, allow_empty=False):
        """Save the current state of strands and groups for undo/redo."""
        # Add debug logging to track save_state calls
        import traceback
        caller_info = traceback.extract_stack()[-2]  # Get the caller info
        
        # Check skip_save flag
        skip_save = getattr(self, '_skip_save', False)
        
        # Skip save if flagged to avoid saving states
        if skip_save:
            return
            
        # Ensure the canvas exists
        if not self.canvas:
            return
            
        # Check if there is content to save (unless explicitly allowing empty states)
        if not allow_empty:
            if not self.canvas.strands and not hasattr(self.canvas, 'groups'):
                return
                
            # Only save if content actually exists
            if not self.canvas.strands and not (hasattr(self.canvas, 'groups') and self.canvas.groups):
                return
            
        # Record the timestamp of this save
        current_time = time.time()
        last_save_time = getattr(self, '_last_save_time', 0)
        
        # If we've saved very recently (<500ms), check if we should skip this save  
        # Increased from 300ms to 500ms to account for 50ms timer delays in signal handlers
        if (current_time - last_save_time < 0.5) and self.current_step > 0:
            # Check if the current state would be identical to the previous state
            if self._would_be_identical_save():
                return
            else:
                pass
        else:
            pass
        
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
            self.state_saved.emit(self.current_step)
            
            # Update button states
            self._update_button_states()
        else:
            # If save failed, revert step counter
            self.current_step -= 1
            if self.max_step > self.current_step:
                self.max_step = self.current_step

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
                    return False # Returns False immediately if layer counts differ

                # --- ADD: Compare Masked Strand Count --- 
                current_masked_count = sum(1 for s in self.canvas.strands if isinstance(s, MaskedStrand))
                # Check previous data for masked strands by looking for the 'type' field set to 'MaskedStrand' in the saved data.
                # This assumes save_strands correctly serializes MaskedStrand instances with this 'type' field.
                prev_masked_count = sum(1 for s_data in prev_data.get('strands', []) if s_data.get('type') == 'MaskedStrand')
                if current_masked_count != prev_masked_count:
                    return False
                # --- END ADD --- 

                # Compare layer names (only if counts are the same)
                current_layer_names = {s.layer_name for s in self.canvas.strands if hasattr(s, 'layer_name')}
                prev_layer_names = {s.get('layer_name') for s in prev_data.get('strands', []) if 'layer_name' in s}
                
                if current_layer_names != prev_layer_names:
                    return False
                    
                # --- NEW CHECK: Compare layer order ---
                current_layer_order = [s.layer_name for s in self.canvas.strands if hasattr(s, 'layer_name')]
                prev_layer_order = [s.get('layer_name') for s in prev_data.get('strands', []) if 'layer_name' in s]
                if current_layer_order != prev_layer_order:
                    return False
                # --- END NEW CHECK ---

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
                    if (abs(current_strand.start.x() - prev_strand['start']['x']) > 0.1 or
                        abs(current_strand.start.y() - prev_strand['start']['y']) > 0.1 or
                        abs(current_strand.end.x() - prev_strand['end']['x']) > 0.1 or
                        abs(current_strand.end.y() - prev_strand['end']['y']) > 0.1):
                        return False
                    
                    # Added comparison for control points to capture their movements separately for undo/redo
                    if (hasattr(current_strand, 'control_point1') and ('control_point1' in prev_strand)):
                        if (abs(current_strand.control_point1.x() - prev_strand['control_point1']['x']) > 0.1 or
                            abs(current_strand.control_point1.y() - prev_strand['control_point1']['y']) > 0.1):
                            return False
                    if (hasattr(current_strand, 'control_point2') and ('control_point2' in prev_strand)):
                        if (abs(current_strand.control_point2.x() - prev_strand['control_point2']['x']) > 0.1 or
                            abs(current_strand.control_point2.y() - prev_strand['control_point2']['y']) > 0.1):
                            return False
                    if (hasattr(current_strand, 'control_point_center') and ('control_point_center' in prev_strand)):
                        if (abs(current_strand.control_point_center.x() - prev_strand['control_point_center']['x']) > 0.1 or
                            abs(current_strand.control_point_center.y() - prev_strand['control_point_center']['y']) > 0.1):
                            return False

                    # Compare colors
                    if hasattr(current_strand, 'color') and 'color' in prev_strand:
                        # Assuming save_strands saves color like {'r': R, 'g': G, 'b': B, 'a': A}
                        prev_color_dict = prev_strand.get('color', {})
                        current_color = current_strand.color
                        # Use integer comparison for colors (0-255)
                        if (current_color.red() != prev_color_dict.get('r', 0) or
                            current_color.green() != prev_color_dict.get('g', 0) or
                            current_color.blue() != prev_color_dict.get('b', 0) or
                            current_color.alpha() != prev_color_dict.get('a', 0)):
                            # Colors differ, so state is not identical
                            return False
                    elif hasattr(current_strand, 'color') != ('color' in prev_strand):
                        # Color attribute presence differs, state is not identical
                        return False

                    # Compare stroke colors
                    if hasattr(current_strand, 'stroke_color') and 'stroke_color' in prev_strand:
                        prev_stroke_color_dict = prev_strand.get('stroke_color', {})
                        current_stroke_color = current_strand.stroke_color
                        # Use integer comparison for stroke colors (0-255)
                        if (current_stroke_color.red() != prev_stroke_color_dict.get('r', 0) or
                            current_stroke_color.green() != prev_stroke_color_dict.get('g', 0) or
                            current_stroke_color.blue() != prev_stroke_color_dict.get('b', 0) or
                            current_stroke_color.alpha() != prev_stroke_color_dict.get('a', 0)):
                            # Stroke colors differ, so state is not identical
                            current_rgba = f"({current_stroke_color.red()},{current_stroke_color.green()},{current_stroke_color.blue()},{current_stroke_color.alpha()})"
                            prev_rgba = f"({prev_stroke_color_dict.get('r', 0)},{prev_stroke_color_dict.get('g', 0)},{prev_stroke_color_dict.get('b', 0)},{prev_stroke_color_dict.get('a', 0)})"
                            return False
                    elif hasattr(current_strand, 'stroke_color') != ('stroke_color' in prev_strand):
                        # Stroke color attribute presence differs, state is not identical
                        return False

                    # --- ADD: Compare mask path for MaskedStrands --- 
                    if isinstance(current_strand, MaskedStrand):
                        # Compare component strand names
                        current_components = sorted(getattr(current_strand, 'component_strand_names', []))
                        prev_components = sorted(prev_strand.get('component_strand_names', []))
                        if current_components != prev_components:
                            return False

                        # Compare deletion rectangles
                        current_rects = getattr(current_strand, 'deletion_rectangles', [])
                        prev_rects = prev_strand.get('deletion_rectangles', [])
                        
                        if len(current_rects) != len(prev_rects):
                            return False
                        
                        # Deep compare rectangles if counts are the same
                        if len(current_rects) > 0:
                            # Helper to produce a comparable tuple for each rectangle, handling both
                            # the legacy corner-based schema and the (x,y,width,height) schema used
                            # during interactive mask editing.
                            def rect_signature(rect_data):
                                if all(k in rect_data for k in ["top_left", "top_right", "bottom_left", "bottom_right"]):
                                    # Corner based – use all four corners rounded to 2 decimals to reduce FP noise
                                    tl = tuple(round(v, 2) for v in rect_data.get("top_left", (0, 0)))
                                    tr = tuple(round(v, 2) for v in rect_data.get("top_right", (0, 0)))
                                    bl = tuple(round(v, 2) for v in rect_data.get("bottom_left", (0, 0)))
                                    br = tuple(round(v, 2) for v in rect_data.get("bottom_right", (0, 0)))
                                    return (tl, tr, bl, br)
                                else:
                                    # Rectangle expressed with position/size.  Round to 2 decimals.
                                    x = round(rect_data.get("x", 0), 2)
                                    y = round(rect_data.get("y", 0), 2)
                                    w = round(rect_data.get("width", 0), 2)
                                    h = round(rect_data.get("height", 0), 2)
                                    # Include optional offsets if present – otherwise default to 0.
                                    ox = round(rect_data.get("offset_x", 0), 2)
                                    oy = round(rect_data.get("offset_y", 0), 2)
                                    return (x, y, w, h, ox, oy)

                            # Build ordered signature lists for comparison (order-independent)
                            sig_curr = sorted([rect_signature(r) for r in current_rects])
                            sig_prev = sorted([rect_signature(r) for r in prev_rects])

                            if sig_curr != sig_prev:
                                return False
                    # --- ADD: Check line visibility ---
                    if hasattr(current_strand, 'start_line_visible') and 'start_line_visible' in prev_strand:
                        # Safer check using .get()
                        prev_start_vis = prev_strand.get('start_line_visible', not current_strand.start_line_visible)
                        if current_strand.start_line_visible != prev_start_vis:
                            return False
                    elif hasattr(current_strand, 'start_line_visible') != ('start_line_visible' in prev_strand):
                         return False

                    if hasattr(current_strand, 'end_line_visible') and 'end_line_visible' in prev_strand:
                        # Safer check using .get()
                        prev_end_vis = prev_strand.get('end_line_visible', not current_strand.end_line_visible)
                        if current_strand.end_line_visible != prev_end_vis:
                            return False
                    elif hasattr(current_strand, 'end_line_visible') != ('end_line_visible' in prev_strand):
                         return False
                    # --- END ADD ---

                    # --- ADD: Check strand width and stroke_width ---
                    if hasattr(current_strand, 'width') and 'width' in prev_strand:
                        if abs(current_strand.width - prev_strand.get('width', 0)) > 0.1:
                            return False
                    elif hasattr(current_strand, 'width') != ('width' in prev_strand):
                        return False

                    if hasattr(current_strand, 'stroke_width') and 'stroke_width' in prev_strand:
                        if abs(current_strand.stroke_width - prev_strand.get('stroke_width', 0)) > 0.1:
                            return False
                    elif hasattr(current_strand, 'stroke_width') != ('stroke_width' in prev_strand):
                        return False
                    # --- END ADD ---

                    # --- ADD: Check layer visibility (is_hidden) ---
                    current_hidden = getattr(current_strand, 'is_hidden', False)
                    # Assume False if 'is_hidden' is not in the saved data (for backward compatibility)
                    prev_hidden = prev_strand.get('is_hidden', False)
                    if current_hidden != prev_hidden:
                        return False
                    # --- END ADD ---

                    # --- NEW: Check extension visibility ---
                    if hasattr(current_strand, 'start_extension_visible') and 'start_extension_visible' in prev_strand:
                        prev_start_ext = prev_strand.get('start_extension_visible', not current_strand.start_extension_visible)
                        if current_strand.start_extension_visible != prev_start_ext:
                            return False
                    elif hasattr(current_strand, 'start_extension_visible') != ('start_extension_visible' in prev_strand):
                         return False

                    if hasattr(current_strand, 'end_extension_visible') and 'end_extension_visible' in prev_strand:
                        prev_end_ext = prev_strand.get('end_extension_visible', not current_strand.end_extension_visible)
                        if current_strand.end_extension_visible != prev_end_ext:
                            return False
                    elif hasattr(current_strand, 'end_extension_visible') != ('end_extension_visible' in prev_strand):
                         return False

                    # --- NEW: Check arrow visibility ---
                    if hasattr(current_strand, 'start_arrow_visible') and 'start_arrow_visible' in prev_strand:
                        prev_start_arr = prev_strand.get('start_arrow_visible', not current_strand.start_arrow_visible)
                        if current_strand.start_arrow_visible != prev_start_arr:
                            return False
                    elif hasattr(current_strand, 'start_arrow_visible') != ('start_arrow_visible' in prev_strand):
                         return False

                    if hasattr(current_strand, 'end_arrow_visible') and 'end_arrow_visible' in prev_strand:
                        prev_end_arr = prev_strand.get('end_arrow_visible', not current_strand.end_arrow_visible)
                        if current_strand.end_arrow_visible != prev_end_arr:
                            return False
                    elif hasattr(current_strand, 'end_arrow_visible') != ('end_arrow_visible' in prev_strand):
                         return False

                    # --- ADD: Check full_arrow_visible ---
                    if hasattr(current_strand, 'full_arrow_visible') and 'full_arrow_visible' in prev_strand:
                        prev_full_arrow_vis = prev_strand.get('full_arrow_visible', not getattr(current_strand, 'full_arrow_visible', False)) # Default to opposite if missing
                        if getattr(current_strand, 'full_arrow_visible', False) != prev_full_arrow_vis:
                            return False
                    elif hasattr(current_strand, 'full_arrow_visible') != ('full_arrow_visible' in prev_strand):
                         return False
                    # --- END ADD ---

                    # --- ADD: Check circle visibility (has_circles) ---
                    if hasattr(current_strand, 'has_circles') and 'has_circles' in prev_strand:
                        # Check if has_circles lists differ
                        current_circles = getattr(current_strand, 'has_circles', [False, False])
                        prev_circles = prev_strand.get('has_circles', [False, False])
                        if current_circles != prev_circles:
                            return False
                    elif hasattr(current_strand, 'has_circles') != ('has_circles' in prev_strand):
                        return False
                    # --- END ADD ---

                    # --- ADD: Check knot connections ---
                    if hasattr(current_strand, 'knot_connections') and 'knot_connections' in prev_strand:
                        current_knots = getattr(current_strand, 'knot_connections', {})
                        prev_knots = prev_strand.get('knot_connections', {})
                        
                        # Compare connection count and end types
                        if set(current_knots.keys()) != set(prev_knots.keys()):
                            return False
                            
                        # Compare each connection
                        for end_type, current_conn in current_knots.items():
                            if end_type in prev_knots:
                                prev_conn = prev_knots[end_type]
                                # Extract connected strand name from current connection (strand object -> layer_name)
                                current_connected_name = None
                                if 'connected_strand' in current_conn and hasattr(current_conn['connected_strand'], 'layer_name'):
                                    current_connected_name = current_conn['connected_strand'].layer_name
                                
                                if (current_connected_name != prev_conn.get('connected_strand_name') or
                                    current_conn.get('connected_end') != prev_conn.get('connected_end') or
                                    current_conn.get('is_closing_strand', False) != prev_conn.get('is_closing_strand', False)):
                                    return False
                    elif hasattr(current_strand, 'knot_connections') != ('knot_connections' in prev_strand):
                        return False
                    # --- END ADD ---

                    # --- ADD: Check closed_connections ---
                    if hasattr(current_strand, 'closed_connections') and 'closed_connections' in prev_strand:
                        current_closed = getattr(current_strand, 'closed_connections', [False, False])
                        prev_closed = prev_strand.get('closed_connections', [False, False])
                        if current_closed != prev_closed:
                            return False
                    elif hasattr(current_strand, 'closed_connections') != ('closed_connections' in prev_strand):
                        return False
                    # --- END ADD ---

                # Check for differences in locked layers
                current_locked_layers = set()
                if hasattr(self.canvas, 'layer_panel') and hasattr(self.canvas.layer_panel, 'locked_layers'):
                    current_locked_layers = self.canvas.layer_panel.locked_layers.copy()
                
                prev_locked_layers = set(prev_data.get("locked_layers", []))
                
                if current_locked_layers != prev_locked_layers:
                    return False
                
                # Check for differences in lock mode
                current_lock_mode = False
                if hasattr(self.canvas, 'layer_panel') and self.canvas.layer_panel:
                    if hasattr(self.canvas.layer_panel, 'lock_mode'):
                        current_lock_mode = self.canvas.layer_panel.lock_mode
                    else:
                        pass
                else:
                    pass
                
                prev_lock_mode = prev_data.get("lock_mode", False)
                
                if current_lock_mode != prev_lock_mode:
                    return False

                # Compare button states
                current_shadow_enabled = getattr(self.canvas, 'shadow_enabled', True)
                prev_shadow_enabled = prev_data.get('shadow_enabled', True)
                
                if current_shadow_enabled != prev_shadow_enabled:
                    return False
                
                current_show_control_points = getattr(self.canvas, 'show_control_points', False)
                prev_show_control_points = prev_data.get('show_control_points', False)
                
                if current_show_control_points != prev_show_control_points:
                    return False

                # If we made it here, states are identical based on checked properties
                return True
                
        except Exception as e:
            pass
            
        # Default to allowing the save if anything goes wrong
        return False

    def _clear_future_states(self):
        """Remove any state files from current_step + 1 to max_step."""
        for step in range(self.current_step + 1, self.max_step + 1):
            filename = self._get_state_filename(step)
            try:
                if os.path.exists(filename):
                    os.remove(filename)
            except OSError as e:
                pass
        
        # Reset max_step to current_step
        self.max_step = self.current_step

    def _ensure_groups_are_saved(self):
        """Ensure that all groups are properly captured in the next save."""
        if not hasattr(self.canvas, 'group_layer_manager') or not self.canvas.group_layer_manager:
            return
            
        group_manager = self.canvas.group_layer_manager
        
        # If canvas.groups doesn't exist, create it
        if not hasattr(self.canvas, 'groups'):
            self.canvas.groups = {}
            
        # IMPORTANT: Do NOT restore groups from panel to canvas.groups
        # The canvas.groups is the authoritative source for what groups exist
        # If a group was deleted from canvas.groups, it should stay deleted
        # The panel will be updated to match canvas.groups, not the other way around
                    
        # Log the groups that will be saved
        if self.canvas.groups:
            pass
        else:
            pass

    def _save_state_file(self, step):
        """Save the current state of the canvas to a file."""
        filename = self._get_state_filename(step)
        
        
        try:
            save_strands(self.canvas.strands, 
                         self.canvas.groups if hasattr(self.canvas, 'groups') else {},
                         filename,
                         self.canvas)
            self.state_saved.emit(step)
            return True
        except Exception as e:
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
            
            # Store original lock state for comparison
            original_lock_mode = getattr(self.layer_panel, 'lock_mode', False) if hasattr(self.layer_panel, 'lock_mode') else False
            original_locked_layers = getattr(self.layer_panel, 'locked_layers', set()).copy() if hasattr(self.layer_panel, 'locked_layers') else set()
            
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
            
            # Suppress window activation events during entire undo operation
            main_window = None
            if hasattr(self.layer_panel, 'parent_window'):
                main_window = self.layer_panel.parent_window
            elif hasattr(self.layer_panel, 'parent'):
                main_window = self.layer_panel.parent()
            
            if main_window and hasattr(main_window, 'suppress_activation_events'):
                main_window.suppress_activation_events = True
            
            # Disable updates to prevent window flash
            if main_window:
                main_window.setUpdatesEnabled(False)
            
            # Suppress attachment status updates during undo to prevent window flash
            self.canvas._suppress_attachment_updates = True
            # Suppress repaint calls during undo to prevent window flash
            self.canvas._suppress_repaint = True
            # Suppress layer panel refresh during undo to prevent window flash
            self.canvas._suppress_layer_panel_refresh = True
            
            # Special case: If undoing to step 0 (empty state)
            if self.current_step == 0:
                # Clear the canvas by removing all strands and groups
                self.canvas.strands = []
                if hasattr(self.canvas, 'groups'):
                    self.canvas.groups = {}
                
                # Skip explicit refresh calls to prevent window flash (they're redundant)
                # Don't call update() here - the refresh will handle it
                # self.canvas.update()  # Removed to prevent double painting
                
                # Do refresh while paint suppression is still active
                if hasattr(self.layer_panel, 'simulate_refresh_button_click'):
                    self.layer_panel.simulate_refresh_button_click()
                
                # Clear the repaint suppression flag after refresh is complete
                self.canvas._suppress_repaint = False
                
                # Re-enable updates after refresh
                if main_window:
                    main_window.setUpdatesEnabled(True)
                
                # Re-enable attachment status updates
                self.canvas._suppress_attachment_updates = False
                
                # Re-enable window activation events after refresh
                if main_window and hasattr(main_window, 'suppress_activation_events'):
                    main_window.suppress_activation_events = False
                
                # Force a single update now that everything is ready
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
                    
                    
                    # --- ADD: Explicit check for layer name set difference --- 
                    if new_layer_names != original_layer_names:
                        has_visual_difference = True
                    else:
                        # --- Original checks (now nested) --- 
                        # Check for meaningful visual differences between states
                        has_visual_difference = False
                        
                        # Check lock state differences
                        # Compare the original lock state with the current (post-undo) lock state
                        current_lock_mode = getattr(self.layer_panel, 'lock_mode', False)
                        current_locked_layers = getattr(self.layer_panel, 'locked_layers', set())
                        
                        if current_lock_mode != original_lock_mode:
                            has_visual_difference = True
                        
                        if current_locked_layers != original_locked_layers:
                            has_visual_difference = True
                        
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
                            
                            # Check control points for differences - important for proper undo/redo of control point changes
                            if (hasattr(new_strand, 'control_point1') and hasattr(original_strand, 'control_point1')):
                                # --- ADD None checks --- 
                                if new_strand.control_point1 is not None and original_strand.control_point1 is not None:
                                    if (abs(new_strand.control_point1.x() - original_strand.control_point1.x()) > 0.1 or
                                        abs(new_strand.control_point1.y() - original_strand.control_point1.y()) > 0.1):
                                        has_visual_difference = True
                                        break
                                # Handle cases where one is None and the other isn't (counts as a difference)
                                elif (new_strand.control_point1 is None) != (original_strand.control_point1 is None):
                                    has_visual_difference = True
                                    break
                                # --- END ADD --- 
                            
                            if (hasattr(new_strand, 'control_point2') and hasattr(original_strand, 'control_point2')):
                                # --- ADD None checks --- 
                                if new_strand.control_point2 is not None and original_strand.control_point2 is not None:
                                    if (abs(new_strand.control_point2.x() - original_strand.control_point2.x()) > 0.1 or
                                        abs(new_strand.control_point2.y() - original_strand.control_point2.y()) > 0.1):
                                        has_visual_difference = True
                                        break
                                # Handle cases where one is None and the other isn't
                                elif (new_strand.control_point2 is None) != (original_strand.control_point2 is None):
                                    has_visual_difference = True
                                    break
                                # --- END ADD --- 
                                    
                            if (hasattr(new_strand, 'control_point_center') and hasattr(original_strand, 'control_point_center')):
                                # --- ADD None checks --- 
                                if new_strand.control_point_center is not None and original_strand.control_point_center is not None:
                                    if (abs(new_strand.control_point_center.x() - original_strand.control_point_center.x()) > 0.1 or
                                        abs(new_strand.control_point_center.y() - original_strand.control_point_center.y()) > 0.1):
                                        has_visual_difference = True
                                        break
                                # Handle cases where one is None and the other isn't
                                elif (new_strand.control_point_center is None) != (original_strand.control_point_center is None):
                                    has_visual_difference = True
                                    break
                                # --- END ADD --- 
                            
                            # Check colors (if one is visibly different)
                            if (hasattr(new_strand, 'color') and hasattr(original_strand, 'color')):
                                # Only consider color difference significant if it's visible
                                if (abs(new_strand.color.red() - original_strand.color.red()) > 0 or
                                    abs(new_strand.color.green() - original_strand.color.green()) > 0 or
                                    abs(new_strand.color.blue() - original_strand.color.blue()) > 0 or
                                    abs(new_strand.color.alpha() - original_strand.color.alpha()) > 0):
                                    has_visual_difference = True
                                    break
                            
                            # --- ADD: Check stroke colors (if one is visibly different) ---
                            if (hasattr(new_strand, 'stroke_color') and hasattr(original_strand, 'stroke_color')):
                                # Only consider stroke color difference significant if it's visible
                                if (abs(new_strand.stroke_color.red() - original_strand.stroke_color.red()) > 0 or
                                    abs(new_strand.stroke_color.green() - original_strand.stroke_color.green()) > 0 or
                                    abs(new_strand.stroke_color.blue() - original_strand.stroke_color.blue()) > 0 or
                                    abs(new_strand.stroke_color.alpha() - original_strand.stroke_color.alpha()) > 0):
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'stroke_color') != hasattr(original_strand, 'stroke_color'):
                                has_visual_difference = True
                                break
                            # --- END ADD ---
                            
                            # --- ADD: Compare deletion rectangles for MaskedStrands ---
                            if isinstance(new_strand, MaskedStrand) and isinstance(original_strand, MaskedStrand):
                                new_rects = getattr(new_strand, 'deletion_rectangles', [])
                                original_rects = getattr(original_strand, 'deletion_rectangles', [])
                                
                                if len(new_rects) != len(original_rects):
                                    has_visual_difference = True
                                    break
                                
                                # Deep compare if counts are the same and non-zero
                                if len(new_rects) > 0:
                                    # Re-use the `rect_signature` logic introduced in _would_be_identical_save
                                    def rect_signature(rect_data):
                                        if all(k in rect_data for k in [
                                            "top_left", "top_right", "bottom_left", "bottom_right"]):
                                            tl = tuple(round(v, 2) for v in rect_data.get("top_left", (0, 0)))
                                            tr = tuple(round(v, 2) for v in rect_data.get("top_right", (0, 0)))
                                            bl = tuple(round(v, 2) for v in rect_data.get("bottom_left", (0, 0)))
                                            br = tuple(round(v, 2) for v in rect_data.get("bottom_right", (0, 0)))
                                            return (tl, tr, bl, br)
                                        else:
                                            x = round(rect_data.get("x", 0), 2)
                                            y = round(rect_data.get("y", 0), 2)
                                            w = round(rect_data.get("width", 0), 2)
                                            h = round(rect_data.get("height", 0), 2)
                                            ox = round(rect_data.get("offset_x", 0), 2)
                                            oy = round(rect_data.get("offset_y", 0), 2)
                                            return (x, y, w, h, ox, oy)

                                    sig_new = sorted(rect_signature(r) for r in new_rects)
                                    sig_orig = sorted(rect_signature(r) for r in original_rects)

                                    if sig_new != sig_orig:
                                        has_visual_difference = True
                                        break
                            elif isinstance(new_strand, MaskedStrand) != isinstance(original_strand, MaskedStrand):
                                # If one is MaskedStrand and the other isn't, they are different
                                has_visual_difference = True
                                break
                            # --- END ADD ---

                            # Check end line visibility
                            if hasattr(new_strand, 'end_line_visible') and hasattr(original_strand, 'end_line_visible'):
                                new_vis = new_strand.end_line_visible
                                orig_vis = original_strand.end_line_visible
                                if new_vis != orig_vis:
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'end_line_visible') != hasattr(original_strand, 'end_line_visible'):
                                has_visual_difference = True
                                break
                            # --- END ADD ---

                            # --- NEW: Check start line visibility ---
                            if hasattr(new_strand, 'start_line_visible') and hasattr(original_strand, 'start_line_visible'):
                                new_vis = new_strand.start_line_visible
                                orig_vis = original_strand.start_line_visible
                                if new_vis != orig_vis:
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'start_line_visible') != hasattr(original_strand, 'start_line_visible'):
                                has_visual_difference = True
                                break
                            # --- END NEW ---

                            # --- NEW: Check layer visibility (is_hidden) ---
                            if hasattr(new_strand, 'is_hidden') and hasattr(original_strand, 'is_hidden'):
                                if new_strand.is_hidden != original_strand.is_hidden:
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'is_hidden') != hasattr(original_strand, 'is_hidden'):
                                has_visual_difference = True
                                break
                            # --- END NEW ---

                            # --- NEW: Check shadow-only mode ---
                            if hasattr(new_strand, 'shadow_only') and hasattr(original_strand, 'shadow_only'):
                                if new_strand.shadow_only != original_strand.shadow_only:
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'shadow_only') != hasattr(original_strand, 'shadow_only'):
                                has_visual_difference = True
                                break
                            # --- END NEW ---

                            # --- NEW: Check extension visibility ---
                            if hasattr(new_strand, 'start_extension_visible') and hasattr(original_strand, 'start_extension_visible'):
                                if new_strand.start_extension_visible != original_strand.start_extension_visible:
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'start_extension_visible') != hasattr(original_strand, 'start_extension_visible'):
                                has_visual_difference = True
                                break

                            if hasattr(new_strand, 'end_extension_visible') and hasattr(original_strand, 'end_extension_visible'):
                                if new_strand.end_extension_visible != original_strand.end_extension_visible:
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'end_extension_visible') != hasattr(original_strand, 'end_extension_visible'):
                                has_visual_difference = True
                                break

                            # --- NEW: Check arrow visibility ---
                            if hasattr(new_strand, 'start_arrow_visible') and hasattr(original_strand, 'start_arrow_visible'):
                                if new_strand.start_arrow_visible != original_strand.start_arrow_visible:
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'start_arrow_visible') != hasattr(original_strand, 'start_arrow_visible'):
                                has_visual_difference = True
                                break

                            if hasattr(new_strand, 'end_arrow_visible') and hasattr(original_strand, 'end_arrow_visible'):
                                if new_strand.end_arrow_visible != original_strand.end_arrow_visible:
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'end_arrow_visible') != hasattr(original_strand, 'end_arrow_visible'):
                                has_visual_difference = True
                                break
                            # --- END NEW ---

                            # --- ADD: Check full_arrow_visible for Undo ---
                            if hasattr(new_strand, 'full_arrow_visible') and hasattr(original_strand, 'full_arrow_visible'):
                                if getattr(new_strand, 'full_arrow_visible', False) != getattr(original_strand, 'full_arrow_visible', False):
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'full_arrow_visible') != hasattr(original_strand, 'full_arrow_visible'):
                                has_visual_difference = True
                                break
                            # --- END ADD ---

                            # --- RE-ADD: Check circle visibility (has_circles) ---
                            if hasattr(new_strand, 'has_circles') and hasattr(original_strand, 'has_circles'):
                                current_circles = getattr(new_strand, 'has_circles', [False, False])
                                original_circles = getattr(original_strand, 'has_circles', [False, False])
                                if current_circles != original_circles:
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'has_circles') != hasattr(original_strand, 'has_circles'):
                                has_visual_difference = True
                                break
                            # --- END RE-ADD ---

                            # --- ADD: Check width for Undo ---
                            if hasattr(new_strand, 'width') and hasattr(original_strand, 'width'):
                                if abs(new_strand.width - original_strand.width) > 0.1:
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'width') != hasattr(original_strand, 'width'):
                                has_visual_difference = True
                                break

                            if hasattr(new_strand, 'stroke_width') and hasattr(original_strand, 'stroke_width'):
                                if abs(new_strand.stroke_width - original_strand.stroke_width) > 0.1:
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'stroke_width') != hasattr(original_strand, 'stroke_width'):
                                has_visual_difference = True
                                break
                            # --- END ADD ---

                    # If no visual difference found, skip this state and continue undoing
                    if not has_visual_difference:
                        # Recursively call undo to get to the next state
                        return self.undo()
                
            self.undo_performed.emit()
            
            # Make sure buttons are properly updated
            self._update_button_states()

            # --- ADD LOGGING FOR SELECTED STRAND ---
            selected_strand_after_undo = getattr(self.canvas, 'selected_strand', None)
            # --- END LOGGING ---

            # Additional logging to track what's being refreshed
            
            # --------------------------------------------------
            # Re-enable all suppression flags *before* we trigger the first
            # repaint so that the very first frame after an undo already
            # contains the fully-restored geometry (circles, attachments …)
            # --------------------------------------------------

            # Re-enable attachment status updates and repaint calls
            self.canvas._suppress_attachment_updates = False
            self.canvas._suppress_repaint = False
            self.canvas._suppress_layer_panel_refresh = False

            # Now trigger the repaint
            self.canvas.update()

            # Re-enable updates after all operations (Qt window flag)
            if main_window:
                main_window.setUpdatesEnabled(True)
            
            # Re-enable attachment status updates
            self.canvas._suppress_attachment_updates = False
            # Re-enable repaint calls
            self.canvas._suppress_repaint = False
            # Re-enable layer panel refresh
            self.canvas._suppress_layer_panel_refresh = False
            
            # Re-enable window activation events
            if main_window and hasattr(main_window, 'suppress_activation_events'):
                main_window.suppress_activation_events = False
            
            # Now that all suppression flags are cleared, do a single refresh to update the UI
            if hasattr(self.layer_panel, 'simulate_refresh_button_click'):
                self.layer_panel.simulate_refresh_button_click()
        else:
            pass

    def redo(self):
        """Load the next state if available."""
        if self.current_step < self.max_step:
            # Store the current strands for comparison
            original_strands = self.canvas.strands.copy() if hasattr(self.canvas, 'strands') else []
            original_strands_count = len(original_strands)
            original_layer_names = {s.layer_name for s in original_strands if hasattr(s, 'layer_name')}
            original_layer_order = [s.layer_name for s in original_strands if hasattr(s, 'layer_name')]
            
            # Store original groups for comparison
            original_groups = {}
            if hasattr(self.canvas, 'groups'):
                original_groups = self.canvas.groups.copy()
            
            # Store original lock state for comparison
            original_lock_mode = getattr(self.layer_panel, 'lock_mode', False) if hasattr(self.layer_panel, 'lock_mode') else False
            original_locked_layers = getattr(self.layer_panel, 'locked_layers', set()).copy() if hasattr(self.layer_panel, 'locked_layers') else set()
            
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
                pass
            
            # Set up suppression flags BEFORE loading state to prevent window flash
            main_window = None
            if hasattr(self.layer_panel, 'parent_window'):
                main_window = self.layer_panel.parent_window
            elif hasattr(self.layer_panel, 'parent'):
                main_window = self.layer_panel.parent()
            
            # Suppress window activation events during redo
            if main_window and hasattr(main_window, 'suppress_activation_events'):
                main_window.suppress_activation_events = True
            
            # Disable updates to prevent window flash
            if main_window:
                main_window.setUpdatesEnabled(False)
            
            # Suppress attachment status updates during redo to prevent window flash
            self.canvas._suppress_attachment_updates = True
            # Suppress repaint calls during redo to prevent window flash
            self.canvas._suppress_repaint = True
            # Suppress layer panel refresh during redo to prevent window flash
            self.canvas._suppress_layer_panel_refresh = True
            
            # Increment the step counter
            self.current_step += 1
            
            # Load the state (with all suppression flags active)
            result = self._load_state(self.current_step)

            if result:
                # --- Log state AFTER loading --- 
                new_strands = self.canvas.strands
                new_strands_count = len(new_strands)
                new_layer_names = {s.layer_name for s in new_strands if hasattr(s, 'layer_name')}
                new_layer_order = [s.layer_name for s in new_strands if hasattr(s, 'layer_name')]
                # --- End Log ---

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
                    
                    
                    # --- ADD: Explicit check for layer name set difference --- 
                    if new_layer_names != original_layer_names:
                        has_visual_difference = True
                    else:
                        # --- Original checks (now nested) --- 
                        # Check for meaningful visual differences between states
                        has_visual_difference = False
                        
                        # Check lock state differences
                        # Compare the original lock state with the current (post-undo) lock state
                        current_lock_mode = getattr(self.layer_panel, 'lock_mode', False)
                        current_locked_layers = getattr(self.layer_panel, 'locked_layers', set())
                        
                        if current_lock_mode != original_lock_mode:
                            has_visual_difference = True
                        
                        if current_locked_layers != original_locked_layers:
                            has_visual_difference = True
                        
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
                            
                            # Check control points for differences - important for proper undo/redo of control point changes
                            if (hasattr(new_strand, 'control_point1') and hasattr(original_strand, 'control_point1')):
                                # --- ADD None checks --- 
                                if new_strand.control_point1 is not None and original_strand.control_point1 is not None:
                                    if (abs(new_strand.control_point1.x() - original_strand.control_point1.x()) > 0.1 or
                                        abs(new_strand.control_point1.y() - original_strand.control_point1.y()) > 0.1):
                                        has_visual_difference = True
                                        break
                                # Handle cases where one is None and the other isn't (counts as a difference)
                                elif (new_strand.control_point1 is None) != (original_strand.control_point1 is None):
                                    has_visual_difference = True
                                    break
                                # --- END ADD --- 
                            
                            if (hasattr(new_strand, 'control_point2') and hasattr(original_strand, 'control_point2')):
                                # --- ADD None checks --- 
                                if new_strand.control_point2 is not None and original_strand.control_point2 is not None:
                                    if (abs(new_strand.control_point2.x() - original_strand.control_point2.x()) > 0.1 or
                                        abs(new_strand.control_point2.y() - original_strand.control_point2.y()) > 0.1):
                                        has_visual_difference = True
                                        break
                                # Handle cases where one is None and the other isn't
                                elif (new_strand.control_point2 is None) != (original_strand.control_point2 is None):
                                    has_visual_difference = True
                                    break
                                # --- END ADD --- 
                                    
                            if (hasattr(new_strand, 'control_point_center') and hasattr(original_strand, 'control_point_center')):
                                # --- ADD None checks --- 
                                if new_strand.control_point_center is not None and original_strand.control_point_center is not None:
                                    if (abs(new_strand.control_point_center.x() - original_strand.control_point_center.x()) > 0.1 or
                                        abs(new_strand.control_point_center.y() - original_strand.control_point_center.y()) > 0.1):
                                        has_visual_difference = True
                                        break
                                # Handle cases where one is None and the other isn't
                                elif (new_strand.control_point_center is None) != (original_strand.control_point_center is None):
                                    has_visual_difference = True
                                    break
                                # --- END ADD --- 
                            
                            # Check colors (if one is visibly different)
                            if (hasattr(new_strand, 'color') and hasattr(original_strand, 'color')):
                                # Only consider color difference significant if it's visible
                                if (abs(new_strand.color.red() - original_strand.color.red()) > 0 or
                                    abs(new_strand.color.green() - original_strand.color.green()) > 0 or
                                    abs(new_strand.color.blue() - original_strand.color.blue()) > 0 or
                                    abs(new_strand.color.alpha() - original_strand.color.alpha()) > 0):
                                    has_visual_difference = True
                                    break
                            
                            # --- ADD: Check stroke colors (if one is visibly different) ---
                            if (hasattr(new_strand, 'stroke_color') and hasattr(original_strand, 'stroke_color')):
                                # Only consider stroke color difference significant if it's visible
                                if (abs(new_strand.stroke_color.red() - original_strand.stroke_color.red()) > 0 or
                                    abs(new_strand.stroke_color.green() - original_strand.stroke_color.green()) > 0 or
                                    abs(new_strand.stroke_color.blue() - original_strand.stroke_color.blue()) > 0 or
                                    abs(new_strand.stroke_color.alpha() - original_strand.stroke_color.alpha()) > 0):
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'stroke_color') != hasattr(original_strand, 'stroke_color'):
                                has_visual_difference = True
                                break
                            # --- END ADD ---
                            
                            # --- ADD: Compare deletion rectangles for MaskedStrands ---
                            if isinstance(new_strand, MaskedStrand) and isinstance(original_strand, MaskedStrand):
                                new_rects = getattr(new_strand, 'deletion_rectangles', [])
                                original_rects = getattr(original_strand, 'deletion_rectangles', [])
                                
                                if len(new_rects) != len(original_rects):
                                    has_visual_difference = True
                                    break
                                
                                # Deep compare if counts are the same and non-zero
                                if len(new_rects) > 0:
                                    # Simple content comparison (assuming order is consistent or not critical for this check)
                                    if new_rects != original_rects:
                                        has_visual_difference = True
                                        break
                            elif isinstance(new_strand, MaskedStrand) != isinstance(original_strand, MaskedStrand):
                                # If one is MaskedStrand and the other isn't, they are different
                                has_visual_difference = True
                                break
                            # --- END ADD ---

                            # Check end line visibility
                            if hasattr(new_strand, 'end_line_visible') and hasattr(original_strand, 'end_line_visible'):
                                new_vis = new_strand.end_line_visible
                                orig_vis = original_strand.end_line_visible
                                if new_vis != orig_vis:
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'end_line_visible') != hasattr(original_strand, 'end_line_visible'):
                                has_visual_difference = True
                                break
                            # --- END ADD ---

                            # --- NEW: Check start line visibility ---
                            if hasattr(new_strand, 'start_line_visible') and hasattr(original_strand, 'start_line_visible'):
                                new_vis = new_strand.start_line_visible
                                orig_vis = original_strand.start_line_visible
                                if new_vis != orig_vis:
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'start_line_visible') != hasattr(original_strand, 'start_line_visible'):
                                has_visual_difference = True
                                break
                            # --- END NEW ---

                            # --- NEW: Check layer visibility (is_hidden) ---
                            if hasattr(new_strand, 'is_hidden') and hasattr(original_strand, 'is_hidden'):
                                if new_strand.is_hidden != original_strand.is_hidden:
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'is_hidden') != hasattr(original_strand, 'is_hidden'):
                                has_visual_difference = True
                                break
                            # --- END NEW ---

                            # --- NEW: Check shadow-only mode ---
                            if hasattr(new_strand, 'shadow_only') and hasattr(original_strand, 'shadow_only'):
                                if new_strand.shadow_only != original_strand.shadow_only:
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'shadow_only') != hasattr(original_strand, 'shadow_only'):
                                has_visual_difference = True
                                break
                            # --- END NEW ---

                            # --- NEW: Check extension visibility ---
                            if hasattr(new_strand, 'start_extension_visible') and hasattr(original_strand, 'start_extension_visible'):
                                if new_strand.start_extension_visible != original_strand.start_extension_visible:
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'start_extension_visible') != hasattr(original_strand, 'start_extension_visible'):
                                has_visual_difference = True
                                break

                            if hasattr(new_strand, 'end_extension_visible') and hasattr(original_strand, 'end_extension_visible'):
                                if new_strand.end_extension_visible != original_strand.end_extension_visible:
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'end_extension_visible') != hasattr(original_strand, 'end_extension_visible'):
                                has_visual_difference = True
                                break

                            # --- NEW: Check arrow visibility ---
                            if hasattr(new_strand, 'start_arrow_visible') and hasattr(original_strand, 'start_arrow_visible'):
                                if new_strand.start_arrow_visible != original_strand.start_arrow_visible:
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'start_arrow_visible') != hasattr(original_strand, 'start_arrow_visible'):
                                has_visual_difference = True
                                break

                            if hasattr(new_strand, 'end_arrow_visible') and hasattr(original_strand, 'end_arrow_visible'):
                                if new_strand.end_arrow_visible != original_strand.end_arrow_visible:
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'end_arrow_visible') != hasattr(original_strand, 'end_arrow_visible'):
                                has_visual_difference = True
                                break
                            # --- END NEW ---

                            # --- ADD: Check full_arrow_visible for Redo ---
                            if hasattr(new_strand, 'full_arrow_visible') and hasattr(original_strand, 'full_arrow_visible'):
                                if getattr(new_strand, 'full_arrow_visible', False) != getattr(original_strand, 'full_arrow_visible', False):
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'full_arrow_visible') != hasattr(original_strand, 'full_arrow_visible'):
                                has_visual_difference = True
                                break
                            # --- END ADD ---

                            # --- RE-ADD: Check circle visibility (has_circles) ---
                            if hasattr(new_strand, 'has_circles') and hasattr(original_strand, 'has_circles'):
                                current_circles = getattr(new_strand, 'has_circles', [False, False])
                                original_circles = getattr(original_strand, 'has_circles', [False, False])
                                if current_circles != original_circles:
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'has_circles') != hasattr(original_strand, 'has_circles'):
                                has_visual_difference = True
                                break
                            # --- END RE-ADD ---

                            # --- ADD: Check width for Redo ---
                            if hasattr(new_strand, 'width') and hasattr(original_strand, 'width'):
                                if abs(new_strand.width - original_strand.width) > 0.1:
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'width') != hasattr(original_strand, 'width'):
                                has_visual_difference = True
                                break

                            if hasattr(new_strand, 'stroke_width') and hasattr(original_strand, 'stroke_width'):
                                if abs(new_strand.stroke_width - original_strand.stroke_width) > 0.1:
                                    has_visual_difference = True
                                    break
                            elif hasattr(new_strand, 'stroke_width') != hasattr(original_strand, 'stroke_width'):
                                has_visual_difference = True
                                break
                            # --- END ADD ---

                    # If no visual difference found, skip this state and continue redoing
                    if not has_visual_difference:
                        # Recursively call redo to get to the next state
                        return self.redo() # Return the result of the recursive call
                    else:
                        pass
                        
                self.redo_performed.emit()
            else:
                # Rollback if loading failed
                self.current_step -= 1
                return False # Indicate failure

            # Make sure buttons are properly updated
            self._update_button_states()

            # --- ADD LOGGING FOR SELECTED STRAND ---
            selected_strand_after_redo = getattr(self.canvas, 'selected_strand', None)
            # --- END LOGGING ---

            # --------------------------------------------------
            # Re-enable suppression flags PRIOR to the first repaint so that
            # the very first frame after a redo already shows the complete
            # geometry (no late-appearing circles).
            # --------------------------------------------------

            self.canvas._suppress_attachment_updates = False
            self.canvas._suppress_repaint = False
            self.canvas._suppress_layer_panel_refresh = False

            # Now refresh the canvas once
            self.canvas.update()

            # Re-enable updates to prevent window flash
            if main_window:
                main_window.setUpdatesEnabled(True)

            # Re-enable window activation events after refresh
            if main_window and hasattr(main_window, 'suppress_activation_events'):
                main_window.suppress_activation_events = False
            
            # Now that all suppression flags are cleared, do a single refresh to update the UI
            # This is needed to refresh the layer panel after redo operation
            if hasattr(self.layer_panel, 'simulate_refresh_button_click'):
                self.layer_panel.simulate_refresh_button_click()
            
            return result # Return the actual result of the load operation
        else:
            return False # Indicate failure or no action

    def _clear_group_panel_ui(self, group_panel):
        """Helper method to reliably clear all widgets from the group panel's scroll layout."""
        if not group_panel or not hasattr(group_panel, 'scroll_layout'):
            return

        layout = group_panel.scroll_layout
        # Remove all widgets from the layout
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                widget = child.widget()
                widget.setParent(None) # Necessary for Qt to schedule deletion
                widget.deleteLater()
            # Clean up the layout item itself if it wasn't holding a widget
            elif child.layout():
                 # Handle nested layouts if necessary, though not expected here
                 pass # Or implement recursive clearing if needed

        # Clear internal tracking in the panel if it exists
        if hasattr(group_panel, 'groups'):
             group_panel.groups.clear()



    def _recreate_group_widgets_from_canvas(self, group_panel):
        """Helper method to recreate group widgets based on self.canvas.groups."""
        if not group_panel or not hasattr(group_panel, 'scroll_layout'):
            return
            
        # Debug: Print the canvas.groups content to diagnose issues
        if not hasattr(self.canvas, 'groups') or not self.canvas.groups:
            return
            
        
        # First clear any existing widgets
        self._clear_group_panel_ui(group_panel)
        
        # Get the scroll_layout to add widgets to
        scroll_layout = group_panel.scroll_layout
        
        # Setup counters for debugging
        processed = 0
        created = 0
        
        # Iterate through a copy of canvas.groups in case we modify it
        for group_name, group_data in dict(self.canvas.groups).items():
            processed += 1
            
            # Debug: Print structure of this group's data
            if isinstance(group_data, dict):
                if 'strands' in group_data:
                    strand_count = len(group_data['strands'])
                    
                    # Check if strands are strings or objects
                    strand_types = []
                    for s in group_data['strands'][:3]:  # Check first few for logging
                        strand_types.append(type(s).__name__)
            elif isinstance(group_data, list):
                pass
            else:
                pass
            
            try:
                # Create a new widget for this group
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
                            else:
                                # Keep the string if we can't find the object
                                updated_strands.append(strand)
                        else:
                            # It's already a strand object (or something else), keep it as is
                            updated_strands.append(strand)
                    
                    # Replace the old strands list with the updated one
                    group_data['strands'] = updated_strands
                    # Update the canvas.groups entry
                    self.canvas.groups[group_name] = group_data
                
                # Determine what strands to process
                if 'strands' in group_data:
                    strands_to_process = group_data['strands']
                elif isinstance(group_data, list):
                    strands_to_process = group_data
                else:
                    strands_to_process = []
                
                
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
                    except Exception as e1:
                        pass
                        
                    # Approach 2: Add using specific attributes    
                    if not added:
                        try:
                            group_widget.add_layer(layer_id, color, is_masked)
                            strand_count += 1
                            added = True
                        except Exception as e2:
                            pass
                    
                    # Approach 3: Add just the ID as a fallback
                    if not added:
                        try:
                            group_widget.add_layer(layer_id)
                            strand_count += 1
                            added = True
                        except Exception as e3:
                            pass
                
                # Check if any strands were added before proceeding
                if strand_count == 0:
                    continue
                
                # Add the widget to the scroll layout with proper alignment container
                
                # Create a horizontal layout container for proper alignment (matching button-created groups)
                from PyQt5.QtWidgets import QWidget, QHBoxLayout
                group_container = QWidget()
                group_container_layout = QHBoxLayout(group_container)
                group_container_layout.setContentsMargins(5, 2, 5, 2)
                group_container_layout.setSpacing(0)
                group_container_layout.addWidget(group_widget, 0, Qt.AlignLeft)
                group_container_layout.addStretch()
                
                scroll_layout.addWidget(group_container)
                
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
                        
                except Exception as e:
                    pass
                
                # If this widget should have collapsed state, set it
                if hasattr(group_widget, 'toggle_collapse') and 'collapsed' in group_data and group_data['collapsed']:
                    try:
                        group_widget.toggle_collapse()
                    except Exception as e:
                        pass

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
                except Exception as e:
                    pass
                
                created += 1

            except Exception as e:
                pass
        
        # Force update
        try:
            # Update scrollbar and layout
            if hasattr(group_panel, 'scroll_area') and group_panel.scroll_area:
                group_panel.scroll_area.verticalScrollBar().setValue(0)
                
            # Make sure the panel gets properly refreshed
            scroll_layout.activate()
            group_panel.updateGeometry()
            group_panel.update()
            
        except Exception as e:
            pass
            
        
        # Output the final result of the groups stored in the panel
        if hasattr(group_panel, 'groups'):
            pass
            
        # Return success/failure status
        return created > 0

    def _refresh_group_panel(self, has_loaded_groups):
        """
        Refreshes the group panel UI based on the loaded state.
        Always clears the UI first, then rebuilds from self.canvas.groups if necessary.
        """

        group_manager = getattr(self.canvas, 'group_layer_manager', None)
        if not group_manager:
            return

        group_panel = getattr(group_manager, 'group_panel', None)
        if not group_panel:
            return

        # --- Step 1: Always Clear the UI ---
        self._clear_group_panel_ui(group_panel)

        # --- Step 2: Recreate UI if state has groups ---
        if has_loaded_groups:
            if hasattr(self.canvas, 'groups') and self.canvas.groups:
                 self._recreate_group_widgets_from_canvas(group_panel)
            else:
                 pass
        else:
            pass

        # --- Step 3: Final UI Update ---
        # Force an update on the panel to ensure layout changes are visible
        try:
            group_panel.update()
            if hasattr(group_panel, 'scroll_area') and group_panel.scroll_area:
                 group_panel.scroll_area.update()
        except Exception as e:
            pass


    def _load_state(self, step):
        """Load the state for the specified step and apply it."""
        filename = self._get_state_filename(step)

        if not os.path.exists(filename):
            return False

        try:
            # --- Step 1: Load data from file and inspect its structure --- 
            
            # First inspect the raw JSON to understand the structure
            with open(filename, 'r') as f:
                raw_data = json.load(f)
                
            # Log information about the raw data structure
            has_groups_in_file = 'groups' in raw_data and bool(raw_data.get('groups', {}))
            if has_groups_in_file:
                group_count = len(raw_data.get('groups', {}))
                group_names = list(raw_data.get('groups', {}).keys())
            
            # Load the data using the normal method
            # --- MODIFIED: Receive selected_strand_name and button states --- 
            loaded_strands, loaded_groups_data, selected_strand_name, locked_layers, lock_mode, shadow_enabled, show_control_points = load_strands(filename, self.canvas)
            # --- END MODIFIED ---
            state_has_groups = bool(loaded_groups_data)
            
            # Check if we lost groups during loading
            if has_groups_in_file and not state_has_groups:
                
                # Try to manually extract group data from the file
                if 'groups' in raw_data:
                    loaded_groups_data = raw_data['groups']
                    state_has_groups = bool(loaded_groups_data)

            # --- Step 2: Replace canvas data --- 
            # Completely replace the existing strands and groups with the loaded data
            self.canvas.strands = loaded_strands
            
            # Ensure self.canvas.groups exists
            if not hasattr(self.canvas, 'groups'):
                self.canvas.groups = {}
            
            # Clear the group panel's internal state before loading new groups
            if hasattr(self.canvas, 'group_layer_manager') and hasattr(self.canvas.group_layer_manager, 'group_panel'):
                self.canvas.group_layer_manager.group_panel.groups = {}
                # Clear the group panel's visual elements
                if hasattr(self.canvas.group_layer_manager.group_panel, 'scroll_layout'):
                    while self.canvas.group_layer_manager.group_panel.scroll_layout.count():
                        child = self.canvas.group_layer_manager.group_panel.scroll_layout.takeAt(0)
                        if child.widget():
                            child.widget().deleteLater()
                
            # Set the groups data on the canvas
            if state_has_groups:
                self.canvas.groups = loaded_groups_data
            else:
                # Clear any existing groups if the state has none
                self.canvas.groups = {}
                
            
            # Update strand properties (like canvas reference) after loading
            for strand in self.canvas.strands:
                 if hasattr(strand, 'set_canvas'):
                      strand.set_canvas(self.canvas)
                 # Add any other necessary post-load initialization for strands here
                 
                 # Check if we're preserving shadow state from before the load
                 if hasattr(self.canvas, '_preserve_shadow_state'):
                     strand.should_draw_shadow = self.canvas._preserve_shadow_state
                 else:
                     # Otherwise use the canvas's current shadow_enabled state
                     strand.should_draw_shadow = self.canvas.shadow_enabled if hasattr(self.canvas, 'shadow_enabled') else True
                 
            # --- NEW: Restore selection AFTER applying strands --- 
            if selected_strand_name:
                found_selected_strand = None
                found_selected_index = -1
                for i, strand in enumerate(self.canvas.strands):
                    if strand.layer_name == selected_strand_name:
                        found_selected_strand = strand
                        found_selected_index = i
                        break
                if found_selected_strand:
                    self.canvas.selected_strand = found_selected_strand
                    self.canvas.selected_strand_index = found_selected_index
                    self.canvas.selected_strand.is_selected = True
                else:
                    self.canvas.selected_strand = None
                    self.canvas.selected_strand_index = None
            else:
                # No selection saved, ensure canvas selection is cleared
                self.canvas.selected_strand = None
                self.canvas.selected_strand_index = None
            # --- END NEW --- 
            
            # --- Step 3: Restore locked layers and lock mode BEFORE UI refresh ---
            # Restore lock mode state first
            if hasattr(self.layer_panel, 'lock_mode'):
                self.layer_panel.lock_mode = lock_mode
                if hasattr(self.layer_panel, 'lock_layers_button'):
                    self.layer_panel.lock_layers_button.setChecked(lock_mode)
                    # Get current language translations
                    from translations import translations
                    language_code = self.canvas.language_code if hasattr(self.canvas, 'language_code') else 'en'
                    _ = translations[language_code]
                    if lock_mode:
                        self.layer_panel.lock_layers_button.setText(_['exit_lock_mode'])
                        if hasattr(self.layer_panel, 'notification_label'):
                            self.layer_panel.notification_label.setText(_['select_layers_to_lock'] if 'select_layers_to_lock' in _ else "")
                        if hasattr(self.layer_panel, 'deselect_all_button'):
                            self.layer_panel.deselect_all_button.setText(_['clear_all_locks'])
                    else:
                        self.layer_panel.lock_layers_button.setText(_['lock_layers'])
                        if hasattr(self.layer_panel, 'notification_label'):
                            self.layer_panel.notification_label.setText("")
                        if hasattr(self.layer_panel, 'deselect_all_button'):
                            self.layer_panel.deselect_all_button.setText(_['deselect_all'])
            
            # Restore locked layers state after lock mode is set
            if hasattr(self.layer_panel, 'locked_layers'):
                self.layer_panel.locked_layers = locked_layers.copy()
                
                # Log current button count for debugging
                button_count = len(getattr(self.layer_panel, 'layer_buttons', []))
                
                # Always call update_layer_buttons_lock_state to apply the visual state
                if hasattr(self.layer_panel, 'update_layer_buttons_lock_state'):
                    self.layer_panel.update_layer_buttons_lock_state()
                
                # Also update MoveMode's locked_layers if it exists
                if hasattr(self.canvas, 'current_mode') and self.canvas.current_mode.__class__.__name__ == 'MoveMode':
                    move_mode = self.canvas.current_mode
                    if hasattr(move_mode, 'set_locked_layers'):
                        move_mode.set_locked_layers(locked_layers.copy(), lock_mode)
                    else:
                        # Fallback - set directly if set_locked_layers doesn't exist
                        move_mode.locked_layers = locked_layers.copy()
                        move_mode.lock_mode_active = lock_mode

            # --- Step 4: Refresh UI Panels AFTER lock state restoration (unless suppressed) --- 
            # Check if we're in an undo/redo operation and skip refreshes to prevent window flash
            if not (hasattr(self.canvas, '_suppress_layer_panel_refresh') and self.canvas._suppress_layer_panel_refresh):
                # Refresh layer panel based on the new self.canvas.strands
                self._refresh_layer_panel() 

                # Try to simulate a refresh button click (preferred method)
                if hasattr(self.layer_panel, 'simulate_refresh_button_click'):
                    self.layer_panel.simulate_refresh_button_click()
                # Fallback to direct method call if simulate method not available
                elif hasattr(self.layer_panel, 'refresh_layers'):
                    self.layer_panel.refresh_layers_no_zoom()
            else:
                pass
            
            # Apply lock state after refresh since refresh recreates buttons (or apply to existing buttons if refresh was suppressed)
            if hasattr(self.layer_panel, 'locked_layers') and hasattr(self.layer_panel, 'update_layer_buttons_lock_state'):
                if hasattr(self.canvas, '_suppress_layer_panel_refresh') and self.canvas._suppress_layer_panel_refresh:
                    pass
                else:
                    pass
                self.layer_panel.update_layer_buttons_lock_state()
            
            # Log which buttons are now locked for verification after refresh
            if hasattr(self.layer_panel, 'layer_buttons'):
                for i in range(min(len(getattr(self.layer_panel, 'layer_buttons', [])), 5)):  # Only log first 5 for brevity
                    button = self.layer_panel.layer_buttons[i]
                    is_locked = getattr(button, 'locked', False)
                    should_be_locked = i in locked_layers

            # Refresh group panel based on the new self.canvas.groups
            success = self._refresh_group_panel(state_has_groups) # Pass the flag indicating if groups exist
            
            if state_has_groups and not success:
                
                # Additional recovery steps for groups
                if hasattr(self.canvas, 'group_layer_manager') and self.canvas.group_layer_manager:
                    try:
                        group_manager = self.canvas.group_layer_manager
                        if hasattr(group_manager, 'refresh'):
                            group_manager.refresh()
                    except Exception as e:
                        pass

            # --- Step 4: Restore button states ---
            self._restore_button_states(shadow_enabled, show_control_points)
                    
            # Update all strands' control points visibility
            for strand in self.canvas.strands:
                if hasattr(strand, 'show_control_points'):
                    strand.show_control_points = show_control_points
            

            # --- Step 5: Update LayerStateManager ---
            # IMPORTANT: After loading all strands, we must recalculate connections
            # to ensure all strands (including new ones like '1_4') are in the connections dictionary
            if hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
                self.canvas.layer_state_manager.save_current_state()
            
            # --- Step 6: Final Canvas Update --- 
            self.canvas.update()
            
            # Optional: Update selection state if needed (e.g., clear selection)
            if hasattr(self.canvas, 'deselect_strand'):
                 self.canvas.deselect_strand()

            return True # Indicate success
            
        except Exception as e:
            # Consider rolling back or handling the error state more gracefully here if needed
            return False # Indicate failure
    
    def _refresh_layer_panel(self):
        """Refresh the layer panel UI to match loaded state."""
        if hasattr(self.layer_panel, 'refresh'):
            self.layer_panel.refresh()
        else:
            pass
        
        # Also refresh/update the layer state manager if available
        if hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
            if hasattr(self.canvas.layer_state_manager, 'update_layer_order'):
                layer_names = [strand.layer_name for strand in self.canvas.strands if hasattr(strand, 'layer_name')]
                self.canvas.layer_state_manager.update_layer_order(layer_names)

    def _force_clear_all_groups(self):
        """Force a complete removal of all groups from both canvas and UI."""
        
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
            pass
            
        # Then clear the groups from the panel itself
        if hasattr(self.canvas, 'group_layer_manager') and hasattr(self.canvas.group_layer_manager, 'group_panel'):
            group_panel = self.canvas.group_layer_manager.group_panel
            
            # Get all groups from the panel and delete them one by one
            groups_to_delete = []
            if hasattr(group_panel, 'groups'):
                groups_to_delete = list(group_panel.groups.keys())
                
                
            for group_name in groups_to_delete:
                try:
                    # Check if group exists in canvas
                    if not hasattr(self.canvas, 'groups') or group_name not in self.canvas.groups:
                        pass
                    
                    # Try to use the delete_group method
                    if hasattr(group_panel, 'delete_group'):
                        group_panel.delete_group(group_name)
                except Exception as e:
                    pass
                    
            # Force reset the groups dictionary to be empty
            if hasattr(group_panel, 'groups'):
                group_panel.groups = {}
                
            # Remove any remaining widgets from the scroll layout
            if hasattr(group_panel, 'scroll_layout'):
                # Find all widgets in the scroll layout
                widget_count = group_panel.scroll_layout.count()
                
                # Remove all widgets
                for i in range(widget_count - 1, -1, -1):  # Remove in reverse order
                    try:
                        widget = group_panel.scroll_layout.itemAt(i).widget()
                        if widget:
                            widget.setParent(None)
                            widget.deleteLater()
                    except Exception as e:
                        pass
                        
                
        # Ensure canvas.groups is empty
        if hasattr(self.canvas, 'groups'):
            self.canvas.groups = {}
            
    
    def _ensure_all_groups_exist_in_panel(self, group_manager):
        """Ensure all groups in canvas.groups exist in the panel."""
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
            
            # Create each missing group
            for group_name in missing_groups:
                if group_name in self.canvas.groups and 'strands' in self.canvas.groups[group_name]:
                    strands = self.canvas.groups[group_name]['strands']
                    if strands and hasattr(group_panel, 'create_group'):
                        try:
                            group_panel.create_group(group_name, strands)
                        except Exception as e:
                            pass
        else:
            pass
    
    def _create_all_groups_in_panel(self, group_panel):
        """Create all groups from canvas.groups in the panel."""
        
        # Loop through the available groups in canvas.groups
        for group_name, group_data in self.canvas.groups.items():
            if 'strands' in group_data and group_data['strands']:
                # If panel has create_group method, use it
                if hasattr(group_panel, 'create_group'):
                    try:
                        # Create group with strands
                        group_panel.create_group(group_name, group_data['strands'])
                    except Exception as e:
                        pass
        

    def load_specific_state(self, filepath):
        """Loads a specific state file, applies it, and preserves the entire history of the loaded session."""
        if os.path.exists(filepath):
            try:
                # Extract the session ID and step from the filepath
                # Filepath format is: /path/to/temp_dir/YYYYMMDDHHMMSS_step.json
                filename = os.path.basename(filepath)
                
                # Store the original session ID for cleanup
                original_session_id = self.session_id
                
                # Parse the session ID and step from the filename
                parts = filename.split('_')
                if len(parts) >= 2:
                    # Extract the session ID (timestamp part before the underscore)
                    loaded_session_id = parts[0]
                    
                    # Extract the step number from the filename (part after underscore, before .json)
                    loaded_step = int(parts[1].split('.')[0])
                    
                    
                    # Update the current session ID to continue with the loaded session
                    self.session_id = loaded_session_id
                else:
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
                except Exception as e:
                    return False
                
                # Clean up any files from the current session before switching
                try:
                    for file in os.listdir(self.temp_dir):
                        if file.startswith(f"{original_session_id}_") and file.endswith(".json"):
                            try:
                                os.remove(os.path.join(self.temp_dir, file))
                            except:
                                pass
                except Exception as e:
                    pass
                
                # Load strands and groups from the specified file
                strands, groups, selected_strand_name, locked_layers, lock_mode, shadow_enabled, show_control_points = load_strands(filepath, self.canvas)
                
                # First inspect the raw JSON directly to ensure we didn't miss anything
                with open(filepath, 'r') as f:
                    raw_data = json.load(f)
                    has_groups_in_file = 'groups' in raw_data and bool(raw_data.get('groups', {}))
                    if has_groups_in_file:
                        group_count = len(raw_data.get('groups', {}))
                        group_names = list(raw_data.get('groups', {}).keys())
                        
                        # Ensure the groups data is properly loaded
                        if not groups and has_groups_in_file:
                            groups = raw_data.get('groups', {})

                # Apply the loaded state to the canvas
                self.canvas.strands = strands
                if hasattr(self.canvas, 'groups'):
                    self.canvas.groups = groups
                else:
                    self.canvas.groups = {}

                # Set the step pointers to match the loaded state
                self.current_step = loaded_step
                self.max_step = max_step

                # Refresh UI
                if hasattr(self.layer_panel, 'refresh'):
                    self.layer_panel.refresh()
                
                # Restore locked layers
                if hasattr(self.layer_panel, 'locked_layers') and locked_layers:
                    self.layer_panel.locked_layers = locked_layers.copy()
                    if hasattr(self.layer_panel, 'update_layer_buttons_lock_state'):
                        self.layer_panel.update_layer_buttons_lock_state()
                
                # Restore lock mode state
                if hasattr(self.layer_panel, 'lock_mode'):
                    self.layer_panel.lock_mode = lock_mode
                    if hasattr(self.layer_panel, 'lock_layers_button'):
                        self.layer_panel.lock_layers_button.setChecked(lock_mode)
                        # Get current language translations
                        from translations import translations
                        language_code = self.canvas.language_code if hasattr(self.canvas, 'language_code') else 'en'
                        _ = translations[language_code]
                        if lock_mode:
                            self.layer_panel.lock_layers_button.setText(_['exit_lock_mode'])
                            if hasattr(self.layer_panel, 'notification_label'):
                                self.layer_panel.notification_label.setText(_['select_layers_to_lock'] if 'select_layers_to_lock' in _ else "")
                            if hasattr(self.layer_panel, 'deselect_all_button'):
                                self.layer_panel.deselect_all_button.setText(_['clear_all_locks'])
                        else:
                            self.layer_panel.lock_layers_button.setText(_['lock_layers'])
                            if hasattr(self.layer_panel, 'notification_label'):
                                self.layer_panel.notification_label.setText("")
                            if hasattr(self.layer_panel, 'deselect_all_button'):
                                self.layer_panel.deselect_all_button.setText(_['deselect_all'])
                
                # Now handle the group panel update
                state_has_groups = bool(self.canvas.groups)
                
                # --- Perform comprehensive group panel refresh ---
                if state_has_groups and hasattr(self.canvas, 'group_layer_manager') and self.canvas.group_layer_manager:
                    group_manager = self.canvas.group_layer_manager
                    group_panel = getattr(group_manager, 'group_panel', None)
                    
                    if group_panel:
                        # First clear the current group panel UI
                        self._clear_group_panel_ui(group_panel)
                        
                        # Rebuild the group panel UI from scratch
                        success = self._recreate_group_widgets_from_canvas(group_panel)
                        
                        # If that didn't work, try group_layer_manager's refresh method
                        if not success and hasattr(group_manager, 'refresh'):
                            group_manager.refresh()
                            
                        # Final approach: recreate each group manually
                        if hasattr(group_panel, 'create_group') and not success:
                            for group_name, group_data in self.canvas.groups.items():
                                if 'strands' in group_data and group_data['strands']:
                                    try:
                                        group_panel.create_group(group_name, group_data['strands'])
                                    except Exception as e:
                                        pass
                            
                        # Force UI update
                        group_panel.update()
                        if hasattr(group_panel, 'scroll_area') and group_panel.scroll_area:
                            group_panel.scroll_area.update()
                        
                
                # --- Button state restoration for load_specific_state ---
                
                # Restore shadow button state
                self.canvas.shadow_enabled = shadow_enabled
                
                # Try to find the main window for button restoration
                main_window = None
                if hasattr(self.canvas, 'main_window') and self.canvas.main_window:
                    main_window = self.canvas.main_window
                elif hasattr(self, 'layer_panel') and hasattr(self.layer_panel, 'main_window'):
                    main_window = self.layer_panel.main_window
                else:
                    pass
                
                if main_window:
                    # Restore shadow button
                    if hasattr(main_window, 'toggle_shadow_button'):
                        main_window.toggle_shadow_button.setChecked(shadow_enabled)
                    else:
                        pass
                    
                    # Restore control points button
                    if hasattr(main_window, 'toggle_control_points_button'):
                        main_window.toggle_control_points_button.setChecked(show_control_points)
                    else:
                        pass
                # --- End button state restoration ---
                
                self.canvas.update()
                self.state_saved.emit(self.current_step) # Emit signal to update buttons

                # Verify the session ID is still set correctly after all operations
                test_filename = self._get_state_filename(self.current_step + 1)  # Get what the next state filename would be

                return True
            except Exception as e:
                return False
        else:
            return False

    def _update_button_states(self):
        """Update the enabled state of undo/redo buttons."""
        if self.undo_button:
            # Enable undo if we have a current step greater than 0
            # This allows undoing from step 1 to the empty state
            can_undo = self.current_step > 0
            self.undo_button.setEnabled(can_undo)
            
            # Update tooltip based on enabled state
            from translations import translations
            language_code = 'en'  # Default
            if hasattr(self.layer_panel, 'language_code'):
                language_code = self.layer_panel.language_code
            elif hasattr(self.layer_panel, 'parent_window') and hasattr(self.layer_panel.parent_window, 'language_code'):
                language_code = self.layer_panel.parent_window.language_code
            
            _ = translations[language_code]
            if can_undo:
                self.undo_button.set_custom_tooltip(_['undo_tooltip'])
            else:
                # Add "currently unavailable" to the tooltip when disabled
                unavailable_text = _['currently_unavailable'] if 'currently_unavailable' in _ else 'Currently unavailable'
                self.undo_button.set_custom_tooltip(_['undo_tooltip'] + f'\n({unavailable_text})')
            
        else:
            pass
            
        if self.redo_button:
            can_redo = self.current_step < self.max_step
            self.redo_button.setEnabled(can_redo)
            
            # Update tooltip based on enabled state
            from translations import translations
            language_code = 'en'  # Default
            if hasattr(self.layer_panel, 'language_code'):
                language_code = self.layer_panel.language_code
            elif hasattr(self.layer_panel, 'parent_window') and hasattr(self.layer_panel.parent_window, 'language_code'):
                language_code = self.layer_panel.parent_window.language_code
            
            _ = translations[language_code]
            if can_redo:
                self.redo_button.set_custom_tooltip(_['redo_tooltip'])
            else:
                # Add "currently unavailable" to the tooltip when disabled
                unavailable_text = _['currently_unavailable'] if 'currently_unavailable' in _ else 'Currently unavailable'
                self.redo_button.set_custom_tooltip(_['redo_tooltip'] + f'\n({unavailable_text})')
                
        else:
            pass

    def setup_buttons(self, top_layout):
        """Create and add undo/redo buttons to the specified layout."""
        # Create buttons using StrokeTextButton for consistent styling
        # Use symbols that render reliably across platforms
        if sys.platform == "darwin":
            # On macOS, the emoji variants may not render in Qt widgets
            undo_symbol = "↶"  # anticlockwise arrow (undo)
            redo_symbol = "↷"  # clockwise arrow (redo)
        else:
            # On Windows/Linux, keep the hook arrows (non-emoji for consistency)
            undo_symbol = "↩️"
            redo_symbol = "↪️"

        self.undo_button = StrokeTextButton(undo_symbol)
        self.redo_button = StrokeTextButton(redo_symbol)
        
        # Get current theme from parent window if available
        current_theme = "default"
        if hasattr(self.layer_panel, 'parent_window') and hasattr(self.layer_panel.parent_window, 'theme_name'):
            current_theme = self.layer_panel.parent_window.theme_name
        elif hasattr(self.layer_panel, 'current_theme'):
            current_theme = self.layer_panel.current_theme
        
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
                "bg_hover": "#5179a0",            # Lighter hover background (consistent with refresh button in dark theme)
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
        
        # Apply same colors to redo button
        self.redo_button.theme_colors = self.undo_button.theme_colors.copy()
        
        # Apply the current theme
        self.undo_button.set_theme(current_theme)
        self.redo_button.set_theme(current_theme)
        
        # Set fixed size to match the refresh button
        self.undo_button.setFixedSize(40, 40)
        self.redo_button.setFixedSize(40, 40)
        
        # Set tooltips using custom tooltip method for right-click with translations
        from translations import translations
        language_code = 'en'  # Default
        if hasattr(self.layer_panel, 'language_code'):
            language_code = self.layer_panel.language_code
        elif hasattr(self.canvas, 'language_code'):
            language_code = self.canvas.language_code
        
        _ = translations[language_code]
        self.undo_button.set_custom_tooltip(_['undo_tooltip'])
        self.redo_button.set_custom_tooltip(_['redo_tooltip'])
        
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
        
        
        return self.undo_button, self.redo_button
    
    def update_button_tooltips(self, language_code='en'):
        """Update button tooltips with the current language"""
        if self.undo_button and self.redo_button:
            from translations import translations
            _ = translations[language_code]
            
            # Check if buttons are enabled and set appropriate tooltip
            if self.undo_button.isEnabled():
                self.undo_button.set_custom_tooltip(_['undo_tooltip'])
            else:
                unavailable_text = _['currently_unavailable'] if 'currently_unavailable' in _ else 'Currently unavailable'
                self.undo_button.set_custom_tooltip(_['undo_tooltip'] + f'\n({unavailable_text})')
                
            if self.redo_button.isEnabled():
                self.redo_button.set_custom_tooltip(_['redo_tooltip'])
            else:
                unavailable_text = _['currently_unavailable'] if 'currently_unavailable' in _ else 'Currently unavailable'
                self.redo_button.set_custom_tooltip(_['redo_tooltip'] + f'\n({unavailable_text})')

    def clear_history(self, save_current=True):
        """Clear all saved states for the current session and reset the history."""
        for step in range(1, self.max_step + 1):
            filename = self._get_state_filename(step)
            try:
                if os.path.exists(filename):
                    os.remove(filename)
            except OSError as e:
                pass

        self.current_step = 0
        self.max_step = 0

        if save_current:
            # Save current state as the initial state (step 1)
            self.save_state() # This increments current_step to 1 and saves
        else:
            # If not saving current, just reset steps and update buttons
            self._update_button_states()
            
    def clear_all_past_history(self):
        """Deletes all *.json state files from the temp_states directory, 
           excluding the files belonging to the current session."""
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
                        cleared_count += 1
                    except OSError as e:
                        error_count += 1
        except Exception as e:
            pass
            
        # Note: This function only deletes files, it doesn't affect the current session's history management

    def cleanup(self):
        """Clean up temporary files when the application closes."""
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            pass

    def get_temp_dir(self):
        """Returns the path to the temporary directory."""
        return self.temp_dir

    def get_session_id(self):
        """Returns the current session ID."""
        return self.session_id

    def _create_group_in_panel(self, group_name, group_data):
        """Directly create a group in the panel from loaded data."""
        
        if not hasattr(self.canvas, 'group_layer_manager') or not self.canvas.group_layer_manager:
            return False
            
        if not hasattr(self.canvas.group_layer_manager, 'group_panel'):
            return False
            
        group_panel = self.canvas.group_layer_manager.group_panel
        
        # Skip if group already exists in panel
        if hasattr(group_panel, 'groups') and group_name in group_panel.groups:
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
        
        
        # Now convert those IDs to actual strand objects
        existing_strands = []
        for strand_id in strand_ids:
            # Find the matching strand object in the canvas
            for strand in self.canvas.strands:
                if hasattr(strand, 'layer_name') and strand.layer_name == strand_id:
                    existing_strands.append(strand)
                    break
        
        if not existing_strands:
            return False
            
        
        # Try several approaches to create the group
        try:
            # First approach: Use the standard create_group method
            group_panel.create_group(group_name, existing_strands)
            return True
        except Exception as e:
            
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
                    return True
            except Exception as e:
                pass
        
        # If all approaches failed, log an error
        return False

    def set_theme(self, theme_name):
        """Apply the specified theme to undo/redo buttons"""
        if not hasattr(self, 'undo_button') or not hasattr(self, 'redo_button'):
            return
            
        if self.undo_button and hasattr(self.undo_button, 'set_theme'):
            self.undo_button.set_theme(theme_name)
            
        if self.redo_button and hasattr(self.redo_button, 'set_theme'):
            self.redo_button.set_theme(theme_name)

    def export_history(self, filepath):
        """Export the entire undo/redo history to a single JSON file.

        The generated file contains a list of *all* state JSON blobs together
        with bookkeeping information so that the history can be reconstructed
        later via `import_history()`.  This allows a project to be saved and,
        when re-opened, have the full undo/redo stack available.
        """
        try:
            # Always make sure the current canvas state is captured first.
            # This guarantees that any changes since the last automatic save
            # are included in the exported history.
            if not self._would_be_identical_save():
                self.save_state()

            history_payload = {
                "type": "OpenStrandStudioHistory",
                "version": 1,
                "current_step": self.current_step,
                "max_step": self.max_step,
                "states": []
            }

            for step in range(1, self.max_step + 1):
                state_file = self._get_state_filename(step)
                if not os.path.exists(state_file):
                    continue
                try:
                    with open(state_file, "r", encoding="utf-8") as f:
                        state_data = json.load(f)
                    history_payload["states"].append({
                        "step": step,
                        "data": state_data
                    })
                except Exception as e:
                    return False

            # Finally write the consolidated history file.
            with open(filepath, "w", encoding="utf-8") as out_f:
                json.dump(history_payload, out_f, indent=2)

            return True
        except Exception as e:
            return False

    def import_history(self, filepath):
        """Import a history JSON previously produced by `export_history()`.

        The function rebuilds the temp state files for a fresh session and
        loads the *current* state so that the application reflects the saved
        canvas exactly while also restoring the entire undo/redo stack.
        """
        try:
            # Read the history file
            with open(filepath, "r", encoding="utf-8") as f:
                history_payload = json.load(f)

            if not isinstance(history_payload, dict) or "states" not in history_payload:
                return False

            states_list = history_payload.get("states", [])
            if not states_list:
                return False

            # Wipe existing temp state files for a clean import
            try:
                for fname in os.listdir(self.temp_dir):
                    if fname.endswith(".json"):
                        os.remove(os.path.join(self.temp_dir, fname))
            except Exception as e:
                pass

            # Start a **new** session id to avoid clashing with prior sessions
            self.session_id = datetime.now().strftime("%Y%m%d%H%M%S")

            # Re-create each state file with the new session id while preserving step numbers
            recreated_steps = 0
            for entry in states_list:
                step_num = entry.get("step")
                state_data = entry.get("data")
                if step_num is None or state_data is None:
                    continue
                try:
                    target_path = self._get_state_filename(step_num)
                    with open(target_path, "w", encoding="utf-8") as out_f:
                        json.dump(state_data, out_f, indent=2)
                    recreated_steps += 1
                except Exception as e:
                    return False

            # Restore bookkeeping counters
            self.max_step = recreated_steps
            self.current_step = min(history_payload.get("current_step", recreated_steps), recreated_steps)


            # Load the canvas state corresponding to current_step
            load_success = self._load_state(self.current_step)
            if not load_success:
                return False

            # Update UI buttons
            self._update_button_states()
            return True
        except Exception as e:
            return False

    def _restore_button_states(self, shadow_enabled, show_control_points):
        """
        Restore button visual states when loading state during undo/redo operations.
        
        Args:
            shadow_enabled (bool): Whether shadow should be enabled
            show_control_points (bool): Whether control points should be shown
        """
        
        # Check if we're preserving states from before the load
        if hasattr(self.canvas, '_preserve_shadow_state'):
            # Use preserved states instead of loaded states
            self.canvas.shadow_enabled = self.canvas._preserve_shadow_state
            shadow_enabled = self.canvas._preserve_shadow_state
        else:
            # Restore canvas properties from file
            self.canvas.shadow_enabled = shadow_enabled
            
        if hasattr(self.canvas, '_preserve_control_points_state'):
            self.canvas.show_control_points = self.canvas._preserve_control_points_state
            show_control_points = self.canvas._preserve_control_points_state
        else:
            self.canvas.show_control_points = show_control_points
        
        # Try to find the main window through parent_window reference
        main_window = None
        if hasattr(self.canvas, 'parent_window') and self.canvas.parent_window:
            main_window = self.canvas.parent_window
        elif hasattr(self.canvas, 'main_window') and self.canvas.main_window:
            main_window = self.canvas.main_window
        elif hasattr(self, 'layer_panel') and hasattr(self.layer_panel, 'main_window'):
            main_window = self.layer_panel.main_window
        else:
            pass
        
        if main_window:
            # Restore shadow button visual state
            if hasattr(main_window, 'toggle_shadow_button'):
                main_window.toggle_shadow_button.setChecked(shadow_enabled)
            else:
                pass
            
            # Restore control points button visual state
            if hasattr(main_window, 'toggle_control_points_button'):
                main_window.toggle_control_points_button.setChecked(show_control_points)
            else:
                pass
        
        # Update all strands' control points visibility
        for strand in self.canvas.strands:
            if hasattr(strand, 'show_control_points'):
                strand.show_control_points = show_control_points
        

def connect_to_move_mode(canvas, undo_redo_manager):
    """
    Connect the move mode's mouse release event to save state, but only if a move occurred.
    
    Args:
        canvas: The canvas object with the move_mode
        undo_redo_manager: The UndoRedoManager instance
    """
    if hasattr(canvas, 'move_mode') and canvas.move_mode:
        # Store a reference to the undo_redo_manager in the canvas
        canvas.undo_redo_manager = undo_redo_manager
        
        # Also store a reference in the move_mode directly to ensure it's available
        canvas.move_mode.undo_redo_manager = undo_redo_manager
        
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
                # If a control point was being moved, reset the last save time to force a new state
                if getattr(canvas.move_mode, 'is_moving_control_point', False):
                    undo_redo_manager._last_save_time = 0
                undo_redo_manager.save_state()
            else:
                pass
        
        # Replace the original function with our enhanced version
        canvas.move_mode.mouseReleaseEvent = enhanced_mouse_release
        
        # Do NOT save initial state automatically - only save when user actions create content
        # undo_redo_manager.save_state() - REMOVED
    else:
        pass


def connect_to_attach_mode(canvas, undo_redo_manager):
    """
    Connect the attach mode's mouse release event to manage state save suppression.
    The actual save is triggered by the strand_created signal.

    Args:
        canvas: The canvas object with the attach_mode
        undo_redo_manager: The UndoRedoManager instance
    """
    if hasattr(canvas, 'attach_mode') and canvas.attach_mode:
        original_mouse_release = canvas.attach_mode.mouseReleaseEvent

        def enhanced_mouse_release_and_save(event):
            """Wrap attach_mode.mouseReleaseEvent to perform a single state save *after* the
            attach operation finishes. Any internal calls to save_state that may occur
            during the original handler are temporarily suppressed using the _skip_save
            flag. Once the original handler completes, the flag is cleared and a single
            save_state call is executed on the next iteration of the event loop so that
            the newly-created or attached strand is fully initialised."""

            # Check if we're already processing an attach operation to prevent multiple saves
            if getattr(undo_redo_manager, '_attach_save_in_progress', False):
                # Still execute the original mouse release logic, just skip the state saving
                original_mouse_release(event)
                return

            # Check if a mask operation was just completed to prevent duplicate saves
            if getattr(undo_redo_manager, '_mask_save_completed', False):
                # Still execute the original mouse release logic, just skip the state saving
                original_mouse_release(event)
                # Clear the mask completion flag since we've handled it
                setattr(undo_redo_manager, '_mask_save_completed', False)
                return

            # Suppress any intermediate saves that might be triggered inside the original handler
            setattr(undo_redo_manager, '_skip_save', True)
            setattr(undo_redo_manager, '_attach_save_in_progress', True)
            
            try:
                # Execute the original attach_mode mouseReleaseEvent logic
                original_mouse_release(event)
            finally:
                # After the attach operation has completed (and other handlers such as
                # layer-panel updates have had a chance to run) perform ONE state save.
                # Keep the suppression flag enabled a little longer so that any other
                # delayed handlers that might try to save are ignored.
                def _finalize_save():
                    # Check if we already saved to prevent duplicate saves
                    if getattr(undo_redo_manager, '_attach_save_completed', False):
                        return
                    
                    # Temporarily lift the suppression to allow exactly one save
                    setattr(undo_redo_manager, '_skip_save', False)
                    undo_redo_manager.save_state()
                    
                    # Mark as completed to prevent duplicate saves
                    setattr(undo_redo_manager, '_attach_save_completed', True)
                    
                    # Re-enable suppression for the next 250 ms to swallow any late calls
                    setattr(undo_redo_manager, '_skip_save', True)
                    QTimer.singleShot(250, lambda: (
                        setattr(undo_redo_manager, '_skip_save', False),
                        setattr(undo_redo_manager, '_attach_save_in_progress', False),
                        setattr(undo_redo_manager, '_attach_save_completed', False)
                    ))
                # Run after 100 ms to ensure all side-effects (group recreation, layer updates…) are done
                QTimer.singleShot(100, _finalize_save)

        # Replace the original function with our enhanced version
        canvas.attach_mode.mouseReleaseEvent = enhanced_mouse_release_and_save
    else:
        pass


def connect_to_mask_mode(canvas, undo_redo_manager):
    """
    Connect the mask mode's mask_created signal to save state when a mask is created.
    
    Args:
        canvas: The canvas object with the mask_mode
        undo_redo_manager: The UndoRedoManager instance
    """
    if hasattr(canvas, 'mask_mode') and canvas.mask_mode:
        # Connect the mask_created signal to save state
        def on_mask_created(_strand1, _strand2):
            
            # Check if we're already processing a mask operation to prevent multiple saves
            if getattr(undo_redo_manager, '_mask_save_in_progress', False):
                return
            
            # Set suppression flags to prevent duplicate saves
            setattr(undo_redo_manager, '_skip_save', True)
            setattr(undo_redo_manager, '_mask_save_in_progress', True)
            
            def _finalize_mask_save():
                # Check if we already saved to prevent duplicate saves
                if getattr(undo_redo_manager, '_mask_save_completed', False):
                    return
                
                # Temporarily lift the suppression to allow exactly one save
                setattr(undo_redo_manager, '_skip_save', False)
                undo_redo_manager.save_state()
                
                # Mark as completed to prevent duplicate saves
                setattr(undo_redo_manager, '_mask_save_completed', True)
                
                # Re-enable suppression for the next 250 ms to swallow any late calls
                setattr(undo_redo_manager, '_skip_save', True)
                QTimer.singleShot(250, lambda: (
                    setattr(undo_redo_manager, '_skip_save', False),
                    setattr(undo_redo_manager, '_mask_save_in_progress', False),
                    setattr(undo_redo_manager, '_mask_save_completed', False)
                ))
            
            # Run after 100 ms to ensure all side-effects are done
            QTimer.singleShot(100, _finalize_mask_save)
            
        # Connect the signal to our handler
        try:
            # Disconnect existing connections first to prevent duplicates
            canvas.mask_mode.mask_created.disconnect(on_mask_created)
        except (TypeError, RuntimeError):
            # Expected if no connection existed or it was already disconnected
            pass
            
        canvas.mask_mode.mask_created.connect(on_mask_created)
    else:
        pass


def connect_to_group_operations(canvas, undo_redo_manager):
    """Connect to group operations to trigger state saves"""
    if not hasattr(canvas, 'group_layer_manager'):
        return
        
    group_manager = canvas.group_layer_manager
    
    # First try to connect to group_operation signal if available
    if hasattr(group_manager, 'group_operation'):
        try:
            # Define a handler for group operations
            def on_group_operation(operation, group_name, layers):
                # For operations that have completion functions, we'll save state at completion
                # For other operations, save state immediately
                if operation not in ["move", "rotate", "edit_angles"]:
                    undo_redo_manager.save_state()
                
            # Connect the signal
            group_manager.group_operation.connect(on_group_operation)
        except Exception as e:
            pass
    
    # Also connect directly to canvas operations if they exist
    if hasattr(canvas, 'finish_group_move'):
        original_canvas_finish_move = canvas.finish_group_move
        def enhanced_canvas_finish_move(*args, **kwargs):
            result = original_canvas_finish_move(*args, **kwargs)
            undo_redo_manager.save_state()
            return result
        canvas.finish_group_move = enhanced_canvas_finish_move
        
    if hasattr(canvas, 'finish_group_rotation'):
        original_canvas_finish_rotation = canvas.finish_group_rotation
        def enhanced_canvas_finish_rotation(*args, **kwargs):
            result = original_canvas_finish_rotation(*args, **kwargs)
            
            # Don't schedule a delayed save for rotation - it should be handled explicitly
                
            return result
        canvas.finish_group_rotation = enhanced_canvas_finish_rotation
    
    # Also connect directly to group_panel if available
    if hasattr(group_manager, 'group_panel') and group_manager.group_panel:
        connect_group_panel_directly(group_manager.group_panel, undo_redo_manager)
        
    # Mark the connection as established
    canvas._group_ops_connected = True
    
    return True

# --- ADD NEW FUNCTION ---
def connect_strand_creation(canvas, undo_redo_manager):
    """
    Connect the canvas's strand_created signal to save the state.
    This function should ONLY save states for regular strands, NOT for AttachedStrands.
    AttachedStrands are handled by the attach mode handler.
    """
    if hasattr(canvas, 'strand_created'):
        def on_strand_really_created(strand):
            # IMPORTANT: Skip saving for AttachedStrands - the attach mode handler will take care of it
            
            # Check if this strand is the current_strand in attach mode (indicates it's an AttachedStrand being created)
            current_strand = getattr(canvas, 'current_strand', None)
            if current_strand == strand:
                return
            
            # Check by isinstance first (most reliable)
            is_attached_strand_instance = isinstance(strand, AttachedStrand)
            if is_attached_strand_instance:
                return
            
            # Additional check for AttachedStrands by class name (fallback)
            is_attached_strand_class = strand.__class__.__name__ == 'AttachedStrand'
            if is_attached_strand_class:
                return
            
            # Additional check for AttachedStrands by parent attribute (fallback)
            has_parent = hasattr(strand, 'parent') and strand.parent
            if has_parent:
                return
            
            # Skip saving for MaskedStrands - they have their own state management
            is_masked_strand = isinstance(strand, MaskedStrand)
            if is_masked_strand:
                return
                
            # Save state for regular main strands only
            # Use a small delay to ensure all strand properties and connections are established
            QTimer.singleShot(50, lambda: undo_redo_manager.save_state())

        try:
            canvas.strand_created.disconnect() # Clear previous connections if any
        except TypeError:
            pass # Ignore if no connection exists
        canvas.strand_created.connect(on_strand_really_created)
    else:
        pass
# --- END ADD NEW FUNCTION ---


def setup_undo_redo(canvas, layer_panel, base_path):
    """
    Set up undo/redo functionality for the application.

    Args:
        canvas: The canvas object
        layer_panel: The layer panel to add buttons to
        base_path: The base directory path for storing temp states

    Returns:
        UndoRedoManager: The created manager instance
    """
    # Create the manager, passing the base_path
    manager = UndoRedoManager(canvas, layer_panel, base_path)

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
        else:
            pass
    else:
        pass

    # Connect to move mode mouse release for saving moves
    connect_to_move_mode(canvas, manager)

    # Connect to attach mode for *suppression* during strand creation
    connect_to_attach_mode(canvas, manager)

    # Connect directly to strand_created for saving *after* creation
    connect_strand_creation(canvas, manager) # <-- ADD THIS CALL

    # Connect to mask mode creation
    connect_to_mask_mode(canvas, manager)

    # Connect to group operations if group_layer_manager exists
    if hasattr(canvas, 'group_layer_manager') and canvas.group_layer_manager:
        connect_to_group_operations(canvas, manager)
    else:
        # Setup a function to connect when group_layer_manager becomes available
        def check_and_connect_group_operations():
            if hasattr(canvas, 'group_layer_manager') and canvas.group_layer_manager:
                if not getattr(canvas, '_group_ops_connected', False): # Check if already connected
                    connect_to_group_operations(canvas, manager)
                    return True
            return False

        # Try connecting after 500ms
        QTimer.singleShot(500, check_and_connect_group_operations)

        # Schedule multiple retries
        for delay in [1000, 2000, 5000]:
             # Use a lambda that captures the current canvas and manager
             def create_retry_lambda(c=canvas, m=manager):
                 return lambda: check_and_connect_group_operations() if not getattr(c, '_group_ops_connected', False) else None
             QTimer.singleShot(delay, create_retry_lambda())


    return manager

# Add a new method to directly connect a group_panel to save state on group operations
def connect_group_panel_directly(group_panel, undo_redo_manager):
    """Connect a specific group panel's signals to save state."""
    if not group_panel:
        return False
        
    
    # Connect to group creation more directly
    original_create_group = group_panel.create_group
    def enhanced_create_group(*args, **kwargs):
        result = original_create_group(*args, **kwargs)
        
        # Record the timestamp before saving state
        current_time = time.time()
        last_save_time = getattr(undo_redo_manager, '_last_save_time', 0)
        
        # Check if a state was saved very recently (within 1 second)
        if current_time - last_save_time < 1.0:
            # Set flag to allow the next save (typically from attach mode) by resetting the prevention flag
            undo_redo_manager._saving_state_now = False
            
            # Force a save anyway to ensure group creation is recorded as a separate step
            # This ensures that strand creation and group creation are treated as separate operations
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
        undo_redo_manager.save_state()
        return result
    group_panel.delete_group = enhanced_delete_group
    
    # Connect to move operation completion
    original_finish_group_move = group_panel.finish_group_move
    def enhanced_finish_group_move(*args, **kwargs):
        result = original_finish_group_move(*args, **kwargs)
        undo_redo_manager.save_state()
        return result
    group_panel.finish_group_move = enhanced_finish_group_move
    
    # Connect to rotation operation completion - DISABLED to prevent duplicate saves
    # The original finish_group_rotation already handles state saving with proper duplicate prevention
    # original_finish_group_rotation = group_panel.finish_group_rotation
    # def enhanced_finish_group_rotation(*args, **kwargs):
    #     result = original_finish_group_rotation(*args, **kwargs)
    #     return result
    # group_panel.finish_group_rotation = enhanced_finish_group_rotation
    
    # Connect to angle edit completion - DISABLED to prevent duplicate saves
    # The StrandAngleEditDialog already handles state saving directly
    # original_update_group_after_angle_edit = getattr(group_panel, 'update_group_after_angle_edit', None)
    # if original_update_group_after_angle_edit:
    #     def enhanced_update_group_after_angle_edit(*args, **kwargs):
    #         result = original_update_group_after_angle_edit(*args, **kwargs)
    #         logging.info("Group angle edit finished, saving state")
    #         undo_redo_manager.save_state()
    #         return result
    #     group_panel.update_group_after_angle_edit = enhanced_update_group_after_angle_edit
    
    # Connect to group operation signal
    def on_group_operation(operation, group_name, layers):
        # For operations that have completion functions, we'll save state at completion
        # For other operations, save state immediately
        if operation not in ["move", "rotate", "edit_angles"]:
            undo_redo_manager.save_state()
    
    group_panel.group_operation.connect(on_group_operation)
    
    return True 