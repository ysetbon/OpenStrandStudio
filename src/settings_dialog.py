from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QWidget, QLabel, QStackedWidget, QComboBox, QPushButton,
    QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal

class SettingsDialog(QDialog):
    theme_changed = pyqtSignal(str)  # Signal to notify theme change

from PyQt5.QtCore import pyqtSignal

class SettingsDialog(QDialog):
    theme_changed = pyqtSignal(str)

    def __init__(self, parent=None, canvas=None):
        super(SettingsDialog, self).__init__(parent)
        self.canvas = canvas  # Reference to the canvas
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 400)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)

        # Left side: categories list
        self.categories_list = QListWidget()
        self.categories_list.setFixedWidth(180)
        self.categories_list.itemClicked.connect(self.change_category)

        categories = [
            "General Settings",
            "Change Language",
            "Tutorial",
            "About OpenStrand Studio"
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
        theme_label = QLabel("Select Theme:")
        self.theme_combobox = QComboBox()
        self.theme_combobox.addItems(["Light", "Dark"])
        current_theme = getattr(self.canvas, 'theme', 'Light')
        index = self.theme_combobox.findText(current_theme)
        if index >= 0:
            self.theme_combobox.setCurrentIndex(index)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combobox)

        # Apply Button
        self.apply_button = QPushButton("ok")
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
        language_label = QLabel("Language settings will be implemented here.")
        language_layout.addWidget(language_label)
        self.stacked_widget.addWidget(self.change_language_widget)

        # Tutorial Page
        self.tutorial_widget = QWidget()
        tutorial_layout = QVBoxLayout(self.tutorial_widget)
        tutorial_label = QLabel("Tutorial content will be displayed here.")
        tutorial_layout.addWidget(tutorial_label)
        self.stacked_widget.addWidget(self.tutorial_widget)

        # About Page
        self.about_widget = QWidget()
        about_layout = QVBoxLayout(self.about_widget)
        about_label = QLabel("Information about OpenStrand Studio.")
        about_layout.addWidget(about_label)
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