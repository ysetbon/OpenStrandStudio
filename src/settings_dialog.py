from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QWidget, QLabel, QStackedWidget, QComboBox, QPushButton,
    QSpacerItem, QSizePolicy, QMessageBox, QTextBrowser, QSlider,
    QColorDialog, QCheckBox, QBoxLayout, QDialogButtonBox,
    QSpinBox, QDoubleSpinBox, QStyleOptionButton # Add these
)
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QRectF, QRect, QTimer
from PyQt5.QtGui import QIcon, QFont, QPainter, QPen, QColor, QPixmap, QPainterPath, QBrush, QFontMetrics
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from translations import translations
from save_load_manager import load_strands, apply_loaded_strands
import os
import sys
import subprocess
from PyQt5.QtCore import QStandardPaths, QDateTime
# Import StrokeTextButton for displaying icons
try:
    from undo_redo_manager import StrokeTextButton
except ImportError:
    # Fallback if StrokeTextButton cannot be imported (e.g., during development)
    StrokeTextButton = QPushButton

# Assuming UndoRedoManager might be needed for history actions
# Import it - adjust path if necessary
try:
    from undo_redo_manager import UndoRedoManager
except ImportError:
    UndoRedoManager = None # Handle cases where it might not be available

class SettingsDialog(QDialog):
    theme_changed = pyqtSignal(str)

    def __init__(self, parent=None, canvas=None, undo_redo_manager=None, layer_panel=None):
        super(SettingsDialog, self).__init__(parent)
        
        # Set window flags directly in the constructor - explicitly remove help button
        flags = self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        self.setWindowFlags(flags)
        
        self.canvas = canvas
        self.layer_panel = layer_panel
        self.parent_window = parent
        
        # Initialize with default values
        self.current_theme = getattr(parent, 'current_theme', 'default')
        # Ensure we always have a language code before any look-ups/translation calls
        # Default to the parent window's language if available, otherwise fall back to English
        self.current_language = getattr(parent, 'language_code', 'en')
        self.shadow_color = QColor(0, 0, 0, 150)  # Default shadow color
        self.draw_only_affected_strand = False  # Default to drawing all strands
        self.enable_third_control_point = False  # Default to two control points
        self.enable_curvature_bias_control = False  # Default to no curvature bias controls
        self.snap_to_grid_enabled = True  # Default to snap to grid enabled
        self.show_move_highlights = True  # Default to showing highlights in move modes
        # NEW: Use extended mask option (controls extra expansion of masked areas)
        # self.use_extended_mask = False  # Default to using exact mask (small +3 offset)
        # Extension line parameters
        self.extension_length = getattr(canvas, 'extension_length', 100)
        self.extension_dash_count = getattr(canvas, 'extension_dash_count', 10)
        self.extension_dash_width = getattr(canvas, 'extension_dash_width', getattr(canvas, 'extension_line_width', 2))  # Default dash width
        self.extension_dash_gap_length = getattr(canvas, 'extension_dash_gap_length', 5.0)  # Default gap length for extension dashes
        self.num_steps = 3  # Default shadow blur steps
        self.max_blur_radius = 29.99  # Default shadow blur radius
        # Arrow head parameters
        self.arrow_head_length = getattr(canvas, 'arrow_head_length', 20.0)
        self.arrow_head_width = getattr(canvas, 'arrow_head_width', 10.0)
        # Add arrow head stroke width parameter
        self.arrow_head_stroke_width = getattr(canvas, 'arrow_head_stroke_width', 4)
        # Add arrow shaft parameters
        self.arrow_gap_length = getattr(canvas, 'arrow_gap_length', 10)
        self.arrow_line_length = getattr(canvas, 'arrow_line_length', 20)
        self.arrow_line_width = getattr(canvas, 'arrow_line_width', 10)
        # Default arrow color parameters
        self.use_default_arrow_color = getattr(canvas, 'use_default_arrow_color', False)
        self.default_arrow_fill_color = getattr(canvas, 'default_arrow_fill_color', QColor(0, 0, 0, 255))
        
        # Add default strand and stroke color properties after line 70
        # Default strand and stroke color parameters
        self.default_strand_color = getattr(canvas, 'default_strand_color', QColor(200, 170, 230, 255))
        self.default_stroke_color = getattr(canvas, 'default_stroke_color', QColor(0, 0, 0, 255))
        # Default strand width parameters
        self.default_strand_width = getattr(canvas, 'strand_width', 46)
        self.default_stroke_width = getattr(canvas, 'stroke_width', 4)
        self.default_width_grid_units = 2  # Default 2 grid squares
        
        # Store the undo/redo manager
        self.undo_redo_manager = undo_redo_manager
        
        # Try to load settings from file first
        self.load_settings_from_file()
        
        # Apply loaded arrow settings to canvas
        if self.canvas:
            self.canvas.arrow_head_length = self.arrow_head_length
            self.canvas.arrow_head_width = self.arrow_head_width
            self.canvas.arrow_head_stroke_width = self.arrow_head_stroke_width
            self.canvas.arrow_gap_length = self.arrow_gap_length
            self.canvas.arrow_line_length = self.arrow_line_length
            self.canvas.arrow_line_width = self.arrow_line_width
            # Apply default arrow color settings
            self.canvas.use_default_arrow_color = self.use_default_arrow_color
            self.canvas.default_arrow_fill_color = self.default_arrow_fill_color
            # Apply default strand and stroke color settings
            self.canvas.default_strand_color = self.default_strand_color
            self.canvas.default_stroke_color = self.default_stroke_color
            # Apply default strand width settings
            self.canvas.strand_width = self.default_strand_width
            self.canvas.stroke_width = self.default_stroke_width
        
        # Apply loaded extension line settings to canvas
        if self.canvas:
            self.canvas.extension_length = self.extension_length
            self.canvas.extension_dash_count = self.extension_dash_count
            self.canvas.extension_dash_width = self.extension_dash_width
            self.canvas.extension_dash_gap_length = self.extension_dash_gap_length
        
        self.setWindowTitle(translations[self.current_language]['settings'])
        
        # Set fixed size for the dialog
        self.setFixedSize(800, 600)
        
        # If no settings were loaded, initialize shadow color from canvas if available
        if self.shadow_color == QColor(0, 0, 0, 150) and canvas:
            if hasattr(canvas, 'shadow_color'):
                # Get shadow color directly from canvas if available
                self.shadow_color = canvas.shadow_color
            elif hasattr(canvas, 'strands') and canvas.strands:
                # Fall back to the first strand's shadow color if canvas shadow color is not available
                self.shadow_color = canvas.strands[0].shadow_color
        
        self.video_paths = []  # Initialize the list to store video paths
        self.setup_ui()
        self.load_video_paths()
        
        # Connect to parent window's language_changed signal to update translations
        # if hasattr(self.parent_window, 'language_changed'):
        #     self.parent_window.language_changed.connect(self.update_translations)
        
        # Apply initial theme
        self.apply_dialog_theme(self.current_theme)
        
        # Set layout direction based on language
        self.update_layout_direction()

    # New helper method to check if a language is RTL
    def is_rtl_language(self, language_code):
        # Currently only Hebrew is RTL in our supported languages
        return language_code == 'he'
        
    # New method to get dropdown arrow CSS based on theme and direction
    def get_dropdown_arrow_css(self, is_rtl=False):
        """Get CSS for dropdown arrow positioning based on direction and theme."""
        arrow_color = "#666666"
        if self.current_theme == "dark":
            arrow_color = "#cccccc"
        elif self.current_theme == "light":
            arrow_color = "#333333"
        
        # Define hover colors for dropdown area only
        dropdown_hover_color = "#e0e0e0"
        if self.current_theme == "dark":
            dropdown_hover_color = "#4d4d4d"
        elif self.current_theme == "light":
            dropdown_hover_color = "#f0f0f0"
        
        if is_rtl:
            # For RTL: dropdown arrow on the left side
            return f"""
                QComboBox::drop-down {{
                    subcontrol-origin: padding;
                    subcontrol-position: left center;
                    width: 80px;
                    border: none;
                }}
                QComboBox::drop-down:hover {{
                    background-color: {dropdown_hover_color};
                    border-radius: 4px;
                }}
                QComboBox::down-arrow {{
                    width: 0;
                    height: 0;
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-top: 6px solid {arrow_color};
                    margin-left: 6px;
                }}
            """
        else:
            # For LTR: dropdown arrow on the left side
            return f"""
                QComboBox::drop-down {{
                    subcontrol-origin: padding;
                    subcontrol-position: left center;
                    width: 50px;
                    border: none;
                }}
                QComboBox::drop-down:hover {{
                    background-color: {dropdown_hover_color};
                    border-radius: 4px;
                }}
                QComboBox::down-arrow {{
                    width: 0;
                    height: 0;
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-top: 6px solid {arrow_color};
                    margin-left: 6px;
                }}
            """
    
    # New method to update layout direction based on language
    def update_layout_direction(self):
        is_rtl = self.is_rtl_language(self.current_language)
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight

        # Keep the main dialog layout as LTR to maintain categories on left, content on right
        self.setLayoutDirection(Qt.LeftToRight)
        
        # Apply layout direction to content widgets only, not the main structure
        if hasattr(self, 'general_settings_widget'):
            # Set the content area to RTL for Hebrew
            self.general_settings_widget.setLayoutDirection(direction)
            
            # Set proper text alignment for general settings labels
            if is_rtl:
                # For Hebrew, align labels to the right
                if hasattr(self, 'theme_label'):
                    self.theme_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if hasattr(self, 'shadow_color_label'):
                    self.shadow_color_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if hasattr(self, 'button_color_label'):
                    self.button_color_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.button_color_label.setLayoutDirection(Qt.RightToLeft)
                    self.button_color_label.setTextFormat(Qt.PlainText)
                    self.button_color_label.setWordWrap(False)
                    self.button_color_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
                if hasattr(self, 'affected_strand_label'):
                    self.affected_strand_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if hasattr(self, 'third_control_label'):
                    self.third_control_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if hasattr(self, 'snap_to_grid_label'):
                    self.snap_to_grid_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if hasattr(self, 'default_arrow_color_label'):
                    self.default_arrow_color_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if hasattr(self, 'extended_mask_label'):
                    self.extended_mask_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if hasattr(self, 'num_steps_label'):
                    self.num_steps_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if hasattr(self, 'blur_radius_label'):
                    self.blur_radius_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if hasattr(self, 'curvature_bias_label'):
                    self.curvature_bias_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if hasattr(self, 'base_fraction_label'):
                    self.base_fraction_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if hasattr(self, 'distance_mult_label'):
                    self.distance_mult_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if hasattr(self, 'curve_response_label'):
                    self.curve_response_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if hasattr(self, 'reset_curvature_label'):
                    self.reset_curvature_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            else:
                # For LTR languages, align labels to the left
                if hasattr(self, 'theme_label'):
                    self.theme_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if hasattr(self, 'shadow_color_label'):
                    self.shadow_color_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if hasattr(self, 'button_color_label'):
                    self.button_color_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if hasattr(self, 'affected_strand_label'):
                    self.affected_strand_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if hasattr(self, 'third_control_label'):
                    self.third_control_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if hasattr(self, 'snap_to_grid_label'):
                    self.snap_to_grid_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if hasattr(self, 'default_arrow_color_label'):
                    self.default_arrow_color_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if hasattr(self, 'extended_mask_label'):
                    self.extended_mask_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if hasattr(self, 'num_steps_label'):
                    self.num_steps_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if hasattr(self, 'blur_radius_label'):
                    self.blur_radius_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if hasattr(self, 'curvature_bias_label'):
                    self.curvature_bias_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if hasattr(self, 'base_fraction_label'):
                    self.base_fraction_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if hasattr(self, 'distance_mult_label'):
                    self.distance_mult_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if hasattr(self, 'curve_response_label'):
                    self.curve_response_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if hasattr(self, 'reset_curvature_label'):
                    self.reset_curvature_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            # Also update direction for QHBoxLayouts within General Settings
            general_setting_layouts = [
                'theme_layout', 'shadow_layout', 'performance_layout', 
                'third_control_layout', 'snap_to_grid_layout', 'show_highlights_layout', # 'extended_mask_layout', 
                'num_steps_layout', 'blur_radius_layout',
                'curvature_bias_layout', 'base_fraction_layout',
                'distance_mult_layout', 'curve_response_layout',
                'reset_curvature_layout'
            ]
            for layout_name in general_setting_layouts:
                if hasattr(self, layout_name):
                    layout = getattr(self, layout_name)
                    if isinstance(layout, QHBoxLayout):
                        layout.setDirection(QBoxLayout.RightToLeft if is_rtl else QBoxLayout.LeftToRight)

        # Apply content direction to other content widgets while keeping main structure
        if hasattr(self, 'change_language_widget'):
            self.change_language_widget.setLayoutDirection(direction)
            # Set proper text alignment for language page labels
            if is_rtl:
                if hasattr(self, 'language_label'):
                    self.language_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if hasattr(self, 'language_info_label'):
                    self.language_info_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            else:
                if hasattr(self, 'language_label'):
                    self.language_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if hasattr(self, 'language_info_label'):
                    self.language_info_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    
        # Update shadow layout spacing for RTL
        if hasattr(self, 'shadow_layout'):
            if is_rtl:
                self.shadow_layout.setSpacing(2)  # Very tight spacing for RTL
                self.shadow_layout.setContentsMargins(-300, 0, 0, 0)  # Push button to far left
            else:
                self.shadow_layout.setSpacing(15)  # Normal spacing for LTR
                self.shadow_layout.setContentsMargins(0, 0, 0, 0)  # Normal margins for LTR

        if hasattr(self, 'tutorial_widget'):
            self.tutorial_widget.setLayoutDirection(direction)
            # Ensure tutorial_label remains center-aligned and handles RTL properly
            if hasattr(self, 'tutorial_label'):
                self.tutorial_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.tutorial_label.setTextFormat(Qt.PlainText)
        if hasattr(self, 'button_explanations_widget'):
            self.button_explanations_widget.setLayoutDirection(direction)
            # Ensure button_guide_label remains center-aligned and handles RTL properly
            if hasattr(self, 'button_guide_label'):
                self.button_guide_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.button_guide_label.setTextFormat(Qt.PlainText)
        if hasattr(self, 'about_widget'):
            self.about_widget.setLayoutDirection(direction)
        if hasattr(self, 'whats_new_widget'):
            self.whats_new_widget.setLayoutDirection(direction)
            
        # Also set direction for specific sub-layouts
        if hasattr(self, 'performance_layout'):
             self.performance_layout.setDirection(QBoxLayout.RightToLeft if is_rtl else QBoxLayout.LeftToRight)
        if hasattr(self, 'third_control_layout'):
             self.third_control_layout.setDirection(QBoxLayout.RightToLeft if is_rtl else QBoxLayout.LeftToRight)
        if hasattr(self, 'snap_to_grid_layout'):
             self.snap_to_grid_layout.setDirection(QBoxLayout.RightToLeft if is_rtl else QBoxLayout.LeftToRight)
        if hasattr(self, 'icon_layout'):
             self.icon_layout.setDirection(QBoxLayout.RightToLeft if is_rtl else QBoxLayout.LeftToRight)
        if hasattr(self, 'third_cp_icon_layout'):
             self.third_cp_icon_layout.setDirection(QBoxLayout.RightToLeft if is_rtl else QBoxLayout.LeftToRight)
             
        # Define specific style adjustments for comboboxes based on direction
        combo_style_adjustments = ""  # Initialize empty by default
        
        if is_rtl:
            # Remove CSS styling that might interfere - rely on layout reorganization
            pass
        else: # LTR
            combo_style_adjustments = """
                QComboBox {
                    padding-left: 8px;
                    padding-right: 24px;
                    text-align: left;
                }
                QComboBox::drop-down {
                    border: none;
                    padding-right: 8px;
                }
            """
            
        # Apply checkbox style to all checkboxes with theme support
        self.apply_checkbox_style()

        if hasattr(self, 'theme_combobox'):
            self.theme_combobox.setLayoutDirection(direction)
            self.theme_combobox.view().setLayoutDirection(direction)
            
            # Update dropdown arrow positioning based on direction
            dropdown_arrow_css = self.get_dropdown_arrow_css(is_rtl)
            theme_hover_color = "#222222" if self.current_theme == 'dark' else "#666666"
            selection_color = "#222222" if self.current_theme == 'dark' else "#666666"
            
            updated_theme_style = f"""
                QComboBox {{
                    padding: 8px;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    min-width: 100px;
                    font-size: 14px;
                    {"padding-left: 24px; padding-right: 8px;" if is_rtl else "padding-left: 8px; padding-right: 24px;"}
                }}
                {dropdown_arrow_css}
                QComboBox QAbstractItemView {{
                    padding: 4px;
                    selection-background-color: {selection_color};
                }}
                QComboBox QAbstractItemView::item {{
                    padding: 4px 8px;
                    min-height: 48px;
                    border: none;
                    text-align: left;
                }}
                QComboBox::item {{
                    padding: 4px 8px;
                    min-height: 48px;
                    text-align: left;
                }}
            """
            self.theme_combobox.setStyleSheet(updated_theme_style)
            
            if is_rtl:
                # Use Qt.TextAlignmentRole to properly position text next to the icon
                self.set_combobox_text_alignment(self.theme_combobox, Qt.AlignRight | Qt.AlignVCenter)
            else:
                # For LTR, use default left alignment and standard padding
                self.set_combobox_text_alignment(self.theme_combobox, Qt.AlignLeft | Qt.AlignVCenter)

        if hasattr(self, 'language_combobox'):
            self.language_combobox.setLayoutDirection(direction)
            self.language_combobox.view().setLayoutDirection(direction)
            
            # Update dropdown arrow positioning based on direction
            lang_hover_color = "#222222" if self.current_theme == 'dark' else "#666666"
            
            updated_lang_style = f"""
                QComboBox {{
                    padding: 8px;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    min-width: 150px;
                    font-size: 14px;
                    padding-left: 8px; padding-right: 24px;
                }}
                {dropdown_arrow_css}
                QComboBox QAbstractItemView {{
                    padding: 4px;
                    min-width: 150px;
                    selection-background-color: {selection_color};
                }}
                QComboBox QAbstractItemView::item {{
                    padding: 4px 8px;
                    min-height: 48px;
                    border: none;
                    text-align: left;
                }}
                QComboBox::item {{
                    padding: 4px 8px;
                    min-height: 48px;
                    text-align: left;
                }}
            """
            self.language_combobox.setStyleSheet(updated_lang_style)
            
            if is_rtl:
                # Use Qt.TextAlignmentRole to properly position text next to the flag icon
                self.set_combobox_text_alignment(self.language_combobox, Qt.AlignRight | Qt.AlignVCenter)
            else:
                # For LTR, use default left alignment and standard padding
                self.set_combobox_text_alignment(self.language_combobox, Qt.AlignLeft | Qt.AlignVCenter)

        # Remove the duplicate language_combobox section below this

        # Apply RTL adjustments to layer panel rows
        if hasattr(self, 'layer_panel_rows'):
            # Keep the layer panel settings widget with content direction
            self.layer_panel_settings_widget.setLayoutDirection(direction)

            for row in self.layer_panel_rows:
                # The stored object can be either a layout or a container QWidget
                if isinstance(row, QBoxLayout):
                    # Directly adjust the box layout direction - FIX: use RightToLeft for RTL
                    row.setDirection(QBoxLayout.RightToLeft if is_rtl else QBoxLayout.LeftToRight)

                    # Additionally, for RTL make sure QLabel children are right-aligned
                    if is_rtl:
                        for idx in range(row.count()):
                            widget = row.itemAt(idx).widget()
                            if isinstance(widget, QLabel):
                                # Special handling for button_color_label to ensure it aligns correctly with its button
                                if widget == getattr(self, 'button_color_label', None):
                                    widget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                                elif widget.parentWidget() and widget.parentWidget().layout() == row:
                                    widget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

                elif isinstance(row, QWidget):
                    # Apply direction to the container widget and its internal layout
                    row.setLayoutDirection(direction)
                    # Update internal layout direction if present
                    inner_layout = row.layout()
                    if isinstance(inner_layout, QBoxLayout):
                        # FIX: use RightToLeft for RTL
                        inner_layout.setDirection(QBoxLayout.RightToLeft if is_rtl else QBoxLayout.LeftToRight)
                        
                        # Special handling for button_color_container
                        if row == getattr(self, 'button_color_container', None):
                            if is_rtl:
                                inner_layout.setContentsMargins(0, 0, 0, 0)  # Use spacers instead of margins
                                inner_layout.setSpacing(10)
                            else:
                                inner_layout.setContentsMargins(0, 0, 0, 0)  # Normal margins
                                inner_layout.setSpacing(10)
                        
                        # Special handling for checkbox_container to maintain consistent 10px spacing
                        elif row == getattr(self, 'checkbox_container', None):
                            inner_layout.setContentsMargins(0, 0, 0, 0)  # No margins
                            inner_layout.setSpacing(4)  # Consistent 10px spacing for both RTL and LTR

                    # Ensure any labels inside are aligned properly in RTL
                    if is_rtl:
                        for child in row.findChildren(QLabel):
                            child.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                            
        # Special handling for default arrow color checkbox
        if is_rtl:
            if hasattr(self, 'default_arrow_color_checkbox'):
                # For checkboxes in RTL, we want the box on the left of the text
                # So we use LeftToRight for the checkbox itself
                self.default_arrow_color_checkbox.setLayoutDirection(Qt.LeftToRight)
            
            # But the container should still be RTL
            for checkbox_container in self.findChildren(QWidget):
                if checkbox_container.layout() and hasattr(self, 'default_arrow_color_checkbox') and self.default_arrow_color_checkbox in checkbox_container.findChildren(QCheckBox):
                    checkbox_container.setLayoutDirection(Qt.RightToLeft)
                    break
        else:  # LTR
            # In LTR mode, show the text first then checkbox indicator by using RTL direction on the checkbox widget
            if hasattr(self, 'default_arrow_color_checkbox'):
                # Setting RightToLeft for the checkbox widget itself places the text on the left, indicator on the right
                self.default_arrow_color_checkbox.setLayoutDirection(Qt.RightToLeft)
                
                # Reset container to LTR as well
                for checkbox_container in self.findChildren(QWidget):
                    if checkbox_container.layout() and self.default_arrow_color_checkbox in checkbox_container.findChildren(QCheckBox):
                        checkbox_container.setLayoutDirection(Qt.LeftToRight)
                        break
                        
        # Reorganize widget order for language change
        self.reorganize_layouts_for_language(is_rtl)

    def reorganize_layouts_for_language(self, is_rtl):
        """Reorganize widget order in layouts based on language direction."""
        
        # Theme layout reorganization
        if hasattr(self, 'theme_layout') and hasattr(self, 'theme_label') and hasattr(self, 'theme_combobox'):
            # Clear and re-add widgets in correct order
            self.clear_layout(self.theme_layout)
            if is_rtl:
                self.theme_layout.addStretch()
                self.theme_layout.addWidget(self.theme_combobox)
                self.theme_layout.addWidget(self.theme_label)
            else:
                self.theme_layout.addWidget(self.theme_label)
                self.theme_layout.addWidget(self.theme_combobox)
                self.theme_layout.addStretch()
            # Force immediate update
            self.theme_layout.invalidate()
            self.theme_layout.activate()
                
        # Shadow layout reorganization  
        if hasattr(self, 'shadow_layout') and hasattr(self, 'shadow_color_label') and hasattr(self, 'shadow_color_button'):
            self.clear_layout(self.shadow_layout)
            if is_rtl:
                # For RTL: Button at far left, stretch in middle, label at far right
                self.shadow_layout.addWidget(self.shadow_color_button)
                self.shadow_layout.addStretch()
                self.shadow_layout.addWidget(self.shadow_color_label)
            else:
                self.shadow_layout.addWidget(self.shadow_color_label)
                self.shadow_layout.addWidget(self.shadow_color_button)
                self.shadow_layout.addStretch()
            # Force immediate update
            self.shadow_layout.invalidate()
            self.shadow_layout.activate()
                
        # Performance layout reorganization
        if hasattr(self, 'performance_layout') and hasattr(self, 'affected_strand_label') and hasattr(self, 'affected_strand_checkbox'):
            self.clear_layout(self.performance_layout)
            if is_rtl:
                self.performance_layout.addStretch()
                self.performance_layout.addWidget(self.affected_strand_checkbox)
                self.performance_layout.addWidget(self.affected_strand_label)
            else:
                self.performance_layout.addWidget(self.affected_strand_label)
                self.performance_layout.addWidget(self.affected_strand_checkbox)
                self.performance_layout.addStretch()
            # Force immediate update
            self.performance_layout.invalidate()
            self.performance_layout.activate()
                
        # Third control layout reorganization
        if hasattr(self, 'third_control_layout') and hasattr(self, 'third_control_label') and hasattr(self, 'third_control_checkbox'):
            self.clear_layout(self.third_control_layout)
            if is_rtl:
                self.third_control_layout.addStretch()
                self.third_control_layout.addWidget(self.third_control_checkbox)
                self.third_control_layout.addWidget(self.third_control_label)
            else:
                self.third_control_layout.addWidget(self.third_control_label)
                self.third_control_layout.addWidget(self.third_control_checkbox)
                self.third_control_layout.addStretch()
            # Force immediate update
            self.third_control_layout.invalidate()
            self.third_control_layout.activate()
                
        # Snap to grid layout reorganization
        if hasattr(self, 'snap_to_grid_layout') and hasattr(self, 'snap_to_grid_label') and hasattr(self, 'snap_to_grid_checkbox'):
            self.clear_layout(self.snap_to_grid_layout)
            if is_rtl:
                self.snap_to_grid_layout.addStretch()
                self.snap_to_grid_layout.addWidget(self.snap_to_grid_checkbox)
                self.snap_to_grid_layout.addWidget(self.snap_to_grid_label)
            else:
                self.snap_to_grid_layout.addWidget(self.snap_to_grid_label)
                self.snap_to_grid_layout.addWidget(self.snap_to_grid_checkbox)
                self.snap_to_grid_layout.addStretch()
            # Force immediate update
            self.snap_to_grid_layout.invalidate()
            self.snap_to_grid_layout.activate()
                
        # Default arrow color checkbox layout reorganization
        if hasattr(self, 'checkbox_layout') and hasattr(self, 'default_arrow_color_label') and hasattr(self, 'default_arrow_color_checkbox'):
            self.clear_layout(self.checkbox_layout)
            if is_rtl:
                self.checkbox_layout.addStretch()
                self.checkbox_layout.addWidget(self.default_arrow_color_checkbox)
                self.checkbox_layout.addWidget(self.default_arrow_color_label)
            else:
                self.checkbox_layout.addWidget(self.default_arrow_color_label)
                self.checkbox_layout.addWidget(self.default_arrow_color_checkbox)
                self.checkbox_layout.addStretch()
            # Force immediate update
            self.checkbox_layout.invalidate()
            self.checkbox_layout.activate()
                
        # Extended mask layout reorganization
        # if hasattr(self, 'extended_mask_layout') and hasattr(self, 'extended_mask_label') and hasattr(self, 'extended_mask_checkbox'):
        #     self.clear_layout(self.extended_mask_layout)
        #     if is_rtl:
        #         self.extended_mask_layout.addStretch()
        #         self.extended_mask_layout.addWidget(self.extended_mask_checkbox)
        #         self.extended_mask_layout.addWidget(self.extended_mask_label)
        #     else:
        #         self.extended_mask_layout.addWidget(self.extended_mask_label)
        #         self.extended_mask_layout.addWidget(self.extended_mask_checkbox)
        #         self.extended_mask_layout.addStretch()
        #     # Force immediate update
        #     self.extended_mask_layout.invalidate()
        #     self.extended_mask_layout.activate()
                
        # Num steps layout reorganization
        if hasattr(self, 'num_steps_layout') and hasattr(self, 'num_steps_label') and hasattr(self, 'num_steps_spinbox'):
            self.clear_layout(self.num_steps_layout)
            if is_rtl:
                self.num_steps_layout.addStretch()
                self.num_steps_layout.addWidget(self.num_steps_spinbox)
                self.num_steps_layout.addWidget(self.num_steps_label)
            else:
                self.num_steps_layout.addWidget(self.num_steps_label)
                self.num_steps_layout.addWidget(self.num_steps_spinbox)
                self.num_steps_layout.addStretch()
            # Force immediate update
            self.num_steps_layout.invalidate()
            self.num_steps_layout.activate()
                
        # Blur radius layout reorganization
        if hasattr(self, 'blur_radius_layout') and hasattr(self, 'blur_radius_label') and hasattr(self, 'blur_radius_spinbox'):
            self.clear_layout(self.blur_radius_layout)
            if is_rtl:
                self.blur_radius_layout.addStretch()
                self.blur_radius_layout.addWidget(self.blur_radius_spinbox)
                self.blur_radius_layout.addWidget(self.blur_radius_label)
            else:
                self.blur_radius_layout.addWidget(self.blur_radius_label)
                self.blur_radius_layout.addWidget(self.blur_radius_spinbox)
                self.blur_radius_layout.addStretch()
            # Force immediate update
            self.blur_radius_layout.invalidate()
            self.blur_radius_layout.activate()
                
        # Curvature bias control layout reorganization
        if hasattr(self, 'curvature_bias_layout') and hasattr(self, 'curvature_bias_label') and hasattr(self, 'curvature_bias_checkbox'):
            self.clear_layout(self.curvature_bias_layout)
            if is_rtl:
                self.curvature_bias_layout.addStretch()
                self.curvature_bias_layout.addWidget(self.curvature_bias_checkbox)
                self.curvature_bias_layout.addWidget(self.curvature_bias_label)
            else:
                self.curvature_bias_layout.addWidget(self.curvature_bias_label)
                self.curvature_bias_layout.addWidget(self.curvature_bias_checkbox)
                self.curvature_bias_layout.addStretch()
            # Force immediate update
            self.curvature_bias_layout.invalidate()
            self.curvature_bias_layout.activate()
                
        # Base fraction layout reorganization
        if hasattr(self, 'base_fraction_layout') and hasattr(self, 'base_fraction_label') and hasattr(self, 'base_fraction_spinbox'):
            self.clear_layout(self.base_fraction_layout)
            if is_rtl:
                self.base_fraction_layout.addStretch()
                self.base_fraction_layout.addWidget(self.base_fraction_spinbox)
                self.base_fraction_layout.addWidget(self.base_fraction_label)
            else:
                self.base_fraction_layout.addWidget(self.base_fraction_label)
                self.base_fraction_layout.addWidget(self.base_fraction_spinbox)
                self.base_fraction_layout.addStretch()
            # Force immediate update
            self.base_fraction_layout.invalidate()
            self.base_fraction_layout.activate()
                
        # Distance multiplier layout reorganization
        if hasattr(self, 'distance_mult_layout') and hasattr(self, 'distance_mult_label') and hasattr(self, 'distance_mult_spinbox'):
            self.clear_layout(self.distance_mult_layout)
            if is_rtl:
                self.distance_mult_layout.addStretch()
                self.distance_mult_layout.addWidget(self.distance_mult_spinbox)
                self.distance_mult_layout.addWidget(self.distance_mult_label)
            else:
                self.distance_mult_layout.addWidget(self.distance_mult_label)
                self.distance_mult_layout.addWidget(self.distance_mult_spinbox)
                self.distance_mult_layout.addStretch()
            # Force immediate update
            self.distance_mult_layout.invalidate()
            self.distance_mult_layout.activate()
                
        # Curve response layout reorganization
        if hasattr(self, 'curve_response_layout') and hasattr(self, 'curve_response_label') and hasattr(self, 'curve_response_spinbox'):
            self.clear_layout(self.curve_response_layout)
            if is_rtl:
                self.curve_response_layout.addStretch()
                self.curve_response_layout.addWidget(self.curve_response_spinbox)
                self.curve_response_layout.addWidget(self.curve_response_label)
            else:
                self.curve_response_layout.addWidget(self.curve_response_label)
                self.curve_response_layout.addWidget(self.curve_response_spinbox)
                self.curve_response_layout.addStretch()
            # Force immediate update
            self.curve_response_layout.invalidate()
            self.curve_response_layout.activate()
                
        # Reset curvature layout reorganization
        if hasattr(self, 'reset_curvature_layout') and hasattr(self, 'reset_curvature_label') and hasattr(self, 'reset_curvature_button'):
            self.clear_layout(self.reset_curvature_layout)
            if is_rtl:
                self.reset_curvature_layout.addStretch()
                self.reset_curvature_layout.addWidget(self.reset_curvature_button)
                self.reset_curvature_layout.addWidget(self.reset_curvature_label)
            else:
                self.reset_curvature_layout.addWidget(self.reset_curvature_label)
                self.reset_curvature_layout.addWidget(self.reset_curvature_button)
                self.reset_curvature_layout.addStretch()
            # Force immediate update
            self.reset_curvature_layout.invalidate()
            self.reset_curvature_layout.activate()
                
        # Button color layout reorganization (this was missing!)
        if hasattr(self, 'button_color_container') and hasattr(self, 'button_color_label') and hasattr(self, 'default_arrow_color_button'):
            # Clear the layout and set proper spacing
            self.clear_layout(self.button_color_layout)
            self.button_color_container.setContentsMargins(0, 0, 0, 0)
            if is_rtl:
                self.button_color_layout.addStretch()
                self.button_color_container.setLayoutDirection(Qt.LeftToRight)
                self.button_color_layout.setDirection(QBoxLayout.LeftToRight)
                self.button_color_layout.setContentsMargins(105, 0, 0, 0)
                self.button_color_layout.setSpacing(5)  # Add some spacing between widgets
                self.button_color_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.button_color_label.setLayoutDirection(Qt.RightToLeft)
                self.button_color_label.setTextFormat(Qt.PlainText)
                self.button_color_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                 # Add spacer at the beginning to shift everything right
                self.button_color_layout.addWidget(self.default_arrow_color_button)
                self.button_color_layout.addWidget(self.button_color_label)
            else:
                self.button_color_container.setLayoutDirection(Qt.LeftToRight)
                self.button_color_layout.setDirection(QBoxLayout.LeftToRight)
                self.button_color_layout.setContentsMargins(0, 0, 0, 0)
                self.button_color_layout.setSpacing(5)  # Small, constant gap
                self.button_color_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.button_color_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
                self.button_color_label.setStyleSheet("QLabel { margin: 0px; padding: 0px; }")
                self.default_arrow_color_button.setStyleSheet("QPushButton { margin: 0px; padding: 0px; }")
                self.button_color_layout.addWidget(self.button_color_label)
               
                self.button_color_layout.addWidget(self.default_arrow_color_button)
                self.button_color_layout.addStretch()
            # Force immediate update (same as theme layout)
            self.button_color_layout.invalidate()
            self.button_color_layout.activate()
            # Also update the container widget
            if hasattr(self, 'button_color_container'):
                self.button_color_container.updateGeometry()
                self.button_color_container.update()
                
            # Log final reorganized layout state  
            for i in range(self.button_color_layout.count()):
                item = self.button_color_layout.itemAt(i)
                if item.widget():
                    widget = item.widget()
                elif item.spacerItem():
                    spacer = item.spacerItem()
            # Log container and layout geometry
            # Let the layout decide the width – zero works fine
            self.button_color_label.setMinimumWidth(0)
            self.button_color_label.updateGeometry()
            self.button_color_label.repaint()


        # Default Strand Color layout reorganization
        if hasattr(self, 'default_strand_color_container') and hasattr(self, 'default_strand_color_label') and hasattr(self, 'default_strand_color_button'):
            # Clear the layout and set proper spacing
            self.clear_layout(self.default_strand_color_layout)
            self.default_strand_color_container.setContentsMargins(0, 0, 0, 0)
            if is_rtl:
                self.default_strand_color_layout.addStretch()
                self.default_strand_color_container.setLayoutDirection(Qt.LeftToRight)
                self.default_strand_color_layout.setDirection(QBoxLayout.LeftToRight)
                self.default_strand_color_layout.setContentsMargins(258, 0, 0, 0)
                self.default_strand_color_layout.setSpacing(10)  # Add some spacing between widgets
                self.default_strand_color_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.default_strand_color_label.setLayoutDirection(Qt.RightToLeft)
                self.default_strand_color_label.setTextFormat(Qt.PlainText)
                self.default_strand_color_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                 # Add spacer at the beginning to shift everything right
                self.default_strand_color_layout.addWidget(self.default_strand_color_button)
                self.default_strand_color_layout.addWidget(self.default_strand_color_label)
            else:
                self.default_strand_color_container.setLayoutDirection(Qt.LeftToRight)
                self.default_strand_color_layout.setDirection(QBoxLayout.LeftToRight)
                self.default_strand_color_layout.setContentsMargins(0, 0, 0, 0)
                self.default_strand_color_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.default_strand_color_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
                self.default_strand_color_label.setStyleSheet("QLabel { margin: 0px; padding: 0px; }")
                self.default_strand_color_button.setStyleSheet("QPushButton { margin: 0px; padding: 0px; }")
                self.default_strand_color_layout.addWidget(self.default_strand_color_label)
               
                self.default_strand_color_layout.addWidget(self.default_strand_color_button)
                self.default_strand_color_layout.addStretch()
            # Force immediate update (same as theme layout)
            self.default_strand_color_layout.invalidate()
            self.default_strand_color_layout.activate()
            # Also update the container widget
            if hasattr(self, 'default_strand_color_container'):
                self.default_strand_color_container.updateGeometry()
                self.default_strand_color_container.update()
                
            # Let the layout decide the width – zero works fine
            self.default_strand_color_label.setMinimumWidth(0)
            self.default_strand_color_label.updateGeometry()
            self.default_strand_color_label.repaint()

        # Default Stroke Color layout reorganization
        if hasattr(self, 'default_stroke_color_container') and hasattr(self, 'default_stroke_color_label') and hasattr(self, 'default_stroke_color_button'):
            # Clear the layout and set proper spacing
            self.clear_layout(self.default_stroke_color_layout)
            self.default_stroke_color_container.setContentsMargins(0, 0, 0, 0)
            if is_rtl:
                self.default_stroke_color_layout.addStretch()
                self.default_stroke_color_container.setLayoutDirection(Qt.LeftToRight)
                self.default_stroke_color_layout.setDirection(QBoxLayout.LeftToRight)
                self.default_stroke_color_layout.setContentsMargins(308, 0, 0, 0) 
                self.default_stroke_color_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.default_stroke_color_label.setLayoutDirection(Qt.RightToLeft)
                self.default_stroke_color_label.setTextFormat(Qt.PlainText)
                self.default_stroke_color_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                 # Add spacer at the beginning to shift everything right
                self.default_stroke_color_layout.addWidget(self.default_stroke_color_button)
                self.default_stroke_color_layout.addWidget(self.default_stroke_color_label)
            else:
                self.default_stroke_color_container.setLayoutDirection(Qt.LeftToRight)
                self.default_stroke_color_layout.setDirection(QBoxLayout.LeftToRight)
                self.default_stroke_color_layout.setContentsMargins(0, 0, 0, 0)
                self.default_stroke_color_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.default_stroke_color_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
                self.default_stroke_color_label.setStyleSheet("QLabel { margin: 0px; padding: 0px; }")
                self.default_stroke_color_button.setStyleSheet("QPushButton { margin: 0px; padding: 0px; }")
                self.default_stroke_color_layout.addWidget(self.default_stroke_color_label)
               
                self.default_stroke_color_layout.addWidget(self.default_stroke_color_button)
                self.default_stroke_color_layout.addStretch()
            # Force immediate update (same as theme layout)
            self.default_stroke_color_layout.invalidate()
            self.default_stroke_color_layout.activate()
            # Also update the container widget
            if hasattr(self, 'default_stroke_color_container'):
                self.default_stroke_color_container.updateGeometry()
                self.default_stroke_color_container.update()
                
            # Let the layout decide the width – zero works fine
            self.default_stroke_color_label.setMinimumWidth(0)
            self.default_stroke_color_label.updateGeometry()
            self.default_stroke_color_label.repaint()

        # Default Strand Width button layout reorganization
        if hasattr(self, 'default_strand_width_container') and hasattr(self, 'default_strand_width_button'):
            # Clear the layout and set proper spacing
            self.clear_layout(self.default_strand_width_layout)
            self.default_strand_width_container.setContentsMargins(0, 0, 0, 0)
            # Center the button for both LTR and RTL languages
            self.default_strand_width_container.setLayoutDirection(Qt.LeftToRight)
            self.default_strand_width_layout.setDirection(QBoxLayout.LeftToRight)
            self.default_strand_width_layout.setContentsMargins(0, 0, 0, 0)
            self.default_strand_width_layout.addStretch()
            self.default_strand_width_layout.addWidget(self.default_strand_width_button, 0, Qt.AlignCenter)
            self.default_strand_width_layout.addStretch()
            # Force immediate update
            self.default_strand_width_layout.invalidate()
            self.default_strand_width_layout.activate()
            # Also update the container widget
            if hasattr(self, 'default_strand_width_container'):
                self.default_strand_width_container.updateGeometry()
                self.default_strand_width_container.update()

        # Layer Panel layout reorganizations
        if hasattr(self, 'ext_length_layout') and hasattr(self, 'extension_length_label') and hasattr(self, 'extension_length_spinbox'):
            self.clear_layout(self.ext_length_layout)
            if is_rtl:
                self.ext_length_layout.addStretch()
                self.ext_length_layout.addWidget(self.extension_length_spinbox)
                self.ext_length_layout.addWidget(self.extension_length_label)
            else:
                self.ext_length_layout.addWidget(self.extension_length_label)
                self.ext_length_layout.addWidget(self.extension_length_spinbox)
                self.ext_length_layout.addStretch()
            # Force immediate update
            self.ext_length_layout.invalidate()
            self.ext_length_layout.activate()
                
        if hasattr(self, 'dash_count_layout') and hasattr(self, 'extension_dash_count_label') and hasattr(self, 'extension_dash_count_spinbox'):
            self.clear_layout(self.dash_count_layout)
            if is_rtl:
                self.dash_count_layout.addStretch()
                self.dash_count_layout.addWidget(self.extension_dash_count_spinbox)
                self.dash_count_layout.addWidget(self.extension_dash_count_label)
            else:
                self.dash_count_layout.addWidget(self.extension_dash_count_label)
                self.dash_count_layout.addWidget(self.extension_dash_count_spinbox)
                self.dash_count_layout.addStretch()
            # Force immediate update
            self.dash_count_layout.invalidate()
            self.dash_count_layout.activate()
                
        if hasattr(self, 'extension_dash_width_layout') and hasattr(self, 'extension_dash_width_label') and hasattr(self, 'extension_dash_width_spinbox'):
            self.clear_layout(self.extension_dash_width_layout)
            if is_rtl:
                self.extension_dash_width_layout.addStretch()
                self.extension_dash_width_layout.addWidget(self.extension_dash_width_spinbox)
                self.extension_dash_width_layout.addWidget(self.extension_dash_width_label)
            else:
                self.extension_dash_width_layout.addWidget(self.extension_dash_width_label)
                self.extension_dash_width_layout.addWidget(self.extension_dash_width_spinbox)
                self.extension_dash_width_layout.addStretch()
            # Force immediate update
            self.extension_dash_width_layout.invalidate()
            self.extension_dash_width_layout.activate()
                
        if hasattr(self, 'gap_length_layout') and hasattr(self, 'extension_dash_gap_length_label') and hasattr(self, 'extension_dash_gap_length_spinbox'):
            self.clear_layout(self.gap_length_layout)
            if is_rtl:
                self.gap_length_layout.addStretch()
                self.gap_length_layout.addWidget(self.extension_dash_gap_length_spinbox)
                self.gap_length_layout.addWidget(self.extension_dash_gap_length_label)
            else:
                self.gap_length_layout.addWidget(self.extension_dash_gap_length_label)
                self.gap_length_layout.addWidget(self.extension_dash_gap_length_spinbox)
                self.gap_length_layout.addStretch()
            # Force immediate update
            self.gap_length_layout.invalidate()
            self.gap_length_layout.activate()
                
        if hasattr(self, 'arrow_len_layout') and hasattr(self, 'arrow_head_length_label') and hasattr(self, 'arrow_head_length_spinbox'):
            self.clear_layout(self.arrow_len_layout)
            if is_rtl:
                self.arrow_len_layout.addStretch()
                self.arrow_len_layout.addWidget(self.arrow_head_length_spinbox)
                self.arrow_len_layout.addWidget(self.arrow_head_length_label)
            else:
                self.arrow_len_layout.addWidget(self.arrow_head_length_label)
                self.arrow_len_layout.addWidget(self.arrow_head_length_spinbox)
                self.arrow_len_layout.addStretch()
            # Force immediate update
            self.arrow_len_layout.invalidate()
            self.arrow_len_layout.activate()
                
        if hasattr(self, 'arrow_width_layout') and hasattr(self, 'arrow_head_width_label') and hasattr(self, 'arrow_head_width_spinbox'):
            self.clear_layout(self.arrow_width_layout)
            if is_rtl:
                self.arrow_width_layout.addStretch()
                self.arrow_width_layout.addWidget(self.arrow_head_width_spinbox)
                self.arrow_width_layout.addWidget(self.arrow_head_width_label)
            else:
                self.arrow_width_layout.addWidget(self.arrow_head_width_label)
                self.arrow_width_layout.addWidget(self.arrow_head_width_spinbox)
                self.arrow_width_layout.addStretch()
            # Force immediate update
            self.arrow_width_layout.invalidate()
            self.arrow_width_layout.activate()
                
        if hasattr(self, 'arrow_stroke_layout') and hasattr(self, 'arrow_head_stroke_width_label') and hasattr(self, 'arrow_head_stroke_width_spinbox'):
            self.clear_layout(self.arrow_stroke_layout)
            if is_rtl:
                self.arrow_stroke_layout.addStretch()
                self.arrow_stroke_layout.addWidget(self.arrow_head_stroke_width_spinbox)
                self.arrow_stroke_layout.addWidget(self.arrow_head_stroke_width_label)
            else:
                self.arrow_stroke_layout.addWidget(self.arrow_head_stroke_width_label)
                self.arrow_stroke_layout.addWidget(self.arrow_head_stroke_width_spinbox)
                self.arrow_stroke_layout.addStretch()
            # Force immediate update
            self.arrow_stroke_layout.invalidate()
            self.arrow_stroke_layout.activate()
                
        if hasattr(self, 'arrow_gap_layout') and hasattr(self, 'arrow_gap_length_label') and hasattr(self, 'arrow_gap_length_spinbox'):
            self.clear_layout(self.arrow_gap_layout)
            if is_rtl:
                self.arrow_gap_layout.addStretch()
                self.arrow_gap_layout.addWidget(self.arrow_gap_length_spinbox)
                self.arrow_gap_layout.addWidget(self.arrow_gap_length_label)
            else:
                self.arrow_gap_layout.addWidget(self.arrow_gap_length_label)
                self.arrow_gap_layout.addWidget(self.arrow_gap_length_spinbox)
                self.arrow_gap_layout.addStretch()
            # Force immediate update
            self.arrow_gap_layout.invalidate()
            self.arrow_gap_layout.activate()
                
        if hasattr(self, 'arrow_line_length_layout') and hasattr(self, 'arrow_line_length_label') and hasattr(self, 'arrow_line_length_spinbox'):
            self.clear_layout(self.arrow_line_length_layout)
            if is_rtl:
                self.arrow_line_length_layout.addStretch()
                self.arrow_line_length_layout.addWidget(self.arrow_line_length_spinbox)
                self.arrow_line_length_layout.addWidget(self.arrow_line_length_label)
            else:
                self.arrow_line_length_layout.addWidget(self.arrow_line_length_label)
                self.arrow_line_length_layout.addWidget(self.arrow_line_length_spinbox)
                self.arrow_line_length_layout.addStretch()
            # Force immediate update
            self.arrow_line_length_layout.invalidate()
            self.arrow_line_length_layout.activate()
                
        if hasattr(self, 'arrow_line_width_layout') and hasattr(self, 'arrow_line_width_label') and hasattr(self, 'arrow_line_width_spinbox'):
            self.clear_layout(self.arrow_line_width_layout)
            if is_rtl:
                self.arrow_line_width_layout.addStretch()
                self.arrow_line_width_layout.addWidget(self.arrow_line_width_spinbox)
                self.arrow_line_width_layout.addWidget(self.arrow_line_width_label)
            else:
                self.arrow_line_width_layout.addWidget(self.arrow_line_width_label)
                self.arrow_line_width_layout.addWidget(self.arrow_line_width_spinbox)
                self.arrow_line_width_layout.addStretch()
            # Force immediate update
            self.arrow_line_width_layout.invalidate()
            self.arrow_line_width_layout.activate()

        # Force a complete visual update after all reorganizations
        
        # Debug: Check actual widget order in shadow layout
        if hasattr(self, 'shadow_layout'):
            widgets_in_order = []
            for i in range(self.shadow_layout.count()):
                item = self.shadow_layout.itemAt(i)
                if item.widget():
                    widgets_in_order.append(item.widget().__class__.__name__)
                elif item.spacerItem():
                    widgets_in_order.append("Spacer")
        
        # Debug: Check actual widget order in button color layout  
        if hasattr(self, 'button_color_layout'):
            widgets_in_order = []
            for i in range(self.button_color_layout.count()):
                item = self.button_color_layout.itemAt(i)
                if item.widget():
                    widgets_in_order.append(item.widget().__class__.__name__)
                elif item.spacerItem():
                    widgets_in_order.append("Spacer")
        
        # Force update of all relevant containers with aggressive repaints
        if hasattr(self, 'general_settings_widget') and self.general_settings_widget:
            self.general_settings_widget.updateGeometry()
            self.general_settings_widget.update()
            self.general_settings_widget.repaint()
            
        if hasattr(self, 'layer_panel_settings_widget') and self.layer_panel_settings_widget:
            self.layer_panel_settings_widget.updateGeometry()
            self.layer_panel_settings_widget.update()
            self.layer_panel_settings_widget.repaint()
        
        # Force a complete repaint of the entire dialog multiple times to ensure update
        self.updateGeometry()
        self.update()
        self.repaint()
        
        # Additional forced repaint after a short delay using QTimer
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(50, lambda: self.repaint())
        
        

    def clear_layout(self, layout):
        """Helper method to clear all widgets from a layout."""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

    def set_combobox_text_alignment(self, combobox, alignment):
        """Set text alignment for combobox using editable mode with read-only line edit."""
        if not combobox.isEditable():
            # Make the combobox editable to get a QLineEdit we can control
            combobox.setEditable(True)
            # Make the line edit read-only to prevent user typing
            combobox.lineEdit().setReadOnly(True)
            
        # For RTL languages, we want the text to start right next to the flag (like LTR)
        # So we use left alignment but with RTL layout direction
        if alignment & Qt.AlignRight:
            # Use left alignment so text starts right next to the flag
            combobox.lineEdit().setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            # But set RTL layout direction for proper Hebrew text rendering
            combobox.lineEdit().setLayoutDirection(Qt.RightToLeft)
            # Force update the display
            combobox.lineEdit().update()
        else:
            # For LTR languages, use standard left alignment
            combobox.lineEdit().setAlignment(alignment)
            combobox.lineEdit().setLayoutDirection(Qt.LeftToRight)
        
        # Also apply to dropdown items for consistency
        for i in range(combobox.count()):
            # For RTL languages, use left alignment in dropdown items too
            # so text starts next to the flag (not pushed to far right)
            if alignment & Qt.AlignRight:
                combobox.setItemData(i, Qt.AlignLeft | Qt.AlignVCenter, Qt.TextAlignmentRole)
            else:
                combobox.setItemData(i, alignment, Qt.TextAlignmentRole)
    
    def get_settings_directory(self):
        """Get the settings directory path consistently across platforms."""
        app_name = "OpenStrand Studio"
        if sys.platform.startswith('darwin'):  # macOS
            program_data_dir = os.path.expanduser('~/Library/Application Support')
            settings_dir = os.path.join(program_data_dir, app_name)
        else:
            program_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            settings_dir = program_data_dir  # AppDataLocation already includes the app name
        return settings_dir

    def load_settings_from_file(self):
        """Load user settings from file to initialize dialog with saved settings."""
        settings_dir = self.get_settings_directory()
        file_path = os.path.join(settings_dir, 'user_settings.txt')
        
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    
                    
                    for line in file:
                        line = line.strip()
                        
                        if line.startswith('Theme:'):
                            self.current_theme = line.split(':', 1)[1].strip()
                            
                        elif line.startswith('Language:'):
                            self.current_language = line.split(':', 1)[1].strip()
                        elif line.startswith('ShadowColor:'):
                            # Parse the RGBA values
                            rgba_str = line.split(':', 1)[1].strip()
                            try:
                                r, g, b, a = map(int, rgba_str.split(','))
                                # Create a fresh QColor instance
                                self.shadow_color = QColor(r, g, b, a)
                            except Exception as e:
                                pass
                        elif line.startswith('DrawOnlyAffectedStrand:'):
                            value = line.split(':', 1)[1].strip().lower()
                            self.draw_only_affected_strand = (value == 'true')
                            
                        elif line.startswith('EnableThirdControlPoint:'):
                            value = line.split(':', 1)[1].strip().lower()
                            self.enable_third_control_point = (value == 'true')
                            
                        elif line.startswith('EnableCurvatureBiasControl:'):
                            value = line.split(':', 1)[1].strip().lower()
                            self.enable_curvature_bias_control = (value == 'true')
                            
                        elif line.startswith('EnableSnapToGrid:'):
                            value = line.split(':', 1)[1].strip().lower()
                            self.snap_to_grid_enabled = (value == 'true')
                        
                        elif line.startswith('ShowMoveHighlights:'):
                            value = line.split(':', 1)[1].strip().lower()
                            self.show_move_highlights = (value == 'true')
                        # elif line.startswith('UseExtendedMask:'):
                        #     value = line.split(':', 1)[1].strip().lower()
                        #     self.use_extended_mask = (value == 'true')
                        #     logging.info(f"SettingsDialog: Found UseExtendedMask: {self.use_extended_mask}")
                        elif line.startswith('NumSteps:'):
                            try:
                                self.num_steps = int(line.split(':', 1)[1].strip())
                            except ValueError:
                                pass
                        elif line.startswith('MaxBlurRadius:'):
                            try:
                                self.max_blur_radius = float(line.split(':', 1)[1].strip())
                            except ValueError:
                                pass
                        elif line.startswith('ControlPointBaseFraction:'):
                            try:
                                value = float(line.split(':', 1)[1].strip())
                                # Store the value to apply later after UI is created
                                self.loaded_base_fraction = value
                                if self.canvas:
                                    self.canvas.control_point_base_fraction = value
                            except ValueError:
                                pass
                        elif line.startswith('DistanceMultiplier:'):
                            try:
                                value = float(line.split(':', 1)[1].strip())
                                # Store the value to apply later after UI is created
                                self.loaded_distance_multiplier = value
                                if self.canvas:
                                    self.canvas.distance_multiplier = value
                            except ValueError:
                                pass
                        elif line.startswith('CurveResponseExponent:'):
                            try:
                                value = float(line.split(':', 1)[1].strip())
                                # Store the value to apply later after UI is created
                                self.loaded_curve_response = value
                                if self.canvas:
                                    self.canvas.curve_response_exponent = value
                            except ValueError:
                                pass
                        elif line.startswith('ExtensionLength:'):
                            try:
                                self.extension_length = float(line.split(':', 1)[1].strip())
                            except ValueError:
                                pass
                        elif line.startswith('ExtensionDashCount:'):
                            try:
                                self.extension_dash_count = int(line.split(':', 1)[1].strip())
                            except ValueError:
                                pass
                        elif line.startswith('ExtensionDashWidth:'):
                            try:
                                self.extension_dash_width = float(line.split(':', 1)[1].strip())
                            except ValueError:
                                pass
                        elif line.startswith('ExtensionLineWidth:'):  # legacy key
                            try:
                                self.extension_dash_width = float(line.split(':', 1)[1].strip())
                            except ValueError:
                                pass
                        elif line.startswith('ArrowHeadLength:'):
                            try:
                                self.arrow_head_length = float(line.split(':', 1)[1].strip())
                            except ValueError:
                                pass
                        elif line.startswith('ArrowHeadWidth:'):
                            try:
                                self.arrow_head_width = float(line.split(':', 1)[1].strip())
                            except ValueError:
                                pass
                        elif line.startswith('ArrowHeadStrokeWidth:'):
                            try:
                                self.arrow_head_stroke_width = int(line.split(':', 1)[1].strip())
                            except ValueError:
                                pass
                        elif line.startswith('ArrowGapLength:'):
                            try:
                                self.arrow_gap_length = float(line.split(':', 1)[1].strip())
                            except ValueError:
                                pass
                        elif line.startswith('ArrowLineLength:'):
                            try:
                                self.arrow_line_length = float(line.split(':', 1)[1].strip())
                            except ValueError:
                                pass
                        elif line.startswith('ArrowLineWidth:'):
                            try:
                                self.arrow_line_width = float(line.split(':', 1)[1].strip())
                            except ValueError:
                                pass
                        elif line.startswith('UseDefaultArrowColor:'):
                            self.use_default_arrow_color = (line.split(':', 1)[1].strip().lower() == 'true')
                            
                        elif line.startswith('DefaultArrowColor:'):
                            try:
                                r, g, b, a = map(int, line.split(':', 1)[1].strip().split(','))
                                self.default_arrow_fill_color = QColor(r, g, b, a)
                            except Exception as e:
                                pass
                        elif line.startswith('ExtensionDashGapLength:'):
                            try:
                                self.extension_dash_gap_length = float(line.split(':', 1)[1].strip())
                            except ValueError:
                                pass
                        elif line.startswith('DefaultStrandColor:'):
                            try:
                                r, g, b, a = map(int, line.split(':', 1)[1].strip().split(','))
                                self.default_strand_color = QColor(r, g, b, a)
                            except Exception as e:
                                pass
                        elif line.startswith('DefaultStrokeColor:'):
                            try:
                                r, g, b, a = map(int, line.split(':', 1)[1].strip().split(','))
                                self.default_stroke_color = QColor(r, g, b, a)
                            except Exception as e:
                                pass
                        elif line.startswith('DefaultStrandWidth:'):
                            try:
                                self.default_strand_width = int(line.split(':', 1)[1].strip())
                            except ValueError:
                                pass
                        elif line.startswith('DefaultStrokeWidth:'):
                            try:
                                self.default_stroke_width = int(line.split(':', 1)[1].strip())
                            except ValueError:
                                pass
                        elif line.startswith('DefaultWidthGridUnits:'):
                            try:
                                self.default_width_grid_units = int(line.split(':', 1)[1].strip())
                            except ValueError:
                                pass
                
                    # logging.info(f"SettingsDialog: User settings loaded successfully. Theme: {self.current_theme}, Language: {self.current_language}, Shadow Color: {self.shadow_color.red()},{self.shadow_color.green()},{self.shadow_color.blue()},{self.shadow_color.alpha()}, Draw Only Affected Strand: {self.draw_only_affected_strand}, Enable Third Control Point: {self.enable_third_control_point}, Use Extended Mask: {self.use_extended_mask}, Num Steps: {self.num_steps}, Max Blur Radius: {self.max_blur_radius:.1f}")
            except Exception as e:
                pass
        else:
            pass

    def setup_ui(self):
        _ = translations[self.current_language]
        main_layout = QHBoxLayout(self)
        
        # Set layout margins to ensure consistent spacing
        main_layout.setContentsMargins(0, 20, 20, 20)  # Left margin 0 for buttons to reach edge
        main_layout.setSpacing(20)

        # Calculate hover colors based on actual current theme
        theme_hover_color = "#222222" if self.current_theme == 'dark' else "#666666"
        lang_hover_color = "#222222" if self.current_theme == 'dark' else "#666666"
        selection_color = "#222222" if self.current_theme == 'dark' else "#666666"

        # Left side: categories list
        self.categories_list = QListWidget()
        self.categories_list.setFixedWidth(200)  # Increased width for better appearance
        self.categories_list.itemClicked.connect(self.change_category)

        categories = [
            _['general_settings'],
            _['layer_panel_title'],  # Add Layer Panel Settings category
            _['change_language'],
            _['tutorial'],
            _['button_explanations'],  # Add Button Guide category
            _['history'],
            _['whats_new'],  # Add What's New category here
            (_['samples'] if 'samples' in _ else 'Samples'),
            _['about']  # Keep About as the last item
        ]
        for category in categories:
            item = QListWidgetItem(category)
            item.setTextAlignment(Qt.AlignCenter)
            self.categories_list.addItem(item)

        # Right side: stacked widget for different settings pages
        self.stacked_widget = QStackedWidget()

        # General Settings Page (index 0)
        self.general_settings_widget = QWidget()
        general_layout = QVBoxLayout(self.general_settings_widget)

        # Theme Selection
        self.theme_layout = QHBoxLayout() # STORE AS INSTANCE ATTRIBUTE
        self.theme_label = QLabel(_['select_theme'])
        self.theme_combobox = QComboBox()
        
        # Get language direction for initial setup
        is_rtl = self.is_rtl_language(self.current_language)
        dropdown_arrow_css = self.get_dropdown_arrow_css(is_rtl)
        
        # Enhanced theme combobox stylesheet with dropdown arrow
        self.theme_combobox_base_style = f"""
            QComboBox {{
                padding: 8px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                min-width: 100px;
                font-size: 14px;
                {"padding-left: 24px; padding-right: 8px;" if is_rtl else "padding-left: 8px; padding-right: 24px;"}
            }}
            {dropdown_arrow_css}
            QComboBox QAbstractItemView {{
                padding: 4px;
                selection-background-color: {selection_color};
            }}
            QComboBox QAbstractItemView::item {{
                padding: 4px 8px;
                min-height: 48px;
                border: none;
                text-align: left;
            }}
            QComboBox::item {{
                padding: 4px 8px;
                min-height: 48px;
                text-align: left;
            }}
        """
        self.theme_combobox.setStyleSheet(self.theme_combobox_base_style)
        
        # Add theme items with color preview icons
        self.add_theme_item(_['default'], 'default')
        self.add_theme_item(_['light'], 'light')
        self.add_theme_item(_['dark'], 'dark')
        
        # Set the current theme in the combobox
        index = self.theme_combobox.findData(self.current_theme)
        if index >= 0:
            self.theme_combobox.setCurrentIndex(index)
        
        # Add widgets in proper order for current language - match shadow layout pattern exactly
        if self.is_rtl_language(self.current_language):
            self.theme_layout.addStretch()
            self.theme_layout.addWidget(self.theme_combobox)
            self.theme_layout.addWidget(self.theme_label)
        else:
            self.theme_layout.addWidget(self.theme_label)
            self.theme_layout.addWidget(self.theme_combobox)
            self.theme_layout.addStretch()

        # Shadow Color Selection
        self.shadow_layout = QHBoxLayout() # STORE AS INSTANCE ATTRIBUTE
        self.shadow_layout.setContentsMargins(0, 0, 0, 0)  # No margins needed now that main layout is fixed
        # Set spacing based on language direction - reduced for RTL
        if self.is_rtl_language(self.current_language):
            self.shadow_layout.setSpacing(5)  # Much smaller spacing for RTL to push button further left
        else:
            self.shadow_layout.setSpacing(15)  # Keep spacing between widgets for LTR
        self.shadow_color_label = QLabel(_['shadow_color'] if 'shadow_color' in _ else "Shadow Color")

        # self.shadow_color_label.setMinimumWidth(0)  # Increased width for better RTL alignment # REMOVED
        self.shadow_color_button = QPushButton()
        self.shadow_color_button.setFixedSize(30, 30)
        self.update_shadow_color_button()
        self.shadow_color_button.clicked.connect(self.choose_shadow_color)
        
        # Add widgets in proper order for current language
        if self.is_rtl_language(self.current_language):
            self.shadow_layout.addWidget(self.shadow_color_button)
            self.shadow_layout.addStretch()
            self.shadow_layout.addWidget(self.shadow_color_label)
        else:
            self.shadow_layout.addWidget(self.shadow_color_label)
            self.shadow_layout.addWidget(self.shadow_color_button)
            self.shadow_layout.addStretch()

        # Performance Settings - Option to draw only affected strand during dragging
        # performance_layout = QHBoxLayout() # Already handled if it's self.performance_layout
        # self.affected_strand_label = QLabel(_['draw_only_affected_strand'] if 'draw_only_affected_strand' in _ else "Draw only affected strand when dragging")
        # Ensure performance_layout is an instance attribute if not already
        if not hasattr(self, 'performance_layout'):
            self.performance_layout = QHBoxLayout()
        self.affected_strand_label = QLabel(_['draw_only_affected_strand'] if 'draw_only_affected_strand' in _ else "Draw only affected strand when dragging")        
        self.affected_strand_checkbox = QCheckBox()
        self.affected_strand_checkbox.setChecked(self.draw_only_affected_strand)
        
        # Add widgets in proper order for current language
        if self.is_rtl_language(self.current_language):
            self.performance_layout.addStretch()
            self.performance_layout.addWidget(self.affected_strand_checkbox)
            self.performance_layout.addWidget(self.affected_strand_label)
        else:
            self.performance_layout.addWidget(self.affected_strand_label)
            self.performance_layout.addWidget(self.affected_strand_checkbox)
            self.performance_layout.addStretch()

        # Third Control Point Option
        # third_control_layout = QHBoxLayout() # Already handled if it's self.third_control_layout
        # self.third_control_label = QLabel(_['enable_third_control_point'] if 'enable_third_control_point' in _ else "Enable third control point at center")
        # Ensure third_control_layout is an instance attribute
        if not hasattr(self, 'third_control_layout'):
            self.third_control_layout = QHBoxLayout()
        self.third_control_label = QLabel(_['enable_third_control_point'] if 'enable_third_control_point' in _ else "Enable third control point at center")
        self.third_control_checkbox = QCheckBox()
        self.third_control_checkbox.setChecked(self.enable_third_control_point)
        
        # Add widgets in proper order for current language
        if self.is_rtl_language(self.current_language):
            self.third_control_layout.addStretch()
            self.third_control_layout.addWidget(self.third_control_checkbox)
            self.third_control_layout.addWidget(self.third_control_label)
        else:
            self.third_control_layout.addWidget(self.third_control_label)
            self.third_control_layout.addWidget(self.third_control_checkbox)
            self.third_control_layout.addStretch()

        # Curvature Bias Control Option (only show when third control point is enabled)
        if not hasattr(self, 'curvature_bias_layout'):
            self.curvature_bias_layout = QHBoxLayout()
        self.curvature_bias_label = QLabel(_['enable_curvature_bias_control'] if 'enable_curvature_bias_control' in _ else "Enable curvature bias controls")
        self.curvature_bias_checkbox = QCheckBox()
        self.curvature_bias_checkbox.setChecked(self.enable_curvature_bias_control)
        
        # Only enable if third control point is enabled
        self.curvature_bias_checkbox.setEnabled(self.enable_third_control_point)
        
        # Connect third control checkbox to enable/disable curvature bias
        def on_third_control_changed(state):
            is_checked = (state == Qt.Checked)
            self.curvature_bias_checkbox.setEnabled(is_checked)
            # Auto-uncheck curvature bias when third control point is disabled
            if not is_checked:
                self.curvature_bias_checkbox.setChecked(False)
        
        self.third_control_checkbox.stateChanged.connect(on_third_control_changed)
        
        # Add widgets in proper order for current language
        if self.is_rtl_language(self.current_language):
            self.curvature_bias_layout.addStretch()
            self.curvature_bias_layout.addWidget(self.curvature_bias_checkbox)
            self.curvature_bias_layout.addWidget(self.curvature_bias_label)
        else:
            self.curvature_bias_layout.addWidget(self.curvature_bias_label)
            self.curvature_bias_layout.addWidget(self.curvature_bias_checkbox)
            self.curvature_bias_layout.addStretch()

        # Snap to Grid Option
        if not hasattr(self, 'snap_to_grid_layout'):
            self.snap_to_grid_layout = QHBoxLayout()
        self.snap_to_grid_label = QLabel(_['enable_snap_to_grid'] if 'enable_snap_to_grid' in _ else "Enable snap to grid")
        self.snap_to_grid_checkbox = QCheckBox()
        self.snap_to_grid_checkbox.setChecked(self.snap_to_grid_enabled)
        
        # Add widgets in proper order for current language
        if self.is_rtl_language(self.current_language):
            self.snap_to_grid_layout.addStretch()
            self.snap_to_grid_layout.addWidget(self.snap_to_grid_checkbox)
            self.snap_to_grid_layout.addWidget(self.snap_to_grid_label)
        else:
            self.snap_to_grid_layout.addWidget(self.snap_to_grid_label)
            self.snap_to_grid_layout.addWidget(self.snap_to_grid_checkbox)
            self.snap_to_grid_layout.addStretch()

        # NEW: Use Extended Mask Option
        # self.extended_mask_layout = QHBoxLayout() # STORE AS INSTANCE ATTRIBUTE
        # self.extended_mask_label = QLabel(_['use_extended_mask'] if 'use_extended_mask' in _ else "Use extended mask (wider overlap)")
        # self.extended_mask_checkbox = QCheckBox()
        # self.extended_mask_checkbox.setChecked(self.use_extended_mask)
        # 
        # # Add widgets in proper order for current language
        # if self.is_rtl_language(self.current_language):
        #     self.extended_mask_layout.addStretch()
        #     self.extended_mask_layout.addWidget(self.extended_mask_checkbox)
        #     self.extended_mask_layout.addWidget(self.extended_mask_label)
        # else:
        #     self.extended_mask_layout.addWidget(self.extended_mask_label)
        #     self.extended_mask_layout.addWidget(self.extended_mask_checkbox)
        #     self.extended_mask_layout.addStretch()
        # # Add tooltip explaining usage
        # self.extended_mask_label.setToolTip(_['use_extended_mask_tooltip'])
        # self.extended_mask_checkbox.setToolTip(_['use_extended_mask_tooltip'])

        # Apply Button
        self.apply_button = QPushButton(_['ok'])
        self.apply_button.clicked.connect(self.apply_all_settings)

        # Spacer to push the apply button to the bottom
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        # Add controls to general settings layout
        general_layout.addLayout(self.theme_layout)
        general_layout.addLayout(self.shadow_layout)
        general_layout.addLayout(self.performance_layout)
        general_layout.addLayout(self.third_control_layout)
        general_layout.addLayout(self.curvature_bias_layout)
        general_layout.addLayout(self.snap_to_grid_layout)
        
        # Show Move Highlights Option
        if not hasattr(self, 'show_highlights_layout'):
            self.show_highlights_layout = QHBoxLayout()
        self.show_highlights_label = QLabel(_['show_move_highlights'] if 'show_move_highlights' in _ else "Show highlights in move modes")
        self.show_highlights_checkbox = QCheckBox()
        self.show_highlights_checkbox.setChecked(self.show_move_highlights)
        
        # Add widgets in proper order for current language
        if self.is_rtl_language(self.current_language):
            self.show_highlights_layout.addStretch()
            self.show_highlights_layout.addWidget(self.show_highlights_checkbox)
            self.show_highlights_layout.addWidget(self.show_highlights_label)
        else:
            self.show_highlights_layout.addWidget(self.show_highlights_label)
            self.show_highlights_layout.addWidget(self.show_highlights_checkbox)
            self.show_highlights_layout.addStretch()
        
        general_layout.addLayout(self.show_highlights_layout)
        # general_layout.addLayout(self.extended_mask_layout)

        # Add Shadow Blur Steps
        self.num_steps_layout = QHBoxLayout() # STORE AS INSTANCE ATTRIBUTE
        self.num_steps_label = QLabel(_['shadow_blur_steps'] if 'shadow_blur_steps' in _ else "Shadow Blur Steps:") # Will be translated later
        self.num_steps_spinbox = QSpinBox()
        self.num_steps_spinbox.setRange(1, 100)
        self.num_steps_spinbox.setValue(self.num_steps)
        self.num_steps_spinbox.setToolTip(_['shadow_blur_steps_tooltip'] if 'shadow_blur_steps_tooltip' in _ else "Number of steps for the shadow fade effect")
        
        # Add widgets in proper order for current language
        if self.is_rtl_language(self.current_language):
            self.num_steps_layout.addStretch()
            self.num_steps_layout.addWidget(self.num_steps_spinbox)
            self.num_steps_layout.addWidget(self.num_steps_label)
        else:
            self.num_steps_layout.addWidget(self.num_steps_label)
            self.num_steps_layout.addWidget(self.num_steps_spinbox)
            self.num_steps_layout.addStretch()
        general_layout.addLayout(self.num_steps_layout)

        # Add Max Blur Radius
        self.blur_radius_layout = QHBoxLayout() # STORE AS INSTANCE ATTRIBUTE
        self.blur_radius_label = QLabel(_['shadow_blur_radius'] if 'shadow_blur_radius' in _ else "Shadow Blur Radius:") # Will be translated later
        self.blur_radius_spinbox = QDoubleSpinBox()
        self.blur_radius_spinbox.setRange(0.0, 360.0)
        self.blur_radius_spinbox.setSingleStep(0.01)
        self.blur_radius_spinbox.setDecimals(2)
        self.blur_radius_spinbox.setValue(self.max_blur_radius)
        self.blur_radius_spinbox.setToolTip(_['shadow_blur_radius_tooltip'] if 'shadow_blur_radius_tooltip' in _ else "Shadow blur radius in pixels (range: 0.0 - 360.0)")
        
        # Add widgets in proper order for current language
        if self.is_rtl_language(self.current_language):
            self.blur_radius_layout.addStretch()
            self.blur_radius_layout.addWidget(self.blur_radius_spinbox)
            self.blur_radius_layout.addWidget(self.blur_radius_label)
        else:
            self.blur_radius_layout.addWidget(self.blur_radius_label)
            self.blur_radius_layout.addWidget(self.blur_radius_spinbox)
            self.blur_radius_layout.addStretch()
        general_layout.addLayout(self.blur_radius_layout)
        
        # Add Control Point Base Fraction
        self.base_fraction_layout = QHBoxLayout()
        self.base_fraction_label = QLabel(_['base_fraction'] if 'base_fraction' in _ else "Control Point Influence:")
        self.base_fraction_spinbox = QDoubleSpinBox()
        self.base_fraction_spinbox.setRange(0.25, 10.0)
        self.base_fraction_spinbox.setSingleStep(0.05)
        self.base_fraction_spinbox.setDecimals(2)
        # Use loaded value if it exists, otherwise use canvas value or default
        if hasattr(self, 'loaded_base_fraction'):
            self.base_fraction_spinbox.setValue(self.loaded_base_fraction)
        else:
            default_base_fraction = getattr(self.canvas, 'control_point_base_fraction', 1.0) if self.canvas else 1.0
            self.base_fraction_spinbox.setValue(default_base_fraction)
        self.base_fraction_spinbox.setToolTip(_['base_fraction_tooltip'] if 'base_fraction_tooltip' in _ else "Base fraction for control point influence (0.25=weak, 0.4=default, 1.0=normal, 3.0=very strong)")
        # Connect using lambda to ensure proper connection
        self.base_fraction_spinbox.valueChanged.connect(lambda v: self.on_curvature_changed(v))
        # DEBUG: Connected base_fraction_spinbox signal
        
        if self.is_rtl_language(self.current_language):
            self.base_fraction_layout.addStretch()
            self.base_fraction_layout.addWidget(self.base_fraction_spinbox)
            self.base_fraction_layout.addWidget(self.base_fraction_label)
        else:
            self.base_fraction_layout.addWidget(self.base_fraction_label)
            self.base_fraction_layout.addWidget(self.base_fraction_spinbox)
            self.base_fraction_layout.addStretch()
        general_layout.addLayout(self.base_fraction_layout)
        
        # Add Distance Multiplier
        self.distance_mult_layout = QHBoxLayout()
        self.distance_mult_label = QLabel(_['distance_multiplier'] if 'distance_multiplier' in _ else "Distance Boost:")
        self.distance_mult_spinbox = QDoubleSpinBox()
        self.distance_mult_spinbox.setRange(1.0, 10.0)
        self.distance_mult_spinbox.setSingleStep(0.1)
        self.distance_mult_spinbox.setDecimals(1)
        # Use loaded value if it exists, otherwise use canvas value or default
        if hasattr(self, 'loaded_distance_multiplier'):
            self.distance_mult_spinbox.setValue(self.loaded_distance_multiplier)
        else:
            default_distance_mult = getattr(self.canvas, 'distance_multiplier', 2.0) if self.canvas else 2.0
            self.distance_mult_spinbox.setValue(default_distance_mult)
        self.distance_mult_spinbox.setToolTip(_['distance_mult_tooltip'] if 'distance_mult_tooltip' in _ else "Distance multiplication factor (1.0=no boost, 2.0=2x boost, 5.0=5x boost, 10.0=10x boost)")
        # Connect using lambda to ensure proper connection
        self.distance_mult_spinbox.valueChanged.connect(lambda v: self.on_curvature_changed(v))
        # DEBUG: Connected distance_mult_spinbox signal
        
        if self.is_rtl_language(self.current_language):
            self.distance_mult_layout.addStretch()
            self.distance_mult_layout.addWidget(self.distance_mult_spinbox)
            self.distance_mult_layout.addWidget(self.distance_mult_label)
        else:
            self.distance_mult_layout.addWidget(self.distance_mult_label)
            self.distance_mult_layout.addWidget(self.distance_mult_spinbox)
            self.distance_mult_layout.addStretch()
        general_layout.addLayout(self.distance_mult_layout)
        
        # Add Curve Response Exponent
        self.curve_response_layout = QHBoxLayout()
        self.curve_response_label = QLabel(_['curve_response'] if 'curve_response' in _ else "Curve Type:")
        self.curve_response_spinbox = QDoubleSpinBox()
        self.curve_response_spinbox.setRange(1.0, 3.0)
        self.curve_response_spinbox.setSingleStep(0.1)
        self.curve_response_spinbox.setDecimals(1)
        # Use loaded value if it exists, otherwise use canvas value or default
        if hasattr(self, 'loaded_curve_response'):
            self.curve_response_spinbox.setValue(self.loaded_curve_response)
        else:
            default_curve_response = getattr(self.canvas, 'curve_response_exponent', 2.0) if self.canvas else 2.0
            self.curve_response_spinbox.setValue(default_curve_response)
        self.curve_response_spinbox.setToolTip(_['curve_response_tooltip'] if 'curve_response_tooltip' in _ else "Curve response type: 1.0=linear, 1.5=mild quadratic, 2.0=quadratic, 3.0=cubic")
        # Connect using lambda to ensure proper connection
        self.curve_response_spinbox.valueChanged.connect(lambda v: self.on_curvature_changed(v))
        # DEBUG: Connected curve_response_spinbox signal
        
        if self.is_rtl_language(self.current_language):
            self.curve_response_layout.addStretch()
            self.curve_response_layout.addWidget(self.curve_response_spinbox)
            self.curve_response_layout.addWidget(self.curve_response_label)
        else:
            self.curve_response_layout.addWidget(self.curve_response_label)
            self.curve_response_layout.addWidget(self.curve_response_spinbox)
            self.curve_response_layout.addStretch()
        general_layout.addLayout(self.curve_response_layout)
        
        # Add Reset Curvature Settings button
        self.reset_curvature_layout = QHBoxLayout()
        self.reset_curvature_label = QLabel(_['reset_curvature_settings'] if 'reset_curvature_settings' in _ else "Reset Curvature Settings:")
        self.reset_curvature_button = QPushButton(_['reset'] if 'reset' in _ else "Reset")
        self.reset_curvature_button.clicked.connect(self.reset_curvature_settings)
        self.reset_curvature_button.setToolTip(_['reset_curvature_tooltip'] if 'reset_curvature_tooltip' in _ else "Reset all curvature settings to default values")
        
        if self.is_rtl_language(self.current_language):
            self.reset_curvature_layout.addStretch()
            self.reset_curvature_layout.addWidget(self.reset_curvature_button)
            self.reset_curvature_layout.addWidget(self.reset_curvature_label)
        else:
            self.reset_curvature_layout.addWidget(self.reset_curvature_label)
            self.reset_curvature_layout.addWidget(self.reset_curvature_button)
            self.reset_curvature_layout.addStretch()
        general_layout.addLayout(self.reset_curvature_layout)

        general_layout.addItem(spacer)
        general_layout.addWidget(self.apply_button)

        self.stacked_widget.addWidget(self.general_settings_widget)

        # Layer Panel Settings Page (index 1)
        self.layer_panel_settings_widget = QWidget()
        # Collect HBox layouts for RTL adjustments
        self.layer_panel_rows = []
        layer_panel_layout = QVBoxLayout(self.layer_panel_settings_widget)
        layer_panel_layout.setContentsMargins(0, 0, 0, 0)

        # Extension line settings
        self.ext_length_layout = QHBoxLayout()  # Store as instance attribute
        self.layer_panel_rows.append(self.ext_length_layout)
        self.extension_length_label = QLabel(_['extension_length'] if 'extension_length' in _ else "Extension Length")
        self.extension_length_spinbox = QDoubleSpinBox()
        self.extension_length_spinbox.setRange(0.0, 1000.0)
        self.extension_length_spinbox.setValue(self.extension_length)
        self.extension_length_spinbox.setToolTip(_['extension_length_tooltip'] if 'extension_length_tooltip' in _ else "Length of extension lines")
        
        # Add widgets in proper order for current language
        if self.is_rtl_language(self.current_language):
            self.ext_length_layout.addStretch()
            self.ext_length_layout.addWidget(self.extension_length_spinbox)
            self.ext_length_layout.addWidget(self.extension_length_label)
        else:
            self.ext_length_layout.addWidget(self.extension_length_label)
            self.ext_length_layout.addWidget(self.extension_length_spinbox)
            self.ext_length_layout.addStretch()
        layer_panel_layout.addLayout(self.ext_length_layout)

        self.dash_count_layout = QHBoxLayout()  # Store as instance attribute
        self.layer_panel_rows.append(self.dash_count_layout)
        self.extension_dash_count_label = QLabel(_['extension_dash_count'] if 'extension_dash_count' in _ else "Dash Count")
        self.extension_dash_count_spinbox = QSpinBox()
        self.extension_dash_count_spinbox.setRange(1, 100)
        self.extension_dash_count_spinbox.setValue(self.extension_dash_count)
        self.extension_dash_count_spinbox.setToolTip(_['extension_dash_count_tooltip'] if 'extension_dash_count_tooltip' in _ else "Number of dashes in extension line")
        
        # Add widgets in proper order for current language
        if self.is_rtl_language(self.current_language):
            self.dash_count_layout.addStretch()
            self.dash_count_layout.addWidget(self.extension_dash_count_spinbox)
            self.dash_count_layout.addWidget(self.extension_dash_count_label)
        else:
            self.dash_count_layout.addWidget(self.extension_dash_count_label)
            self.dash_count_layout.addWidget(self.extension_dash_count_spinbox)
            self.dash_count_layout.addStretch()
        layer_panel_layout.addLayout(self.dash_count_layout)

        self.extension_dash_width_layout = QHBoxLayout()  # Store as instance attribute - renamed for clarity
        self.layer_panel_rows.append(self.extension_dash_width_layout)
        self.extension_dash_width_label = QLabel(_['extension_dash_width'] if 'extension_dash_width' in _ else "Dash Width")
        self.extension_dash_width_spinbox = QDoubleSpinBox()
        self.extension_dash_width_spinbox.setRange(0.1, 20.0)
        self.extension_dash_width_spinbox.setValue(self.extension_dash_width)
        self.extension_dash_width_spinbox.setToolTip(_['extension_dash_width_tooltip'] if 'extension_dash_width_tooltip' in _ else "Width of  dashes")
        
        # Add widgets in proper order for current language
        if self.is_rtl_language(self.current_language):
            self.extension_dash_width_layout.addStretch()
            self.extension_dash_width_layout.addWidget(self.extension_dash_width_spinbox)
            self.extension_dash_width_layout.addWidget(self.extension_dash_width_label)
        else:
            self.extension_dash_width_layout.addWidget(self.extension_dash_width_label)
            self.extension_dash_width_layout.addWidget(self.extension_dash_width_spinbox)
            self.extension_dash_width_layout.addStretch()
        layer_panel_layout.addLayout(self.extension_dash_width_layout)

        # Extension Dash Gap Length setting
        self.gap_length_layout = QHBoxLayout()  # Store as instance attribute
        self.layer_panel_rows.append(self.gap_length_layout)
        self.extension_dash_gap_length_label = QLabel(_['extension_dash_gap_length'] if 'extension_dash_gap_length' in _ else 'Dash Gap Length')
        self.extension_dash_gap_length_spinbox = QDoubleSpinBox()
        self.extension_dash_gap_length_spinbox.setRange(0.0, 1000.0)
        self.extension_dash_gap_length_spinbox.setValue(self.extension_dash_gap_length)
        self.extension_dash_gap_length_spinbox.setToolTip(_['extension_dash_gap_length_tooltip'] if 'extension_dash_gap_length_tooltip' in _ else 'Gap between strand and the start of the dashes')
        
        # Add widgets in proper order for current language
        if self.is_rtl_language(self.current_language):
            self.gap_length_layout.addStretch()
            self.gap_length_layout.addWidget(self.extension_dash_gap_length_spinbox)
            self.gap_length_layout.addWidget(self.extension_dash_gap_length_label)
        else:
            self.gap_length_layout.addWidget(self.extension_dash_gap_length_label)
            self.gap_length_layout.addWidget(self.extension_dash_gap_length_spinbox)
            self.gap_length_layout.addStretch()
        layer_panel_layout.addLayout(self.gap_length_layout)

        # --- NEW: Arrow head settings ---
        self.arrow_len_layout = QHBoxLayout()  # Store as instance attribute
        self.layer_panel_rows.append(self.arrow_len_layout)
        self.arrow_head_length_label = QLabel(_['arrow_head_length'] if 'arrow_head_length' in _ else 'Arrow Head Length')
        self.arrow_head_length_spinbox = QDoubleSpinBox()
        self.arrow_head_length_spinbox.setRange(0.0, 500.0)
        self.arrow_head_length_spinbox.setValue(self.arrow_head_length)
        self.arrow_head_length_spinbox.setToolTip(_['arrow_head_length_tooltip'] if 'arrow_head_length_tooltip' in _ else 'Length of arrow head in pixels')
        
        # Add widgets in proper order for current language
        if self.is_rtl_language(self.current_language):
            self.arrow_len_layout.addStretch()
            self.arrow_len_layout.addWidget(self.arrow_head_length_spinbox)
            self.arrow_len_layout.addWidget(self.arrow_head_length_label)
        else:
            self.arrow_len_layout.addWidget(self.arrow_head_length_label)
            self.arrow_len_layout.addWidget(self.arrow_head_length_spinbox)
            self.arrow_len_layout.addStretch()
        layer_panel_layout.addLayout(self.arrow_len_layout)

        self.arrow_width_layout = QHBoxLayout()  # Store as instance attribute
        self.layer_panel_rows.append(self.arrow_width_layout)
        self.arrow_head_width_label = QLabel(_['arrow_head_width'] if 'arrow_head_width' in _ else 'Arrow Head Width')
        self.arrow_head_width_spinbox = QDoubleSpinBox()
        self.arrow_head_width_spinbox.setRange(0.0, 500.0)
        self.arrow_head_width_spinbox.setValue(self.arrow_head_width)
        self.arrow_head_width_spinbox.setToolTip(_['arrow_head_width_tooltip'] if 'arrow_head_width_tooltip' in _ else 'Width of arrow head base in pixels')
        
        # Add widgets in proper order for current language
        if self.is_rtl_language(self.current_language):
            self.arrow_width_layout.addStretch()
            self.arrow_width_layout.addWidget(self.arrow_head_width_spinbox)
            self.arrow_width_layout.addWidget(self.arrow_head_width_label)
        else:
            self.arrow_width_layout.addWidget(self.arrow_head_width_label)
            self.arrow_width_layout.addWidget(self.arrow_head_width_spinbox)
            self.arrow_width_layout.addStretch()
        layer_panel_layout.addLayout(self.arrow_width_layout)
        # --- END NEW ---

        # --- NEW: Arrow head stroke width setting ---
        self.arrow_stroke_layout = QHBoxLayout()  # Store as instance attribute
        self.layer_panel_rows.append(self.arrow_stroke_layout)
        self.arrow_head_stroke_width_label = QLabel(_['arrow_head_stroke_width'] if 'arrow_head_stroke_width' in _ else 'Arrow Head Stroke Width')
        self.arrow_head_stroke_width_spinbox = QSpinBox()
        self.arrow_head_stroke_width_spinbox.setRange(1, 30)
        self.arrow_head_stroke_width_spinbox.setValue(getattr(self.canvas, 'arrow_head_stroke_width', 4))
        self.arrow_head_stroke_width_spinbox.setToolTip(_['arrow_head_stroke_width_tooltip'] if 'arrow_head_stroke_width_tooltip' in _ else 'Thickness of arrow head border in pixels')
        
        # Add widgets in proper order for current language
        if self.is_rtl_language(self.current_language):
            self.arrow_stroke_layout.addStretch()
            self.arrow_stroke_layout.addWidget(self.arrow_head_stroke_width_spinbox)
            self.arrow_stroke_layout.addWidget(self.arrow_head_stroke_width_label)
        else:
            self.arrow_stroke_layout.addWidget(self.arrow_head_stroke_width_label)
            self.arrow_stroke_layout.addWidget(self.arrow_head_stroke_width_spinbox)
            self.arrow_stroke_layout.addStretch()
        layer_panel_layout.addLayout(self.arrow_stroke_layout)
        # --- END NEW ---

        # Add arrow shaft settings
        self.arrow_gap_layout = QHBoxLayout()  # Store as instance attribute - renamed to avoid conflict
        self.layer_panel_rows.append(self.arrow_gap_layout)
        self.arrow_gap_length_label = QLabel(_['arrow_gap_length'] if 'arrow_gap_length' in _ else 'Arrow Gap Length')
        self.arrow_gap_length_spinbox = QDoubleSpinBox()
        self.arrow_gap_length_spinbox.setRange(0.0, 1000.0)
        self.arrow_gap_length_spinbox.setValue(self.arrow_gap_length)
        self.arrow_gap_length_spinbox.setToolTip(_['arrow_gap_length_tooltip'] if 'arrow_gap_length_tooltip' in _ else 'Gap between strand end and arrow shaft start')
        
        # Add widgets in proper order for current language
        if self.is_rtl_language(self.current_language):
            self.arrow_gap_layout.addStretch()
            self.arrow_gap_layout.addWidget(self.arrow_gap_length_spinbox)
            self.arrow_gap_layout.addWidget(self.arrow_gap_length_label)
        else:
            self.arrow_gap_layout.addWidget(self.arrow_gap_length_label)
            self.arrow_gap_layout.addWidget(self.arrow_gap_length_spinbox)
            self.arrow_gap_layout.addStretch()
        layer_panel_layout.addLayout(self.arrow_gap_layout)

        self.arrow_line_length_layout = QHBoxLayout()  # Store as instance attribute - renamed to avoid conflict
        self.layer_panel_rows.append(self.arrow_line_length_layout)
        self.arrow_line_length_label = QLabel(_['arrow_line_length'] if 'arrow_line_length' in _ else 'Arrow Line Length')
        self.arrow_line_length_spinbox = QDoubleSpinBox()
        self.arrow_line_length_spinbox.setRange(0.0, 1000.0)
        self.arrow_line_length_spinbox.setValue(self.arrow_line_length)
        self.arrow_line_length_spinbox.setToolTip(_['arrow_line_length_tooltip'] if 'arrow_line_length_tooltip' in _ else 'Length of the arrow shaft')
        
        # Add widgets in proper order for current language
        if self.is_rtl_language(self.current_language):
            self.arrow_line_length_layout.addStretch()
            self.arrow_line_length_layout.addWidget(self.arrow_line_length_spinbox)
            self.arrow_line_length_layout.addWidget(self.arrow_line_length_label)
        else:
            self.arrow_line_length_layout.addWidget(self.arrow_line_length_label)
            self.arrow_line_length_layout.addWidget(self.arrow_line_length_spinbox)
            self.arrow_line_length_layout.addStretch()
        layer_panel_layout.addLayout(self.arrow_line_length_layout)

        self.arrow_line_width_layout = QHBoxLayout()  # Store as instance attribute - renamed to avoid conflict
        self.layer_panel_rows.append(self.arrow_line_width_layout)
        self.arrow_line_width_label = QLabel(_['arrow_line_width'] if 'arrow_line_width' in _ else 'Arrow Line Width')
        self.arrow_line_width_spinbox = QDoubleSpinBox()
        self.arrow_line_width_spinbox.setRange(0.1, 100.0)
        self.arrow_line_width_spinbox.setValue(self.arrow_line_width)
        self.arrow_line_width_spinbox.setToolTip(_['arrow_line_width_tooltip'] if 'arrow_line_width_tooltip' in _ else 'Thickness of the arrow shaft')
        
        # Add widgets in proper order for current language
        if self.is_rtl_language(self.current_language):
            self.arrow_line_width_layout.addStretch()
            self.arrow_line_width_layout.addWidget(self.arrow_line_width_spinbox)
            self.arrow_line_width_layout.addWidget(self.arrow_line_width_label)
        else:
            self.arrow_line_width_layout.addWidget(self.arrow_line_width_label)
            self.arrow_line_width_layout.addWidget(self.arrow_line_width_spinbox)
            self.arrow_line_width_layout.addStretch()
        layer_panel_layout.addLayout(self.arrow_line_width_layout)
        # Default Arrow Color toggle and selector
        # Create a vertical layout to hold the checkbox and button containers
        default_arrow_container_layout = QVBoxLayout()
        # We might not need to add this sub-layout to layer_panel_rows for RTL handling,
        # as the parent widget's layout direction should propagate.

        # --- Checkbox Container ---
        self.checkbox_container = QWidget()  # Store as instance attribute
        self.checkbox_layout = QHBoxLayout(self.checkbox_container)  # Store as instance attribute
        self.checkbox_layout.setContentsMargins(0, 0, 0, 0)
        #self.checkbox_layout.setSpacing(0)  # Match spacing from general settings
        
        # Create separate label and checkbox (like in general settings)
        self.default_arrow_color_label = QLabel(_['use_default_arrow_color'] if 'use_default_arrow_color' in _ else "Use Default Arrow Color")
        self.default_arrow_color_checkbox = QCheckBox()  # No text on checkbox itself
        self.default_arrow_color_checkbox.setChecked(self.use_default_arrow_color)
        self.default_arrow_color_checkbox.stateChanged.connect(self.on_default_arrow_color_changed)

        # Add widgets in proper order for current language
        if self.is_rtl_language(self.current_language):
            self.checkbox_layout.addStretch()
            self.checkbox_layout.addWidget(self.default_arrow_color_checkbox)
            self.checkbox_layout.addWidget(self.default_arrow_color_label)
        else:
            self.checkbox_layout.addWidget(self.default_arrow_color_label)
            self.checkbox_layout.addWidget(self.default_arrow_color_checkbox)
            self.checkbox_layout.addStretch()
        # Add the checkbox container widget to the default arrow container layout
        default_arrow_container_layout.addWidget(self.checkbox_container)

        # Ensure the checkbox row (container) is included for RTL direction updates
        self.layer_panel_rows.append(self.checkbox_container)

        # Button Color - Label and button in SAME layout
        # Create a container widget to hold the layout so margins work properly
        self.button_color_container = QWidget()
        self.button_color_layout = QHBoxLayout(self.button_color_container) # Create QHBoxLayout and assign to widget
        
        # Set initial margins and spacing for the button_color_layout (QHBoxLayout)
        if self.is_rtl_language(self.current_language):
            self.button_color_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins, use spacer instead
            self.button_color_layout.setSpacing(10) 
        else:
            self.button_color_layout.setContentsMargins(0, 0, 0, 0)  # Normal margins for LTR
            self.button_color_layout.setSpacing(10)

        self.button_color_label = QLabel(_['button_color'] if 'button_color' in _ else 'Button Color:')
        # Add these lines right after creating the label:
        self.button_color_label.setTextFormat(Qt.PlainText)
        self.button_color_label.setWordWrap(False)
        self.button_color_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        # Set proper alignment for RTL
        if self.is_rtl_language(self.current_language):
            self.button_color_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.button_color_label.setLayoutDirection(Qt.RightToLeft)
        else:
            self.button_color_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.button_color_label.setLayoutDirection(Qt.LeftToRight)
        # Ensure text is visible with proper styling
        self.button_color_label.setStyleSheet("QLabel { color: white; }" if self.current_theme == "dark" else "QLabel { color: black; }")
        # Force word wrap off and ensure text is not clipped
        self.button_color_label.setWordWrap(False)
        self.button_color_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.button_color_layout.setContentsMargins(0, 0, 0, 0)
        self.button_color_container.setContentsMargins(0, 0, 0, 0)
        # Force update to ensure label has proper size
        self.button_color_label.adjustSize()
        self.default_arrow_color_button = QPushButton()
        self.default_arrow_color_button.setFixedSize(30, 30)
        self.update_default_arrow_color_button()
        self.default_arrow_color_button.clicked.connect(self.choose_default_arrow_color)

        # Add widgets in proper order for current language (to self.button_color_layout)
        if self.is_rtl_language(self.current_language):
            self.button_color_layout.addWidget(self.button_color_label)
            self.button_color_layout.addStretch()
            self.button_color_layout.addWidget(self.default_arrow_color_button)
        else:
            self.button_color_layout.addWidget(self.button_color_label)
            self.button_color_layout.addWidget(self.default_arrow_color_button)
            self.button_color_layout.addStretch()
        
        # Log final layout state
        for i in range(self.button_color_layout.count()):
            item = self.button_color_layout.itemAt(i)
            if item.widget():
                widget = item.widget()
            elif item.spacerItem():
                spacer = item.spacerItem()
        # Log container and layout geometry
        # Try to force label to fill available space
        self.button_color_label.setMinimumWidth(self.button_color_container.width())
        self.button_color_label.updateGeometry()
        self.button_color_label.repaint()

        default_arrow_container_layout.addWidget(self.button_color_container) # Add the container widget instead of layout directly
        self.layer_panel_rows.append(self.button_color_container) # Add container to rows for RTL handling instead of layout
        
        # Default Strand Color - Label and button
        self.default_strand_color_container = QWidget()
        self.default_strand_color_layout = QHBoxLayout(self.default_strand_color_container)
        self.default_strand_color_container.setContentsMargins(0, 0, 0, 0)
        if self.is_rtl_language(self.current_language):
            self.default_strand_color_layout.setContentsMargins(278, 0, 0, 0)
            self.default_strand_color_layout.setSpacing(20)
        else:
            self.default_strand_color_layout.setContentsMargins(0, 0, 0, 0)
            self.default_strand_color_layout.setSpacing(15)

        self.default_strand_color_label = QLabel(_['default_strand_color'] if 'default_strand_color' in _ else 'Default Strand Color:')
        self.default_strand_color_label.setTextFormat(Qt.PlainText)
        self.default_strand_color_label.setWordWrap(False)
        self.default_strand_color_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        if self.is_rtl_language(self.current_language):
            self.default_strand_color_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.default_strand_color_label.setLayoutDirection(Qt.RightToLeft)
        else:
            self.default_strand_color_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.default_strand_color_label.setLayoutDirection(Qt.LeftToRight)
        
        self.default_strand_color_label.setStyleSheet("QLabel { color: white; }" if self.current_theme == "dark" else "QLabel { color: black; }")
        self.default_strand_color_label.adjustSize()
        
        self.default_strand_color_button = QPushButton()
        self.default_strand_color_button.setFixedSize(30, 30)
        self.update_default_strand_color_button()
        self.default_strand_color_button.clicked.connect(self.choose_default_strand_color)

        if self.is_rtl_language(self.current_language):
            self.default_strand_color_layout.addWidget(self.default_strand_color_label)
            self.default_strand_color_layout.addStretch()
            self.default_strand_color_layout.addWidget(self.default_strand_color_button)
        else:
            self.default_strand_color_layout.addWidget(self.default_strand_color_label)
            self.default_strand_color_layout.addWidget(self.default_strand_color_button)
            self.default_strand_color_layout.addStretch()

        default_arrow_container_layout.addWidget(self.default_strand_color_container)
        self.layer_panel_rows.append(self.default_strand_color_container)
        
        # Default Stroke Color - Label and button
        self.default_stroke_color_container = QWidget()
        self.default_stroke_color_layout = QHBoxLayout(self.default_stroke_color_container)
        self.default_stroke_color_container.setContentsMargins(0, 0, 0, 0)
        if self.is_rtl_language(self.current_language):
            self.default_stroke_color_layout.setContentsMargins(308, 0, 0, 0)
            self.default_stroke_color_layout.setSpacing(20)
        else:
            self.default_stroke_color_layout.setContentsMargins(0, 0, 0, 0)
            self.default_stroke_color_layout.setSpacing(15)

        self.default_stroke_color_label = QLabel(_['default_stroke_color'] if 'default_stroke_color' in _ else 'Default Stroke Color:')
        self.default_stroke_color_label.setTextFormat(Qt.PlainText)
        self.default_stroke_color_label.setWordWrap(False)
        self.default_stroke_color_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        if self.is_rtl_language(self.current_language):
            self.default_stroke_color_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.default_stroke_color_label.setLayoutDirection(Qt.RightToLeft)
        else:
            self.default_stroke_color_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.default_stroke_color_label.setLayoutDirection(Qt.LeftToRight)
        
        self.default_stroke_color_label.setStyleSheet("QLabel { color: white; }" if self.current_theme == "dark" else "QLabel { color: black; }")
        self.default_stroke_color_label.adjustSize()
        
        self.default_stroke_color_button = QPushButton()
        self.default_stroke_color_button.setFixedSize(30, 30)
        self.update_default_stroke_color_button()
        self.default_stroke_color_button.clicked.connect(self.choose_default_stroke_color)

        if self.is_rtl_language(self.current_language):
            self.default_stroke_color_layout.addWidget(self.default_stroke_color_label)
            self.default_stroke_color_layout.addStretch()
            self.default_stroke_color_layout.addWidget(self.default_stroke_color_button)
        else:
            self.default_stroke_color_layout.addWidget(self.default_stroke_color_label)
            self.default_stroke_color_layout.addWidget(self.default_stroke_color_button)
            self.default_stroke_color_layout.addStretch()

        default_arrow_container_layout.addWidget(self.default_stroke_color_container)
        self.layer_panel_rows.append(self.default_stroke_color_container)
        
        # Default Strand Width - Button only
        self.default_strand_width_container = QWidget()
        self.default_strand_width_layout = QHBoxLayout(self.default_strand_width_container)
        self.default_strand_width_container.setContentsMargins(0, 0, 0, 0)
        # Use consistent margins and spacing for centered button
        self.default_strand_width_layout.setContentsMargins(0, 0, 0, 0)
        self.default_strand_width_layout.setSpacing(15)

        self.default_strand_width_button = QPushButton(_['default_strand_width'])
        self.default_strand_width_button.setToolTip(_['default_strand_width_tooltip'])
        self.default_strand_width_button.clicked.connect(self.open_default_width_dialog)
        # Set dynamic width based on translated text length
        self.update_default_strand_width_button_size()
        
        # Center the button for both LTR and RTL languages
        self.default_strand_width_layout.addStretch()
        self.default_strand_width_layout.addWidget(self.default_strand_width_button, 0, Qt.AlignCenter)
        self.default_strand_width_layout.addStretch()
        
        default_arrow_container_layout.addWidget(self.default_strand_width_container)
        self.layer_panel_rows.append(self.default_strand_width_container)
        
        # Add the vertical layout containing checkbox, button label, and button to the main layer panel layout
        layer_panel_layout.addLayout(default_arrow_container_layout)
        # OK button for layer panel settings
        self.layer_panel_ok_button = QPushButton(_['ok'])
        self.layer_panel_ok_button.clicked.connect(self.apply_all_settings)
        layer_panel_layout.addStretch()
        layer_panel_layout.addWidget(self.layer_panel_ok_button)
        self.stacked_widget.addWidget(self.layer_panel_settings_widget)

        # Change Language Page (index 1)
        self.change_language_widget = QWidget()
        language_layout = QVBoxLayout(self.change_language_widget)

        # Language Selection
        self.language_label = QLabel(_['select_language'])
        self.language_combobox = QComboBox()

        # Enhanced language combobox stylesheet with dropdown arrow
        self.lang_combobox_base_style = f"""
            QComboBox {{
                padding: 8px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                min-width: 150px;
                font-size: 14px;
                padding-left: 8px; padding-right: 24px;
            }}
            {dropdown_arrow_css}
            QComboBox QAbstractItemView {{
                padding: 4px;
                min-width: 150px;
                selection-background-color: {selection_color};
            }}
            QComboBox QAbstractItemView::item {{
                padding: 4px 8px;
                min-height: 48px;
                border: none;
                text-align: left;
            }}
            QComboBox::item {{
                padding: 4px 8px;
                min-height: 48px;
                text-align: left;
            }}
        """
        self.language_combobox.setStyleSheet(self.lang_combobox_base_style)
        
        # Add language items with generated icons - using current translations
        self.add_lang_item_en(_['english'], 'en')
        self.add_lang_item_fr(_['french'], 'fr')
        self.add_lang_item_de(_['german'], 'de')
        self.add_lang_item_it(_['italian'], 'it')
        self.add_lang_item_es(_['spanish'], 'es')
        self.add_lang_item_pt(_['portuguese'], 'pt')
        self.add_lang_item_he(_['hebrew'], 'he')
        
        # Set the current language
        current_language = getattr(self, 'current_language', 'en')
        index = self.language_combobox.findData(current_language)
        if index >= 0:
            self.language_combobox.setCurrentIndex(index)
            
        # Apply text alignment based on current language
        if self.is_rtl_language(current_language):
            self.set_combobox_text_alignment(self.language_combobox, Qt.AlignRight | Qt.AlignVCenter)
        else:
            self.set_combobox_text_alignment(self.language_combobox, Qt.AlignLeft | Qt.AlignVCenter)

        self.language_info_label = QLabel(_['language_settings_info'])
        # Add widgets to language layout with logical leading alignment
        language_layout.addWidget(self.language_label, 0, Qt.AlignLeading | Qt.AlignVCenter)
        language_layout.addWidget(self.language_combobox, 0, Qt.AlignLeading | Qt.AlignVCenter)
        language_layout.addWidget(self.language_info_label, 0, Qt.AlignLeading | Qt.AlignVCenter)

        # Add the "OK" button
        self.language_ok_button = QPushButton(_['ok'])
        self.language_ok_button.clicked.connect(self.apply_all_settings)
        language_layout.addWidget(self.language_ok_button)

        self.stacked_widget.addWidget(self.change_language_widget)

        # Tutorial Page (index 2)
        self.tutorial_widget = QWidget()
        tutorial_layout = QVBoxLayout(self.tutorial_widget)

        # Add a tutorial label
        self.tutorial_label = QLabel(_['tutorial_info'])
        self.tutorial_label.setAlignment(Qt.AlignCenter)
        self.tutorial_label.setWordWrap(True)  # Enable word wrap for multiline text
        self.tutorial_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tutorial_layout.addWidget(self.tutorial_label)

        self.video_buttons = []

        for i in range(4):  # Changed from 5 to 4 tutorials
            # Explanation Label
            explanation_label = QLabel(_[f'gif_explanation_{i+1}'])
            tutorial_layout.addWidget(explanation_label, 0, Qt.AlignLeft) # Default alignment, will be updated

            # Play Video Button
            play_button = QPushButton(_['play_video'])
            # Set fixed size based on longest translation and increased height
            play_button.setFixedSize(180, 40)  # Width for "Reproducir Vídeo" + padding, height increased
            play_button.setStyleSheet("QPushButton { padding: 5px; }")
            
            # Create a horizontal layout to center the button
            button_container = QHBoxLayout()
            button_container.addStretch()
            button_container.addWidget(play_button)
            button_container.addStretch()
            tutorial_layout.addLayout(button_container)
            
            play_button.clicked.connect(lambda checked, idx=i: self.play_video(idx))
            self.video_buttons.append(play_button)

        self.stacked_widget.addWidget(self.tutorial_widget)

        # Button Explanations Page (index 4)
        self.button_explanations_widget = QWidget()
        button_explanations_layout = QVBoxLayout(self.button_explanations_widget)
        
        # Add the main info label at the top
        self.button_guide_label = QLabel(_['button_guide_info'])
        self.button_guide_label.setAlignment(Qt.AlignCenter)
        self.button_guide_label.setWordWrap(True)
        self.button_guide_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        button_explanations_layout.addWidget(self.button_guide_label)
        
        # Add some spacing
        button_explanations_layout.addSpacing(10)
        
        # Use QTextBrowser for the button explanations content
        self.button_explanations_text_browser = QTextBrowser()
        self.button_explanations_text_browser.setOpenExternalLinks(False)
        
        # Build the HTML content for button explanations
        # Determine title color based on theme
        title_color = '#333'  # Default for light theme
        if self.current_theme == 'dark':
            title_color = '#ffffff'  # White for dark theme
        elif self.current_theme == 'light':
            title_color = '#000000'  # Black for light theme
            
        button_html = f'''
        <style>
            body {{ font-family: Arial, sans-serif; padding: 10px; }}
            h2 {{ color: {title_color}; margin-top: 15px; margin-bottom: 10px; }}
            ul {{ margin-top: 5px; margin-bottom: 15px; }}
            li {{ margin-bottom: 8px; }}
            .button-name {{ font-weight: bold; }}
        </style>
        
        <h2>{_['layer_panel_buttons']}</h2>
        <ul>
            <li><span class="button-name">{_['draw_names_desc'].split(' - ')[0]}</span> - {_['draw_names_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['lock_layers_desc'].split(' - ')[0]}</span> - {_['lock_layers_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['add_new_strand_desc'].split(' - ')[0]}</span> - {_['add_new_strand_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['delete_strand_desc'].split(' - ')[0]}</span> - {_['delete_strand_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['deselect_all_desc'].split(' - ')[0]}</span> - {_['deselect_all_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['pan_desc'].split(' - ')[0]}</span> - {_['pan_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['zoom_in_desc'].split(' - ')[0]}</span> - {_['zoom_in_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['zoom_out_desc'].split(' - ')[0]}</span> - {_['zoom_out_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['center_strands_desc'].split(' - ')[0]}</span> - {_['center_strands_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['multi_select_desc'].split(' - ')[0]}</span> - {_['multi_select_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['refresh_desc'].split(' - ')[0]}</span> - {_['refresh_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['reset_states_desc'].split(' - ')[0]}</span> - {_['reset_states_desc'].split(' - ')[1]}</li>
        </ul>
        
        <h2>{_['main_window_buttons']}</h2>
        <ul>
            <li><span class="button-name">{_['attach_mode_desc'].split(' - ')[0]}</span> - {_['attach_mode_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['move_mode_desc'].split(' - ')[0]}</span> - {_['move_mode_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['rotate_mode_desc'].split(' - ')[0]}</span> - {_['rotate_mode_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['toggle_grid_desc'].split(' - ')[0]}</span> - {_['toggle_grid_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['angle_adjust_desc'].split(' - ')[0]}</span> - {_['angle_adjust_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['save_desc'].split(' - ')[0]}</span> - {_['save_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['load_desc'].split(' - ')[0]}</span> - {_['load_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['save_image_desc'].split(' - ')[0]}</span> - {_['save_image_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['select_strand_desc'].split(' - ')[0]}</span> - {_['select_strand_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['mask_mode_desc'].split(' - ')[0]}</span> - {_['mask_mode_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['settings_desc'].split(' - ')[0]}</span> - {_['settings_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['toggle_control_points_desc'].split(' - ')[0]}</span> - {_['toggle_control_points_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['toggle_shadow_desc'].split(' - ')[0]}</span> - {_['toggle_shadow_desc'].split(' - ')[1]}</li>
        </ul>
        
        <h2>{_['group_buttons']}</h2>
        <ul>
            <li><span class="button-name">{_['create_group_desc'].split(' - ')[0]}</span> - {_['create_group_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['group_header_desc'].split(' - ')[0]}</span> - {_['group_header_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['select_group_desc'].split(' - ')[0]}</span> - {_['select_group_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['move_group_desc'].split(' - ')[0]}</span> - {_['move_group_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['rotate_group_desc'].split(' - ')[0]}</span> - {_['rotate_group_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['edit_strand_angles_desc'].split(' - ')[0]}</span> - {_['edit_strand_angles_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['duplicate_group_desc'].split(' - ')[0]}</span> - {_['duplicate_group_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['rename_group_desc'].split(' - ')[0]}</span> - {_['rename_group_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['delete_group_desc'].split(' - ')[0]}</span> - {_['delete_group_desc'].split(' - ')[1]}</li>
        </ul>
        
        <h2>{_['general_settings_buttons'] if 'general_settings_buttons' in _ else 'General Settings'}</h2>
        <ul>
            <li><span class="button-name">{_['theme_select_desc'].split(' - ')[0] if 'theme_select_desc' in _ else 'Theme Selection'}</span> - {_['theme_select_desc'].split(' - ')[1] if 'theme_select_desc' in _ else 'Choose between light and dark themes for the interface'}</li>
            <li><span class="button-name">{_['shadow_color_desc'].split(' - ')[0] if 'shadow_color_desc' in _ else 'Shadow Color'}</span> - {_['shadow_color_desc'].split(' - ')[1] if 'shadow_color_desc' in _ else 'Set the color and opacity for strand shadows'}</li>
            <li><span class="button-name">{_['draw_only_affected_desc'].split(' - ')[0] if 'draw_only_affected_desc' in _ else 'Draw Only Affected Strand'}</span> - {_['draw_only_affected_desc'].split(' - ')[1] if 'draw_only_affected_desc' in _ else 'When enabled, only shows the strand being edited during drag operations'}</li>
            <li><span class="button-name">{_['enable_third_cp_desc'].split(' - ')[0] if 'enable_third_cp_desc' in _ else 'Enable Third Control Point'}</span> - {_['enable_third_cp_desc'].split(' - ')[1] if 'enable_third_cp_desc' in _ else 'Adds an additional control point at the center for more complex curves'}</li>
            <li><span class="button-name">{_['enable_snap_desc'].split(' - ')[0] if 'enable_snap_desc' in _ else 'Enable Snap to Grid'}</span> - {_['enable_snap_desc'].split(' - ')[1] if 'enable_snap_desc' in _ else 'Automatically aligns strands to grid points when moving'}</li>
            <li><span class="button-name">{_['shadow_blur_steps_desc'].split(' - ')[0] if 'shadow_blur_steps_desc' in _ else 'Shadow Blur Steps'}</span> - {_['shadow_blur_steps_desc'].split(' - ')[1] if 'shadow_blur_steps_desc' in _ else 'Number of steps for creating smooth shadow fade effect (1-10)'}</li>
            <li><span class="button-name">{_['shadow_blur_radius_desc'].split(' - ')[0] if 'shadow_blur_radius_desc' in _ else 'Shadow Blur Radius'}</span> - {_['shadow_blur_radius_desc'].split(' - ')[1] if 'shadow_blur_radius_desc' in _ else 'Controls the spread of the shadow blur in pixels'}</li>
            <li><span class="button-name">{_['control_point_influence_desc'].split(' - ')[0] if 'control_point_influence_desc' in _ else 'Control Point Influence'}</span> - {_['control_point_influence_desc'].split(' - ')[1] if 'control_point_influence_desc' in _ else 'Adjusts how strongly control points affect curve shape (1.0=normal)'}</li>
            <li><span class="button-name">{_['distance_boost_desc'].split(' - ')[0] if 'distance_boost_desc' in _ else 'Distance Boost'}</span> - {_['distance_boost_desc'].split(' - ')[1] if 'distance_boost_desc' in _ else 'Multiplies the distance influence for stronger curves (2.0=double strength)'}</li>
            <li><span class="button-name">{_['curvature_type_desc'].split(' - ')[0] if 'curvature_type_desc' in _ else 'Curvature Type'}</span> - {_['curvature_type_desc'].split(' - ')[1] if 'curvature_type_desc' in _ else 'Changes the mathematical curve response (1.0=linear, 2.0=quadratic, 3.0=cubic)'}</li>
            <li><span class="button-name">{_['reset_curvature_desc'].split(' - ')[0] if 'reset_curvature_desc' in _ else 'Reset Curvature'}</span> - {_['reset_curvature_desc'].split(' - ')[1] if 'reset_curvature_desc' in _ else 'Restores all curvature settings to default values (1.0, 2.0, 2.0)'}</li>
        </ul>
        '''
        
        self.button_explanations_text_browser.setHtml(button_html)
        button_explanations_layout.addWidget(self.button_explanations_text_browser)
        
        self.stacked_widget.addWidget(self.button_explanations_widget)

        # History Page (index 5)
        self.history_widget = QWidget()
        history_layout = QVBoxLayout(self.history_widget)

        self.history_explanation_label = QLabel(_['history_explanation'])
        if self.is_rtl_language(self.current_language):
            history_layout.addWidget(self.history_explanation_label, 0, Qt.AlignLeft)
        else:
            history_layout.addWidget(self.history_explanation_label) # Default alignment, will be updated later

        self.history_list = QListWidget()
        self.history_list.setToolTip(_['history_list_tooltip'] if 'history_list_tooltip' in _ else "Select a session to load its final state")
        history_layout.addWidget(self.history_list)
        
        # Move the populate_history_list call to after button creation
        # self.populate_history_list() - Removing this call from here

        history_button_layout = QHBoxLayout()
        self.load_history_button = QPushButton(_['load_selected_history'])
        self.load_history_button.clicked.connect(self.load_selected_history)
        self.load_history_button.setEnabled(False) # Disable initially
        self.history_list.currentItemChanged.connect(lambda item: self.load_history_button.setEnabled(item is not None))

        self.clear_history_button = QPushButton(_['clear_all_history'])
        self.clear_history_button.clicked.connect(self.clear_all_history_action)

        history_button_layout.addWidget(self.load_history_button)
        history_button_layout.addWidget(self.clear_history_button)
        history_button_layout.addStretch()
        
        history_layout.addLayout(history_button_layout)
        
        # Call populate_history_list after creating all the UI elements it needs
        self.populate_history_list()
        
        self.stacked_widget.addWidget(self.history_widget)

        # What's New Page (index 4)
        self.whats_new_widget = QWidget()
        whats_new_layout = QVBoxLayout(self.whats_new_widget)

        # Use QTextBrowser to display rich text content for What's New
        self.whats_new_text_browser = QTextBrowser()
        # Render HTML with runtime assets (e.g., flag icons) replaced
        self.whats_new_text_browser.setHtml(self.render_whats_new_html(_['whats_new_info']))
        self.whats_new_text_browser.setOpenExternalLinks(True)
        whats_new_layout.addWidget(self.whats_new_text_browser)

        self.stacked_widget.addWidget(self.whats_new_widget)

        # Samples Page (second to last, before About)
        self.samples_widget = QWidget()
        samples_layout = QVBoxLayout(self.samples_widget)

        # Store labels as instance attributes so they can be updated on language change
        self.samples_header_label = QLabel((_['samples_header'] if 'samples_header' in _ else 'Sample projects'))
        self.samples_header_label.setAlignment(Qt.AlignCenter)
        self.samples_header_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.samples_sub_label = QLabel((_['samples_sub'] if 'samples_sub' in _ else 'Choose a sample to load and learn from. The dialog will close and the sample will be loaded.'))
        self.samples_sub_label.setWordWrap(True)
        self.samples_sub_label.setAlignment(Qt.AlignCenter)
        self.samples_sub_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        samples_layout.addWidget(self.samples_header_label)
        samples_layout.addWidget(self.samples_sub_label)

        # Build sample buttons for the three curated samples (static, not scanning folder)
        self.sample_buttons = []
        # Use proper path resolution for samples directory
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            if sys.platform.startswith('darwin'):
                # For macOS .app bundles
                base_path = os.path.join(os.path.dirname(sys.executable), '..', 'Resources')
            else:
                # For Windows/Linux executables
                base_path = sys._MEIPASS
        else:
            # Running as script
            base_path = os.path.dirname(__file__)
        
        samples_dir = os.path.join(base_path, 'samples')

        # Closed Knot
        self.sample_button_closed_knot = QPushButton(_['sample_closed_knot'] if 'sample_closed_knot' in _ else 'Closed Knot')
        closed_knot_path = os.path.join(samples_dir, 'closed_knot.json')
        self.sample_button_closed_knot.clicked.connect(lambda _, p=closed_knot_path: self.on_sample_button_clicked(p))
        samples_layout.addWidget(self.sample_button_closed_knot)
        self.sample_buttons.append(self.sample_button_closed_knot)

        # Box Stitch
        self.sample_button_box_stitch = QPushButton(_['sample_box_stitch'] if 'sample_box_stitch' in _ else 'Box Stitch')
        box_stitch_path = os.path.join(samples_dir, 'box_stitch.json')
        self.sample_button_box_stitch.clicked.connect(lambda _, p=box_stitch_path: self.on_sample_button_clicked(p))
        samples_layout.addWidget(self.sample_button_box_stitch)
        self.sample_buttons.append(self.sample_button_box_stitch)

        # Overhand Knot
        self.sample_button_overhand_knot = QPushButton(_['sample_overhand_knot'] if 'sample_overhand_knot' in _ else 'Overhand Knot')
        overhand_knot_path = os.path.join(samples_dir, 'overhand_knot.json')
        self.sample_button_overhand_knot.clicked.connect(lambda _, p=overhand_knot_path: self.on_sample_button_clicked(p))
        samples_layout.addWidget(self.sample_button_overhand_knot)
        self.sample_buttons.append(self.sample_button_overhand_knot)

        # Three-Strand Braid
        self.sample_button_three_strand_braid = QPushButton(
            _['sample_three_strand_braid'] if 'sample_three_strand_braid' in _ else 'Three-Strand Braid'
        )
        three_strand_braid_path = os.path.join(samples_dir, 'three_strand_braid.json')
        self.sample_button_three_strand_braid.clicked.connect(
            lambda _, p=three_strand_braid_path: self.on_sample_button_clicked(p)
        )
        samples_layout.addWidget(self.sample_button_three_strand_braid)
        self.sample_buttons.append(self.sample_button_three_strand_braid)

        # Interwoven Double Closed Knot
        self.sample_button_interwoven_double_closed_knot = QPushButton(
            _['sample_interwoven_double_closed_knot'] if 'sample_interwoven_double_closed_knot' in _ else 'Interwoven Double Closed Knot'
        )
        interwoven_double_closed_knot_path = os.path.join(samples_dir, 'Interwoven_double_closed_knot.json')
        self.sample_button_interwoven_double_closed_knot.clicked.connect(
            lambda _, p=interwoven_double_closed_knot_path: self.on_sample_button_clicked(p)
        )
        samples_layout.addWidget(self.sample_button_interwoven_double_closed_knot)
        self.sample_buttons.append(self.sample_button_interwoven_double_closed_knot)

        samples_layout.addStretch()
        self.stacked_widget.addWidget(self.samples_widget)


        # About Page (index 5) - LAST
        self.about_widget = QWidget()
        about_layout = QVBoxLayout(self.about_widget)

        # Use QTextBrowser to display rich text with links
        self.about_text_browser = QTextBrowser()
        self.about_text_browser.setHtml(_['about_info'])
        self.about_text_browser.setOpenExternalLinks(True)  # Enable clicking on links

        about_layout.addWidget(self.about_text_browser)
        self.stacked_widget.addWidget(self.about_widget)

        # Ensure consistent sizes for all pages
        self.general_settings_widget.setMinimumWidth(550)  # Set minimum width for content
        self.change_language_widget.setMinimumWidth(550)
        self.tutorial_widget.setMinimumWidth(550)
        self.button_explanations_widget.setMinimumWidth(550)  # Add min width for button explanations
        self.history_widget.setMinimumWidth(550)
        self.whats_new_widget.setMinimumWidth(550) # Set min width for new page
        self.about_widget.setMinimumWidth(550)
        self.samples_widget.setMinimumWidth(550)

        # Add widgets to main layout with proper spacing
        main_layout.addWidget(self.categories_list)
        main_layout.addWidget(self.stacked_widget)

        # Prevent dialog from being resizable
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMinimizeButtonHint)

        # Set default category
        self.categories_list.setCurrentRow(0)
        self.stacked_widget.setCurrentIndex(0)
  
        # Style the buttons consistently
        self.style_dialog_buttons()

    def style_dialog_buttons(self):
        """Apply consistent styling to all buttons in the dialog"""
        buttons = [
            self.apply_button,
            self.language_ok_button,
            self.layer_panel_ok_button,  # Add the missing layer panel OK button
            *self.video_buttons,  # Unpack video buttons list
            self.load_history_button, # Style history buttons
            self.clear_history_button,
            self.default_strand_width_button,  # ensure this specific button is included
            self.reset_curvature_button  # Add the reset curvature button
        ]
        # Include sample buttons if present
        if hasattr(self, 'sample_buttons'):
            buttons.extend(self.sample_buttons)
        
        for button in buttons:
            button.setFixedHeight(32)  # Match MainWindow button height
            button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            # Dynamically set minimum width based on the button text length
            # Use boundingRect for more accurate width and add generous padding (20 px each side)
            fm = button.fontMetrics()
            text_rect = fm.boundingRect(button.text())
            calculated_width = text_rect.width() + 40  # 40 px total padding

            # Special-case: "Default Strand Width" button uses dynamic sizing based on translated text
            if button is self.default_strand_width_button:
                # Use the dedicated dynamic sizing method for this button
                self.update_default_strand_width_button_size()
            else:
                # Ensure a sensible lower bound (120) while allowing wider texts to fit
                button.setMinimumWidth(max(120, calculated_width))

            # Force Qt to recalculate the size hint after updating the minimum width
            button.updateGeometry()
            button.adjustSize()
            # Don't override colors - let the theme stylesheet handle colors
            # Only ensure consistent size and basic properties

    def setup_custom_checkmark(self, checkbox):
        """Setup custom checkmark for the checkbox using Qt's native indicator"""
        # Create a custom paintEvent for the checkbox to draw checkmark
        original_paintEvent = checkbox.paintEvent
        
        def custom_paintEvent(event):
            # Call the original paint event first
            original_paintEvent(event)
            
            # If checked, draw a custom checkmark
            if checkbox.isChecked():
                painter = QPainter(checkbox)
                painter.setRenderHint(QPainter.Antialiasing)
                
                # Calculate the exact position of the checkbox indicator
                # Get the checkbox style option to find the actual indicator position
                checkbox_rect = checkbox.rect()
                is_rtl = self.is_rtl_language(self.current_language)
                
                # Use Qt's style system to get the ACTUAL indicator position
                # This will work regardless of the checkbox's specific layout direction settings
                style_option = QStyleOptionButton()
                checkbox.initStyleOption(style_option)
                
                # Get the actual indicator rectangle from Qt's style system
                style = checkbox.style()
                indicator_rect_from_style = style.subElementRect(
                    style.SE_CheckBoxIndicator, style_option, checkbox
                )
                
                # Use the actual indicator position and size from Qt's calculations
                indicator_x = indicator_rect_from_style.x()
                indicator_y = indicator_rect_from_style.y()
                indicator_width = indicator_rect_from_style.width()
                indicator_height = indicator_rect_from_style.height()
                

                
                # Use the actual indicator rectangle from Qt
                indicator_rect = QRect(indicator_x, indicator_y, indicator_width, indicator_height)
                
                # Set pen for white checkmark with proper thickness
                pen = QPen(QColor(255, 255, 255), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.setPen(pen)
                
                # Calculate perfectly centered checkmark coordinates using actual indicator size
                center_x = indicator_rect.x() + indicator_rect.width() // 2
                center_y = indicator_rect.y() + indicator_rect.height() // 2
                
                # Make checkmark proportional to actual indicator size (40% of size - 20% smaller than before)
                checkmark_size = min(indicator_rect.width(), indicator_rect.height()) * 0.24  # 24% radius = 48% total (20% smaller than 60%)
                checkmark_size = int(checkmark_size)
                
                # Left stroke of the checkmark (shorter diagonal line)
                x1, y1 = center_x - checkmark_size + 1, center_y - 1
                x2, y2 = center_x - 1, center_y + checkmark_size - 1
                
                # Right stroke of the checkmark (longer diagonal line)  
                x3, y3 = center_x + checkmark_size, center_y - checkmark_size + 1
                
                # Draw the checkmark lines with precise positioning
                painter.drawLine(x1, y1, x2, y2)
                painter.drawLine(x2, y2, x3, y3)
                
                painter.end()
        
        # Replace the paintEvent method
        checkbox.paintEvent = custom_paintEvent

    def apply_checkbox_style(self):
        """Apply checkbox styling based on current theme with improved checkmark visibility"""
        
        if self.current_theme == 'dark':
            checkbox_style = """
                QCheckBox {
                    spacing: 5px;
                    font-size: 14px;
                    color: #ffffff;
                }
                QCheckBox::indicator {
                    width: 22px;
                    height: 22px;
                    border: 2px solid #666666;
                    border-radius: 3px;
                    background-color: #2d2d2d;
                }
                QCheckBox::indicator:hover {
                    border-color: #888888;
                    background-color: #3d3d3d;
                }
                QCheckBox::indicator:checked {
                    border-color: #28a745;
                    background-color: #28a745;
                }
                QCheckBox::indicator:checked:hover {
                    background-color: #218838;
                }
            """
        else:
            checkbox_style = """
                QCheckBox {
                    spacing: 5px;
                    font-size: 14px;
                    color: #000000;
                }
                QCheckBox::indicator {
                    width: 22px;
                    height: 22px;
                    border: 2px solid #cccccc;
                    border-radius: 3px;
                    background-color: white;
                }
                QCheckBox::indicator:hover {
                    border-color: #999999;
                    background-color: #f5f5f5;
                }
                QCheckBox::indicator:checked {
                    border-color: #28a745;
                    background-color: #28a745;
                }
                QCheckBox::indicator:checked:hover {
                    background-color: #218838;
                }
            """
        
        # Find and style all checkboxes in the dialog (including layer panel section)
        all_checkboxes = self.findChildren(QCheckBox)
        
        for checkbox in all_checkboxes:
            checkbox.setStyleSheet(checkbox_style)
            # Setup custom checkmark for each checkbox
            self.setup_custom_checkmark(checkbox)
            
            # Set proper layout direction for checkbox based on language
            # Special handling for default_arrow_color_checkbox which has its own layout logic
            if hasattr(self, 'default_arrow_color_checkbox') and checkbox == self.default_arrow_color_checkbox:
                # This checkbox has special RTL handling elsewhere - don't override it here
                pass
            else:
                # Apply standard RTL/LTR layout for other checkboxes
                if self.is_rtl_language(self.current_language):
                    checkbox.setLayoutDirection(Qt.RightToLeft)
                else:
                    checkbox.setLayoutDirection(Qt.LeftToRight)
            
            # Force update to ensure styling is applied
            checkbox.update()

    def apply_dialog_theme(self, theme_name):
        """Apply theme to dialog components"""
        # Update current theme for dropdown arrow colors
        self.current_theme = theme_name
        is_rtl = self.is_rtl_language(self.current_language)
        dropdown_arrow_css = self.get_dropdown_arrow_css(is_rtl)
        
        # Apply checkbox styling for current theme
        self.apply_checkbox_style()
        
        # Schedule a delayed checkbox styling to catch any dynamically created checkboxes
        QTimer.singleShot(100, self.apply_checkbox_style)
        
        if theme_name == "dark":
            button_style = f"""
                /* Main dialog background */
                QDialog {{
                    background-color: #2C2C2C;
                    color: white;
                }}
                
                /* Buttons */
                QPushButton {{
                    background-color: #3D3D3D;
                    color: white;
                    border: 1px solid #505050;
                    padding: 8px 16px;
                    border-radius: 4px;
                    height: 32px;
                    min-width: 120px;
                }}
                QPushButton:hover {{
                    background-color: #4D4D4D;
                }}
                QPushButton:pressed {{
                    background-color: #2D2D2D;
                }}
                QPushButton:checked {{
                    background-color: #505050;
                    border: 2px solid #808080;
                }}
                
                /* ComboBox */
                QComboBox {{
                    background-color: #3D3D3D;
                    color: white;
                    border: 1px solid #505050;
                    padding: 8px;
                    border-radius: 4px;
                    min-width: 100px;
                    {"padding-left: 24px; padding-right: 8px;" if is_rtl else "padding-left: 8px; padding-right: 24px;"}
                }}
                {dropdown_arrow_css}
                QComboBox QAbstractItemView {{
                    background-color: #3D3D3D;
                    color: white;
                    selection-background-color: #505050;
                    selection-color: white;
                    border: 1px solid #505050;
                    padding: 4px;
                }}
                QComboBox QAbstractItemView::item {{
                    padding: 4px 8px;
                    min-height: 48px;
                    border: none;
                    text-align: left;
                }}
                QComboBox::item {{
                    padding: 4px 8px;
                    min-height: 48px;
                    text-align: left;
                }}
                
                /* List Widget */
                QListWidget {{
                    background-color: #3D3D3D;
                    color: white;
                    border: 1px solid #505050;
                    border-radius: 4px;
                }}
                QListWidget::item {{
                    padding: 8px;
                }}
                QListWidget::item:selected {{
                    background-color: #505050;
                    color: white;
                }}
                QListWidget::item:hover {{
                    background-color: #4D4D4D;
                }}
                
                /* Labels */
                QLabel {{
                    color: white;
                }}
                
                /* Text Browser */
                QTextBrowser {{
                    background-color: #3D3D3D;
                    color: white;
                    border: 1px solid #505050;
                    border-radius: 4px;
                    padding: 8px;
                }}
                
                /* Scroll Bars */
                QScrollBar:vertical {{
                    background-color: #2C2C2C;
                    width: 12px;
                    border-radius: 6px;
                }}
                QScrollBar::handle:vertical {{
                    background-color: #505050;
                    border-radius: 6px;
                    min-height: 20px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background-color: #606060;
                }}
                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical {{
                    height: 0px;
                }}
                QScrollBar::add-page:vertical,
                QScrollBar::sub-page:vertical {{
                    background-color: #2C2C2C;
                }}
                
                /* Horizontal Scroll Bar */
                QScrollBar:horizontal {{
                    background-color: #2C2C2C;
                    height: 12px;
                    border-radius: 6px;
                }}
                QScrollBar::handle:horizontal {{
                    background-color: #505050;
                    border-radius: 6px;
                    min-width: 20px;
                }}
                QScrollBar::handle:horizontal:hover {{
                    background-color: #606060;
                }}
                QScrollBar::add-line:horizontal,
                QScrollBar::sub-line:horizontal {{
                    width: 0px;
                }}
                QScrollBar::add-page:horizontal,
                QScrollBar::sub-page:horizontal {{
                    background-color: #2C2C2C;
                }}
                
                /* Widgets */
                QWidget {{
                    background-color: #2C2C2C;
                    color: white;
                }}
                
                /* Stacked Widget */
                QStackedWidget {{
                    background-color: #2C2C2C;
                    color: white;
                }}
            """
        elif theme_name == "light":
            button_style = f"""
                QPushButton {{
                    background-color: #F0F0F0;
                    color: black;
                    border: 1px solid #CCCCCC;
                    padding: 8px 16px;
                    border-radius: 4px;
                    height: 32px;
                    min-width: 120px;
                }}
                QPushButton:hover {{
                    background-color: #E0E0E0;
                }}
                QPushButton:pressed {{
                    background-color: #D0D0D0;
                }}
                QPushButton:checked {{
                    background-color: #E0E0E0;
                    border: 2px solid #A0A0A0;
                }}
                QComboBox {{
                    background-color: white;
                    color: black;
                    border: 1px solid #CCCCCC;
                    padding: 8px;
                    border-radius: 4px;
                    min-width: 100px;
                    {"padding-left: 24px; padding-right: 8px;" if is_rtl else "padding-left: 8px; padding-right: 24px;"}
                }}
                {dropdown_arrow_css}
                QListWidget {{
                    background-color: white;
                    color: black;
                    border: 1px solid #CCCCCC;
                }}
                QLabel {{
                    color: black;
                }}
                QTextBrowser {{
                    background-color: white;
                    color: black;
                    border: 1px solid #CCCCCC;
                }}
            """
        else:  # default theme
            button_style = f"""
                QPushButton {{
                    background-color: #E8E8E8;
                    color: black;
                    border: 1px solid #CCCCCC;
                    padding: 8px 16px;
                    border-radius: 4px;
                    height: 32px;
                    min-width: 120px;
                }}
                QPushButton:hover {{
                    background-color: #DADADA;
                }}
                QPushButton:pressed {{
                    background-color: #C8C8C8;
                }}
                QPushButton:checked {{
                    background-color: #D0D0D0;
                    border: 2px solid #A0A0A0;
                }}
                QComboBox {{
                    background-color: #F5F5F5;
                    color: black;
                    border: 1px solid #CCCCCC;
                    padding: 8px;
                    border-radius: 4px;
                    min-width: 100px;
                    {"padding-left: 24px; padding-right: 8px;" if is_rtl else "padding-left: 8px; padding-right: 24px;"}
                }}
                {dropdown_arrow_css}
                QListWidget {{
                    background-color: #F5F5F5;
                    color: black;
                    border: 1px solid #CCCCCC;
                }}
                QLabel {{
                    color: black;
                }}
                QTextBrowser {{
                    background-color: #F5F5F5;
                    color: black;
                    border: 1px solid #CCCCCC;
                }}
            """

        self.setStyleSheet(button_style)
        self.style_dialog_buttons()

    def refresh_button_explanations_html(self):
        """Refresh the button explanations HTML with current theme colors"""
        _ = translations[self.current_language]
        
        # Determine title color based on theme
        title_color = '#333'  # Default for light theme
        if self.current_theme == 'dark':
            title_color = '#ffffff'  # White for dark theme
        elif self.current_theme == 'light':
            title_color = '#000000'  # Black for light theme
            
        button_html = f'''
        <style>
            body {{ font-family: Arial, sans-serif; padding: 10px; }}
            h2 {{ color: {title_color}; margin-top: 15px; margin-bottom: 10px; }}
            ul {{ margin-top: 5px; margin-bottom: 15px; }}
            li {{ margin-bottom: 8px; }}
            .button-name {{ font-weight: bold; }}
        </style>
        
        <h2>{_['layer_panel_buttons']}</h2>
        <ul>
            <li><span class="button-name">{_['draw_names_desc'].split(' - ')[0]}</span> - {_['draw_names_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['lock_layers_desc'].split(' - ')[0]}</span> - {_['lock_layers_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['add_new_strand_desc'].split(' - ')[0]}</span> - {_['add_new_strand_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['delete_strand_desc'].split(' - ')[0]}</span> - {_['delete_strand_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['deselect_all_desc'].split(' - ')[0]}</span> - {_['deselect_all_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['pan_desc'].split(' - ')[0]}</span> - {_['pan_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['zoom_in_desc'].split(' - ')[0]}</span> - {_['zoom_in_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['zoom_out_desc'].split(' - ')[0]}</span> - {_['zoom_out_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['center_strands_desc'].split(' - ')[0]}</span> - {_['center_strands_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['multi_select_desc'].split(' - ')[0]}</span> - {_['multi_select_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['refresh_desc'].split(' - ')[0]}</span> - {_['refresh_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['reset_states_desc'].split(' - ')[0]}</span> - {_['reset_states_desc'].split(' - ')[1]}</li>
        </ul>
        
        <h2>{_['main_window_buttons']}</h2>
        <ul>
            <li><span class="button-name">{_['attach_mode_desc'].split(' - ')[0]}</span> - {_['attach_mode_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['move_mode_desc'].split(' - ')[0]}</span> - {_['move_mode_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['rotate_mode_desc'].split(' - ')[0]}</span> - {_['rotate_mode_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['toggle_grid_desc'].split(' - ')[0]}</span> - {_['toggle_grid_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['angle_adjust_desc'].split(' - ')[0]}</span> - {_['angle_adjust_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['save_desc'].split(' - ')[0]}</span> - {_['save_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['load_desc'].split(' - ')[0]}</span> - {_['load_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['save_image_desc'].split(' - ')[0]}</span> - {_['save_image_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['select_strand_desc'].split(' - ')[0]}</span> - {_['select_strand_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['mask_mode_desc'].split(' - ')[0]}</span> - {_['mask_mode_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['settings_desc'].split(' - ')[0]}</span> - {_['settings_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['toggle_control_points_desc'].split(' - ')[0]}</span> - {_['toggle_control_points_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['toggle_shadow_desc'].split(' - ')[0]}</span> - {_['toggle_shadow_desc'].split(' - ')[1]}</li>
        </ul>
        
        <h2>{_['group_buttons']}</h2>
        <ul>
            <li><span class="button-name">{_['create_group_desc'].split(' - ')[0]}</span> - {_['create_group_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['group_header_desc'].split(' - ')[0]}</span> - {_['group_header_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['select_group_desc'].split(' - ')[0]}</span> - {_['select_group_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['move_group_desc'].split(' - ')[0]}</span> - {_['move_group_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['rotate_group_desc'].split(' - ')[0]}</span> - {_['rotate_group_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['edit_strand_angles_desc'].split(' - ')[0]}</span> - {_['edit_strand_angles_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['duplicate_group_desc'].split(' - ')[0]}</span> - {_['duplicate_group_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['rename_group_desc'].split(' - ')[0]}</span> - {_['rename_group_desc'].split(' - ')[1]}</li>
            <li><span class="button-name">{_['delete_group_desc'].split(' - ')[0]}</span> - {_['delete_group_desc'].split(' - ')[1]}</li>
        </ul>
        '''
        
        self.button_explanations_text_browser.setHtml(button_html)
    
    def apply_all_settings(self):
        # Capture previous extended mask setting to detect changes
        # previous_use_extended_mask = self.use_extended_mask
        # Apply Theme Settings
        selected_theme = self.theme_combobox.currentData()
        if selected_theme and self.canvas:
            self.canvas.set_theme(selected_theme)
            self.canvas.update()

        # Store the selected theme
        self.current_theme = selected_theme

        # Emit signal to notify main window of theme change
        self.theme_changed.emit(selected_theme)
        
        # Update button explanations HTML with new theme colors
        if hasattr(self, 'button_explanations_text_browser'):
            self.refresh_button_explanations_html()
        
        # Apply Shadow Color Settings
        if self.canvas:
            # Use the new set_shadow_color method to update all strands
            self.canvas.set_shadow_color(self.shadow_color)
            self.canvas.update()
            # Store the shadow color in the main window
            if hasattr(self.parent_window, 'canvas'):
                self.parent_window.canvas.default_shadow_color = self.shadow_color

        # Apply Performance Settings
        self.draw_only_affected_strand = self.affected_strand_checkbox.isChecked()
        if self.canvas:
            # Set for all modes that support draw_only_affected_strand
            if hasattr(self.canvas, 'move_mode'):
                self.canvas.move_mode.draw_only_affected_strand = self.draw_only_affected_strand
            if hasattr(self.canvas, 'rotate_mode'):
                self.canvas.rotate_mode.draw_only_affected_strand = self.draw_only_affected_strand
            if hasattr(self.canvas, 'angle_adjust_mode'):
                self.canvas.angle_adjust_mode.draw_only_affected_strand = self.draw_only_affected_strand

        # Apply Third Control Point Setting
        # Store previous setting to check if it changed
        previous_third_control_point = self.enable_third_control_point
        # Get new setting from checkbox
        self.enable_third_control_point = self.third_control_checkbox.isChecked()
        
        if self.canvas:
            # Set the new value in canvas
            self.canvas.enable_third_control_point = self.enable_third_control_point
            
            # Check if the setting changed
            if previous_third_control_point != self.enable_third_control_point:
                pass

        # Apply Curvature Bias Control Setting
        self.enable_curvature_bias_control = self.curvature_bias_checkbox.isChecked()
        if self.canvas:
            # Set the new value in canvas
            self.canvas.enable_curvature_bias_control = self.enable_curvature_bias_control
        
        # Apply Snap to Grid Setting
        self.snap_to_grid_enabled = self.snap_to_grid_checkbox.isChecked()
        
        if self.canvas:
            # Set the new value in canvas
            self.canvas.snap_to_grid_enabled = self.snap_to_grid_enabled
        
        # Apply Show Move Highlights Setting
        self.show_move_highlights = self.show_highlights_checkbox.isChecked()
        
        if self.canvas:
            # Set the new value in canvas
            self.canvas.show_move_highlights = self.show_move_highlights

            # Check if the third control point setting changed
            if previous_third_control_point != self.enable_third_control_point:
                # Reset all masked strands if the canvas has strands
                if hasattr(self.canvas, 'strands'):
                    for i, strand in enumerate(self.canvas.strands):
                        # Check if this is a masked strand
                        if hasattr(strand, '__class__') and strand.__class__.__name__ == 'MaskedStrand':
                            # Call the canvas's reset_mask method - this is the same one called
                            # when right-clicking on a layer in the layer panel
                            self.canvas.reset_mask(i)
                
                # Force redraw to show/hide third control point and reset masks
                self.canvas.update()
                
                # Force a full refresh of the canvas 
                if hasattr(self.canvas, 'force_redraw'):
                    self.canvas.force_redraw()

        # Apply Shadow Blur Settings
        self.num_steps = self.num_steps_spinbox.value()
        self.max_blur_radius = self.blur_radius_spinbox.value()
        if self.canvas:
            self.canvas.num_steps = self.num_steps
            self.canvas.max_blur_radius = self.max_blur_radius
            
        # Apply Control Point Influence Settings
        base_fraction_value = self.base_fraction_spinbox.value()
        distance_mult_value = self.distance_mult_spinbox.value()
        curve_response_value = self.curve_response_spinbox.value()
        
        if self.canvas:
            # Update canvas curvature values
            self.canvas.control_point_base_fraction = base_fraction_value
            self.canvas.distance_multiplier = distance_mult_value
            self.canvas.curve_response_exponent = curve_response_value
            
            # Update all strands with new curvature values
            for strand in self.canvas.strands:
                strand.control_point_base_fraction = base_fraction_value
                strand.distance_multiplier = distance_mult_value
                strand.curve_response_exponent = curve_response_value
            
            # Use the refresh button functionality to update everything properly
            if hasattr(self.layer_panel, 'simulate_refresh_button_click'):
                # This preserves zoom and properly updates everything
                self.layer_panel.simulate_refresh_button_click()
            elif hasattr(self.canvas, 'refresh_canvas'):
                # Fallback to direct canvas refresh
                self.canvas.refresh_canvas()
            else:
                # Final fallback
                self.canvas.update()

        # Apply Extension Line Settings
        self.extension_length = self.extension_length_spinbox.value()
        self.extension_dash_count = self.extension_dash_count_spinbox.value()
        self.extension_dash_width = self.extension_dash_width_spinbox.value()
        self.extension_dash_gap_length = self.extension_dash_gap_length_spinbox.value()
        # --- NEW: Arrow head settings ---
        self.arrow_head_length = self.arrow_head_length_spinbox.value()
        self.arrow_head_width = self.arrow_head_width_spinbox.value()
        self.arrow_head_stroke_width = self.arrow_head_stroke_width_spinbox.value()
        # --- NEW: Arrow shaft settings ---
        self.arrow_gap_length = self.arrow_gap_length_spinbox.value()
        self.arrow_line_length = self.arrow_line_length_spinbox.value()
        self.arrow_line_width = self.arrow_line_width_spinbox.value()
        # --- END NEW ---
        if self.canvas:
            self.canvas.extension_length = self.extension_length
            self.canvas.extension_dash_count = self.extension_dash_count
            self.canvas.extension_dash_width = self.extension_dash_width
            self.canvas.extension_dash_gap_length = self.extension_dash_gap_length
            # --- NEW: apply arrow settings to canvas ---
            self.canvas.arrow_head_length = self.arrow_head_length
            self.canvas.arrow_head_width = self.arrow_head_width
            self.canvas.arrow_head_stroke_width = self.arrow_head_stroke_width
            self.canvas.arrow_gap_length = self.arrow_gap_length
            self.canvas.arrow_line_length = self.arrow_line_length
            self.canvas.arrow_line_width = self.arrow_line_width
            # --- END NEW ---
            # Apply default strand width settings
            self.canvas.strand_width = self.default_strand_width
            self.canvas.stroke_width = self.default_stroke_width

        # Apply Language Settings
        language_code = self.language_combobox.currentData()
        previous_language = self.current_language
        
        # Update the language in the main window
        self.parent_window.set_language(language_code)
        # Store the selected language
        self.current_language = language_code
        
        # Update the canvas language code and emit the signal
        if self.canvas:
            self.canvas.language_code = language_code
            self.canvas.language_changed.emit()
        else:
            # Emit language_changed signal from the parent window
            self.parent_window.language_changed.emit()
        
        # If language has changed, update translations in the dialog
        if previous_language != language_code:
            self.update_translations()
            # Update layout direction immediately after language change
            self.update_layout_direction()
            # Force redraw of language-specific elements
            self.repaint()
        
        # Apply Layer Panel Settings
        if self.canvas and hasattr(self.canvas, 'layer_panel'):
            panel = self.canvas.layer_panel

        # Apply Default Arrow Color Setting
        self.use_default_arrow_color = self.default_arrow_color_checkbox.isChecked()
        if self.canvas:
            self.canvas.use_default_arrow_color = self.use_default_arrow_color
            self.canvas.default_arrow_fill_color = self.default_arrow_fill_color
            # Force redraw to update arrow colors
            if hasattr(self.canvas, 'force_redraw'):
                self.canvas.force_redraw()
            self.canvas.update()

        # Apply Extended Mask Setting before saving
        # self.use_extended_mask = self.extended_mask_checkbox.isChecked()
        # if self.canvas:
        #     self.canvas.use_extended_mask = self.use_extended_mask

        # Save all settings to file (after updating all values including extended mask)
        self.save_settings_to_file()

        # Apply the theme to the dialog before hiding
        self.apply_dialog_theme(self.current_theme)
        self.hide()

        # If extended mask setting changed, force redraw of masked strands
        # if previous_use_extended_mask != self.use_extended_mask:
        #     logging.info(f"SettingsDialog: Use extended mask changed to {self.use_extended_mask}. Forcing redraw of masked strands")
        #     if self.canvas and hasattr(self.canvas, 'strands'):
        #         for strand in self.canvas.strands:
        #             if getattr(strand, '__class__', None) and strand.__class__.__name__ == 'MaskedStrand':
                        # No need to reset mask, just force shadow update to refresh +3 offset
                        #if hasattr(strand, 'force_shadow_update'):
                            #strand.force_shadow_update()
        if self.canvas:
            self.canvas.update()

    def update_attached_strands_curvature(self, strand, base_fraction, distance_mult, curve_response):
        """Recursively update curvature settings for all attached strands."""
        if hasattr(strand, 'attached_strands'):
            for attached in strand.attached_strands:
                attached.control_point_base_fraction = base_fraction
                attached.distance_multiplier = distance_mult
                attached.curve_response_exponent = curve_response
                
                # Force updating_position to False
                if hasattr(attached, 'updating_position'):
                    attached.updating_position = False
                
                # Notify Qt that the geometry is about to change
                if hasattr(attached, 'prepareGeometryChange'):
                    attached.prepareGeometryChange()
                
                # Update the shape to recalculate control points with new curvature
                if hasattr(attached, 'update_shape'):
                    attached.update_shape()
                
                # Use force_path_update if available
                if hasattr(attached, 'force_path_update'):
                    attached.force_path_update()
                else:
                    # Fallback: invalidate cached path
                    try:
                        if hasattr(attached, '_path'):
                            delattr(attached, '_path')
                    except AttributeError:
                        pass  # Attribute was removed between check and delete
                
                # Force path recalculation by invalidating boundingRect cache if it exists
                try:
                    if hasattr(attached, '_bounding_rect_cache'):
                        delattr(attached, '_bounding_rect_cache')
                except AttributeError:
                    pass  # Attribute was removed between check and delete
                
                # Recursively update any strands attached to this attached strand
                self.update_attached_strands_curvature(attached, base_fraction, distance_mult, curve_response)

    def change_category(self, item):
        index = self.categories_list.row(item)
        self.stacked_widget.setCurrentIndex(index)

    def update_translations(self):
        _ = translations[self.current_language]
        self.setWindowTitle(_['settings'])
        # Update category names
        self.categories_list.item(0).setText(_['general_settings'])
        self.categories_list.item(1).setText(_['layer_panel_title'])
        self.categories_list.item(2).setText(_['change_language'])
        self.categories_list.item(3).setText(_['tutorial'])
        self.categories_list.item(4).setText(_['button_explanations']) # Update button guide category name
        self.categories_list.item(5).setText(_['history']) # Update history category name
        self.categories_list.item(6).setText(_['whats_new']) # Update what's new category name
        self.categories_list.item(7).setText(_['samples'] if 'samples' in _ else 'Samples')
        self.categories_list.item(8).setText(_['about']) # About remains last
        # Update labels and buttons
        self.theme_label.setText(_['select_theme'])
        self.shadow_color_label.setText(_['shadow_color'] if 'shadow_color' in _ else "Shadow Color")
        self.affected_strand_label.setText(_['draw_only_affected_strand'] if 'draw_only_affected_strand' in _ else "Draw only affected strand when dragging")
        self.third_control_label.setText(_['enable_third_control_point'] if 'enable_third_control_point' in _ else "Enable third control point at center")
        self.curvature_bias_label.setText(_['enable_curvature_bias_control'] if 'enable_curvature_bias_control' in _ else "Enable curvature bias controls")
        self.snap_to_grid_label.setText(_['enable_snap_to_grid'] if 'enable_snap_to_grid' in _ else "Enable snap to grid")
        self.show_highlights_label.setText(_['show_move_highlights'] if 'show_move_highlights' in _ else "Show highlights in move modes")
        # self.extended_mask_label.setText(_['use_extended_mask'] if 'use_extended_mask' in _ else "Use extended mask (wider overlap)")
        self.num_steps_label.setText(_['shadow_blur_steps'] if 'shadow_blur_steps' in _ else "Shadow Blur Steps:")
        self.blur_radius_label.setText(_['shadow_blur_radius'] if 'shadow_blur_radius' in _ else "Shadow Blur Radius:")
        self.base_fraction_label.setText(_['base_fraction'] if 'base_fraction' in _ else "Control Point Influence:")
        self.distance_mult_label.setText(_['distance_multiplier'] if 'distance_multiplier' in _ else "Distance Boost:")
        self.curve_response_label.setText(_['curve_response'] if 'curve_response' in _ else "Curve Type:")
        self.reset_curvature_label.setText(_['reset_curvature_settings'] if 'reset_curvature_settings' in _ else "Reset Curvature Settings:")
        self.reset_curvature_button.setText(_['reset'] if 'reset' in _ else "Reset")
        self.reset_curvature_button.setToolTip(_['reset_curvature_tooltip'] if 'reset_curvature_tooltip' in _ else "Reset all curvature settings to default values")
        self.apply_button.setText(_['ok'])
        self.language_ok_button.setText(_['ok'])
        self.layer_panel_ok_button.setText(_['ok'])
        self.language_label.setText(_['select_language'])
        # Update Layer Panel Settings labels for extension and arrow parameters
        self.extension_length_label.setText(_['extension_length'] if 'extension_length' in _ else "Extension Length")
        self.extension_dash_count_label.setText(_['extension_dash_count'] if 'extension_dash_count' in _ else "Dash Count")
        self.extension_dash_width_label.setText(_['extension_dash_width'] if 'extension_dash_width' in _ else "Extension Dash Width")
        self.extension_dash_gap_length_label.setText(_['extension_dash_gap_length'] if 'extension_dash_gap_length' in _ else "Gap length between strand end and start of dashes")
        self.extension_dash_gap_length_spinbox.setToolTip(_['extension_dash_gap_length_tooltip'] if 'extension_dash_gap_length_tooltip' in _ else "Gap between the strand end and the start of the dashes")
        self.arrow_head_length_label.setText(_['arrow_head_length'] if 'arrow_head_length' in _ else "Arrow Head Length")
        self.arrow_head_width_label.setText(_['arrow_head_width'] if 'arrow_head_width' in _ else "Arrow Head Width")
        self.arrow_head_stroke_width_label.setText(_['arrow_head_stroke_width'] if 'arrow_head_stroke_width' in _ else "Arrow Head Stroke Width")
        self.arrow_gap_length_label.setText(_['arrow_gap_length'] if 'arrow_gap_length' in _ else "Arrow Gap Length")
        self.arrow_line_length_label.setText(_['arrow_line_length'] if 'arrow_line_length' in _ else "Arrow Line Length")
        self.arrow_line_width_label.setText(_['arrow_line_width'] if 'arrow_line_width' in _ else "Arrow Line Width")
        # Update default arrow color label text
        if hasattr(self, 'default_arrow_color_label'):
            self.default_arrow_color_label.setText(_['use_default_arrow_color'] if 'use_default_arrow_color' in _ else "Use Default Arrow Color")
        self.button_color_label.setText(_['button_color'] if 'button_color' in _ else "Button Color:")
        if self.is_rtl_language(self.current_language):
            self.button_color_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.button_color_label.setLayoutDirection(Qt.RightToLeft)
        else:
            self.button_color_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.button_color_label.setLayoutDirection(Qt.LeftToRight)
        # Update default strand and stroke color labels
        self.default_strand_color_label.setText(_['default_strand_color'] if 'default_strand_color' in _ else "Default Strand Color:")
        if self.is_rtl_language(self.current_language):
            self.default_strand_color_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.default_strand_color_label.setLayoutDirection(Qt.RightToLeft)
        else:
            self.default_strand_color_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.default_strand_color_label.setLayoutDirection(Qt.LeftToRight)
        
        self.default_stroke_color_label.setText(_['default_stroke_color'] if 'default_stroke_color' in _ else "Default Stroke Color:")
        if self.is_rtl_language(self.current_language):
            self.default_stroke_color_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.default_stroke_color_label.setLayoutDirection(Qt.RightToLeft)
        else:
            self.default_stroke_color_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.default_stroke_color_label.setLayoutDirection(Qt.LeftToRight)
        
        # Update default strand width button
        self.default_strand_width_button.setText(_['default_strand_width'] if 'default_strand_width' in _ else "Default Strand Width")
        self.default_strand_width_button.setToolTip(_['default_strand_width_tooltip'] if 'default_strand_width_tooltip' in _ else "Configure default strand width")
        
        # Update all layer panel tooltips
        self.num_steps_spinbox.setToolTip(_['shadow_blur_steps_tooltip'] if 'shadow_blur_steps_tooltip' in _ else "Number of steps for the shadow fade effect")
        self.blur_radius_spinbox.setToolTip(_['shadow_blur_radius_tooltip'] if 'shadow_blur_radius_tooltip' in _ else "Shadow blur radius in pixels (range: 0.0 - 360.0)")
        self.extension_length_spinbox.setToolTip(_['extension_length_tooltip'] if 'extension_length_tooltip' in _ else "Length of extension lines")
        self.extension_dash_count_spinbox.setToolTip(_['extension_dash_count_tooltip'] if 'extension_dash_count_tooltip' in _ else "Number of dashes in extension line")
        self.extension_dash_width_spinbox.setToolTip(_['extension_dash_width_tooltip'] if 'extension_dash_width_tooltip' in _ else "Width of extension dashes")
        self.arrow_head_length_spinbox.setToolTip(_['arrow_head_length_tooltip'] if 'arrow_head_length_tooltip' in _ else "Length of arrow head in pixels")
        self.arrow_head_width_spinbox.setToolTip(_['arrow_head_width_tooltip'] if 'arrow_head_width_tooltip' in _ else "Width of arrow head base in pixels")
        self.arrow_head_stroke_width_spinbox.setToolTip(_['arrow_head_stroke_width_tooltip'] if 'arrow_head_stroke_width_tooltip' in _ else "Thickness of arrow head border in pixels")
        self.arrow_gap_length_spinbox.setToolTip(_['arrow_gap_length_tooltip'] if 'arrow_gap_length_tooltip' in _ else "Gap between strand end and arrow shaft start")
        self.arrow_line_length_spinbox.setToolTip(_['arrow_line_length_tooltip'] if 'arrow_line_length_tooltip' in _ else "Length of the arrow shaft")
        self.arrow_line_width_spinbox.setToolTip(_['arrow_line_width_tooltip'] if 'arrow_line_width_tooltip' in _ else "Thickness of the arrow shaft")
        
        # Update button size based on new translated text
        self.update_default_strand_width_button_size()
        
        # Update the layout to ensure proper spacing
        if hasattr(self, 'default_strand_width_layout'):
            self.default_strand_width_layout.update()
        # Also update the parent container if it exists
        if hasattr(self, 'default_strand_width_container'):
            self.default_strand_width_container.updateGeometry()
        
        # Update information labels
        self.language_info_label.setText(_['language_settings_info'])
        self.tutorial_label.setText(_['tutorial_info'])
        
        # Update button explanations page
        if hasattr(self, 'button_guide_label'):
            self.button_guide_label.setText(_['button_guide_info'])
            
        # Update the button explanations text browser content
        if hasattr(self, 'button_explanations_text_browser'):
            # Determine title color based on theme
            title_color = '#333'  # Default for light theme
            if self.current_theme == 'dark':
                title_color = '#ffffff'  # White for dark theme
            elif self.current_theme == 'light':
                title_color = '#000000'  # Black for light theme
                
            button_html = f'''
            <style>
                body {{ font-family: Arial, sans-serif; padding: 10px; }}
                h2 {{ color: {title_color}; margin-top: 15px; margin-bottom: 10px; }}
                ul {{ margin-top: 5px; margin-bottom: 15px; }}
                li {{ margin-bottom: 8px; }}
                .button-name {{ font-weight: bold; }}
            </style>
            
            <h2>{_['layer_panel_buttons']}</h2>
            <ul>
                <li><span class="button-name">{_['draw_names_desc'].split(' - ')[0]}</span> - {_['draw_names_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['lock_layers_desc'].split(' - ')[0]}</span> - {_['lock_layers_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['add_new_strand_desc'].split(' - ')[0]}</span> - {_['add_new_strand_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['delete_strand_desc'].split(' - ')[0]}</span> - {_['delete_strand_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['deselect_all_desc'].split(' - ')[0]}</span> - {_['deselect_all_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['pan_desc'].split(' - ')[0]}</span> - {_['pan_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['zoom_in_desc'].split(' - ')[0]}</span> - {_['zoom_in_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['zoom_out_desc'].split(' - ')[0]}</span> - {_['zoom_out_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['center_strands_desc'].split(' - ')[0]}</span> - {_['center_strands_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['multi_select_desc'].split(' - ')[0]}</span> - {_['multi_select_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['refresh_desc'].split(' - ')[0]}</span> - {_['refresh_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['reset_states_desc'].split(' - ')[0]}</span> - {_['reset_states_desc'].split(' - ')[1]}</li>
            </ul>
            
            <h2>{_['main_window_buttons']}</h2>
            <ul>
                <li><span class="button-name">{_['attach_mode_desc'].split(' - ')[0]}</span> - {_['attach_mode_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['move_mode_desc'].split(' - ')[0]}</span> - {_['move_mode_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['rotate_mode_desc'].split(' - ')[0]}</span> - {_['rotate_mode_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['toggle_grid_desc'].split(' - ')[0]}</span> - {_['toggle_grid_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['angle_adjust_desc'].split(' - ')[0]}</span> - {_['angle_adjust_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['save_desc'].split(' - ')[0]}</span> - {_['save_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['load_desc'].split(' - ')[0]}</span> - {_['load_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['save_image_desc'].split(' - ')[0]}</span> - {_['save_image_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['select_strand_desc'].split(' - ')[0]}</span> - {_['select_strand_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['mask_mode_desc'].split(' - ')[0]}</span> - {_['mask_mode_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['settings_desc'].split(' - ')[0]}</span> - {_['settings_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['toggle_control_points_desc'].split(' - ')[0]}</span> - {_['toggle_control_points_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['toggle_shadow_desc'].split(' - ')[0]}</span> - {_['toggle_shadow_desc'].split(' - ')[1]}</li>
            </ul>
            
            <h2>{_['group_buttons']}</h2>
            <ul>
                <li><span class="button-name">{_['create_group_desc'].split(' - ')[0]}</span> - {_['create_group_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['group_header_desc'].split(' - ')[0]}</span> - {_['group_header_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['select_group_desc'].split(' - ')[0]}</span> - {_['select_group_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['move_group_desc'].split(' - ')[0]}</span> - {_['move_group_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['rotate_group_desc'].split(' - ')[0]}</span> - {_['rotate_group_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['edit_strand_angles_desc'].split(' - ')[0]}</span> - {_['edit_strand_angles_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['duplicate_group_desc'].split(' - ')[0]}</span> - {_['duplicate_group_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['rename_group_desc'].split(' - ')[0]}</span> - {_['rename_group_desc'].split(' - ')[1]}</li>
                <li><span class="button-name">{_['delete_group_desc'].split(' - ')[0]}</span> - {_['delete_group_desc'].split(' - ')[1]}</li>
            </ul>
            '''
            self.button_explanations_text_browser.setHtml(button_html)
        # Update history page elements
        self.history_explanation_label.setText(_['history_explanation'])
        self.load_history_button.setText(_['load_selected_history'])
        self.clear_history_button.setText(_['clear_all_history'])
        self.history_list.setToolTip(_['history_list_tooltip'] if 'history_list_tooltip' in _ else "Select a session to load its final state")
        # Update What's New page elements
        self.whats_new_text_browser.setHtml(self.render_whats_new_html(_['whats_new_info']))
        # Update about text browser instead of label
        self.about_text_browser.setHtml(_['about_info'])
        
        # Update samples page labels
        if hasattr(self, 'samples_header_label'):
            self.samples_header_label.setText((_['samples_header'] if 'samples_header' in _ else 'Sample projects'))
            self.samples_header_label.setAlignment(Qt.AlignCenter)
        if hasattr(self, 'samples_sub_label'):
            self.samples_sub_label.setText((_['samples_sub'] if 'samples_sub' in _ else 'Choose a sample to load and learn from. The dialog will close and the sample will be loaded.'))
            self.samples_sub_label.setAlignment(Qt.AlignCenter)
        # Update theme combobox items
        self.theme_combobox.setItemText(0, _['default'])
        self.theme_combobox.setItemText(1, _['light'])
        self.theme_combobox.setItemText(2, _['dark'])
        
        # Update sample buttons' text
        if hasattr(self, 'sample_button_closed_knot'):
            self.sample_button_closed_knot.setText(_['sample_closed_knot'] if 'sample_closed_knot' in _ else 'Closed Knot')
        if hasattr(self, 'sample_button_box_stitch'):
            self.sample_button_box_stitch.setText(_['sample_box_stitch'] if 'sample_box_stitch' in _ else 'Box Stitch')
        if hasattr(self, 'sample_button_overhand_knot'):
            self.sample_button_overhand_knot.setText(_['sample_overhand_knot'] if 'sample_overhand_knot' in _ else 'Overhand Knot')
        if hasattr(self, 'sample_button_three_strand_braid'):
            self.sample_button_three_strand_braid.setText(
                _['sample_three_strand_braid'] if 'sample_three_strand_braid' in _ else 'Three-Strand Braid'
            )
        if hasattr(self, 'sample_button_interwoven_double_closed_knot'):
            self.sample_button_interwoven_double_closed_knot.setText(
                _['sample_interwoven_double_closed_knot'] if 'sample_interwoven_double_closed_knot' in _ else 'Interwoven Double Closed Knot'
            )
        
        # Completely rebuild the language combobox to ensure proper translation
        current_data = self.language_combobox.currentData()
        self.language_combobox.clear()
        
        # Re-add language items with properly translated names
        self.add_lang_item_en(_['english'], 'en')
        self.add_lang_item_fr(_['french'], 'fr')
        self.add_lang_item_de(_['german'], 'de')
        self.add_lang_item_it(_['italian'], 'it')
        self.add_lang_item_es(_['spanish'], 'es')
        self.add_lang_item_pt(_['portuguese'], 'pt')
        self.add_lang_item_he(_['hebrew'], 'he')
        
        # Restore the previously selected language
        index = self.language_combobox.findData(current_data)
        if index >= 0:
            self.language_combobox.setCurrentIndex(index)
        
        # Apply proper text alignment to both comboboxes after rebuild
        is_rtl = self.is_rtl_language(self.current_language)
        if is_rtl:
            # For RTL languages, align text to the right so it sits next to the icons
            self.set_combobox_text_alignment(self.theme_combobox, Qt.AlignRight | Qt.AlignVCenter)
            self.set_combobox_text_alignment(self.language_combobox, Qt.AlignRight | Qt.AlignVCenter)
        else:
            # For LTR languages, use left alignment
            self.set_combobox_text_alignment(self.theme_combobox, Qt.AlignLeft | Qt.AlignVCenter)
            self.set_combobox_text_alignment(self.language_combobox, Qt.AlignLeft | Qt.AlignVCenter)
        
        # For Hebrew, force refresh the combobox text display after rebuilding
        if self.is_rtl_language(self.current_language):
            # Force the combobox to update its text display for RTL after rebuild
            if index >= 0:
                # Force refresh by temporarily changing and restoring the current item
                self.language_combobox.setCurrentIndex(-1)
                self.language_combobox.setCurrentIndex(index)
                # Also force a repaint of the combobox
                self.language_combobox.update()
                self.language_combobox.repaint()
        
        # For Hebrew, use proper CSS styling instead of adding spaces to text
        if self.is_rtl_language(self.current_language):
            # Remove CSS that might interfere with layout - rely purely on layout reorganization
            pass
        else:
            # For LTR languages, ensure clean text without any added spaces
            # Reset theme combobox text to original translations
            self.theme_combobox.setItemText(0, _['default'])
            self.theme_combobox.setItemText(1, _['light'])
            self.theme_combobox.setItemText(2, _['dark'])
            
            # Reset language combobox text to original translations
            for lang_code in ['en', 'fr', 'it', 'es', 'pt', 'he']:
                lang_index = self.language_combobox.findData(lang_code)
                if lang_index >= 0:
                    lang_key = {'en': 'english', 'fr': 'french', 'it': 'italian', 
                               'es': 'spanish', 'pt': 'portuguese', 'he': 'hebrew'}[lang_code]
                    self.language_combobox.setItemText(lang_index, _[lang_key])

        # Update tutorial explanations and play buttons
        for i in range(4):  # Changed from 5 to 4
            index = i * 2  # Since each explanation and button are added sequentially
            explanation_label = self.tutorial_widget.layout().itemAt(index + 1).widget()
            explanation_label.setText(_[f'gif_explanation_{i+1}'])
            play_button = self.video_buttons[i]
            play_button.setText(_['play_video'])
            
        # Update layout direction based on current language
        self.update_layout_direction()
        
        # Update text alignment for RTL languages
        self.update_text_alignment()

        # Recompute button widths based on translated text to prevent truncation
        self.style_dialog_buttons()



    # New method to update text alignment based on language direction
    def update_text_alignment(self):
        # Set text alignment for all QLabel widgets based on language direction
        rtl = self.is_rtl_language(self.current_language)
        alignment = Qt.AlignRight | Qt.AlignVCenter if rtl else Qt.AlignLeft | Qt.AlignVCenter
        
        # Update alignment for all labels
        for widget in self.findChildren(QLabel):
            # Keep samples header/subtitle centered regardless of language direction
            if hasattr(self, 'samples_header_label') and widget is self.samples_header_label:
                widget.setAlignment(Qt.AlignCenter)
                continue
            if hasattr(self, 'samples_sub_label') and widget is self.samples_sub_label:
                widget.setAlignment(Qt.AlignCenter)
                continue
            # Skip labels within specific layouts where alignment might be handled differently
            # or where center alignment is intended (like category items)
            parent_layout = widget.parentWidget().layout() if widget.parentWidget() else None
            # Remove the check that skips icon labels
            # if parent_layout == self.icon_layout or parent_layout == self.third_cp_icon_layout:
            #      continue # Skip icon labels

            # Check if the label is a direct child of the main categories list widget item
            # This is a bit fragile, might need a better way to identify category labels if structure changes
            is_category_label = False
            if isinstance(widget.parentWidget(), QListWidgetItem):
                 is_category_label = True
            elif hasattr(widget.parentWidget(), 'parentWidget') and isinstance(widget.parentWidget().parentWidget(), QListWidgetItem):
                 is_category_label = True

            # Also skip the tutorial explanation labels which should follow document direction
            # Remove the check for tutorial explanation labels
            # if widget.objectName() and widget.objectName().startswith("tutorial_explanation_"): # Need to set object names
            #      continue # Skip tutorial explanations for now

            # Apply alignment unless it's a category label or explicitly skipped
            if not is_category_label:
                 # Remove special exception for shadow_color_label - treat it normally
                 widget.setAlignment(alignment)
   
        # For text browsers, set alignment through HTML if RTL
        if rtl:
            # Update text browsers with RTL direction
            for text_browser in self.findChildren(QTextBrowser):
                # Get current HTML content
                content = text_browser.toHtml()
                # Add dir="rtl" attribute if not already present
                if 'dir="rtl"' not in content:
                    content = content.replace('<html>', '<html dir="rtl">')
                    text_browser.setHtml(content)

    def save_settings_to_file(self):
        # Use the stored current theme and language
        current_theme = getattr(self, 'current_theme', 'default')
        current_language = getattr(self, 'current_language', 'en')
        
        # Make sure we have a shadow color to save
        if not hasattr(self, 'shadow_color') or not self.shadow_color:
            if self.canvas and hasattr(self.canvas, 'default_shadow_color'):
                self.shadow_color = self.canvas.default_shadow_color
            else:
                self.shadow_color = QColor(0, 0, 0, 150)  # Default shadow color

        # Use consistent settings directory path
        settings_dir = self.get_settings_directory()
        
        # Print the settings directory to help with troubleshooting
        # Saving settings to directory: {settings_dir}
        
        # Ensure directory exists with proper permissions
        if not os.path.exists(settings_dir):
            try:
                os.makedirs(settings_dir, mode=0o755)  # Add mode for proper permissions
            except Exception as e:
                return

        file_path = os.path.join(settings_dir, 'user_settings.txt')
        # Full settings file path: {file_path}
        
        # Write the settings to the file with error handling
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(f"Theme: {self.current_theme}\n")
                file.write(f"Language: {self.current_language}\n")
                # Save shadow color in RGBA format
                file.write(f"ShadowColor: {self.shadow_color.red()},{self.shadow_color.green()},{self.shadow_color.blue()},{self.shadow_color.alpha()}\n")
                # Save draw only affected strand setting
                file.write(f"DrawOnlyAffectedStrand: {str(self.draw_only_affected_strand).lower()}\n")
                # Save enable third control point setting
                file.write(f"EnableThirdControlPoint: {str(self.enable_third_control_point).lower()}\n")
                # Save enable curvature bias control setting
                file.write(f"EnableCurvatureBiasControl: {str(self.enable_curvature_bias_control).lower()}\n")
                # Save enable snap to grid setting
                file.write(f"EnableSnapToGrid: {str(self.snap_to_grid_enabled).lower()}\n")
                # Save show move highlights setting
                file.write(f"ShowMoveHighlights: {str(self.show_move_highlights).lower()}\n")
                # Save shadow blur settings
                file.write(f"NumSteps: {self.num_steps}\n")
                file.write(f"MaxBlurRadius: {self.max_blur_radius:.1f}\n") # Save float with one decimal place
                # Save curvature settings
                file.write(f"ControlPointBaseFraction: {self.base_fraction_spinbox.value():.2f}\n")
                file.write(f"DistanceMultiplier: {self.distance_mult_spinbox.value():.1f}\n")
                file.write(f"CurveResponseExponent: {self.curve_response_spinbox.value():.1f}\n")
                # file.write(f"UseExtendedMask: {str(self.use_extended_mask).lower()}\n")
                file.write(f"ExtensionLength: {self.extension_length}\n")
                file.write(f"ExtensionDashCount: {self.extension_dash_count}\n")
                file.write(f"ExtensionDashWidth: {self.extension_dash_width:.1f}\n")
                file.write(f"ExtensionDashGapLength: {self.extension_dash_gap_length:.1f}\n")
                file.write(f"ExtensionLineWidth: {self.extension_dash_width:.1f}\n")
                file.write(f"ArrowHeadLength: {self.arrow_head_length}\n")
                file.write(f"ArrowHeadWidth: {self.arrow_head_width}\n")
                file.write(f"ArrowHeadStrokeWidth: {self.arrow_head_stroke_width}\n")
                file.write(f"ArrowGapLength: {self.arrow_gap_length:.1f}\n")
                file.write(f"ArrowLineLength: {self.arrow_line_length:.1f}\n")
                file.write(f"ArrowLineWidth: {self.arrow_line_width:.1f}\n")
                file.write(f"UseDefaultArrowColor: {str(self.use_default_arrow_color).lower()}\n")
                file.write(f"DefaultArrowColor: {self.default_arrow_fill_color.red()},{self.default_arrow_fill_color.green()},{self.default_arrow_fill_color.blue()},{self.default_arrow_fill_color.alpha()}\n")
                file.write(f"DefaultStrandColor: {self.default_strand_color.red()},{self.default_strand_color.green()},{self.default_strand_color.blue()},{self.default_strand_color.alpha()}\n")
                file.write(f"DefaultStrokeColor: {self.default_stroke_color.red()},{self.default_stroke_color.green()},{self.default_stroke_color.blue()},{self.default_stroke_color.alpha()}\n")
                file.write(f"DefaultStrandWidth: {self.default_strand_width}\n")
                file.write(f"DefaultStrokeWidth: {self.default_stroke_width}\n")
                file.write(f"DefaultWidthGridUnits: {self.default_width_grid_units}\n")
            # Settings saved to {file_path}
            
            # Create a copy in the root directory for easier viewing (optional)
            try:
                local_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'user_settings.txt')
                with open(local_file_path, 'w', encoding='utf-8') as local_file:
                    local_file.write(f"Theme: {self.current_theme}\n")
                    local_file.write(f"Language: {self.current_language}\n")
                    local_file.write(f"ShadowColor: {self.shadow_color.red()},{self.shadow_color.green()},{self.shadow_color.blue()},{self.shadow_color.alpha()}\n")
                    local_file.write(f"DrawOnlyAffectedStrand: {str(self.draw_only_affected_strand).lower()}\n")
                    local_file.write(f"EnableThirdControlPoint: {str(self.enable_third_control_point).lower()}\n")
                    local_file.write(f"EnableSnapToGrid: {str(self.snap_to_grid_enabled).lower()}\n")
                    local_file.write(f"ShowMoveHighlights: {str(self.show_move_highlights).lower()}\n")
                    local_file.write(f"NumSteps: {self.num_steps}\n")
                    local_file.write(f"MaxBlurRadius: {self.max_blur_radius:.1f}\n") # Save float with one decimal place
                    # Save curvature settings
                    local_file.write(f"ControlPointBaseFraction: {self.base_fraction_spinbox.value():.2f}\n")
                    local_file.write(f"DistanceMultiplier: {self.distance_mult_spinbox.value():.1f}\n")
                    local_file.write(f"CurveResponseExponent: {self.curve_response_spinbox.value():.1f}\n")
                    # local_file.write(f"UseExtendedMask: {str(self.use_extended_mask).lower()}\n")
                    local_file.write(f"ExtensionLength: {self.extension_length}\n")
                    local_file.write(f"ExtensionDashCount: {self.extension_dash_count}\n")
                    local_file.write(f"ExtensionDashWidth: {self.extension_dash_width:.1f}\n")
                    local_file.write(f"ExtensionDashGapLength: {self.extension_dash_gap_length:.1f}\n")
                    local_file.write(f"ExtensionLineWidth: {self.extension_dash_width:.1f}\n")
                    local_file.write(f"ArrowHeadLength: {self.arrow_head_length}\n")
                    local_file.write(f"ArrowHeadWidth: {self.arrow_head_width}\n")
                    local_file.write(f"ArrowHeadStrokeWidth: {self.arrow_head_stroke_width}\n")
                    local_file.write(f"ArrowGapLength: {self.arrow_gap_length:.1f}\n")
                    local_file.write(f"ArrowLineLength: {self.arrow_line_length:.1f}\n")
                    local_file.write(f"ArrowLineWidth: {self.arrow_line_width:.1f}\n")
                    local_file.write(f"UseDefaultArrowColor: {str(self.use_default_arrow_color).lower()}\n")
                    local_file.write(f"DefaultArrowColor: {self.default_arrow_fill_color.red()},{self.default_arrow_fill_color.green()},{self.default_arrow_fill_color.blue()},{self.default_arrow_fill_color.alpha()}\n")
                    local_file.write(f"DefaultStrandColor: {self.default_strand_color.red()},{self.default_strand_color.green()},{self.default_strand_color.blue()},{self.default_strand_color.alpha()}\n")
                    local_file.write(f"DefaultStrokeColor: {self.default_stroke_color.red()},{self.default_stroke_color.green()},{self.default_stroke_color.blue()},{self.default_stroke_color.alpha()}\n")
                    local_file.write(f"DefaultStrandWidth: {self.default_strand_width}\n")
                    local_file.write(f"DefaultStrokeWidth: {self.default_stroke_width}\n")
                    local_file.write(f"DefaultWidthGridUnits: {self.default_width_grid_units}\n")
                # Created copy of settings at: {local_file_path}
            except Exception as e:
                print(f"Could not create settings copy: {e}")
                
        except Exception as e:
            # Optionally show an error message to the user
            QMessageBox.warning(
                self,
                "Settings Error",
                f"Could not save settings: {str(e)}"
            )

    def load_video_paths(self):
        if getattr(sys, 'frozen', False):
            if sys.platform.startswith('darwin'):
                # For macOS .app bundles, resources are in a different location
                base_path = os.path.join(os.path.dirname(sys.executable), '..', 'Resources')
                base_path = os.path.realpath(base_path)
            else:
                base_path = sys._MEIPASS
        else:
            # Use the directory of this file in dev mode to reliably find bundled assets
            base_path = os.path.dirname(os.path.abspath(__file__))

        # Use .mov files on Mac for better compatibility with QuickTime
        if sys.platform.startswith('darwin'):
            video_directory = os.path.join(base_path, 'mov')
            video_extension = '.mov'
        else:
            video_directory = os.path.join(base_path, 'mp4')
            video_extension = '.mp4'

        self.video_paths = [
            os.path.join(video_directory, f'tutorial_1{video_extension}'),
            os.path.join(video_directory, f'tutorial_2{video_extension}'),
            os.path.join(video_directory, f'tutorial_3{video_extension}'),
            os.path.join(video_directory, f'tutorial_4{video_extension}'),  # Previously tutorial_6.mp4
        ]

        # Optional: Log the video paths for debugging
        for path in self.video_paths:
            if not os.path.exists(path):
                pass


    def play_video(self, index):
        video_path = self.video_paths[index]
        if os.path.exists(video_path):
            try:
                if sys.platform.startswith('win'):
                    os.startfile(video_path)
                    return
                elif sys.platform.startswith('darwin'):
                    # Some macOS systems/QuickTime versions refuse to open files from inside app bundles.
                    # Workaround: copy the video to a temporary folder and open it from there.
                    try:
                        import shutil, tempfile, subprocess as _sub
                        temp_target = video_path
                        # Heuristic: if file is inside the .app bundle resources, copy it out
                        if '/Contents/Resources/' in video_path or '\\Contents\\Resources\\' in video_path:
                            temp_dir = tempfile.mkdtemp(prefix='OpenStrandVideo_')
                            temp_target = os.path.join(temp_dir, os.path.basename(video_path))
                            shutil.copy2(video_path, temp_target)
                            # Best effort: clear quarantine attribute in case it was inherited
                            try:
                                _sub.run(['xattr', '-d', 'com.apple.quarantine', temp_target], check=False)
                            except Exception:
                                pass
                        # Prefer opening with default app
                        subprocess.run(['open', temp_target], check=True)
                        return
                    except Exception:
                        # Fallback: explicitly try QuickTime Player
                        try:
                            subprocess.run(['open', '-a', 'QuickTime Player', video_path], check=True)
                            return
                        except Exception:
                            # Final fallback: use the built-in Qt player dialog
                            try:
                                dlg = VideoPlayerDialog(video_path, self)
                                dlg.exec_()
                                return
                            except Exception:
                                pass
                else:
                    subprocess.run(['xdg-open', video_path], check=True)
                    return
            except subprocess.SubprocessError as e:
                QMessageBox.warning(
                    self,
                    "Error Playing Video",
                    f"Could not play the video. Error: {str(e)}"
                )
        else:
            QMessageBox.warning(
                self,
                "Video Not Found",
                f"The video file was not found:\n{video_path}"
            )

    def add_theme_item(self, text, data):
        # Create a 26x26 pixmap with theme colors preview
        pixmap = QPixmap(26, 26)
        pixmap.fill(Qt.black)  # Initialize with transparent background
        painter = QPainter(pixmap)
        
        # Set colors based on theme
        if data == 'default':
            fill = QColor(230, 230, 230)    # Medium-light gray
            border = QColor(200, 200, 200)  # Light gray
        elif data == 'light':
            fill = QColor(255, 255, 255)    # White
            border = QColor(200, 200, 200)  # Light gray
        elif data == 'dark':
            fill = QColor(44, 44, 44)       # Dark gray
            border = QColor(102, 102, 102)  # Medium gray
        else:
            fill = Qt.white
            border = Qt.black

        # Draw the preview with improved anti-aliasing and precise measurements
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        
        # Use integer coordinates and adjust pen alignment
        painter.setBrush(fill)
        pen = QPen(border, 1)
        pen.setJoinStyle(Qt.MiterJoin)  # Sharp corners
        painter.setPen(pen)
        
        # Draw slightly inset to avoid edge artifacts
        painter.drawRoundedRect(2, 2, 22, 22, 4, 4)
        
        painter.end()
        
        # Create icon and add to combobox
        icon = QIcon(pixmap)
        self.theme_combobox.addItem(icon, text, data)

    def get_flag_path(self, flag_filename):
        """Get the path to a flag image file."""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            if sys.platform.startswith('darwin'):
                # For macOS .app bundles
                base_path = os.path.join(os.path.dirname(sys.executable), '..', 'Resources')
            else:
                # For Windows/Linux executables
                base_path = sys._MEIPASS
        else:
            # Running as script
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        flag_path = os.path.join(base_path, 'flags', flag_filename)
        return flag_path
    
    def render_whats_new_html(self, html):
        """Replace emoji flags with inline images to ensure consistent rendering in QTextBrowser."""
        try:
            de_flag_path = self.get_flag_path('de.png')
            if de_flag_path and os.path.exists(de_flag_path):
                de_url = QUrl.fromLocalFile(de_flag_path).toString()
                img_tag = f'<img src="{de_url}" alt="DE" width="30" height="20" style="vertical-align:text-bottom;" />'
                # Replace true emoji if present
                html = html.replace('🇩🇪', img_tag)
                # Replace fallback textual rendering "DE" that some systems show instead of the flag
                html = html.replace(' DE:', f' {img_tag}:')
                html = html.replace(' DE</', f' {img_tag}</')
                html = html.replace(' DE.', f' {img_tag}.')
                html = html.replace(' DE ', f' {img_tag} ')
            return html
        except Exception:
            return html
    
    def create_flag_icon(self, flag_filename):
        """Create a flag icon from high-resolution flag images, scaled appropriately for dropdown."""
        flag_path = self.get_flag_path(flag_filename)
        if flag_path and os.path.exists(flag_path):
            # Load the original high-resolution flag image
            original_flag = QPixmap(flag_path)
            
            # Calculate optimal size for dropdown display
            # Target height around 40px for good visibility in dropdown
            target_height = 40
            original_width = original_flag.width()
            original_height = original_flag.height()
            
            # Calculate width maintaining aspect ratio
            aspect_ratio = original_width / original_height
            target_width = int(target_height * aspect_ratio)
            
            # Create high-quality scaled flag
            scaled_flag = original_flag.scaled(
                target_width, target_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Add small border around the flag
            border_width = 2
            canvas_width = scaled_flag.width() + 2 * border_width
            canvas_height = scaled_flag.height() + 2 * border_width
            
            # Create canvas for the final icon
            pixmap = QPixmap(canvas_width, canvas_height)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            
            # Enable all quality rendering hints for crisp display
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
            
            # Draw the scaled flag
            flag_rect = QRect(border_width, border_width, scaled_flag.width(), scaled_flag.height())
            painter.drawPixmap(flag_rect.topLeft(), scaled_flag)
            
            # Add crisp border based on theme
            border_color = QColor("#000000")
            if self.current_theme == "dark":
                border_color = QColor("#ffffff")
            
            # Use precise pen for crisp border lines
            pen = QPen(border_color, 1)
            pen.setStyle(Qt.SolidLine)
            painter.setPen(pen)
            
            # Draw crisp border rectangle
            painter.drawRect(border_width - 1, border_width - 1, 
                           scaled_flag.width() + 1, scaled_flag.height() + 1)
            
            painter.end()
            return QIcon(pixmap), pixmap.size()
        else:
            return None, None
    
    def add_lang_item_en(self, text, data):
        icon, icon_size = self.create_flag_icon('us.png')
        if icon:
            self.language_combobox.addItem(icon, text, data)
            self.language_combobox.setIconSize(icon_size)
        else:
            # Fallback to text-only if flag image not found
            self.language_combobox.addItem(text, data)

    def add_lang_item_fr(self, text, data):
        icon, icon_size = self.create_flag_icon('fr.png')
        if icon:
            self.language_combobox.addItem(icon, text, data)
            self.language_combobox.setIconSize(icon_size)
        else:
            self.language_combobox.addItem(text, data)

    def add_lang_item_de(self, text, data):
        icon, icon_size = self.create_flag_icon('de.png')
        if icon:
            self.language_combobox.addItem(icon, text, data)
            self.language_combobox.setIconSize(icon_size)
        else:
            self.language_combobox.addItem(text, data)

    def add_lang_item_it(self, text, data):
        icon, icon_size = self.create_flag_icon('it.png')
        if icon:
            self.language_combobox.addItem(icon, text, data)
            self.language_combobox.setIconSize(icon_size)
        else:
            self.language_combobox.addItem(text, data) # Ensure combobox uses the new size

    def add_lang_item_es(self, text, data):
        icon, icon_size = self.create_flag_icon('es.png')
        if icon:
            self.language_combobox.addItem(icon, text, data)
            self.language_combobox.setIconSize(icon_size)
        else:
            self.language_combobox.addItem(text, data) # Ensure combobox uses the new size

    def add_lang_item_pt(self, text, data):
        icon, icon_size = self.create_flag_icon('pt.png')
        if icon:
            self.language_combobox.addItem(icon, text, data)
            self.language_combobox.setIconSize(icon_size)
        else:
            self.language_combobox.addItem(text, data) # Ensure combobox uses the new size

    def add_lang_item_he(self, text, data):
        icon, icon_size = self.create_flag_icon('il.png')
        if icon:
            self.language_combobox.addItem(icon, text, data)
            self.language_combobox.setIconSize(icon_size)
        else:
            self.language_combobox.addItem(text, data) # Ensure combobox uses the new size
            
        # For Hebrew item, explicitly set left alignment so text starts next to flag
        item_index = self.language_combobox.count() - 1
        self.language_combobox.setItemData(item_index, Qt.AlignLeft | Qt.AlignVCenter, Qt.TextAlignmentRole)
        
        # Also set layout direction for the dropdown view to handle Hebrew properly
        if hasattr(self.language_combobox, 'view'):
            view = self.language_combobox.view()
            if view:
                view.setLayoutDirection(Qt.RightToLeft)

    def update_shadow_color_button(self):
        """Update the shadow color button appearance to reflect the current shadow color."""
        pixmap = QPixmap(30, 30)
        pixmap.fill(self.shadow_color)
        self.shadow_color_button.setIcon(QIcon(pixmap))
        self.shadow_color_button.setIconSize(pixmap.size())
        
    def on_curvature_changed(self, value=None):
        """Handle immediate updates when any curvature spinbox value changes."""
        # Import QApplication for processEvents
        from PyQt5.QtWidgets import QApplication
        
        # Get current values directly from spinboxes
        base_fraction_value = self.base_fraction_spinbox.value()
        distance_mult_value = self.distance_mult_spinbox.value()
        curve_response_value = self.curve_response_spinbox.value()
        
        print(f"DEBUG: on_curvature_changed called")
        print(f"  Spinbox values - base: {base_fraction_value}, dist: {distance_mult_value}, curve: {curve_response_value}")
        print(f"  Canvas values before - base: {getattr(self.canvas, 'control_point_base_fraction', 'N/A')}, dist: {getattr(self.canvas, 'distance_multiplier', 'N/A')}, curve: {getattr(self.canvas, 'curve_response_exponent', 'N/A')}")
        
        # Apply to canvas immediately (same as reset button)
        if self.canvas:
            self.canvas.control_point_base_fraction = base_fraction_value
            self.canvas.distance_multiplier = distance_mult_value
            self.canvas.curve_response_exponent = curve_response_value
            
            # Update all existing strands with new parameters
            # First update all strands (including attached ones that are in the list)
            for strand in self.canvas.strands:
                strand.control_point_base_fraction = base_fraction_value
                strand.distance_multiplier = distance_mult_value
                strand.curve_response_exponent = curve_response_value
                
                # Force updating_position to False
                if hasattr(strand, 'updating_position'):
                    strand.updating_position = False
                
                # Prepare geometry change for Qt
                if hasattr(strand, 'prepareGeometryChange'):
                    strand.prepareGeometryChange()
                
                # Clear any cached paths first
                try:
                    if hasattr(strand, '_path'):
                        delattr(strand, '_path')
                except AttributeError:
                    pass  # Attribute was removed between check and delete
                try:
                    if hasattr(strand, '_bounding_rect_cache'):
                        delattr(strand, '_bounding_rect_cache')
                except AttributeError:
                    pass  # Attribute was removed between check and delete
                
                # Update shape
                if hasattr(strand, 'update_shape'):
                    strand.update_shape()
                
                # Force path update
                if hasattr(strand, 'force_path_update'):
                    strand.force_path_update()
                
                # Update all attached strands recursively
                self.update_attached_strands_curvature(strand, base_fraction_value, distance_mult_value, curve_response_value)
            
            # Clear render buffer to force recreation
            if hasattr(self.canvas, 'render_buffer'):
                self.canvas.render_buffer = None
            
            # Refresh the canvas
            self.canvas.update()
            self.canvas.repaint()
            
            # If canvas has a scene (QGraphicsScene), update it too
            if hasattr(self.canvas, 'scene') and hasattr(self.canvas.scene, 'update'):
                self.canvas.scene.update()
            
            # Force redraw if available
            if hasattr(self.canvas, 'force_redraw'):
                self.canvas.force_redraw()
            
            # Force immediate processing of paint events
            QApplication.processEvents()
            
            print(f"DEBUG: Canvas updated with {len(self.canvas.strands)} strands")
        
        # Save settings immediately
        self.save_settings_to_file()
        print(f"DEBUG: Settings saved")
    
    def reset_curvature_settings(self):
        """Reset all curvature settings to their default values."""
        # Don't disconnect signals - just set values and let them trigger naturally
        # Reset to default values
        self.base_fraction_spinbox.setValue(1.0)  # Default control point influence
        self.distance_mult_spinbox.setValue(2.0)  # Default distance boost
        self.curve_response_spinbox.setValue(2.0)  # Default curvature type
        
    def choose_shadow_color(self):
        """Open a color dialog to choose a new shadow color."""
        color_dialog = QColorDialog(self)
        color_dialog.setCurrentColor(self.shadow_color)
        color_dialog.setOption(QColorDialog.ShowAlphaChannel)
        
        if color_dialog.exec_():
            self.shadow_color = color_dialog.currentColor()
            self.update_shadow_color_button()
            
            # Apply the shadow color change to the canvas
            if self.canvas:
                self.canvas.set_shadow_color(self.shadow_color)
                self.canvas.update()
                # Store the shadow color in the main window
                if hasattr(self.parent_window, 'canvas'):
                    self.parent_window.canvas.default_shadow_color = self.shadow_color
            
            # Store the current settings
            self.current_theme = self.theme_combobox.currentData()
            self.current_language = self.language_combobox.currentData()
            
            # Save settings to file to persist the change
            self.save_settings_to_file()

    def update_default_arrow_color_button(self):
        """Update the default arrow color button to reflect current color."""
        pixmap = QPixmap(30, 30)
        pixmap.fill(self.default_arrow_fill_color)
        self.default_arrow_color_button.setIcon(QIcon(pixmap))
        self.default_arrow_color_button.setIconSize(pixmap.size())

    def choose_default_arrow_color(self):
        """Open a color dialog to choose a new default arrow color."""
        color_dialog = QColorDialog(self)
        color_dialog.setCurrentColor(self.default_arrow_fill_color)
        color_dialog.setOption(QColorDialog.ShowAlphaChannel)
        if color_dialog.exec_():
            self.default_arrow_fill_color = color_dialog.currentColor()
            self.update_default_arrow_color_button()
            # Save new setting immediately
            self.save_settings_to_file()
            # Apply to canvas immediately
            if self.canvas:
                self.canvas.default_arrow_fill_color = self.default_arrow_fill_color
                if hasattr(self.canvas, 'force_redraw'):
                    self.canvas.force_redraw()
                self.canvas.update()

    def on_default_arrow_color_changed(self, state):
        """Handle default arrow color checkbox state change."""
        self.use_default_arrow_color = bool(state)
        if self.canvas:
            self.canvas.use_default_arrow_color = self.use_default_arrow_color
            if hasattr(self.canvas, 'force_redraw'):
                self.canvas.force_redraw()
            self.canvas.update()

    def update_default_strand_color_button(self):
        """Update the default strand color button to reflect current color."""
        pixmap = QPixmap(30, 30)
        pixmap.fill(self.default_strand_color)
        self.default_strand_color_button.setIcon(QIcon(pixmap))
        self.default_strand_color_button.setIconSize(pixmap.size())

    def choose_default_strand_color(self):
        """Open a color dialog to choose a new default strand color."""
        color_dialog = QColorDialog(self)
        color_dialog.setCurrentColor(self.default_strand_color)
        color_dialog.setOption(QColorDialog.ShowAlphaChannel)
        if color_dialog.exec_():
            self.default_strand_color = color_dialog.currentColor()
            self.update_default_strand_color_button()
            # Save new setting immediately
            self.save_settings_to_file()
            # Apply to canvas immediately
            if self.canvas:
                self.canvas.default_strand_color = self.default_strand_color
                # Update the strand_color property as well for backward compatibility
                self.canvas.strand_color = self.default_strand_color
                if hasattr(self.canvas, 'force_redraw'):
                    self.canvas.force_redraw()
                self.canvas.update()

    def update_default_stroke_color_button(self):
        """Update the default stroke color button to reflect current color."""
        pixmap = QPixmap(30, 30)
        pixmap.fill(self.default_stroke_color)
        self.default_stroke_color_button.setIcon(QIcon(pixmap))
        self.default_stroke_color_button.setIconSize(pixmap.size())

    def choose_default_stroke_color(self):
        """Open a color dialog to choose a new default stroke color."""
        color_dialog = QColorDialog(self)
        color_dialog.setCurrentColor(self.default_stroke_color)
        color_dialog.setOption(QColorDialog.ShowAlphaChannel)
        if color_dialog.exec_():
            self.default_stroke_color = color_dialog.currentColor()
            self.update_default_stroke_color_button()
            # Save new setting immediately
            self.save_settings_to_file()
            # Apply to canvas immediately
            if self.canvas:
                # Use the new set_stroke_color method to apply to all existing strands
                self.canvas.set_stroke_color(self.default_stroke_color)
                if hasattr(self.canvas, 'force_redraw'):
                    self.canvas.force_redraw()
                self.canvas.update()

    def update_default_strand_width_button_size(self):
        """Calculate and set the optimal width for the default strand width button based on current language text."""
        if not hasattr(self, 'default_strand_width_button'):
            return
            
        # Get current translation
        _ = translations[self.current_language]
        button_text = _['default_strand_width'] if 'default_strand_width' in _ else "Default Strand Width"
        
        # Calculate required width using font metrics
        fm = self.default_strand_width_button.fontMetrics()
        text_rect = fm.boundingRect(button_text)
        text_width = text_rect.width()
        
        # Add very generous padding to account for button styling, borders, and DPI variations
        # Base padding increased significantly
        padding = 80  # Increased from 40 to 80
        if text_width > 120:  # For longer translations
            padding += 40  # Increased from 20 to 40
        if text_width > 150:  # For very long translations
            padding += 60  # Increased from 30 to 60
            
        # Much larger buffer for high-DPI screens and button styling
        dpi_buffer = 80  # Increased from 40 to 80
        
        calculated_width = text_width + padding + dpi_buffer
        
        # Set higher minimum to ensure button is never too small
        final_width = max(260, calculated_width)  # Increased from 180 to 260
        
        self.default_strand_width_button.setMinimumWidth(final_width)
        self.default_strand_width_button.setMaximumWidth(final_width)
        self.default_strand_width_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # Get current screen DPI for logging
        try:
            current_screen = self.screen()
            if current_screen:
                logical_dpi = current_screen.logicalDotsPerInch()
            else:
                pass
        except:
            pass

    def open_default_width_dialog(self):
        """Open a dialog to configure default strand width."""
        dialog = DefaultWidthConfigDialog(self, self.parent())
        if dialog.exec_() == QDialog.Accepted:
            # Get the new values
            new_width, new_stroke_width = dialog.get_values()
            self.default_strand_width = new_width
            self.default_stroke_width = new_stroke_width
            self.default_width_grid_units = dialog.thickness_spinbox.value()
            
            # Save settings immediately
            self.save_settings_to_file()
            
            # Apply to canvas
            if self.canvas:
                self.canvas.strand_width = new_width
                self.canvas.stroke_width = new_stroke_width

    def populate_history_list(self):
        """Scans the temp_states directory and populates the history list."""
        self.history_list.clear()
        self.load_history_button.setEnabled(False) # Disable load button initially

        # Get translations based on current language
        _ = translations[self.current_language]

        if not self.undo_redo_manager:
            self.history_list.addItem(_['no_history_found']) # Show message if manager missing
            self.clear_history_button.setEnabled(False) # Also disable clear button
            return

        temp_dir = self.undo_redo_manager.get_temp_dir()
        current_session_id = self.undo_redo_manager.get_session_id()
        sessions = {}
        found_history = False

        try:
            for filename in os.listdir(temp_dir):
                if filename.endswith(".json"):
                    parts = filename.split('_')
                    if len(parts) == 2:
                        session_id = parts[0]
                        
                        # Skip files from the current session
                        if session_id == current_session_id:
                            continue
                            
                        try:
                            step = int(parts[1].split('.')[0])
                            filepath = os.path.join(temp_dir, filename)
                            
                            # Store the file with the highest step number for each session
                            if session_id not in sessions or step > sessions[session_id]['step']:
                                sessions[session_id] = {'step': step, 'filepath': filepath}
                            found_history = True
                        except (ValueError, IndexError):
                            pass
        except FileNotFoundError:
            pass
        except Exception as e:
            pass

        if not found_history:
            self.history_list.addItem(_['no_history_found'])
            self.clear_history_button.setEnabled(False) # Disable clear if no history
        else:
            # Sort sessions by session ID (datetime string) descending
            sorted_sessions = sorted(sessions.items(), key=lambda item: item[0], reverse=True)
            
            for session_id, data in sorted_sessions:
                try:
                    # Format the session_id (YYYYMMDDHHMMSS) into a readable string
                    dt = QDateTime.fromString(session_id, "yyyyMMddHHmmss")
                    display_text = dt.toString("yyyy-MM-dd hh:mm:ss") + f" (State {data['step']})"
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.UserRole, data['filepath']) # Store filepath
                    self.history_list.addItem(item)
                except Exception as parse_e:
                    item = QListWidgetItem(f"{session_id} (State {data['step']}) - Invalid Date Format")
                    item.setData(Qt.UserRole, data['filepath'])
                    self.history_list.addItem(item)
            self.clear_history_button.setEnabled(True) # Enable clear if history exists
            
    def load_selected_history(self):
        """Loads the final state of the selected history session."""
        _ = translations[self.current_language]
        selected_item = self.history_list.currentItem()
        
        if not selected_item or not self.undo_redo_manager:
            return
            
        filepath = selected_item.data(Qt.UserRole)
        if not filepath:
            return
            
        # Confirmation might be good here, but prompt asks for OK anyway
        # Load the state using the undo/redo manager
        success = self.undo_redo_manager.load_specific_state(filepath)
        
        if success:
            # Close the settings dialog after loading
            self.accept() # Use accept to signal successful operation if needed
        else:
            QMessageBox.warning(
                self,
                _['history_load_error_title'],
                _['history_load_error_text']
            )
            
    def clear_all_history_action(self):
        """Clears all past history files without asking for confirmation."""
        _ = translations[self.current_language]
        
        if not self.undo_redo_manager:
            return
            
        # Get temp directory and current session ID
        temp_dir = self.undo_redo_manager.get_temp_dir()
        current_session_id = self.undo_redo_manager.get_session_id()
        
        # Delete all history files EXCEPT the current session
        deleted_count = 0
        
        try:
            # Get list of all files
            all_files = os.listdir(temp_dir)
            
            # First delete all temp_states in other directories (sometimes files are created elsewhere)
            root_dir = os.path.dirname(os.path.dirname(temp_dir))
            for root, dirs, files in os.walk(root_dir):
                if "temp_states" in root and root != temp_dir:
                    for file in files:
                        if file.endswith(".json"):
                            try:
                                file_path = os.path.join(root, file)
                                os.remove(file_path)
                                deleted_count += 1
                            except Exception as e:
                                pass
            
            # Now delete files in the main temp directory that don't belong to current session
            for filename in all_files:
                if filename.endswith(".json"):
                    # Keep only current session files
                    if not filename.startswith(current_session_id):
                        file_path = os.path.join(temp_dir, filename)
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                        except Exception as e:
                            pass
        except Exception as e:
            pass
        
        # Also call the undo_redo_manager's method for any internal cleanup
        self.undo_redo_manager.clear_all_past_history()
        
        # Refresh the list to show it's empty
        self.populate_history_list()
        
        # Show brief notification
        if deleted_count > 0:
            QMessageBox.information(
                self,
                _['history_cleared_title'],
                f"{deleted_count} history files removed."
            )

    def showEvent(self, event):
        """Override showEvent to ensure translations are always up-to-date before showing."""
        # Always get the current language from the parent and update translations
        if hasattr(self.parent_window, 'language_code'):
            self.current_language = self.parent_window.language_code
            self.update_translations()
            # Update layout direction after updating translations
            self.update_layout_direction()

        super().showEvent(event) # Call parent method AFTER ensuring translations

        # Recalculate button size for current DPI after dialog is shown
        self.update_default_strand_width_button_size()

        # Refresh the history list (can happen after super)
        if hasattr(self, 'history_list') and hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
            self.populate_history_list()

        # Refresh icon widgets on show (can happen after super)
        if hasattr(self, 'undo_icon_widget'):
            self.update_icon_widget(self.undo_icon_widget, '↶')
        if hasattr(self, 'redo_icon_widget'):
            self.update_icon_widget(self.redo_icon_widget, '↷')
        if hasattr(self, 'third_cp_icon_widget'):
            self.update_third_cp_icon_widget(self.third_cp_icon_widget)

        # Update default arrow color checkbox state
        if hasattr(self, 'default_arrow_color_checkbox') and hasattr(self, 'use_default_arrow_color'):
            self.default_arrow_color_checkbox.setChecked(self.use_default_arrow_color)

    def moveEvent(self, event):
        """Handle dialog movement between screens with different DPI."""
        super().moveEvent(event)
        # Recalculate button size when dialog moves (in case it moved to a different DPI screen)
        if hasattr(self, 'default_strand_width_button'):
            # Use a small delay to ensure the move is complete
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, self.update_default_strand_width_button_size)

    def changeEvent(self, event):
        """Handle DPI changes and other window state changes."""
        super().changeEvent(event)
        # Recalculate button size on DPI changes
        if hasattr(self, 'default_strand_width_button'):
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(50, self.update_default_strand_width_button_size)

    def resizeEvent(self, event):
        """Handle resize events that might indicate DPI changes."""
        super().resizeEvent(event)
        # Recalculate button size on resize (might be due to DPI change)
        if hasattr(self, 'default_strand_width_button'):
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(25, self.update_default_strand_width_button_size)

    def update_icon_widget(self, label_widget, character):
        """Helper function to draw the styled icon onto a QLabel's pixmap."""
        pixmap_size = 40 # Match button size
        pixmap = QPixmap(pixmap_size, pixmap_size)
        pixmap.fill(Qt.transparent) # Ensure transparent background

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw the blue circle background
        circle_color = QColor("#76acdc")
        painter.setBrush(QBrush(circle_color))
        painter.setPen(Qt.NoPen) # No border for the circle itself
        # Draw ellipse slightly inset to avoid clipping
        radius = (pixmap_size / 2) - 1 # Slightly smaller radius
        center_offset = (pixmap_size / 2)
        painter.drawEllipse(int(center_offset - radius), int(center_offset - radius), int(radius * 2), int(radius * 2))

        # Draw the text character
        # Use a suitable font, similar to StrokeTextButton
        font = QFont()
        font.setPixelSize(30) # Match pixel size from StrokeTextButton
        font.setBold(True)
        painter.setFont(font)

        # --- Mimic StrokeTextButton text drawing (stroke + fill) --- 
        path = QPainterPath()
        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(character)
        text_height = fm.height()
        # Adjust position slightly for better centering if needed
        x = (pixmap_size - text_width) / 2
        y = (pixmap_size + text_height) / 2 - fm.descent() + 1 # Small adjustment often needed
        path.addText(x, y, font, character)

        # Define stroke and fill based on StrokeTextButton's normal blue theme
        # Using the 'default' blue theme values from UndoRedoManager
        stroke_color = QColor("#e0ecfa") # Normal stroke for blue theme
        stroke_width = 3.0
        fill_color = QColor("#000000") # Black fill

        # Draw stroke
        pen = QPen(stroke_color, stroke_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.strokePath(path, pen)

        # Draw fill
        painter.fillPath(path, fill_color)
        # --- End mimic --- 

        painter.end()
        label_widget.setPixmap(pixmap)

    def update_third_cp_icon_widget(self, label_widget):
        """Helper function to draw the styled third control point icon (green square)."""
        pixmap_size = 40 # Match button size
        pixmap = QPixmap(pixmap_size, pixmap_size)
        pixmap.fill(Qt.transparent) # Ensure transparent background

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Parameters from draw_control_points for the center point
        control_point_radius = 11 # Original radius used for sizing
        stroke_color = QColor('black')
        fill_color = QColor('green')
        square_size_factor = 0.618 # Original factor
        new_stroke_width = 2 # New smaller stroke width

        # Calculate square size based on original parameters, centered in pixmap
        # Scale based on pixmap size relative to original control point diameter
        scale_factor = pixmap_size / (control_point_radius * 2.5) # Adjust scale factor as needed
        square_dimension = control_point_radius * 2 * square_size_factor * scale_factor

        center_x = pixmap_size / 2
        center_y = pixmap_size / 2

        # Define the square rectangle
        square_rect = QRectF(
            center_x - square_dimension / 2,
            center_y - square_dimension / 2,
            square_dimension,
            square_dimension
        )

        # 1. Draw the filled green square
        painter.setPen(Qt.NoPen) # No border for the fill
        painter.setBrush(QBrush(fill_color))
        painter.drawRect(square_rect)

        # 2. Draw the thinner black stroke on top
        stroke_pen = QPen(stroke_color, new_stroke_width)
        stroke_pen.setJoinStyle(Qt.MiterJoin) # Sharp corners
        painter.setPen(stroke_pen)
        painter.setBrush(Qt.NoBrush) # No fill for the stroke
        painter.drawRect(square_rect)

        painter.end()
        label_widget.setPixmap(pixmap)

    def log_button_color_debug_info(self):
        """Log detailed information about button color layout positioning for debugging."""
        
        if hasattr(self, 'button_color_container') and self.button_color_container:
            pass
            
        if hasattr(self, 'button_color_layout') and self.button_color_layout:
            
            for i in range(self.button_color_layout.count()):
                item = self.button_color_layout.itemAt(i)
                if item.widget():
                    widget = item.widget()
                elif item.spacerItem():
                    spacer = item.spacerItem()
                    
        if hasattr(self, 'button_color_label') and self.button_color_label:
            pass
            
        if hasattr(self, 'default_arrow_color_button') and self.default_arrow_color_button:
            pass
            

    # --- Samples helpers ---
    def find_sample_files(self, limit=12):
        """Locate sample JSON files from common sample directories.
        Returns a list of absolute file paths, newest first.
        """
        candidates = []
        
        # Determine base path based on whether app is frozen or not
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            if sys.platform.startswith('darwin'):
                # For macOS .app bundles, resources are in a different location
                base_path = os.path.join(os.path.dirname(sys.executable), '..', 'Resources')
            else:
                # For Windows/Linux executables
                base_path = sys._MEIPASS
        else:
            # Running as script - samples is in the same directory as this file
            base_path = os.path.dirname(os.path.abspath(__file__))

        # Common locations that can contain prepared samples
        sample_dirs = [
            os.path.join(base_path, 'samples'),                 # samples folder
        ]

        seen = set()
        for d in sample_dirs:
            if os.path.isdir(d):
                try:
                    # Walk recursively to include JSONs inside subfolders such as versioned dirs
                    for root, _, files in os.walk(d):
                        for name in files:
                            if name.lower().endswith('.json'):
                                full = os.path.join(root, name)
                                if full not in seen:
                                    seen.add(full)
                                    candidates.append(full)
                except Exception:
                    continue

        # Sort by modified time, newest first
        try:
            candidates.sort(key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0, reverse=True)
        except Exception:
            pass
        if limit and limit > 0:
            candidates = candidates[:limit]
        return candidates

    def on_sample_button_clicked(self, file_path):
        """Close the dialog and then load the selected sample JSON into the canvas."""
        # Close the dialog first, then load after the event loop processes close
        self.close()

        def _load():
            try:
                parent = self.parent_window if hasattr(self, 'parent_window') else self.parent()
                if not parent:
                    return

                # Try to import full history first if available
                undo_mgr = getattr(getattr(parent, 'layer_panel', None), 'undo_redo_manager', None)
                history_loaded = False
                if undo_mgr:
                    try:
                        history_loaded = undo_mgr.import_history(file_path)
                    except Exception as e:
                        history_loaded = False

                if history_loaded:
                    if hasattr(parent.canvas, 'layer_panel'):
                        parent.canvas.layer_panel.refresh()
                    parent.canvas.update()
                    return

                # Fallback: simple snapshot
                strands, groups, selected_strand_name, locked_layers, lock_mode, shadow_enabled, show_control_points = load_strands(file_path, parent.canvas)

                # Clear existing canvas state
                parent.canvas.strands = []
                parent.canvas.groups = {}

                # Clear group panel UI/state for clean reload
                if hasattr(parent.canvas, 'group_layer_manager') and hasattr(parent.canvas.group_layer_manager, 'group_panel'):
                    group_panel = parent.canvas.group_layer_manager.group_panel
                    if hasattr(group_panel, 'scroll_layout'):
                        while group_panel.scroll_layout.count():
                            child = group_panel.scroll_layout.takeAt(0)
                            if child.widget():
                                child.widget().deleteLater()
                    group_panel.groups = {}
                    group_panel.groups_loaded_from_json = False

                # Apply loaded data
                apply_loaded_strands(parent.canvas, strands, groups)

                # Restore UI button states
                if hasattr(parent, 'toggle_control_points_button'):
                    parent.toggle_control_points_button.setChecked(show_control_points)
                parent.canvas.show_control_points = show_control_points

                if hasattr(parent, 'toggle_shadow_button'):
                    parent.toggle_shadow_button.setChecked(shadow_enabled)
                parent.canvas.shadow_enabled = shadow_enabled

                # Update layer panel and canvas
                if hasattr(parent.canvas, 'layer_panel'):
                    parent.canvas.layer_panel.refresh()
                parent.canvas.update()


                # Reset undo history since snapshot load discards previous history
                if undo_mgr:
                    try:
                        undo_mgr.clear_history(save_current=True)
                    except Exception:
                        pass
                # Save initial state
                if hasattr(parent, 'layer_state_manager'):
                    try:
                        parent.layer_state_manager.save_initial_state()
                    except Exception:
                        pass
            except Exception as e:
                pass

        QTimer.singleShot(0, _load)

class VideoPlayerDialog(QDialog):
    def __init__(self, video_path, parent=None):
        super(VideoPlayerDialog, self).__init__(parent)
        self.video_path = video_path
        self.setWindowTitle("Video Player")
        self.setMinimumSize(600, 400)
        self.setup_ui()
        self.load_video()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)

        # Video Widget
        self.video_widget = QVideoWidget()
        self.layout.addWidget(self.video_widget)

        # Media Player
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)

        # Control Buttons Layout
        control_layout = QHBoxLayout()

        # Play Button
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.media_player.play)
        control_layout.addWidget(self.play_button)

        # Pause Button
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.media_player.pause)
        control_layout.addWidget(self.pause_button)

        # Progress Slider
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_position)
        control_layout.addWidget(self.position_slider)

        # Close Button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        control_layout.addWidget(self.close_button)

        self.layout.addLayout(control_layout)

        # Connect media player signals
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.mediaStatusChanged.connect(self.handle_media_status)

        # Connect error signal
        self.media_player.error.connect(self.handle_error)

    def load_video(self):
        media_content = QMediaContent(QUrl.fromLocalFile(self.video_path))
        self.media_player.setMedia(media_content)

    def position_changed(self, position):
        self.position_slider.setValue(position)

    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)

    def set_position(self, position):
        self.media_player.setPosition(position)

    def handle_media_status(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.media_player.stop()
            self.position_slider.setValue(0)
        elif status == QMediaPlayer.InvalidMedia:
            QMessageBox.critical(self, "Error", "Invalid media. Unable to play the video.")

    def handle_error(self, error):
        error_message = self.media_player.errorString()
        QMessageBox.critical(self, "Media Player Error", f"An error occurred: {error_message}")


class DefaultWidthConfigDialog(QDialog):
    """Dialog for configuring default strand width and stroke width."""
    
    def __init__(self, settings_dialog, parent=None):
        super().__init__(parent)
        self.settings_dialog = settings_dialog
        
        # Get translations
        _ = translations.get(settings_dialog.current_language, translations['en'])
        
        self.setWindowTitle(_['default_strand_width'] if 'default_strand_width' in _ else "Default Strand Width")
        self.setModal(True)
        self.setMinimumSize(400, 220)
        self.resize(450, 240)
        
        # Find the main window to inherit its theme
        main_window = parent
        while main_window and not hasattr(main_window, 'current_theme'):
            main_window = main_window.parent()
        
        # Apply theme styling to dialog if main window found
        if main_window and hasattr(main_window, 'current_theme'):
            theme = main_window.current_theme
            if theme == 'dark':
                self.setStyleSheet("""
                    QDialog {
                        background-color: #2C2C2C;
                        color: white;
                    }
                    QLabel {
                        color: white;
                    }
                    QSpinBox, QSlider {
                        background-color: #3D3D3D;
                        color: white;
                        border: 1px solid #555;
                        border-radius: 3px;
                        padding: 2px;
                    }
                    QSpinBox:hover, QSlider:hover {
                        border: 1px solid #777;
                    }
                    QPushButton, QDialogButtonBox QPushButton {
                        background-color: #252525;
                        color: white;
                        font-weight: bold;
                        border: 2px solid #000000;
                        padding: 10px;
                        border-radius: 4px;
                        min-width: 80px;
                    }
                    QPushButton:hover, QDialogButtonBox QPushButton:hover {
                        background-color: #505050;
                    }
                    QPushButton:pressed, QDialogButtonBox QPushButton:pressed {
                        background-color: #151515;
                        border: 2px solid #000000;
                    }
                    QDialogButtonBox {
                        background-color: transparent;
                    }
                """)
            elif theme == 'light':
                self.setStyleSheet("""
                    QDialog {
                        background-color: #F5F5F5;
                        color: black;
                    }
                    QLabel {
                        color: black;
                    }
                    QSpinBox, QSlider {
                        background-color: white;
                        color: black;
                        border: 1px solid #CCC;
                        border-radius: 3px;
                        padding: 2px;
                    }
                    QSpinBox:hover, QSlider:hover {
                        border: 1px solid #999;
                    }
                    QPushButton, QDialogButtonBox QPushButton {
                        background-color: #F0F0F0;
                        color: #000000;
                        border: 1px solid #BBBBBB;
                        border-radius: 5px;
                        padding: 10px;
                        min-width: 80px;
                        font-weight: bold;
                    }
                    QPushButton:hover, QDialogButtonBox QPushButton:hover {
                        background-color: #E0E0E0;
                    }
                    QPushButton:pressed, QDialogButtonBox QPushButton:pressed {
                        background-color: #D0D0D0;
                    }
                    QDialogButtonBox {
                        background-color: transparent;
                    }
                """)
        
        # Calculate grid unit (assuming 23 pixels per grid square)
        self.grid_unit = 23
        
        # Get current default values from settings dialog
        current_total_width = settings_dialog.default_strand_width + 2 * settings_dialog.default_stroke_width
        current_total_squares = round(current_total_width / self.grid_unit)
        if current_total_squares < 2:
            current_total_squares = 2
        elif current_total_squares % 2 != 0:
            current_total_squares += 1  # Make it even
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Total thickness in grid squares
        thickness_layout = QHBoxLayout()
        thickness_layout.addWidget(QLabel(_['total_thickness_label'] if 'total_thickness_label' in _ else "Total Thickness (grid squares):"))
        self.thickness_spinbox = QSpinBox()
        self.thickness_spinbox.setRange(2, 20)  # Even numbers from 2 to 20
        self.thickness_spinbox.setSingleStep(2)  # Only even numbers
        self.thickness_spinbox.setValue(current_total_squares)
        thickness_layout.addWidget(self.thickness_spinbox)
        thickness_layout.addWidget(QLabel(_['grid_squares'] if 'grid_squares' in _ else "squares"))
        layout.addLayout(thickness_layout)
        
        # Color width percentage (slider)
        color_layout = QVBoxLayout()
        color_layout.addWidget(QLabel(_['color_vs_stroke_label'] if 'color_vs_stroke_label' in _ else "Color vs Stroke Distribution (total thickness fixed):"))
        
        self.color_slider = QSlider(Qt.Horizontal)
        self.color_slider.setRange(10, 90)  # 10% to 90% of available color space
        
        # Calculate current color percentage based on default values
        current_percentage = int((settings_dialog.default_strand_width / current_total_width) * 100) if current_total_width > 0 else 50
        self.color_slider.setValue(max(10, min(90, current_percentage)))
        
        color_layout.addWidget(self.color_slider)
        
        # Slider labels
        slider_labels = QHBoxLayout()
        slider_labels.addStretch()
        percent_text = _['percent_available_color'] if 'percent_available_color' in _ else "% of Available Color Space"
        self.percentage_label = QLabel(f"{self.color_slider.value()}{percent_text}")
        slider_labels.addWidget(self.percentage_label)
        slider_labels.addStretch()
        color_layout.addLayout(slider_labels)
        
        layout.addLayout(color_layout)
        
        # Connect slider to update label
        self.color_slider.valueChanged.connect(self.update_percentage_label)
        
        # Preview section
        preview_layout = QVBoxLayout()
        self.preview_label = QLabel()
        self.preview_label.setWordWrap(True)
        self.preview_label.setMinimumHeight(40)
        self.update_preview()
        preview_layout.addWidget(self.preview_label)
        layout.addLayout(preview_layout)
        
        # Connect changes to update preview
        self.thickness_spinbox.valueChanged.connect(self.update_preview)
        self.color_slider.valueChanged.connect(self.update_preview)
        
        # Buttons using custom translated buttons instead of QDialogButtonBox
        button_layout = QHBoxLayout()
        
        # Create OK button with translation
        ok_text = _['ok'] if 'ok' in _ else "OK"
        self.ok_button = QPushButton(ok_text)
        self.ok_button.clicked.connect(self.accept)
        
        # Create Cancel button with translation
        cancel_text = _['cancel'] if 'cancel' in _ else "Cancel"
        self.cancel_button = QPushButton(cancel_text)
        self.cancel_button.clicked.connect(self.reject)
        
        # Add buttons to layout with stretch to push them to the right
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Connect to language change signal if available
        if hasattr(settings_dialog, 'parent_window') and hasattr(settings_dialog.parent_window, 'language_changed'):
            settings_dialog.parent_window.language_changed.connect(self.update_translations)
    
    def update_translations(self):
        """Update all text elements when language changes."""
        # Get new translations
        _ = translations.get(self.settings_dialog.current_language, translations['en'])
        
        # Update window title
        self.setWindowTitle(_['default_strand_width'] if 'default_strand_width' in _ else "Default Strand Width")
        
        # Update button texts
        ok_text = _['ok'] if 'ok' in _ else "OK"
        cancel_text = _['cancel'] if 'cancel' in _ else "Cancel"
        self.ok_button.setText(ok_text)
        self.cancel_button.setText(cancel_text)
        
        # Update other labels if needed
        self.update_percentage_label()
        self.update_preview()
    
    def update_percentage_label(self):
        """Update the percentage label when slider changes."""
        slider_value = self.color_slider.value()
        # Get translations
        _ = translations.get(self.settings_dialog.current_language, translations['en'])
        percent_text = _['percent_available_color'] if 'percent_available_color' in _ else "% of Available Color Space"
        self.percentage_label.setText(f"{slider_value}{percent_text}")
    
    def update_preview(self):
        """Update the preview display keeping total thickness fixed."""
        total_grid_squares = self.thickness_spinbox.value()
        total_grid_width = total_grid_squares * self.grid_unit
        color_percentage = self.color_slider.value() / 100.0


        # Compute widths
        color_width = total_grid_width * color_percentage
        stroke_width = (total_grid_width - color_width) / 2


        # Get translations
        _ = translations.get(self.settings_dialog.current_language, translations['en'])
        preview_template = _['width_preview_label'] if 'width_preview_label' in _ else "Total: {total}px | Color: {color}px | Stroke: {stroke}px each side"
        self.preview_label.setText(
            preview_template.format(total=int(total_grid_width), color=int(color_width), stroke=int(stroke_width))
        )
    
    def get_values(self):
        """Return new color and stroke width ensuring total thickness remains fixed."""
        total_grid_width = self.thickness_spinbox.value() * self.grid_unit
        color_percentage = self.color_slider.value() / 100.0

        color_width = total_grid_width * color_percentage
        stroke_width = (total_grid_width - color_width) / 2


        return int(color_width), int(stroke_width)