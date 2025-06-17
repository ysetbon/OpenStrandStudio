from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QWidget, QLabel, QStackedWidget, QComboBox, QPushButton,
    QSpacerItem, QSizePolicy, QMessageBox, QTextBrowser, QSlider,
    QColorDialog, QCheckBox, QBoxLayout, QDialogButtonBox,
    QSpinBox, QDoubleSpinBox # Add these
)
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QRectF
from PyQt5.QtGui import QIcon, QFont, QPainter, QPen, QColor, QPixmap, QPainterPath, QBrush, QFontMetrics
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from translations import translations
import logging
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

    def __init__(self, parent=None, canvas=None, undo_redo_manager=None):
        super(SettingsDialog, self).__init__(parent)
        
        # Set window flags directly in the constructor - explicitly remove help button
        flags = self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        self.setWindowFlags(flags)
        
        self.canvas = canvas
        self.parent_window = parent
        
        # Initialize with default values
        self.current_theme = getattr(parent, 'current_theme', 'default')
        # self.current_language = self.parent_window.language_code # REMOVED - Handled by showEvent
        self.shadow_color = QColor(0, 0, 0, 150)  # Default shadow color
        self.draw_only_affected_strand = False  # Default to drawing all strands
        self.enable_third_control_point = False  # Default to two control points
        # NEW: Use extended mask option (controls extra expansion of masked areas)
        self.use_extended_mask = False  # Default to using exact mask (small +3 offset)
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
            logging.info(f"SettingsDialog: Applied default arrow color settings to canvas - use_default: {self.use_default_arrow_color}, color: {self.default_arrow_fill_color.red()},{self.default_arrow_fill_color.green()},{self.default_arrow_fill_color.blue()},{self.default_arrow_fill_color.alpha()}")
            logging.info(f"SettingsDialog: Applied default width settings to canvas - strand_width: {self.default_strand_width}, stroke_width: {self.default_stroke_width}")
        
        # Apply loaded extension line settings to canvas
        if self.canvas:
            self.canvas.extension_length = self.extension_length
            self.canvas.extension_dash_count = self.extension_dash_count
            self.canvas.extension_dash_width = self.extension_dash_width
            self.canvas.extension_dash_gap_length = self.extension_dash_gap_length
            logging.info(f"SettingsDialog: Applied extension settings to canvas - length: {self.extension_length}, dash_count: {self.extension_dash_count}, dash_width: {self.extension_dash_width}, dash_gap_length: {self.extension_dash_gap_length}")
        
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
                if hasattr(self, 'extended_mask_label'):
                    self.extended_mask_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if hasattr(self, 'num_steps_label'):
                    self.num_steps_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if hasattr(self, 'blur_radius_label'):
                    self.blur_radius_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
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
                if hasattr(self, 'extended_mask_label'):
                    self.extended_mask_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if hasattr(self, 'num_steps_label'):
                    self.num_steps_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                if hasattr(self, 'blur_radius_label'):
                    self.blur_radius_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            # Also update direction for QHBoxLayouts within General Settings
            general_setting_layouts = [
                'theme_layout', 'shadow_layout', 'performance_layout', 
                'third_control_layout', 'extended_mask_layout', 
                'num_steps_layout', 'blur_radius_layout'
            ]
            for layout_name in general_setting_layouts:
                if hasattr(self, layout_name):
                    layout = getattr(self, layout_name)
                    if isinstance(layout, QHBoxLayout):
                        layout.setDirection(QBoxLayout.RightToLeft if is_rtl else QBoxLayout.LeftToRight)
                        logging.info(f"Set direction for {layout_name} to {'RTL' if is_rtl else 'LTR'}")

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
        if hasattr(self, 'about_widget'):
            self.about_widget.setLayoutDirection(direction)
        if hasattr(self, 'whats_new_widget'):
            self.whats_new_widget.setLayoutDirection(direction)
            
        # Also set direction for specific sub-layouts
        if hasattr(self, 'performance_layout'):
             self.performance_layout.setDirection(QBoxLayout.RightToLeft if is_rtl else QBoxLayout.LeftToRight)
        if hasattr(self, 'third_control_layout'):
             self.third_control_layout.setDirection(QBoxLayout.RightToLeft if is_rtl else QBoxLayout.LeftToRight)
        if hasattr(self, 'icon_layout'):
             self.icon_layout.setDirection(QBoxLayout.RightToLeft if is_rtl else QBoxLayout.LeftToRight)
        if hasattr(self, 'third_cp_icon_layout'):
             self.third_cp_icon_layout.setDirection(QBoxLayout.RightToLeft if is_rtl else QBoxLayout.LeftToRight)
             
        # Define specific style adjustments for comboboxes based on direction
        combo_style_adjustments = ""  # Initialize empty by default
        
        if is_rtl:
            # Remove CSS styling that might interfere - rely on layout reorganization
            logging.info("RTL mode: Relying on layout reorganization rather than CSS overrides")
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
            
        # Apply checkbox style to all checkboxes
        checkbox_style = """
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 13px;
                height: 13px;
            }
        """
        
        for checkbox in self.findChildren(QCheckBox):
            checkbox.setStyleSheet(checkbox_style)
            # Use appropriate direction for checkbox
            checkbox.setLayoutDirection(Qt.LeftToRight if not self.is_rtl_language(self.current_language) else Qt.LeftToRight)

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
                    padding: 8px;
                    selection-background-color: {selection_color};
                }}
            """
            self.theme_combobox.setStyleSheet(updated_theme_style)
            
            if is_rtl:
                # Use Qt.TextAlignmentRole to properly position text next to the icon
                self.set_combobox_text_alignment(self.theme_combobox, Qt.AlignRight | Qt.AlignVCenter)
                logging.info("RTL: Applied TextAlignmentRole for theme combobox text positioning")
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
                    {"padding-left: 24px; padding-right: 8px;" if is_rtl else "padding-left: 8px; padding-right: 24px;"}
                }}
                {dropdown_arrow_css}
                QComboBox QAbstractItemView {{
                    padding: 8px;
                    min-width: 150px;
                    selection-background-color: {selection_color};
                }}
            """
            self.language_combobox.setStyleSheet(updated_lang_style)
            
            if is_rtl:
                # Use Qt.TextAlignmentRole to properly position text next to the flag icon
                self.set_combobox_text_alignment(self.language_combobox, Qt.AlignRight | Qt.AlignVCenter)
                logging.info("RTL: Applied TextAlignmentRole for language combobox text positioning")
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
                                inner_layout.setSpacing(20)
                            else:
                                inner_layout.setContentsMargins(0, 0, 0, 0)  # Normal margins
                                inner_layout.setSpacing(15)

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
            # Reset checkbox to normal LTR
            if hasattr(self, 'default_arrow_color_checkbox'):
                self.default_arrow_color_checkbox.setLayoutDirection(Qt.LeftToRight)
                
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
                
        # Extended mask layout reorganization
        if hasattr(self, 'extended_mask_layout') and hasattr(self, 'extended_mask_label') and hasattr(self, 'extended_mask_checkbox'):
            self.clear_layout(self.extended_mask_layout)
            if is_rtl:
                self.extended_mask_layout.addStretch()
                self.extended_mask_layout.addWidget(self.extended_mask_checkbox)
                self.extended_mask_layout.addWidget(self.extended_mask_label)
            else:
                self.extended_mask_layout.addWidget(self.extended_mask_label)
                self.extended_mask_layout.addWidget(self.extended_mask_checkbox)
                self.extended_mask_layout.addStretch()
            # Force immediate update
            self.extended_mask_layout.invalidate()
            self.extended_mask_layout.activate()
                
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
                self.button_color_layout.setSpacing(10)  # Add some spacing between widgets
                self.button_color_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.button_color_label.setLayoutDirection(Qt.RightToLeft)
                self.button_color_label.setTextFormat(Qt.PlainText)
                self.button_color_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                 # Add spacer at the beginning to shift everything right
                self.button_color_layout.addWidget(self.default_arrow_color_button)
                self.button_color_layout.addWidget(self.button_color_label)
                logging.info("RTL REORGANIZE: Added stretch, button, then label for proper RTL positioning")
            else:
                self.button_color_container.setLayoutDirection(Qt.LeftToRight)
                self.button_color_layout.setDirection(QBoxLayout.LeftToRight)
                self.button_color_layout.setContentsMargins(0, 0, 0, 0)
                self.button_color_layout.setSpacing(10)  # Small, constant gap
                self.button_color_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.button_color_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
                self.button_color_label.setStyleSheet("QLabel { margin: 0px; padding: 0px; }")
                self.default_arrow_color_button.setStyleSheet("QPushButton { margin: 0px; padding: 0px; }")
                self.button_color_layout.addWidget(self.button_color_label)
               
                self.button_color_layout.addWidget(self.default_arrow_color_button)
                self.button_color_layout.addStretch()
                logging.info("LTR REORGANIZE: Added label, spacing, then button")
            # Force immediate update (same as theme layout)
            self.button_color_layout.invalidate()
            self.button_color_layout.activate()
            # Also update the container widget
            if hasattr(self, 'button_color_container'):
                self.button_color_container.updateGeometry()
                self.button_color_container.update()
                logging.info(f"REORGANIZE: Updated container geometry")
                
            # Log final reorganized layout state  
            logging.info(f"REORGANIZE_FINAL: Total items after reorganize: {self.button_color_layout.count()}")
            for i in range(self.button_color_layout.count()):
                item = self.button_color_layout.itemAt(i)
                if item.widget():
                    widget = item.widget()
                    logging.info(f"  Item {i}: Widget {widget.__class__.__name__} - text: '{getattr(widget, 'text', lambda: 'N/A')()}' geometry: {widget.geometry()} pos: {widget.pos()} size: {widget.size()}")
                elif item.spacerItem():
                    spacer = item.spacerItem()
                    logging.info(f"  Item {i}: Spacer - size hint: {spacer.sizeHint()}, policy: {spacer.sizePolicy().horizontalPolicy()}")
            # Log container and layout geometry
            logging.info(f"BUTTON_COLOR_CONTAINER geometry: {self.button_color_container.geometry()} size: {self.button_color_container.size()} pos: {self.button_color_container.pos()}")
            logging.info(f"BUTTON_COLOR_LAYOUT geometry: {self.button_color_layout.geometry()}")
            # Let the layout decide the width – zero works fine
            self.button_color_label.setMinimumWidth(0)
            self.button_color_label.updateGeometry()
            self.button_color_label.repaint()
            logging.info(f"BUTTON_COLOR_LABEL after min width set: minWidth={self.button_color_label.minimumWidth()} size={self.button_color_label.size()} geom={self.button_color_label.geometry()} pos={self.button_color_label.pos()}")

        # Checkbox layout reorganization (this was also missing!)
        if hasattr(self, 'checkbox_layout') and hasattr(self, 'default_arrow_color_checkbox'):
            self.clear_layout(self.checkbox_layout)
            if is_rtl:
                self.checkbox_layout.addStretch()
                self.checkbox_layout.addWidget(self.default_arrow_color_checkbox)
                logging.info("RTL: Reorganized checkbox layout - checkbox on right")
            else:
                self.checkbox_layout.addWidget(self.default_arrow_color_checkbox)
                self.checkbox_layout.addStretch()
                logging.info("LTR: Reorganized checkbox layout - checkbox on left")
            
            # Force immediate update and repaint
            self.checkbox_layout.invalidate()
            self.checkbox_layout.activate()
            self.default_arrow_color_checkbox.update()
            if hasattr(self, 'checkbox_container'):
                self.checkbox_container.updateGeometry()
                self.checkbox_container.update()
                self.checkbox_container.repaint()

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
                logging.info("RTL REORGANIZE: Added stretch, button, then label for default strand color proper RTL positioning")
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
                logging.info("LTR REORGANIZE: Added label, spacing, then button for default strand color")
            # Force immediate update (same as theme layout)
            self.default_strand_color_layout.invalidate()
            self.default_strand_color_layout.activate()
            # Also update the container widget
            if hasattr(self, 'default_strand_color_container'):
                self.default_strand_color_container.updateGeometry()
                self.default_strand_color_container.update()
                logging.info(f"REORGANIZE: Updated default strand color container geometry")
                
            # Let the layout decide the width – zero works fine
            self.default_strand_color_label.setMinimumWidth(0)
            self.default_strand_color_label.updateGeometry()
            self.default_strand_color_label.repaint()
            logging.info(f"DEFAULT_STRAND_COLOR_LABEL after min width set: minWidth={self.default_strand_color_label.minimumWidth()} size={self.default_strand_color_label.size()} geom={self.default_strand_color_label.geometry()} pos={self.default_strand_color_label.pos()}")

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
                logging.info("RTL REORGANIZE: Added stretch, button, then label for default stroke color proper RTL positioning")
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
                logging.info("LTR REORGANIZE: Added label, spacing, then button for default stroke color")
            # Force immediate update (same as theme layout)
            self.default_stroke_color_layout.invalidate()
            self.default_stroke_color_layout.activate()
            # Also update the container widget
            if hasattr(self, 'default_stroke_color_container'):
                self.default_stroke_color_container.updateGeometry()
                self.default_stroke_color_container.update()
                logging.info(f"REORGANIZE: Updated default stroke color container geometry")
                
            # Let the layout decide the width – zero works fine
            self.default_stroke_color_label.setMinimumWidth(0)
            self.default_stroke_color_label.updateGeometry()
            self.default_stroke_color_label.repaint()
            logging.info(f"DEFAULT_STROKE_COLOR_LABEL after min width set: minWidth={self.default_stroke_color_label.minimumWidth()} size={self.default_stroke_color_label.size()} geom={self.default_stroke_color_label.geometry()} pos={self.default_stroke_color_label.pos()}")

        # Default Strand Width button layout reorganization
        if hasattr(self, 'default_strand_width_container') and hasattr(self, 'default_strand_width_button'):
            # Clear the layout and set proper spacing
            self.clear_layout(self.default_strand_width_layout)
            self.default_strand_width_container.setContentsMargins(0, 0, 0, 0)
            if is_rtl:
                self.default_strand_width_layout.addStretch()
                self.default_strand_width_container.setLayoutDirection(Qt.LeftToRight)
                self.default_strand_width_layout.setDirection(QBoxLayout.LeftToRight)
                # Apply the same left margin as other RTL rows for alignment consistency
                self.default_strand_width_layout.setContentsMargins(258, 0, 0, 0)
                self.default_strand_width_layout.addWidget(self.default_strand_width_button)
                logging.info("RTL REORGANIZE: Added stretch then button for default strand width")
            else:
                self.default_strand_width_container.setLayoutDirection(Qt.LeftToRight)
                self.default_strand_width_layout.setDirection(QBoxLayout.LeftToRight)
                self.default_strand_width_layout.setContentsMargins(0, 0, 0, 0)
                self.default_strand_width_layout.addWidget(self.default_strand_width_button)
                self.default_strand_width_layout.addStretch()
                logging.info("LTR REORGANIZE: Added button then stretch for default strand width")
            # Force immediate update
            self.default_strand_width_layout.invalidate()
            self.default_strand_width_layout.activate()
            # Also update the container widget
            if hasattr(self, 'default_strand_width_container'):
                self.default_strand_width_container.updateGeometry()
                self.default_strand_width_container.update()
                logging.info(f"REORGANIZE: Updated default strand width container geometry")

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
        logging.info(f"Completed layout reorganization for {'RTL' if is_rtl else 'LTR'} - forcing visual update")
        
        # Debug: Check actual widget order in shadow layout
        if hasattr(self, 'shadow_layout'):
            widgets_in_order = []
            for i in range(self.shadow_layout.count()):
                item = self.shadow_layout.itemAt(i)
                if item.widget():
                    widgets_in_order.append(item.widget().__class__.__name__)
                elif item.spacerItem():
                    widgets_in_order.append("Spacer")
            logging.info(f"DEBUG: Shadow layout widget order: {widgets_in_order}")
        
        # Debug: Check actual widget order in button color layout  
        if hasattr(self, 'button_color_layout'):
            widgets_in_order = []
            for i in range(self.button_color_layout.count()):
                item = self.button_color_layout.itemAt(i)
                if item.widget():
                    widgets_in_order.append(item.widget().__class__.__name__)
                elif item.spacerItem():
                    widgets_in_order.append("Spacer")
            logging.info(f"DEBUG: Button color layout widget order: {widgets_in_order}")
        
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
        
        logging.info("Layout reorganization complete and aggressive visual update forced")

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
            
        # Set the alignment on the line edit - this actually works!
        combobox.lineEdit().setAlignment(alignment)
        
        # Also apply to dropdown items for consistency
        for i in range(combobox.count()):
            combobox.setItemData(i, alignment, Qt.TextAlignmentRole)
    
    def load_settings_from_file(self):
        """Load user settings from file to initialize dialog with saved settings."""
        # Use the appropriate directory for each OS
        app_name = "OpenStrand Studio"
        if sys.platform == 'darwin':  # macOS
            program_data_dir = os.path.expanduser('~/Library/Application Support')
            settings_dir = os.path.join(program_data_dir, app_name)
        else:
            program_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            settings_dir = program_data_dir  # AppDataLocation already includes the app name

        file_path = os.path.join(settings_dir, 'user_settings.txt')
        logging.info(f"SettingsDialog: Looking for settings file at: {file_path}")
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    logging.info("SettingsDialog: Reading settings from user_settings.txt")
                    
                    for line in file:
                        line = line.strip()
                        
                        if line.startswith('Theme:'):
                            self.current_theme = line.split(':', 1)[1].strip()
                            logging.info(f"SettingsDialog: Found Theme: {self.current_theme}")
                        elif line.startswith('Language:'):
                            self.current_language = line.split(':', 1)[1].strip()
                            logging.info(f"SettingsDialog: Found Language: {self.current_language}")
                        elif line.startswith('ShadowColor:'):
                            # Parse the RGBA values
                            rgba_str = line.split(':', 1)[1].strip()
                            try:
                                r, g, b, a = map(int, rgba_str.split(','))
                                # Create a fresh QColor instance
                                self.shadow_color = QColor(r, g, b, a)
                                logging.info(f"SettingsDialog: Successfully parsed shadow color: {r},{g},{b},{a}")
                            except Exception as e:
                                logging.error(f"SettingsDialog: Error parsing shadow color values: {e}. Using default shadow color.")
                        elif line.startswith('DrawOnlyAffectedStrand:'):
                            value = line.split(':', 1)[1].strip().lower()
                            self.draw_only_affected_strand = (value == 'true')
                            logging.info(f"SettingsDialog: Found DrawOnlyAffectedStrand: {self.draw_only_affected_strand}")
                        elif line.startswith('EnableThirdControlPoint:'):
                            value = line.split(':', 1)[1].strip().lower()
                            self.enable_third_control_point = (value == 'true')
                            logging.info(f"SettingsDialog: Found EnableThirdControlPoint: {self.enable_third_control_point}")
                        elif line.startswith('UseExtendedMask:'):
                            value = line.split(':', 1)[1].strip().lower()
                            self.use_extended_mask = (value == 'true')
                            logging.info(f"SettingsDialog: Found UseExtendedMask: {self.use_extended_mask}")
                        elif line.startswith('NumSteps:'):
                            try:
                                self.num_steps = int(line.split(':', 1)[1].strip())
                                logging.info(f"SettingsDialog: Found NumSteps: {self.num_steps}")
                            except ValueError:
                                logging.error(f"SettingsDialog: Error parsing NumSteps value. Using default {self.num_steps}.")
                        elif line.startswith('MaxBlurRadius:'):
                            try:
                                self.max_blur_radius = float(line.split(':', 1)[1].strip())
                                logging.info(f"SettingsDialog: Found MaxBlurRadius: {self.max_blur_radius}")
                            except ValueError:
                                logging.error(f"SettingsDialog: Error parsing MaxBlurRadius value. Using default {self.max_blur_radius}.")
                        elif line.startswith('ExtensionLength:'):
                            try:
                                self.extension_length = float(line.split(':', 1)[1].strip())
                                logging.info(f"SettingsDialog: Found ExtensionLength: {self.extension_length}")
                            except ValueError:
                                logging.error(f"SettingsDialog: Error parsing ExtensionLength value. Using default {self.extension_length}.")
                        elif line.startswith('ExtensionDashCount:'):
                            try:
                                self.extension_dash_count = int(line.split(':', 1)[1].strip())
                                logging.info(f"SettingsDialog: Found ExtensionDashCount: {self.extension_dash_count}")
                            except ValueError:
                                logging.error(f"SettingsDialog: Error parsing ExtensionDashCount value. Using default {self.extension_dash_count}.")
                        elif line.startswith('ExtensionDashWidth:'):
                            try:
                                self.extension_dash_width = float(line.split(':', 1)[1].strip())
                                logging.info(f"SettingsDialog: Found ExtensionDashWidth: {self.extension_dash_width}")
                            except ValueError:
                                logging.error(f"SettingsDialog: Error parsing ExtensionDashWidth value. Using default {self.extension_dash_width}.")
                        elif line.startswith('ExtensionLineWidth:'):  # legacy key
                            try:
                                self.extension_dash_width = float(line.split(':', 1)[1].strip())
                                logging.info(f"SettingsDialog: Found ExtensionLineWidth (legacy): {self.extension_dash_width}")
                            except ValueError:
                                logging.error(f"SettingsDialog: Error parsing legacy ExtensionLineWidth value. Using default {self.extension_dash_width}.")
                        elif line.startswith('ArrowHeadLength:'):
                            try:
                                self.arrow_head_length = float(line.split(':', 1)[1].strip())
                                logging.info(f"SettingsDialog: Found ArrowHeadLength: {self.arrow_head_length}")
                            except ValueError:
                                logging.error(f"SettingsDialog: Error parsing ArrowHeadLength value. Using default {getattr(self, 'arrow_head_length',20.0)}")
                        elif line.startswith('ArrowHeadWidth:'):
                            try:
                                self.arrow_head_width = float(line.split(':', 1)[1].strip())
                                logging.info(f"SettingsDialog: Found ArrowHeadWidth: {self.arrow_head_width}")
                            except ValueError:
                                logging.error(f"SettingsDialog: Error parsing ArrowHeadWidth value. Using default {getattr(self, 'arrow_head_width',10.0)}")
                        elif line.startswith('ArrowHeadStrokeWidth:'):
                            try:
                                self.arrow_head_stroke_width = int(line.split(':', 1)[1].strip())
                                logging.info(f"SettingsDialog: Found ArrowHeadStrokeWidth: {self.arrow_head_stroke_width}")
                            except ValueError:
                                logging.error(f"SettingsDialog: Error parsing ArrowHeadStrokeWidth value. Using default {getattr(self, 'arrow_head_stroke_width',4)}")
                        elif line.startswith('ArrowGapLength:'):
                            try:
                                self.arrow_gap_length = float(line.split(':', 1)[1].strip())
                                logging.info(f"SettingsDialog: Found ArrowGapLength: {self.arrow_gap_length}")
                            except ValueError:
                                logging.error(f"SettingsDialog: Error parsing ArrowGapLength value. Using default {self.arrow_gap_length}.")
                        elif line.startswith('ArrowLineLength:'):
                            try:
                                self.arrow_line_length = float(line.split(':', 1)[1].strip())
                                logging.info(f"SettingsDialog: Found ArrowLineLength: {self.arrow_line_length}")
                            except ValueError:
                                logging.error(f"SettingsDialog: Error parsing ArrowLineLength value. Using default {self.arrow_line_length}.")
                        elif line.startswith('ArrowLineWidth:'):
                            try:
                                self.arrow_line_width = float(line.split(':', 1)[1].strip())
                                logging.info(f"SettingsDialog: Found ArrowLineWidth: {self.arrow_line_width}")
                            except ValueError:
                                logging.error(f"SettingsDialog: Error parsing ArrowLineWidth value. Using default {self.arrow_line_width}.")
                        elif line.startswith('UseDefaultArrowColor:'):
                            self.use_default_arrow_color = (line.split(':', 1)[1].strip().lower() == 'true')
                            logging.info(f"SettingsDialog: Found UseDefaultArrowColor: {self.use_default_arrow_color}")
                        elif line.startswith('DefaultArrowColor:'):
                            try:
                                r, g, b, a = map(int, line.split(':', 1)[1].strip().split(','))
                                self.default_arrow_fill_color = QColor(r, g, b, a)
                                logging.info(f"SettingsDialog: Found DefaultArrowColor: {r},{g},{b},{a}")
                            except Exception as e:
                                logging.error(f"SettingsDialog: Error parsing DefaultArrowColor: {e}. Using default {self.default_arrow_fill_color}.")
                        elif line.startswith('ExtensionDashGapLength:'):
                            try:
                                self.extension_dash_gap_length = float(line.split(':', 1)[1].strip())
                                logging.info(f"SettingsDialog: Found ExtensionDashGapLength: {self.extension_dash_gap_length}")
                            except ValueError:
                                logging.error(f"SettingsDialog: Error parsing ExtensionDashGapLength value. Using default {self.extension_dash_gap_length}.")
                        elif line.startswith('DefaultStrandColor:'):
                            try:
                                r, g, b, a = map(int, line.split(':', 1)[1].strip().split(','))
                                self.default_strand_color = QColor(r, g, b, a)
                                logging.info(f"SettingsDialog: Found DefaultStrandColor: {r},{g},{b},{a}")
                            except Exception as e:
                                logging.error(f"SettingsDialog: Error parsing DefaultStrandColor: {e}. Using default {self.default_strand_color}.")
                        elif line.startswith('DefaultStrokeColor:'):
                            try:
                                r, g, b, a = map(int, line.split(':', 1)[1].strip().split(','))
                                self.default_stroke_color = QColor(r, g, b, a)
                                logging.info(f"SettingsDialog: Found DefaultStrokeColor: {r},{g},{b},{a}")
                            except Exception as e:
                                logging.error(f"SettingsDialog: Error parsing DefaultStrokeColor: {e}. Using default {self.default_stroke_color}.")
                        elif line.startswith('DefaultStrandWidth:'):
                            try:
                                self.default_strand_width = int(line.split(':', 1)[1].strip())
                                logging.info(f"SettingsDialog: Found DefaultStrandWidth: {self.default_strand_width}")
                            except ValueError:
                                logging.error(f"SettingsDialog: Error parsing DefaultStrandWidth value. Using default {self.default_strand_width}.")
                        elif line.startswith('DefaultStrokeWidth:'):
                            try:
                                self.default_stroke_width = int(line.split(':', 1)[1].strip())
                                logging.info(f"SettingsDialog: Found DefaultStrokeWidth: {self.default_stroke_width}")
                            except ValueError:
                                logging.error(f"SettingsDialog: Error parsing DefaultStrokeWidth value. Using default {self.default_stroke_width}.")
                        elif line.startswith('DefaultWidthGridUnits:'):
                            try:
                                self.default_width_grid_units = int(line.split(':', 1)[1].strip())
                                logging.info(f"SettingsDialog: Found DefaultWidthGridUnits: {self.default_width_grid_units}")
                            except ValueError:
                                logging.error(f"SettingsDialog: Error parsing DefaultWidthGridUnits value. Using default {self.default_width_grid_units}.")
                
                    logging.info(f"SettingsDialog: User settings loaded successfully. Theme: {self.current_theme}, Language: {self.current_language}, Shadow Color: {self.shadow_color.red()},{self.shadow_color.green()},{self.shadow_color.blue()},{self.shadow_color.alpha()}, Draw Only Affected Strand: {self.draw_only_affected_strand}, Enable Third Control Point: {self.enable_third_control_point}, Use Extended Mask: {self.use_extended_mask}, Num Steps: {self.num_steps}, Max Blur Radius: {self.max_blur_radius:.1f}")
            except Exception as e:
                logging.error(f"SettingsDialog: Error reading user settings: {e}. Using default values.")
        else:
            logging.info(f"SettingsDialog: Settings file not found at {file_path}. Using default settings.")

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
            _['history'],
            _['whats_new'],  # Add What's New category here
            _['about']  # Make sure About is the last item
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
                padding: 8px;
                selection-background-color: {selection_color};
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
            logging.info(f"Initial setup: RTL shadow layout for language {self.current_language} - button at far left, label at far right")
        else:
            self.shadow_layout.addWidget(self.shadow_color_label)
            self.shadow_layout.addWidget(self.shadow_color_button)
            self.shadow_layout.addStretch()
            logging.info(f"Initial setup: LTR shadow layout for language {self.current_language} - label before button")

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

        # NEW: Use Extended Mask Option
        self.extended_mask_layout = QHBoxLayout() # STORE AS INSTANCE ATTRIBUTE
        self.extended_mask_label = QLabel(_['use_extended_mask'] if 'use_extended_mask' in _ else "Use extended mask (wider overlap)")
        self.extended_mask_checkbox = QCheckBox()
        self.extended_mask_checkbox.setChecked(self.use_extended_mask)
        
        # Add widgets in proper order for current language
        if self.is_rtl_language(self.current_language):
            self.extended_mask_layout.addStretch()
            self.extended_mask_layout.addWidget(self.extended_mask_checkbox)
            self.extended_mask_layout.addWidget(self.extended_mask_label)
        else:
            self.extended_mask_layout.addWidget(self.extended_mask_label)
            self.extended_mask_layout.addWidget(self.extended_mask_checkbox)
            self.extended_mask_layout.addStretch()
        # Add tooltip explaining usage
        self.extended_mask_label.setToolTip(_['use_extended_mask_tooltip'])
        self.extended_mask_checkbox.setToolTip(_['use_extended_mask_tooltip'])

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
        general_layout.addLayout(self.extended_mask_layout)

        # Add Shadow Blur Steps
        self.num_steps_layout = QHBoxLayout() # STORE AS INSTANCE ATTRIBUTE
        self.num_steps_label = QLabel(_['shadow_blur_steps'] if 'shadow_blur_steps' in _ else "Shadow Blur Steps:") # Will be translated later
        self.num_steps_spinbox = QSpinBox()
        self.num_steps_spinbox.setRange(1, 100)
        self.num_steps_spinbox.setValue(self.num_steps)
        self.num_steps_spinbox.setToolTip("Number of steps for the shadow fade effect (default 3)")
        
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
        self.blur_radius_spinbox.setRange(0.0, 60.0)
        self.blur_radius_spinbox.setSingleStep(0.01)
        self.blur_radius_spinbox.setDecimals(2)
        self.blur_radius_spinbox.setValue(self.max_blur_radius)
        self.blur_radius_spinbox.setToolTip("Maximum radius of the shadow blur in pixels (default 29.99)")
        
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
        # Ensure the container widget uses LTR so the indicator appears on the left of the text
        self.checkbox_container.setLayoutDirection(Qt.LeftToRight if self.is_rtl_language(self.current_language) else Qt.RightToLeft)
        self.checkbox_layout = QHBoxLayout(self.checkbox_container)  # Store as instance attribute
        self.checkbox_layout.setContentsMargins(0, 0, 0, 0)
        self.checkbox_layout.setSpacing(5)
        
        self.default_arrow_color_checkbox = QCheckBox(_['use_default_arrow_color'] if 'use_default_arrow_color' in _ else "Use Default Arrow Color")
        self.default_arrow_color_checkbox.setChecked(self.use_default_arrow_color)
        self.default_arrow_color_checkbox.stateChanged.connect(self.on_default_arrow_color_changed)

        # Add widgets in proper order for current language
        if self.is_rtl_language(self.current_language):
            self.checkbox_layout.addStretch()
            self.checkbox_layout.addWidget(self.default_arrow_color_checkbox)
        else:
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
            self.button_color_layout.setSpacing(20) 
        else:
            self.button_color_layout.setContentsMargins(0, 0, 0, 0)  # Normal margins for LTR
            self.button_color_layout.setSpacing(15)

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
        logging.info(f"LABEL CONFIG: After adjustSize - size: {self.button_color_label.size()}, sizeHint: {self.button_color_label.sizeHint()}")
        self.default_arrow_color_button = QPushButton()
        self.default_arrow_color_button.setFixedSize(30, 30)
        self.update_default_arrow_color_button()
        self.default_arrow_color_button.clicked.connect(self.choose_default_arrow_color)

        # Add widgets in proper order for current language (to self.button_color_layout)
        if self.is_rtl_language(self.current_language):
            self.button_color_layout.addWidget(self.button_color_label)
            self.button_color_layout.addStretch()
            self.button_color_layout.addWidget(self.default_arrow_color_button)
            logging.info("RTL SETUP: Added label, stretch, then button")
        else:
            self.button_color_layout.addWidget(self.button_color_label)
            self.button_color_layout.addWidget(self.default_arrow_color_button)
            self.button_color_layout.addStretch()
            logging.info("LTR SETUP: Added label, button, then stretch")
        
        # Log final layout state
        logging.info(f"BUTTON_COLOR_LAYOUT: Total items: {self.button_color_layout.count()}")
        for i in range(self.button_color_layout.count()):
            item = self.button_color_layout.itemAt(i)
            if item.widget():
                widget = item.widget()
                logging.info(f"  Item {i}: Widget {widget.__class__.__name__} - text: '{getattr(widget, 'text', lambda: 'N/A')()}' size: {widget.size()} pos: {widget.pos()} geom: {widget.geometry()}")
            elif item.spacerItem():
                spacer = item.spacerItem()
                logging.info(f"  Item {i}: Spacer - size hint: {spacer.sizeHint()}, policy: {spacer.sizePolicy().horizontalPolicy()}")
        # Log container and layout geometry
        logging.info(f"BUTTON_COLOR_CONTAINER geometry: {self.button_color_container.geometry()} size: {self.button_color_container.size()} pos: {self.button_color_container.pos()}")
        logging.info(f"BUTTON_COLOR_LAYOUT geometry: {self.button_color_layout.geometry()}")
        # Try to force label to fill available space
        self.button_color_label.setMinimumWidth(self.button_color_container.width())
        self.button_color_label.updateGeometry()
        self.button_color_label.repaint()
        logging.info(f"BUTTON_COLOR_LABEL after min width set: minWidth={self.button_color_label.minimumWidth()} size={self.button_color_label.size()} geom={self.button_color_label.geometry()} pos={self.button_color_label.pos()}")

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
        if self.is_rtl_language(self.current_language):
            self.default_strand_width_layout.setContentsMargins(278, 0, 0, 0)
            self.default_strand_width_layout.setSpacing(20)
        else:
            self.default_strand_width_layout.setContentsMargins(0, 0, 0, 0)
            self.default_strand_width_layout.setSpacing(15)

        self.default_strand_width_button = QPushButton(_['default_strand_width'])
        self.default_strand_width_button.setToolTip(_['default_strand_width_tooltip'])
        self.default_strand_width_button.clicked.connect(self.open_default_width_dialog)
        # Set dynamic width based on translated text length
        self.update_default_strand_width_button_size()
        
        if self.is_rtl_language(self.current_language):
            self.default_strand_width_layout.addStretch()
            self.default_strand_width_layout.addWidget(self.default_strand_width_button)
        else:
            self.default_strand_width_layout.addWidget(self.default_strand_width_button)
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
                {"padding-left: 24px; padding-right: 8px;" if is_rtl else "padding-left: 8px; padding-right: 24px;"}
            }}
            {dropdown_arrow_css}
            QComboBox QAbstractItemView {{
                padding: 8px;
                min-width: 150px;
                selection-background-color: {selection_color};
            }}
        """
        self.language_combobox.setStyleSheet(self.lang_combobox_base_style)
        
        # Add language items with generated icons - using current translations
        self.add_lang_item_en(_['english'], 'en')
        self.add_lang_item_fr(_['french'], 'fr')
        self.add_lang_item_it(_['italian'], 'it')
        self.add_lang_item_es(_['spanish'], 'es')
        self.add_lang_item_pt(_['portuguese'], 'pt')
        self.add_lang_item_he(_['hebrew'], 'he')
        
        # Set the current language
        current_language = getattr(self, 'current_language', 'en')
        index = self.language_combobox.findData(current_language)
        if index >= 0:
            self.language_combobox.setCurrentIndex(index)

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
        tutorial_layout.addWidget(self.tutorial_label, 0, Qt.AlignLeft) # Default alignment, will be updated

        self.video_buttons = []

        for i in range(5):  # Changed from 7 to 5 tutorials
            # Explanation Label
            explanation_label = QLabel(_[f'gif_explanation_{i+1}'])
            tutorial_layout.addWidget(explanation_label, 0, Qt.AlignLeft) # Default alignment, will be updated

            # Play Video Button
            play_button = QPushButton(_['play_video'])
            tutorial_layout.addWidget(play_button) # Default alignment, will be updated
            play_button.clicked.connect(lambda checked, idx=i: self.play_video(idx))
            self.video_buttons.append(play_button)

        self.stacked_widget.addWidget(self.tutorial_widget)

        # History Page (index 3)
        self.history_widget = QWidget()
        history_layout = QVBoxLayout(self.history_widget)

        self.history_explanation_label = QLabel(_['history_explanation'])
        if self.is_rtl_language(self.current_language):
            history_layout.addWidget(self.history_explanation_label, 0, Qt.AlignLeft)
        else:
            history_layout.addWidget(self.history_explanation_label) # Default alignment, will be updated later

        self.history_list = QListWidget()
        self.history_list.setToolTip("Select a session to load its final state")
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
        self.whats_new_text_browser.setHtml(_['whats_new_info'])
        self.whats_new_text_browser.setOpenExternalLinks(True)
        whats_new_layout.addWidget(self.whats_new_text_browser)

        self.stacked_widget.addWidget(self.whats_new_widget)


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
        self.history_widget.setMinimumWidth(550)
        self.whats_new_widget.setMinimumWidth(550) # Set min width for new page
        self.about_widget.setMinimumWidth(550)

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
            self.default_strand_width_button  # ensure this specific button is included
        ]
        
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

    def apply_dialog_theme(self, theme_name):
        """Apply theme to dialog components"""
        # Update current theme for dropdown arrow colors
        self.current_theme = theme_name
        is_rtl = self.is_rtl_language(self.current_language)
        dropdown_arrow_css = self.get_dropdown_arrow_css(is_rtl)
        
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

    def apply_all_settings(self):
        # Capture previous extended mask setting to detect changes
        previous_use_extended_mask = self.use_extended_mask
        # Apply Theme Settings
        selected_theme = self.theme_combobox.currentData()
        if selected_theme and self.canvas:
            self.canvas.set_theme(selected_theme)
            self.canvas.update()

        # Store the selected theme
        self.current_theme = selected_theme

        # Emit signal to notify main window of theme change
        self.theme_changed.emit(selected_theme)
        
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
        if self.canvas and hasattr(self.canvas, 'move_mode'):
            self.canvas.move_mode.draw_only_affected_strand = self.draw_only_affected_strand
            logging.info(f"SettingsDialog: Set draw_only_affected_strand to {self.draw_only_affected_strand}")

        # Apply Third Control Point Setting
        # Store previous setting to check if it changed
        previous_third_control_point = self.enable_third_control_point
        # Get new setting from checkbox
        self.enable_third_control_point = self.third_control_checkbox.isChecked()
        
        if self.canvas:
            # Set the new value in canvas
            self.canvas.enable_third_control_point = self.enable_third_control_point
            logging.info(f"SettingsDialog: Set enable_third_control_point to {self.enable_third_control_point}")
            
            # Check if the setting changed
            if previous_third_control_point != self.enable_third_control_point:
                logging.info("SettingsDialog: Third control point setting changed, resetting all masked strands")
                
                # Reset all masked strands if the canvas has strands
                if hasattr(self.canvas, 'strands'):
                    for i, strand in enumerate(self.canvas.strands):
                        # Check if this is a masked strand
                        if hasattr(strand, '__class__') and strand.__class__.__name__ == 'MaskedStrand':
                            # Call the canvas's reset_mask method - this is the same one called
                            # when right-clicking on a layer in the layer panel
                            self.canvas.reset_mask(i)
                            logging.info(f"Reset mask for masked strand at index {i}: {strand.layer_name}")
                
                # Force redraw to show/hide third control point and reset masks
                self.canvas.update()
                
                # Force a full refresh of the canvas 
                if hasattr(self.canvas, 'force_redraw'):
                    self.canvas.force_redraw()
                    logging.info("Called force_redraw to ensure proper highlighting of masked strands")

        # Apply Shadow Blur Settings
        self.num_steps = self.num_steps_spinbox.value()
        self.max_blur_radius = self.blur_radius_spinbox.value()
        if self.canvas:
            self.canvas.num_steps = self.num_steps
            self.canvas.max_blur_radius = self.max_blur_radius
            logging.info(f"SettingsDialog: Set num_steps to {self.num_steps} and max_blur_radius to {self.max_blur_radius:.1f} on canvas")

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
            logging.info(f"SettingsDialog: Set extension_length to {self.extension_length}, dash_count to {self.extension_dash_count}, dashed_width to {self.extension_dash_width} on canvas")
            logging.info(f"SettingsDialog: Set arrow_head_length to {self.arrow_head_length}, arrow_head_width to {self.arrow_head_width}")
            logging.info(f"SettingsDialog: Set default strand_width to {self.default_strand_width}, stroke_width to {self.default_stroke_width}")

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
            logging.info(f"Applied layout direction change for language: {language_code}")
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
            logging.info(f"SettingsDialog: Set use_default_arrow_color to {self.use_default_arrow_color} and default_arrow_fill_color RGBA: {self.default_arrow_fill_color.red()},{self.default_arrow_fill_color.green()},{self.default_arrow_fill_color.blue()},{self.default_arrow_fill_color.alpha()}")
            # Force redraw to update arrow colors
            if hasattr(self.canvas, 'force_redraw'):
                self.canvas.force_redraw()
            self.canvas.update()

        # Apply Extended Mask Setting before saving
        self.use_extended_mask = self.extended_mask_checkbox.isChecked()
        if self.canvas:
            self.canvas.use_extended_mask = self.use_extended_mask

        # Save all settings to file (after updating all values including extended mask)
        self.save_settings_to_file()

        # Apply the theme to the dialog before hiding
        self.apply_dialog_theme(self.current_theme)
        self.hide()

        # If extended mask setting changed, force redraw of masked strands
        if previous_use_extended_mask != self.use_extended_mask:
            logging.info(f"SettingsDialog: Use extended mask changed to {self.use_extended_mask}. Forcing redraw of masked strands")
            if self.canvas and hasattr(self.canvas, 'strands'):
                for strand in self.canvas.strands:
                    if getattr(strand, '__class__', None) and strand.__class__.__name__ == 'MaskedStrand':
                        # No need to reset mask, just force shadow update to refresh +3 offset
                        if hasattr(strand, 'force_shadow_update'):
                            strand.force_shadow_update()
            if self.canvas:
                self.canvas.update()

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
        self.categories_list.item(4).setText(_['history']) # Update history category name
        self.categories_list.item(5).setText(_['whats_new']) # Update what's new category name
        self.categories_list.item(6).setText(_['about']) # Adjust index for About
        # Update labels and buttons
        self.theme_label.setText(_['select_theme'])
        self.shadow_color_label.setText(_['shadow_color'] if 'shadow_color' in _ else "Shadow Color")
        self.affected_strand_label.setText(_['draw_only_affected_strand'] if 'draw_only_affected_strand' in _ else "Draw only affected strand when dragging")
        self.third_control_label.setText(_['enable_third_control_point'] if 'enable_third_control_point' in _ else "Enable third control point at center")
        self.extended_mask_label.setText(_['use_extended_mask'] if 'use_extended_mask' in _ else "Use extended mask (wider overlap)")
        self.num_steps_label.setText(_['shadow_blur_steps'] if 'shadow_blur_steps' in _ else "Shadow Blur Steps:")
        self.blur_radius_label.setText(_['shadow_blur_radius'] if 'shadow_blur_radius' in _ else "Shadow Blur Radius:")
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
        # Update default arrow color checkbox text
        self.default_arrow_color_checkbox.setText(_['use_default_arrow_color'] if 'use_default_arrow_color' in _ else "Use Default Arrow Color")
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
        # Update history page elements
        self.history_explanation_label.setText(_['history_explanation'])
        self.load_history_button.setText(_['load_selected_history'])
        self.clear_history_button.setText(_['clear_all_history'])
        # Update What's New page elements
        self.whats_new_text_browser.setHtml(_['whats_new_info'])
        # Update about text browser instead of label
        self.about_text_browser.setHtml(_['about_info'])
        # Update theme combobox items
        self.theme_combobox.setItemText(0, _['default'])
        self.theme_combobox.setItemText(1, _['light'])
        self.theme_combobox.setItemText(2, _['dark'])
        
        # Completely rebuild the language combobox to ensure proper translation
        current_data = self.language_combobox.currentData()
        self.language_combobox.clear()
        
        # Re-add language items with properly translated names
        self.add_lang_item_en(_['english'], 'en')
        self.add_lang_item_fr(_['french'], 'fr')
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
            logging.info("RTL: Applied text alignment to comboboxes after translation update")
        else:
            # For LTR languages, use left alignment
            self.set_combobox_text_alignment(self.theme_combobox, Qt.AlignLeft | Qt.AlignVCenter)
            self.set_combobox_text_alignment(self.language_combobox, Qt.AlignLeft | Qt.AlignVCenter)
            logging.info("LTR: Applied text alignment to comboboxes after translation update")
        
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
                logging.info(f"RTL: Forced language combobox refresh after rebuild for index {index}")
        
        # For Hebrew, use proper CSS styling instead of adding spaces to text
        if self.is_rtl_language(self.current_language):
            # Remove CSS that might interfere with layout - rely purely on layout reorganization
            logging.info("RTL language detected - relying on layout reorganization for positioning")
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
        for i in range(5):  # Changed from 7 to 5
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

        # Use the appropriate directory for each OS
        app_name = "OpenStrand Studio"
        if sys.platform == 'darwin':  # macOS
            program_data_dir = os.path.expanduser('~/Library/Application Support')
            settings_dir = os.path.join(program_data_dir, app_name)
        else:
            program_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            settings_dir = program_data_dir  # AppDataLocation already includes the app name
        
        # Print the settings directory to help with troubleshooting
        print(f"Saving settings to directory: {settings_dir}")
        logging.info(f"Saving settings to directory: {settings_dir}")
        
        # Ensure directory exists with proper permissions
        if not os.path.exists(settings_dir):
            try:
                os.makedirs(settings_dir, mode=0o755)  # Add mode for proper permissions
                logging.info(f"Created settings directory: {settings_dir}")
            except Exception as e:
                logging.error(f"Cannot create directory {settings_dir}: {e}")
                return

        file_path = os.path.join(settings_dir, 'user_settings.txt')
        print(f"Full settings file path: {file_path}")
        logging.info(f"Full settings file path: {file_path}")
        
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
                # Save shadow blur settings
                file.write(f"NumSteps: {self.num_steps}\n")
                file.write(f"MaxBlurRadius: {self.max_blur_radius:.1f}\n") # Save float with one decimal place
                file.write(f"UseExtendedMask: {str(self.use_extended_mask).lower()}\n")
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
            print(f"Settings saved to {file_path} with Shadow Color: {self.shadow_color.red()},{self.shadow_color.green()},{self.shadow_color.blue()},{self.shadow_color.alpha()}, Draw Only Affected Strand: {self.draw_only_affected_strand}, Enable Third Control Point: {self.enable_third_control_point}, Num Steps: {self.num_steps}, Max Blur Radius: {self.max_blur_radius}")
            logging.info(f"Settings saved to {file_path} with Shadow Color: {self.shadow_color.red()},{self.shadow_color.green()},{self.shadow_color.blue()},{self.shadow_color.alpha()}, Draw Only Affected Strand: {self.draw_only_affected_strand}, Enable Third Control Point: {self.enable_third_control_point}, Num Steps: {self.num_steps}, Max Blur Radius: {self.max_blur_radius}")
            
            # Create a copy in the root directory for easier viewing (optional)
            try:
                local_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'user_settings.txt')
                with open(local_file_path, 'w', encoding='utf-8') as local_file:
                    local_file.write(f"Theme: {self.current_theme}\n")
                    local_file.write(f"Language: {self.current_language}\n")
                    local_file.write(f"ShadowColor: {self.shadow_color.red()},{self.shadow_color.green()},{self.shadow_color.blue()},{self.shadow_color.alpha()}\n")
                    local_file.write(f"DrawOnlyAffectedStrand: {str(self.draw_only_affected_strand).lower()}\n")
                    local_file.write(f"EnableThirdControlPoint: {str(self.enable_third_control_point).lower()}\n")
                    local_file.write(f"NumSteps: {self.num_steps}\n")
                    local_file.write(f"MaxBlurRadius: {self.max_blur_radius:.1f}\n") # Save float with one decimal place
                    local_file.write(f"UseExtendedMask: {str(self.use_extended_mask).lower()}\n")
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
                print(f"Created copy of settings at: {local_file_path}")
            except Exception as e:
                print(f"Could not create settings copy: {e}")
                
        except Exception as e:
            logging.error(f"Error saving settings to {file_path}: {e}")
            # Optionally show an error message to the user
            QMessageBox.warning(
                self,
                "Settings Error",
                f"Could not save settings: {str(e)}"
            )

    def load_video_paths(self):
        if getattr(sys, 'frozen', False):
            if sys.platform == 'darwin':
                # For macOS .app bundles, resources are in a different location
                base_path = os.path.join(os.path.dirname(sys.executable), '..', 'Resources')
            else:
                base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        mp4_directory = os.path.join(base_path, 'mp4')

        self.video_paths = [
            os.path.join(mp4_directory, 'tutorial_1.mp4'),
            os.path.join(mp4_directory, 'tutorial_2.mp4'),
            os.path.join(mp4_directory, 'tutorial_3.mp4'),
            os.path.join(mp4_directory, 'tutorial_4.mp4'),  # Previously tutorial_6.mp4
            os.path.join(mp4_directory, 'tutorial_5.mp4'),  # Previously tutorial_7.mp4
        ]

        # Optional: Log the video paths for debugging
        for path in self.video_paths:
            if not os.path.exists(path):
                logging.warning(f"Video file not found: {path}")


    def play_video(self, index):
        video_path = self.video_paths[index]
        if os.path.exists(video_path):
            try:
                if sys.platform.startswith('win'):  # Windows
                    os.startfile(video_path)
                elif sys.platform.startswith('darwin'):  # macOS
                    subprocess.run(['open', video_path], check=True)
                else:  # Linux and other Unix-like
                    subprocess.run(['xdg-open', video_path], check=True)
            except subprocess.SubprocessError as e:
                QMessageBox.warning(
                    self,
                    "Error Playing Video",
                    f"Could not play the video. Error: {str(e)}"
                )
                logging.error(f"Error playing video: {e}")
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

    def add_lang_item_en(self, text, data):
        # Get the border color for the current theme
        icon_size = 32 # Increased icon size
        pixmap = QPixmap(icon_size, icon_size)
        pixmap.fill(Qt.transparent)  # Start with transparent background
        painter = QPainter(pixmap)

        painter.setRenderHint(QPainter.Antialiasing, True)

        # Determine border color based on theme
        border_color = QColor("#000000")
        if self.current_theme == "dark":
            border_color = QColor("#ffffff")

        # Surround emoji with theme-dependent border
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(Qt.transparent)
        # Adjust border rect for new size
        painter.drawRoundedRect(2, 2, icon_size - 4, icon_size - 4, 4, 4)

        # Draw the US flag emoji - adjust font size if needed
        font = painter.font()
        font.setPointSize(font.pointSize() + 2) # Slightly larger emoji
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "🇺🇸")

        painter.end()
        self.language_combobox.addItem(QIcon(pixmap), text, data)
        self.language_combobox.setIconSize(pixmap.size()) # Ensure combobox uses the new size

    def add_lang_item_fr(self, text, data):
        # Get the border color for the current theme
        icon_size = 32 # Increased icon size
        pixmap = QPixmap(icon_size, icon_size)
        pixmap.fill(Qt.transparent)  # Start with transparent background
        painter = QPainter(pixmap)

        painter.setRenderHint(QPainter.Antialiasing, True)

        # Determine border color based on theme
        border_color = QColor("#000000")
        if self.current_theme == "dark":
            border_color = QColor("#ffffff")

        # Surround emoji with theme-dependent border
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(Qt.transparent)
        # Adjust border rect for new size
        painter.drawRoundedRect(2, 2, icon_size - 4, icon_size - 4, 4, 4)

        # Draw the French flag emoji - adjust font size if needed
        font = painter.font()
        font.setPointSize(font.pointSize() + 2) # Slightly larger emoji
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "🇫🇷")

        painter.end()
        self.language_combobox.addItem(QIcon(pixmap), text, data)
        self.language_combobox.setIconSize(pixmap.size()) # Ensure combobox uses the new size

    def add_lang_item_it(self, text, data):
        # Get the border color for the current theme
        icon_size = 32 # Increased icon size
        pixmap = QPixmap(icon_size, icon_size)
        pixmap.fill(Qt.transparent)  # Start with transparent background
        painter = QPainter(pixmap)

        painter.setRenderHint(QPainter.Antialiasing, True)

        # Determine border color based on theme
        border_color = QColor("#000000")
        if self.current_theme == "dark":
            border_color = QColor("#ffffff")

        # Surround emoji with theme-dependent border
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(Qt.transparent)
        # Adjust border rect for new size
        painter.drawRoundedRect(2, 2, icon_size - 4, icon_size - 4, 4, 4)

        # Draw the Italian flag emoji - adjust font size if needed
        font = painter.font()
        font.setPointSize(font.pointSize() + 2) # Slightly larger emoji
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "🇮🇹")

        painter.end()
        self.language_combobox.addItem(QIcon(pixmap), text, data)
        self.language_combobox.setIconSize(pixmap.size()) # Ensure combobox uses the new size

    def add_lang_item_es(self, text, data):
        # Get the border color for the current theme
        icon_size = 32 # Increased icon size
        pixmap = QPixmap(icon_size, icon_size)
        pixmap.fill(Qt.transparent)  # Start with transparent background
        painter = QPainter(pixmap)

        painter.setRenderHint(QPainter.Antialiasing, True)

        # Determine border color based on theme
        border_color = QColor("#000000")
        if self.current_theme == "dark":
            border_color = QColor("#ffffff")

        # Surround emoji with theme-dependent border
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(Qt.transparent)
        # Adjust border rect for new size
        painter.drawRoundedRect(2, 2, icon_size - 4, icon_size - 4, 4, 4)

        # Draw the Spanish flag emoji - adjust font size if needed
        font = painter.font()
        font.setPointSize(font.pointSize() + 2) # Slightly larger emoji
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "🇪🇸")

        painter.end()
        self.language_combobox.addItem(QIcon(pixmap), text, data)
        self.language_combobox.setIconSize(pixmap.size()) # Ensure combobox uses the new size

    def add_lang_item_pt(self, text, data):
        # Get the border color for the current theme
        icon_size = 32 # Increased icon size
        pixmap = QPixmap(icon_size, icon_size)
        pixmap.fill(Qt.transparent)  # Start with transparent background
        painter = QPainter(pixmap)

        painter.setRenderHint(QPainter.Antialiasing, True)

        # Determine border color based on theme
        border_color = QColor("#000000")
        if self.current_theme == "dark":
            border_color = QColor("#ffffff")

        # Surround emoji with theme-dependent border
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(Qt.transparent)
        # Adjust border rect for new size
        painter.drawRoundedRect(2, 2, icon_size - 4, icon_size - 4, 4, 4)

        # Draw the Portuguese flag emoji - adjust font size if needed
        font = painter.font()
        font.setPointSize(font.pointSize() + 2) # Slightly larger emoji
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "🇵🇹")

        painter.end()
        self.language_combobox.addItem(QIcon(pixmap), text, data)
        self.language_combobox.setIconSize(pixmap.size()) # Ensure combobox uses the new size

    def add_lang_item_he(self, text, data):
        # Get the border color for the current theme
        icon_size = 32 # Increased icon size
        pixmap = QPixmap(icon_size, icon_size)
        pixmap.fill(Qt.transparent)  # Start with transparent background
        painter = QPainter(pixmap)

        painter.setRenderHint(QPainter.Antialiasing, True)

        # Determine border color based on theme
        border_color = QColor("#000000")
        if self.current_theme == "dark":
            border_color = QColor("#ffffff")

        # Surround emoji with theme-dependent border
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(Qt.transparent)
        # Adjust border rect for new size
        painter.drawRoundedRect(2, 2, icon_size - 4, icon_size - 4, 4, 4)

        # Draw the Israeli flag emoji - adjust font size if needed
        font = painter.font()
        font.setPointSize(font.pointSize() + 2) # Slightly larger emoji
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "🇮🇱")

        painter.end()
        self.language_combobox.addItem(QIcon(pixmap), text, data)
        self.language_combobox.setIconSize(pixmap.size()) # Ensure combobox uses the new size

    def update_shadow_color_button(self):
        """Update the shadow color button appearance to reflect the current shadow color."""
        pixmap = QPixmap(30, 30)
        pixmap.fill(self.shadow_color)
        self.shadow_color_button.setIcon(QIcon(pixmap))
        self.shadow_color_button.setIconSize(pixmap.size())
        
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
            logging.info(f"SettingsDialog: Default arrow color enabled changed to {self.use_default_arrow_color}")

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
                logging.info(f"Updated default strand width button: text='{button_text}', text_width={text_width}, final_width={final_width}, screen_dpi={logical_dpi}")
            else:
                logging.info(f"Updated default strand width button: text='{button_text}', text_width={text_width}, final_width={final_width}")
        except:
            logging.info(f"Updated default strand width button: text='{button_text}', text_width={text_width}, final_width={final_width}")

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
                logging.info(f"Updated canvas default widths: strand_width={new_width}, stroke_width={new_stroke_width}")

    def populate_history_list(self):
        """Scans the temp_states directory and populates the history list."""
        self.history_list.clear()
        self.load_history_button.setEnabled(False) # Disable load button initially

        # Get translations based on current language
        _ = translations[self.current_language]

        if not self.undo_redo_manager:
            logging.warning("UndoRedoManager not available, cannot populate history.")
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
                            logging.warning(f"Could not parse step from filename: {filename}")
        except FileNotFoundError:
            logging.warning(f"History directory not found: {temp_dir}")
        except Exception as e:
            logging.error(f"Error reading history directory {temp_dir}: {e}")

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
                    logging.warning(f"Could not parse session ID {session_id}: {parse_e}")
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
            logging.warning("Selected history item has no associated filepath.")
            return
            
        # Confirmation might be good here, but prompt asks for OK anyway
        # Load the state using the undo/redo manager
        success = self.undo_redo_manager.load_specific_state(filepath)
        
        if success:
            logging.info(f"Successfully loaded history state from {filepath}")
            # Close the settings dialog after loading
            self.accept() # Use accept to signal successful operation if needed
        else:
            logging.error(f"Failed to load history state from {filepath}")
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
            logging.info(f"Found {len(all_files)} files in {temp_dir}: {', '.join(all_files)}")
            
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
                                logging.info(f"Deleted history file from other directory: {file_path}")
                            except Exception as e:
                                logging.error(f"Failed to delete {file_path}: {e}")
            
            # Now delete files in the main temp directory that don't belong to current session
            for filename in all_files:
                if filename.endswith(".json"):
                    # Keep only current session files
                    if not filename.startswith(current_session_id):
                        file_path = os.path.join(temp_dir, filename)
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                            logging.info(f"Deleted history file: {file_path}")
                        except Exception as e:
                            logging.error(f"Failed to delete {file_path}: {e}")
        except Exception as e:
            logging.error(f"Error while cleaning history directory: {e}")
        
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
            logging.info(f"SettingsDialog showEvent: Ensuring translations for '{self.current_language}'.")
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
            logging.info(f"SettingsDialog showEvent: Updated default arrow color checkbox to {self.use_default_arrow_color}")

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
        logging.info("=== BUTTON COLOR LAYOUT DEBUG INFO ===")
        
        if hasattr(self, 'button_color_container') and self.button_color_container:
            logging.info(f"Container geometry: {self.button_color_container.geometry()}")
            logging.info(f"Container size policy: {self.button_color_container.sizePolicy().horizontalPolicy()}")
            
        if hasattr(self, 'button_color_layout') and self.button_color_layout:
            logging.info(f"Layout count: {self.button_color_layout.count()}")
            logging.info(f"Layout geometry: {self.button_color_layout.geometry()}")
            logging.info(f"Layout spacing: {self.button_color_layout.spacing()}")
            logging.info(f"Layout margins: {self.button_color_layout.contentsMargins()}")
            
            for i in range(self.button_color_layout.count()):
                item = self.button_color_layout.itemAt(i)
                if item.widget():
                    widget = item.widget()
                    logging.info(f"  Widget {i} ({widget.__class__.__name__}): geometry={widget.geometry()}, visible={widget.isVisible()}, text='{getattr(widget, 'text', lambda: 'N/A')()}'")
                elif item.spacerItem():
                    spacer = item.spacerItem()
                    logging.info(f"  Spacer {i}: sizeHint={spacer.sizeHint()}, geometry={spacer.geometry()}")
                    
        if hasattr(self, 'button_color_label') and self.button_color_label:
            logging.info(f"Label: text='{self.button_color_label.text()}', geometry={self.button_color_label.geometry()}")
            logging.info(f"Label: font={self.button_color_label.font().toString()}, alignment={self.button_color_label.alignment()}")
            logging.info(f"Label: styleSheet='{self.button_color_label.styleSheet()}'")
            
        if hasattr(self, 'default_arrow_color_button') and self.default_arrow_color_button:
            logging.info(f"Button: geometry={self.default_arrow_color_button.geometry()}, visible={self.default_arrow_color_button.isVisible()}")
            
        logging.info("=== END BUTTON COLOR LAYOUT DEBUG INFO ===")

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
        logging.info(f"Loading video: {self.video_path}")
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
        logging.error(f"Media player error: {error_message}")
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
        
        # Buttons using QDialogButtonBox for consistent theme styling
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        # Localize standard buttons according to current language
        ok_btn = self.button_box.button(QDialogButtonBox.Ok)
        cancel_btn = self.button_box.button(QDialogButtonBox.Cancel)
        if ok_btn and 'ok' in _:
            ok_btn.setText(_['ok'])
        if cancel_btn and 'cancel' in _:
            cancel_btn.setText(_['cancel'])

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
    
    def update_percentage_label(self):
        """Update the percentage label when slider changes."""
        slider_value = self.color_slider.value()
        logging.info(f"[DefaultWidthConfigDialog] Color slider changed to {slider_value}%")
        # Get translations
        _ = translations.get(self.settings_dialog.current_language, translations['en'])
        percent_text = _['percent_available_color'] if 'percent_available_color' in _ else "% of Available Color Space"
        self.percentage_label.setText(f"{slider_value}{percent_text}")
    
    def update_preview(self):
        """Update the preview display keeping total thickness fixed."""
        total_grid_squares = self.thickness_spinbox.value()
        total_grid_width = total_grid_squares * self.grid_unit
        color_percentage = self.color_slider.value() / 100.0

        logging.info(f"[DefaultWidthConfigDialog] Preview updated - Grid squares: {total_grid_squares}, Color percentage: {color_percentage*100:.0f}%")

        # Compute widths
        color_width = total_grid_width * color_percentage
        stroke_width = (total_grid_width - color_width) / 2

        logging.info(f"[DefaultWidthConfigDialog] Calculated widths - Total: {total_grid_width}px, Color: {color_width:.0f}px, Stroke: {stroke_width:.0f}px each side")

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

        logging.info(
            f"DEFAULT WIDTH - Values: grid_total={total_grid_width}, color%={color_percentage*100:.0f}, color_width={color_width:.0f}, stroke_width={stroke_width:.0f}"
        )

        return int(color_width), int(stroke_width)