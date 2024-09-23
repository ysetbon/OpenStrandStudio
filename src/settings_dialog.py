from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QWidget, QLabel, QStackedWidget, QComboBox, QPushButton,
    QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QMovie
from translations import translations

class SettingsDialog(QDialog):
    theme_changed = pyqtSignal(str)

    def __init__(self, parent=None, canvas=None):
        super(SettingsDialog, self).__init__(parent)
        self.canvas = canvas  # Reference to the canvas
        self.setWindowTitle(translations[self.parent().language_code]['settings'])
        self.setMinimumSize(600, 400)
        self.setup_ui()
        self.load_gifs()  # Load GIFs after setting up the UI

    def setup_ui(self):
        _ = translations[self.parent().language_code]
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
        self.theme_combobox.addItems([_['light'], _['dark']])
        current_theme = getattr(self.canvas, 'theme', _['light'])
        index = self.theme_combobox.findText(current_theme)
        if index >= 0:
            self.theme_combobox.setCurrentIndex(index)
        theme_layout.addWidget(self.theme_label)
        theme_layout.addWidget(self.theme_combobox)

        # Apply Button
        self.apply_button = QPushButton(_['ok'])
        self.apply_button.clicked.connect(self.apply_general_settings)

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
        # Remove the automatic change on combo box selection
        # self.language_combobox.currentIndexChanged.connect(self.change_language)
        
        self.language_info_label = QLabel(_['language_settings_info'])
        language_layout.addWidget(self.language_label)
        language_layout.addWidget(self.language_combobox)
        language_layout.addWidget(self.language_info_label)

        # Add the "OK" button
        self.language_ok_button = QPushButton(_['ok'])
        self.language_ok_button.clicked.connect(self.apply_language_settings)
        language_layout.addWidget(self.language_ok_button)

        self.stacked_widget.addWidget(self.change_language_widget)

        # Tutorial Page
        self.tutorial_widget = QWidget()
        tutorial_layout = QVBoxLayout(self.tutorial_widget)

        self.gif_labels = []  # Store references to the labels

        for i in range(6):
            # Explanation Label
            explanation_label = QLabel(_[f'gif_explanation_{i+1}'])
            tutorial_layout.addWidget(explanation_label)

            # GIF Label
            gif_label = QLabel()
            gif_label.setFixedSize(400, 300)
            gif_label.setAlignment(Qt.AlignCenter)
            tutorial_layout.addWidget(gif_label)
            self.gif_labels.append(gif_label)

        self.stacked_widget.addWidget(self.tutorial_widget)

        # About Page
        self.about_widget = QWidget()
        about_layout = QVBoxLayout(self.about_widget)
        self.about_label = QLabel(_['about_info'])
        about_layout.addWidget(self.about_label)
        self.stacked_widget.addWidget(self.about_widget)

        # Add widgets to main layout
        main_layout.addWidget(self.categories_list)
        main_layout.addWidget(self.stacked_widget)

        # Set default category
        self.categories_list.setCurrentRow(0)
        self.stacked_widget.setCurrentIndex(0)

    def apply_general_settings(self):
        # Update theme
        selected_theme = self.theme_combobox.currentText()
        if self.canvas:
            self.canvas.set_theme(selected_theme)
            self.canvas.update()
        
        # Emit signal to notify main window of theme change
        self.theme_changed.emit(selected_theme)
        
        # Close the settings dialog
        self.accept()

    def change_category(self, item):
        index = self.categories_list.row(item)
        self.stacked_widget.setCurrentIndex(index)

    def change_language(self):
        selected_language = self.language_combobox.currentText()
        if selected_language == "French":
            self.parent().set_language('fr')
        else:
            self.parent().set_language('en')

    def update_translations(self):
        _ = translations[self.parent().language_code]
        self.setWindowTitle(_['settings'])
        # Update category names
        self.categories_list.item(0).setText(_['general_settings'])
        self.categories_list.item(1).setText(_['change_language'])
        self.categories_list.item(2).setText(_['tutorial'])
        self.categories_list.item(3).setText(_['about'])
        # Update labels and buttons
        self.theme_label.setText(_['select_theme'])
        self.apply_button.setText(_['ok'])
        self.language_ok_button.setText(_['ok'])  # Update the "OK" button text
        self.language_label.setText(_['select_language'])
        # Update information labels
        self.language_info_label.setText(_['language_settings_info'])
        self.tutorial_label.setText(_['tutorial_info'])
        self.about_label.setText(_['about_info'])

    def apply_language_settings(self):
        # Get the selected language code from the combo box
        language_code = self.language_combobox.currentData()
        # Update the language in the main window
        self.parent().set_language(language_code)
        # Update the canvas language code
        if self.canvas:
            self.canvas.language_code = language_code
        # Update translations in the settings dialog
        self.update_translations()
        # Close the settings dialog
        self.accept()

    def load_gifs(self):
        gif_paths = [
            r'C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\gif1.gif',
            r'C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\gif2.gif',
            r'C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\gif3.gif',
            r'C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\gif4.gif',
            r'C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\gif5.gif',
            r'C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\gif6.gif',
        ]

        for gif_label, gif_path in zip(self.gif_labels, gif_paths):
            movie = QMovie(gif_path)
            if movie.isValid():
                gif_label.setMovie(movie)
                movie.start()
            else:
                gif_label.setText("Failed to load GIF")