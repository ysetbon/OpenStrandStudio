from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QWidget, QLabel, QStackedWidget, QComboBox, QPushButton,
    QSpacerItem, QSizePolicy, QMessageBox, QTextBrowser, QSlider,
    QColorDialog, QCheckBox, QBoxLayout
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
        self.current_language = self.parent_window.language_code
        self.shadow_color = QColor(0, 0, 0, 150)  # Default shadow color
        self.draw_only_affected_strand = False  # Default to drawing all strands
        self.enable_third_control_point = False  # Default to two control points
        
        # Store the undo/redo manager
        self.undo_redo_manager = undo_redo_manager
        
        # Try to load settings from file first
        self.load_settings_from_file()
        
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
        
    # New method to update layout direction based on language
    def update_layout_direction(self):
        is_rtl = self.is_rtl_language(self.current_language)
        direction = Qt.RightToLeft if is_rtl else Qt.LeftToRight

        self.setLayoutDirection(direction)
        
        # Apply layout direction to widgets
        if hasattr(self, 'general_settings_widget'):
            self.general_settings_widget.setLayoutDirection(direction)

        if hasattr(self, 'change_language_widget'):
            self.change_language_widget.setLayoutDirection(direction)
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
        if is_rtl:
            combo_style_adjustments = """
                QComboBox {
                    padding-left: 30px; 
                    padding-right: 0px;
                    margin-right: 0px;
                    text-align: right !important;
                    direction: rtl;
                }
                QComboBox::drop-down {
                    subcontrol-origin: padding;
                    subcontrol-position: left top;
                    left: 5px;
                    border: none;
                    width: 20px;
                }

                QComboBox QAbstractItemView {
                    direction: rtl;
                    text-align: right !important;
                }
            """
            # Add styling for checkboxes in RTL mode
            checkbox_style = """
                QCheckBox {
                    spacing: 0px;
                }
                QCheckBox::indicator {
                    width: 13px;
                    height: 13px;
                }
            """
            
            # Apply checkbox style to all checkboxes
            for checkbox in self.findChildren(QCheckBox):
                checkbox.setStyleSheet(checkbox_style)
                # Set layout direction to RTL for the checkbox itself
                checkbox.setLayoutDirection(Qt.RightToLeft)

        else: # LTR
            combo_style_adjustments = """
                QComboBox {
                    padding-left: 8px;
                    padding-right: 24px;
                    text-align: left;
                    direction: ltr;
                }
                QComboBox::drop-down {
                    border: none;
                    padding-right: 8px;
                }
                QComboBox::down-arrow:after {
                    right: 8px;
                    left: auto;
                }
            """
            
        if hasattr(self, 'theme_combobox'):
            self.theme_combobox.setLayoutDirection(direction)
            self.theme_combobox.view().setLayoutDirection(direction)
            # Get current style, append adjustments
            current_style = self.theme_combobox.styleSheet() # Get theme/base style
            self.theme_combobox.setStyleSheet(current_style + "\n" + combo_style_adjustments)
            
            # Apply the same RTL fixes to theme combobox
            if is_rtl:
                # Force the list items in the dropdown to be right-aligned
                view = self.theme_combobox.view()
                if view:
                    view.setTextElideMode(Qt.ElideLeft)  # Elide left for RTL text
                
                # Update item text alignment
                if self.theme_combobox.count() > 0:
                    # Apply text alignment to each item
                    for i in range(self.theme_combobox.count()):
                        item_text = self.theme_combobox.itemText(i)
                        # This triggers a redraw of the item with proper RTL
                        self.theme_combobox.setItemText(i, item_text)

        if hasattr(self, 'language_combobox'):
            self.language_combobox.setLayoutDirection(direction)
            self.language_combobox.view().setLayoutDirection(direction)
            # Get current style, append adjustments
            current_style = self.language_combobox.styleSheet() # Get theme/base style
            self.language_combobox.setStyleSheet(current_style + "\n" + combo_style_adjustments)
            
            # Force the view to update its layout direction as well
            if is_rtl:
                # Check if the combobox has a lineEdit (editable combobox)
                try:
                    lineEdit = self.language_combobox.lineEdit()
                    if lineEdit:
                        lineEdit.setAlignment(Qt.AlignRight)
                except:
                    pass
                
                # Force the list items in the dropdown to be right-aligned
                view = self.language_combobox.view()
                if view:
                    view.setTextElideMode(Qt.ElideLeft)  # Elide left for RTL text
            
            # If the combobox has items, update their text alignment
            if is_rtl and self.language_combobox.count() > 0:
                # Apply text alignment to each item
                for i in range(self.language_combobox.count()):
                    item_text = self.language_combobox.itemText(i)
                    # Re-add the item with the same data but RTL-aware text
                    item_data = self.language_combobox.itemData(i)
                    # This triggers a redraw of the item with proper RTL
                    self.language_combobox.setItemText(i, item_text)

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
                
                logging.info(f"SettingsDialog: User settings loaded successfully. Theme: {self.current_theme}, Language: {self.current_language}, Shadow Color: {self.shadow_color.red()},{self.shadow_color.green()},{self.shadow_color.blue()},{self.shadow_color.alpha()}, Draw Only Affected Strand: {self.draw_only_affected_strand}, Enable Third Control Point: {self.enable_third_control_point}")
            except Exception as e:
                logging.error(f"SettingsDialog: Error reading user settings: {e}. Using default values.")
        else:
            logging.info(f"SettingsDialog: Settings file not found at {file_path}. Using default settings.")

    def setup_ui(self):
        _ = translations[self.current_language]
        main_layout = QHBoxLayout(self)
        
        # Set layout margins to ensure consistent spacing
        main_layout.setContentsMargins(20, 20, 20, 20)
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
        theme_layout = QHBoxLayout()
        self.theme_label = QLabel(_['select_theme'])
        self.theme_combobox = QComboBox()
        
        # Modified theme combobox stylesheet
        self.theme_combobox_base_style = f""" \
            QComboBox {{ \
                padding: 8px; \
                padding-right: 24px; \
                border: 1px solid #cccccc; \
                border-radius: 4px; \
                min-width: 150px; \
                font-size: 14px; \
            }} \
            QComboBox:hover {{ \
                background-color: {theme_hover_color}; \
            }} \
            QComboBox::drop-down {{ \
                border: none; \
                width: 24px; \
            }} \
            QComboBox::down-arrow {{ \
                image: none; \
                width: 24px; \
                height: 24px; \
            }} \
            QComboBox::down-arrow:after {{ \
                content: "▼"; \
                color: #666666; \
                position: absolute; \
                top: 0; \
                right: 8px; \
                font-size: 12px; \
            }} \
            QComboBox QAbstractItemView {{ \
                padding: 8px; \
                selection-background-color: {selection_color}; \
            }} \
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
        theme_layout.addWidget(self.theme_label)
        theme_layout.addWidget(self.theme_combobox)

        # Shadow Color Selection
        shadow_layout = QHBoxLayout()
        self.shadow_color_label = QLabel(_['shadow_color'] if 'shadow_color' in _ else "Shadow Color")
        if self.is_rtl_language(self.current_language):
            print("RTL language detected")
            self.shadow_color_label.setMinimumWidth(70)
        self.shadow_color_button = QPushButton()
        self.shadow_color_button.setFixedSize(30, 30)
        self.update_shadow_color_button()
        self.shadow_color_button.clicked.connect(self.choose_shadow_color)
        shadow_layout.addWidget(self.shadow_color_label)
        # Add alignment for RTL languages
        if self.is_rtl_language(self.current_language) != True:
            shadow_layout.addWidget(self.shadow_color_button)
        else:
            shadow_layout.addWidget(self.shadow_color_button, 0, Qt.AlignLeft)
        shadow_layout.addStretch()

        # Performance Settings - Option to draw only affected strand during dragging
        performance_layout = QHBoxLayout()
        self.affected_strand_label = QLabel(_['draw_only_affected_strand'] if 'draw_only_affected_strand' in _ else "Draw only affected strand when dragging")
        self.affected_strand_checkbox = QCheckBox()
        self.affected_strand_checkbox.setChecked(self.draw_only_affected_strand)
        performance_layout.addWidget(self.affected_strand_label)
        performance_layout.addWidget(self.affected_strand_checkbox)
        performance_layout.addStretch()

        # Third Control Point Option
        third_control_layout = QHBoxLayout()
        self.third_control_label = QLabel(_['enable_third_control_point'] if 'enable_third_control_point' in _ else "Enable third control point at center")
        self.third_control_checkbox = QCheckBox()
        self.third_control_checkbox.setChecked(self.enable_third_control_point)
        third_control_layout.addWidget(self.third_control_label)
        third_control_layout.addWidget(self.third_control_checkbox)
        third_control_layout.addStretch()

        # Apply Button
        self.apply_button = QPushButton(_['ok'])
        self.apply_button.clicked.connect(self.apply_all_settings)

        # Spacer to push the apply button to the bottom
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        # Add controls to general settings layout
        general_layout.addLayout(theme_layout)
        general_layout.addLayout(shadow_layout)
        general_layout.addLayout(performance_layout)
        general_layout.addLayout(third_control_layout)
        general_layout.addItem(spacer)
        general_layout.addWidget(self.apply_button)

        self.stacked_widget.addWidget(self.general_settings_widget)

        # Change Language Page (index 1)
        self.change_language_widget = QWidget()
        language_layout = QVBoxLayout(self.change_language_widget)

        # Language Selection
        self.language_label = QLabel(_['select_language'])
        self.language_combobox = QComboBox()

        # Modified language combobox stylesheet
        self.lang_combobox_base_style = f""" \
            QComboBox {{ \
                padding: 8px; \
                padding-right: 24px; \
                border: 1px solid #cccccc; \
                border-radius: 4px; \
                min-width: 200px; \
                font-size: 14px; \
            }} \
            QComboBox:hover {{ \
                background-color: {lang_hover_color}; \
            }} \
            QComboBox::drop-down {{ \
                border: none; \
                width: 24px; \
            }} \
            QComboBox::down-arrow {{ \
                image: none; \
                width: 24px; \
                height: 24px; \
            }} \
            QComboBox::down-arrow:after {{ \
                content: "▼"; \
                color: #666666; \
                position: absolute; \
                top: 0; \
                right: 8px; \
                font-size: 12px; \
            }} \
            QComboBox QAbstractItemView {{ \
                padding: 8px; \
                min-width: 200px; \
                selection-background-color: {selection_color}; \
                text-align: right; \
            }} \
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
        # Add widgets to layout with alignment flags
        if self.is_rtl_language(self.current_language) != True:
            language_layout.addWidget(self.language_label, 0, Qt.AlignLeft) # Default alignment, will be updated
            language_layout.addWidget(self.language_combobox, 0, Qt.AlignLeft)
        else:
            language_layout.addWidget(self.language_label, 0, Qt.AlignLeft) # Default alignment, will be updated
            language_layout.addWidget(self.language_combobox, 0, Qt.AlignRight)
        language_layout.addWidget(self.language_info_label, 0, Qt.AlignLeft) # Default alignment, will be updated

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

        # Use QTextBrowser for What's New info - Part 1 (Undo/Redo)
        self.whats_new_text_browser_part1 = QTextBrowser()
        self.whats_new_text_browser_part1.setHtml(_['whats_new_info_part1'])
        self.whats_new_text_browser_part1.setOpenExternalLinks(True)
        self.whats_new_text_browser_part1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        whats_new_layout.addWidget(self.whats_new_text_browser_part1)

        # Add Undo/Redo icons and labels
        self.icon_layout = QHBoxLayout()
        self.icon_layout.addStretch()
        self.undo_icon_label = QLabel(_['undo_icon_label'])
        self.undo_icon_widget = QLabel()
        self.undo_icon_widget.setFixedSize(40, 40)
        self.update_icon_widget(self.undo_icon_widget, '↶')
        if self.is_rtl_language(self.current_language) != True:
            
            self.icon_layout.addWidget(self.undo_icon_label)
            self.icon_layout.addWidget(self.undo_icon_widget)
            # Add the label second
        else:
            
            self.icon_layout.addWidget(self.undo_icon_widget)
            self.icon_layout.addWidget(self.undo_icon_label)
        self.icon_layout.addSpacing(20)
        self.redo_icon_label = QLabel(_['redo_icon_label'])
        self.redo_icon_widget = QLabel()
        self.redo_icon_widget.setFixedSize(40, 40)
        self.update_icon_widget(self.redo_icon_widget, '↷')
        if self.is_rtl_language(self.current_language) != True:
            
            self.icon_layout.addWidget(self.redo_icon_label)
            self.icon_layout.addWidget(self.redo_icon_widget)
        else:
            self.icon_layout.addWidget(self.redo_icon_widget)
            self.icon_layout.addWidget(self.redo_icon_label)
            
        self.icon_layout.addStretch()
        whats_new_layout.addLayout(self.icon_layout)

        # Use QTextBrowser for What's New info - Combined History/CP Text
        self.whats_new_text_browser_history_cp = QTextBrowser()
        self.whats_new_text_browser_history_cp.setHtml(_['whats_new_history_cp_text'])
        self.whats_new_text_browser_history_cp.setOpenExternalLinks(True)
        self.whats_new_text_browser_history_cp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        whats_new_layout.addWidget(self.whats_new_text_browser_history_cp)

        # Add Third Control Point Icon Layout
        self.third_cp_icon_layout = QHBoxLayout()
        self.third_cp_icon_layout.addStretch()
        self.third_cp_icon_label = QLabel(_['third_cp_icon_label'])
        self.third_cp_icon_widget = QLabel()
        self.third_cp_icon_widget.setFixedSize(40, 40)
        self.update_third_cp_icon_widget(self.third_cp_icon_widget)
        if self.is_rtl_language(self.current_language) != True:
            self.third_cp_icon_layout.addWidget(self.third_cp_icon_label)
            self.third_cp_icon_layout.addWidget(self.third_cp_icon_widget)
        else:
            self.third_cp_icon_layout.addWidget(self.third_cp_icon_widget)
            self.third_cp_icon_layout.addWidget(self.third_cp_icon_label)
        self.third_cp_icon_layout.addStretch()
        whats_new_layout.addLayout(self.third_cp_icon_layout)

        # Use QTextBrowser for What's New info - Bug Fixes
        self.whats_new_text_browser_bugs = QTextBrowser()
        self.whats_new_text_browser_bugs.setHtml(_['whats_new_bug_fixes_text'])
        self.whats_new_text_browser_bugs.setOpenExternalLinks(True)
        self.whats_new_text_browser_bugs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        whats_new_layout.addWidget(self.whats_new_text_browser_bugs)

        whats_new_layout.addStretch()

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
            *self.video_buttons,  # Unpack video buttons list
            self.load_history_button, # Style history buttons
            self.clear_history_button
        ]
        
        for button in buttons:
            button.setFixedHeight(32)  # Match MainWindow button height
            button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            button.setMinimumWidth(120)  # Set minimum width for buttons

    def apply_dialog_theme(self, theme_name):
        """Apply theme to dialog components"""
        if theme_name == "dark":
            button_style = """
                /* Main dialog background */
                QDialog {
                    background-color: #2C2C2C;
                    color: white;
                }
                
                /* Buttons */
                QPushButton {
                    background-color: #3D3D3D;
                    color: white;
                    border: 1px solid #505050;
                    padding: 8px 16px;
                    border-radius: 4px;
                    height: 32px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #4D4D4D;
                }
                QPushButton:pressed {
                    background-color: #2D2D2D;
                }
                QPushButton:checked {
                    background-color: #505050;
                    border: 2px solid #808080;
                }
                
                /* ComboBox */
                QComboBox {
                    background-color: #3D3D3D;
                    color: white;
                    border: 1px solid #505050;
                    padding: 5px;
                    border-radius: 4px;
                    min-width: 150px;
                }
                QComboBox:hover {
                    background-color: #4D4D4D;
                }
                QComboBox:drop-down {
                    border: none;
                    padding-right: 8px;
                }
                QComboBox::down-arrow {
                    image: none;
                    border: none;
                }
                QComboBox QAbstractItemView {
                    background-color: #3D3D3D;
                    color: white;
                    selection-background-color: #505050;
                    selection-color: white;
                    border: 1px solid #505050;
                }
                
                /* List Widget */
                QListWidget {
                    background-color: #3D3D3D;
                    color: white;
                    border: 1px solid #505050;
                    border-radius: 4px;
                }
                QListWidget::item {
                    padding: 8px;
                }
                QListWidget::item:selected {
                    background-color: #505050;
                    color: white;
                }
                QListWidget::item:hover {
                    background-color: #4D4D4D;
                }
                
                /* Labels */
                QLabel {
                    color: white;
                }
                
                /* Text Browser */
                QTextBrowser {
                    background-color: #3D3D3D;
                    color: white;
                    border: 1px solid #505050;
                    border-radius: 4px;
                    padding: 8px;
                }
                
                /* Scroll Bars */
                QScrollBar:vertical {
                    background-color: #2C2C2C;
                    width: 12px;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical {
                    background-color: #505050;
                    border-radius: 6px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #606060;
                }
                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical {
                    height: 0px;
                }
                QScrollBar::add-page:vertical,
                QScrollBar::sub-page:vertical {
                    background-color: #2C2C2C;
                }
                
                /* Horizontal Scroll Bar */
                QScrollBar:horizontal {
                    background-color: #2C2C2C;
                    height: 12px;
                    border-radius: 6px;
                }
                QScrollBar::handle:horizontal {
                    background-color: #505050;
                    border-radius: 6px;
                    min-width: 20px;
                }
                QScrollBar::handle:horizontal:hover {
                    background-color: #606060;
                }
                QScrollBar::add-line:horizontal,
                QScrollBar::sub-line:horizontal {
                    width: 0px;
                }
                QScrollBar::add-page:horizontal,
                QScrollBar::sub-page:horizontal {
                    background-color: #2C2C2C;
                }
                
                /* Widgets */
                QWidget {
                    background-color: #2C2C2C;
                    color: white;
                }
                
                /* Stacked Widget */
                QStackedWidget {
                    background-color: #2C2C2C;
                    color: white;
                }
            """
        elif theme_name == "light":
            button_style = """
                QPushButton {
                    background-color: #F0F0F0;
                    color: black;
                    border: 1px solid #CCCCCC;
                    padding: 8px 16px;
                    border-radius: 4px;
                    height: 32px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #E0E0E0;
                }
                QPushButton:pressed {
                    background-color: #D0D0D0;
                }
                QPushButton:checked {
                    background-color: #E0E0E0;
                    border: 2px solid #A0A0A0;
                }
                QComboBox {
                    background-color: white;
                    color: black;
                    border: 1px solid #CCCCCC;
                    padding: 5px;
                    border-radius: 4px;
                    min-width: 150px;
                }
                QListWidget {
                    background-color: white;
                    color: black;
                    border: 1px solid #CCCCCC;
                }
                QLabel {
                    color: black;
                }
                QTextBrowser {
                    background-color: white;
                    color: black;
                    border: 1px solid #CCCCCC;
                }
            """
        else:  # default theme
            button_style = """
                QPushButton {
                    background-color: #E8E8E8;
                    color: black;
                    border: 1px solid #CCCCCC;
                    padding: 8px 16px;
                    border-radius: 4px;
                    height: 32px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #DADADA;
                }
                QPushButton:pressed {
                    background-color: #C8C8C8;
                }
                QPushButton:checked {
                    background-color: #D0D0D0;
                    border: 2px solid #A0A0A0;
                }
                QComboBox {
                    background-color: #F5F5F5;
                    color: black;
                    border: 1px solid #CCCCCC;
                    padding: 5px;
                    border-radius: 4px;
                    min-width: 150px;
                }
                QListWidget {
                    background-color: #F5F5F5;
                    color: black;
                    border: 1px solid #CCCCCC;
                }
                QLabel {
                    color: black;
                }
                QTextBrowser {
                    background-color: #F5F5F5;
                    color: black;
                    border: 1px solid #CCCCCC;
                }
            """

        self.setStyleSheet(button_style)
        self.style_dialog_buttons()

    def apply_all_settings(self):
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
            # Force redraw of language-specific elements
            self.repaint()
        
        # Save all settings to file
        self.save_settings_to_file()

        # Apply the theme to the dialog before hiding
        self.apply_dialog_theme(self.current_theme)
        self.hide()

    def change_category(self, item):
        index = self.categories_list.row(item)
        self.stacked_widget.setCurrentIndex(index)

    def update_translations(self):
        _ = translations[self.current_language]
        self.setWindowTitle(_['settings'])
        # Update category names
        self.categories_list.item(0).setText(_['general_settings'])
        self.categories_list.item(1).setText(_['change_language'])
        self.categories_list.item(2).setText(_['tutorial'])
        self.categories_list.item(3).setText(_['history']) # Update history category name
        self.categories_list.item(4).setText(_['whats_new']) # Update what's new category name
        self.categories_list.item(5).setText(_['about']) # Adjust index for About
        # Update labels and buttons
        self.theme_label.setText(_['select_theme'])
        self.shadow_color_label.setText(_['shadow_color'] if 'shadow_color' in _ else "Shadow Color")
        self.affected_strand_label.setText(_['draw_only_affected_strand'] if 'draw_only_affected_strand' in _ else "Draw only affected strand when dragging")
        self.third_control_label.setText(_['enable_third_control_point'] if 'enable_third_control_point' in _ else "Enable third control point at center")
        self.apply_button.setText(_['ok'])
        self.language_ok_button.setText(_['ok'])
        self.language_label.setText(_['select_language'])
        # Update information labels
        self.language_info_label.setText(_['language_settings_info'])
        self.tutorial_label.setText(_['tutorial_info'])
        # Update about text browser instead of label
        self.about_text_browser.setHtml(_['about_info'])
        # Update history page elements
        self.history_explanation_label.setText(_['history_explanation'])
        self.load_history_button.setText(_['load_selected_history'])
        self.clear_history_button.setText(_['clear_all_history'])
        # Update What's New page elements
        self.whats_new_text_browser_part1.setHtml(_['whats_new_info_part1'])
        self.whats_new_text_browser_history_cp.setHtml(_['whats_new_history_cp_text'])
        self.whats_new_text_browser_bugs.setHtml(_['whats_new_bug_fixes_text'])
        # Find labels within the icon layout to update text
        if hasattr(self, 'icon_layout'):
            for i in range(self.icon_layout.count()):
                item = self.icon_layout.itemAt(i)
                if isinstance(item.widget(), QLabel):
                    widget = item.widget()
                    # Use more robust identification if possible
                    if widget == self.undo_icon_label:
                        widget.setText(_['undo_icon_label'])
                    elif widget == self.redo_icon_label:
                        widget.setText(_['redo_icon_label'])
                    # Check if it is one of the icon widgets we need to redraw
                    elif widget == self.undo_icon_widget:
                        self.update_icon_widget(widget, '↶')
                    elif widget == self.redo_icon_widget:
                        self.update_icon_widget(widget, '↷')
                    # Check for the new third CP icon label and widget
                    elif widget == self.third_cp_icon_label:
                        widget.setText(_['third_cp_icon_label'])
                    elif widget == self.third_cp_icon_widget:
                        self.update_third_cp_icon_widget(widget)
        else:
            logging.warning("self.icon_layout or self.third_cp_icon_layout not found during translation update.")

        # Add separate handling for third_cp_icon_layout
        if hasattr(self, 'third_cp_icon_layout'):
            for i in range(self.third_cp_icon_layout.count()):
                item = self.third_cp_icon_layout.itemAt(i)
                if isinstance(item.widget(), QLabel):
                    widget = item.widget()
                    if widget == self.third_cp_icon_label:
                        widget.setText(_['third_cp_icon_label'])
                    elif widget == self.third_cp_icon_widget:
                        self.update_third_cp_icon_widget(widget)

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
        
        # For Hebrew, adjust text in the combobox to get proper positioning
        if self.is_rtl_language(self.current_language):
            # Apply RTL text positioning to comboboxes
            self.theme_combobox.setItemText(0, "        " + _['default'])  # Add space to move text closer to checkbox
            self.theme_combobox.setItemText(1, "        " + _['light'])
            self.theme_combobox.setItemText(2, "        " + _['dark'])
            
            # Add padding to the Hebrew item in the language combobox
            hebrew_index = self.language_combobox.findData('he')
            self.language_combobox.setItemText(hebrew_index, "           " + _['hebrew'])
            english_index = self.language_combobox.findData('en')
            self.language_combobox.setItemText(english_index, "           " + _['english'])
            french_index = self.language_combobox.findData('fr')
            self.language_combobox.setItemText(french_index, "           " + _['french'])
            italian_index = self.language_combobox.findData('it')
            self.language_combobox.setItemText(italian_index, "           " + _['italian'])
            spanish_index = self.language_combobox.findData('es')
            self.language_combobox.setItemText(spanish_index, "           " + _['spanish'])
            portuguese_index = self.language_combobox.findData('pt')
            self.language_combobox.setItemText(portuguese_index, "           " + _['portuguese'])

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
                 # *** Add condition to skip shadow color label in RTL ***
                 if widget == self.shadow_color_label and rtl:
                     continue
                 if parent_layout != self.icon_layout and parent_layout != self.third_cp_icon_layout: # Check it's not an icon label before aligning
                    widget.setAlignment(alignment)
                    if rtl:
                        widget.setLayoutDirection(Qt.RightToLeft)
                    else:
                        widget.setLayoutDirection(Qt.LeftToRight)

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
            print(f"Settings saved to {file_path} with Shadow Color: {self.shadow_color.red()},{self.shadow_color.green()},{self.shadow_color.blue()},{self.shadow_color.alpha()}, Draw Only Affected Strand: {self.draw_only_affected_strand}, Enable Third Control Point: {self.enable_third_control_point}")
            logging.info(f"Settings saved to {file_path} with Shadow Color: {self.shadow_color.red()},{self.shadow_color.green()},{self.shadow_color.blue()},{self.shadow_color.alpha()}, Draw Only Affected Strand: {self.draw_only_affected_strand}, Enable Third Control Point: {self.enable_third_control_point}")
            
            # Create a copy in the root directory for easier viewing (optional)
            try:
                local_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'user_settings.txt')
                with open(local_file_path, 'w', encoding='utf-8') as local_file:
                    local_file.write(f"Theme: {self.current_theme}\n")
                    local_file.write(f"Language: {self.current_language}\n")
                    local_file.write(f"ShadowColor: {self.shadow_color.red()},{self.shadow_color.green()},{self.shadow_color.blue()},{self.shadow_color.alpha()}\n")
                    local_file.write(f"DrawOnlyAffectedStrand: {str(self.draw_only_affected_strand).lower()}\n")
                    local_file.write(f"EnableThirdControlPoint: {str(self.enable_third_control_point).lower()}\n")
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

        super().showEvent(event) # Call parent method AFTER ensuring translations

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