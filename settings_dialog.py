from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QWidget, QLabel, QStackedWidget, QComboBox, QPushButton,
    QSpacerItem, QSizePolicy, QMessageBox, QTextBrowser, QSlider
)
from PyQt5.QtCore import Qt, pyqtSignal, QUrl
from PyQt5.QtGui import QIcon, QFont, QPainter, QPen, QColor, QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from translations import translations
import logging
import os
import sys
import subprocess
import sys
from PyQt5.QtCore import QStandardPaths

class SettingsDialog(QDialog):
    theme_changed = pyqtSignal(str)

    def __init__(self, parent=None, canvas=None):
        super(SettingsDialog, self).__init__(parent)
        self.canvas = canvas
        self.parent_window = parent
        self.current_theme = getattr(parent, 'current_theme', 'default')
        self.current_language = self.parent_window.language_code
        self.setWindowTitle(translations[self.current_language]['settings'])
        
        # Set fixed size for the dialog
        self.setFixedSize(800, 600)
        
        # Set window flags to prevent resizing
        self.setWindowFlags(Qt.Dialog | Qt.MSWindowsFixedSizeDialogHint)
        
        self.video_paths = []  # Initialize the list to store video paths
        self.setup_ui()
        self.load_video_paths()
        
        # Apply initial theme
        self.apply_dialog_theme(self.current_theme)

    def setup_ui(self):
        _ = translations[self.parent_window.language_code]
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
            _['about']
        ]
        for category in categories:
            item = QListWidgetItem(category)
            item.setTextAlignment(Qt.AlignCenter)
            self.categories_list.addItem(item)

        # Right side: stacked widget for different settings pages
        self.stacked_widget = QStackedWidget()

        # General Settings Page
        self.general_settings_widget = QWidget()
        general_layout = QVBoxLayout(self.general_settings_widget)

        # Theme Selection
        theme_layout = QHBoxLayout()
        self.theme_label = QLabel(_['select_theme'])
        self.theme_combobox = QComboBox()
        
        # Modified theme combobox stylesheet
        self.theme_combobox.setStyleSheet(f"""
            QComboBox {{
                padding: 8px;
                padding-right: 24px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                min-width: 150px;
                font-size: 14px;
            }}
            QComboBox:hover {{
                background-color: {theme_hover_color};
                
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: none;
                width: 24px;
                height: 24px;
            }}
            QComboBox::down-arrow:after {{
                content: "▼";
                color: #666666;
                position: absolute;
                top: 0;
                right: 8px;
                font-size: 12px;
            }}
            QComboBox QAbstractItemView {{
                padding: 8px;
                selection-background-color: {selection_color};
                
            }}
        """)
        
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

        # Apply Button
        self.apply_button = QPushButton(_['ok'])
        self.apply_button.clicked.connect(self.apply_all_settings)

        # Spacer to push the apply button to the bottom
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        # Add controls to general settings layout
        general_layout.addLayout(theme_layout)
        general_layout.addItem(spacer)
        general_layout.addWidget(self.apply_button)

        self.stacked_widget.addWidget(self.general_settings_widget)

        # Change Language Page
        self.change_language_widget = QWidget()
        language_layout = QVBoxLayout(self.change_language_widget)

        # Language Selection
        self.language_label = QLabel(_['select_language'])
        self.language_combobox = QComboBox()

        # Modified language combobox stylesheet
        self.language_combobox.setStyleSheet(f"""
            QComboBox {{
                padding: 8px;
                padding-right: 24px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                min-width: 200px;
                font-size: 14px;
            }}
            QComboBox:hover {{
                background-color: {lang_hover_color};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: none;
                width: 24px;
                height: 24px;
            }}
            QComboBox::down-arrow:after {{
                content: "▼";
                color: #666666;
                position: absolute;
                top: 0;
                right: 8px;
                font-size: 12px;
            }}
            QComboBox QAbstractItemView {{
                padding: 8px;
                min-width: 200px;
                selection-background-color: {selection_color};
            }}
        """)
        
        # Add language items with generated icons
        self.add_lang_item_en(_['english'], 'en')
        self.add_lang_item_fr(_['french'], 'fr')
        
        # Set the current language
        current_language = getattr(self, 'current_language', 'en')
        index = self.language_combobox.findData(current_language)
        if index >= 0:
            self.language_combobox.setCurrentIndex(index)

        self.language_info_label = QLabel(_['language_settings_info'])
        language_layout.addWidget(self.language_label)
        language_layout.addWidget(self.language_combobox)
        language_layout.addWidget(self.language_info_label)

        # Add the "OK" button
        self.language_ok_button = QPushButton(_['ok'])
        self.language_ok_button.clicked.connect(self.apply_all_settings)
        language_layout.addWidget(self.language_ok_button)

        self.stacked_widget.addWidget(self.change_language_widget)

        # Tutorial Page
        self.tutorial_widget = QWidget()
        tutorial_layout = QVBoxLayout(self.tutorial_widget)

        # Add a tutorial label
        self.tutorial_label = QLabel(_['tutorial_info'])
        tutorial_layout.addWidget(self.tutorial_label)

        self.video_buttons = []

        for i in range(5):  # Changed from 7 to 5 tutorials
            # Explanation Label
            explanation_label = QLabel(_[f'gif_explanation_{i+1}'])
            tutorial_layout.addWidget(explanation_label)

            # Play Video Button
            play_button = QPushButton(_['play_video'])
            tutorial_layout.addWidget(play_button)
            play_button.clicked.connect(lambda checked, idx=i: self.play_video(idx))
            self.video_buttons.append(play_button)

        self.stacked_widget.addWidget(self.tutorial_widget)

        # About Page
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

        # Apply Language Settings
        language_code = self.language_combobox.currentData()
        # Update the language in the main window
        self.parent_window.set_language(language_code)
        # Update the canvas language code and emit the signal
        if self.canvas:
            self.canvas.language_code = language_code
            self.canvas.language_changed.emit()
        else:
            # Emit language_changed signal from the parent window
            self.parent_window.language_changed.emit()

        # Store the selected language code
        self.current_language = language_code

        # Save settings to file
        self.save_settings_to_file()

        # Apply the theme to the dialog before hiding
        self.apply_dialog_theme(self.current_theme)
        self.hide()

    def change_category(self, item):
        index = self.categories_list.row(item)
        self.stacked_widget.setCurrentIndex(index)

    def update_translations(self):
        _ = translations[self.parent_window.language_code]
        self.setWindowTitle(_['settings'])
        # Update category names
        self.categories_list.item(0).setText(_['general_settings'])
        self.categories_list.item(1).setText(_['change_language'])
        self.categories_list.item(2).setText(_['tutorial'])
        self.categories_list.item(3).setText(_['about'])
        # Update labels and buttons
        self.theme_label.setText(_['select_theme'])
        self.apply_button.setText(_['ok'])
        self.language_ok_button.setText(_['ok'])
        self.language_label.setText(_['select_language'])
        # Update information labels
        self.language_info_label.setText(_['language_settings_info'])
        self.tutorial_label.setText(_['tutorial_info'])
        # Update about text browser instead of label
        self.about_text_browser.setHtml(_['about_info'])
        # Update theme combobox items
        self.theme_combobox.setItemText(0, _['default'])
        self.theme_combobox.setItemText(1, _['light'])
        self.theme_combobox.setItemText(2, _['dark'])
        # Update language combobox items
        self.language_combobox.setItemText(0, _['english'])
        self.language_combobox.setItemText(1, _['french'])
        # Update tutorial explanations and play buttons
        for i in range(5):  # Changed from 7 to 5
            index = i * 2  # Since each explanation and button are added sequentially
            explanation_label = self.tutorial_widget.layout().itemAt(index + 1).widget()
            explanation_label.setText(_[f'gif_explanation_{i+1}'])
            play_button = self.video_buttons[i]
            play_button.setText(_['play_video'])

    def save_settings_to_file(self):
        # Use the stored current theme and language
        current_theme = getattr(self, 'current_theme', 'default')
        current_language = getattr(self, 'current_language', 'en')

        # Use the appropriate directory for each OS
        app_name = "OpenStrand Studio"
        if sys.platform == 'darwin':  # macOS
            program_data_dir = os.path.expanduser('~/Library/Application Support')
            settings_dir = os.path.join(program_data_dir, app_name)
        else:
            program_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            settings_dir = program_data_dir  # AppDataLocation already includes the app name
        
        # Ensure directory exists with proper permissions
        if not os.path.exists(settings_dir):
            try:
                os.makedirs(settings_dir, mode=0o755)  # Add mode for proper permissions
                logging.info(f"Created settings directory: {settings_dir}")
            except Exception as e:
                logging.error(f"Cannot create directory {settings_dir}: {e}")
                return

        file_path = os.path.join(settings_dir, 'user_settings.txt')
        
        # Write the settings to the file with error handling
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(f"Theme: {self.current_theme}\n")
                file.write(f"Language: {self.current_language}\n")
            logging.info(f"Settings saved to {file_path}")
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
        pixmap = QPixmap(26, 26)
        pixmap.fill(QColor("#cccccc"))
        painter = QPainter(pixmap)

        painter.setRenderHint(QPainter.Antialiasing, True)

        # Surround emoji with theme-dependent border
        painter.setPen(QPen(QColor("#000000"), 2))
        painter.setBrush(Qt.transparent)
        painter.drawRoundedRect(2, 2, 22, 22, 4, 4)

        # Draw the US flag emoji
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "🇺🇸")

        painter.end()
        self.language_combobox.addItem(QIcon(pixmap), text, data)

    def add_lang_item_fr(self, text, data):
        # Get the border color for the current theme
        pixmap = QPixmap(26, 26)
        pixmap.fill(QColor("#cccccc"))
        painter = QPainter(pixmap)

        painter.setRenderHint(QPainter.Antialiasing, True)

        # Surround emoji with theme-dependent border
        painter.setPen(QPen(QColor("#000000"), 2))
        painter.setBrush(Qt.transparent)
        painter.drawRoundedRect(2, 2, 22, 22, 4, 4)

        # Draw the French flag emoji
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "🇫🇷")

        painter.end()
        self.language_combobox.addItem(QIcon(pixmap), text, data)



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