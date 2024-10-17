from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QWidget, QLabel, QStackedWidget, QComboBox, QPushButton,
    QSpacerItem, QSizePolicy, QMessageBox, QTextBrowser, QSlider
)
from PyQt5.QtCore import Qt, pyqtSignal, QUrl
from PyQt5.QtGui import QIcon, QFont
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
        self.current_theme = 'default'  # Initialize current_theme
        self.current_language = self.parent_window.language_code  # Initialize current_language
        self.setWindowTitle(translations[self.current_language]['settings'])
        self.setMinimumSize(600, 400)
        self.video_paths = []  # Initialize the list to store video paths
        self.setup_ui()
        self.load_video_paths()  # Load video paths after setting up the UI

    def setup_ui(self):
        _ = translations[self.parent_window.language_code]
        main_layout = QHBoxLayout(self)

        # Left side: categories list
        self.categories_list = QListWidget()
        self.categories_list.setFixedWidth(180)
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

        # Add items with associated internal theme identifiers
        self.theme_combobox.addItem(_['default'], 'default')
        self.theme_combobox.addItem(_['light'], 'light')
        self.theme_combobox.addItem(_['dark'], 'dark')

        # Set the current theme
        current_theme = getattr(self, 'current_theme', 'default')
        index = self.theme_combobox.findData(current_theme)
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

        # Add items with associated language codes
        self.language_combobox.addItem(_['english'], 'en')
        self.language_combobox.addItem(_['french'], 'fr')

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

        for i in range(7):  # Assuming you have 7 tutorials
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

        # Add widgets to main layout
        main_layout.addWidget(self.categories_list)
        main_layout.addWidget(self.stacked_widget)

        # Set default category
        self.categories_list.setCurrentRow(0)
        self.stacked_widget.setCurrentIndex(0)

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

        # Close the settings dialog
        self.accept()

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
        self.about_label.setText(_['about_info'])
        # Update theme combobox items
        self.theme_combobox.setItemText(0, _['default'])
        self.theme_combobox.setItemText(1, _['light'])
        self.theme_combobox.setItemText(2, _['dark'])
        # Update language combobox items
        self.language_combobox.setItemText(0, _['english'])
        self.language_combobox.setItemText(1, _['french'])
        # Update tutorial explanations and play buttons
        for i in range(7):
            index = i * 2  # Since each explanation and button are added sequentially
            explanation_label = self.tutorial_widget.layout().itemAt(index + 1).widget()
            explanation_label.setText(_[f'gif_explanation_{i+1}'])
            play_button = self.video_buttons[i]
            play_button.setText(_['play_video'])

    def save_settings_to_file(self):
        # Use the stored current theme and language
        current_theme = getattr(self, 'current_theme', 'default')
        current_language = getattr(self, 'current_language', 'en')

        # Use the AppData\Local directory
        app_name = "OpenStrand Studio"
        program_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        logging.info(f"Program data directory: {program_data_dir}")
        settings_dir = os.path.join(program_data_dir, app_name)
        logging.info(f"Settings directory: {settings_dir}")

        if not os.path.exists(settings_dir):
            try:
                os.makedirs(settings_dir)
            except Exception as e:
                logging.error(f"Cannot create directory {settings_dir}: {e}")
                return  # Exit if we cannot create the directory

        file_path = os.path.join(settings_dir, 'user_settings.txt')
        logging.info(f"Settings file path: {file_path}")

        # Write the settings to the file
        try:
            with open(file_path, 'w') as file:
                file.write(f"Theme: {current_theme}\n")
                file.write(f"Language: {current_language}\n")
            logging.info(f"Settings saved to {file_path}")
        except Exception as e:
            logging.error(f"Error saving settings to file: {e}")

    def load_video_paths(self):
        import sys
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundled executable
            base_path = sys._MEIPASS
        else:
            # If the application is run from the source
            base_path = os.path.abspath(".")

        mp4_directory = os.path.join(base_path, 'mp4')

        self.video_paths = [
            os.path.join(mp4_directory, 'tutorial_1.mp4'),
            os.path.join(mp4_directory, 'tutorial_2.mp4'),
            os.path.join(mp4_directory, 'tutorial_3.mp4'),
            os.path.join(mp4_directory, 'tutorial_4_1.mp4'),
            os.path.join(mp4_directory, 'tutorial_4_2.mp4'),
            os.path.join(mp4_directory, 'tutorial_5.mp4'),
            os.path.join(mp4_directory, 'tutorial_6.mp4'),
        ]

        # Optional: Log the video paths for debugging
        for path in self.video_paths:
            if not os.path.exists(path):
                logging.warning(f"Video file not found: {path}")


    def play_video(self, index):
        video_path = self.video_paths[index]
        if os.path.exists(video_path):
            if sys.platform.startswith('win'):
                os.startfile(video_path)
            elif sys.platform.startswith('darwin'):
                subprocess.call(('open', video_path))
            else:
                subprocess.call(('xdg-open', video_path))
        else:
            QMessageBox.warning(self, "Video Not Found", f"The video file was not found:\n{video_path}")

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