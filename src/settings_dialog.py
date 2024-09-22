from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QWidget, QLabel, QStackedWidget, QSpinBox, QPushButton, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, parent=None, canvas=None):
        super(SettingsDialog, self).__init__(parent)
        self.canvas = canvas  # Save the reference to the canvas
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 400)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)

        # Left side: categories list
        self.categories_list = QListWidget()
        self.categories_list.setFixedWidth(150)
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

        # Add Grid Size Control
        grid_size_layout = QHBoxLayout()
        grid_size_label = QLabel("Grid Size:")
        self.grid_size_spinbox = QSpinBox()
        self.grid_size_spinbox.setRange(5, 100)  # Adjust the range as appropriate

        # Use grid_size from the canvas if available
        if self.canvas:
            self.grid_size_spinbox.setValue(self.canvas.grid_size)
        else:
            self.grid_size_spinbox.setValue(30)  # Default grid size if canvas is None

        self.grid_size_spinbox.setSuffix(" px")  # Optional suffix for clarity
        grid_size_layout.addWidget(grid_size_label)
        grid_size_layout.addWidget(self.grid_size_spinbox)

        # Add Apply Button
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_general_settings)

        # Spacer to push the apply button to the bottom
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        general_layout.addLayout(grid_size_layout)
        general_layout.addItem(spacer)
        general_layout.addWidget(self.apply_button)

        self.stacked_widget.addWidget(self.general_settings_widget)

        # Change Language Page
        self.change_language_widget = QWidget()
        language_layout = QVBoxLayout(self.change_language_widget)
        language_label = QLabel("Language settings will be here.")
        language_layout.addWidget(language_label)
        self.stacked_widget.addWidget(self.change_language_widget)

        # Tutorial Page
        self.tutorial_widget = QWidget()
        tutorial_layout = QVBoxLayout(self.tutorial_widget)
        tutorial_label = QLabel("Tutorials will be shown here.")
        tutorial_layout.addWidget(tutorial_label)
        self.stacked_widget.addWidget(self.tutorial_widget)

        # About Page
        self.about_widget = QWidget()
        about_layout = QVBoxLayout(self.about_widget)
        about_label = QLabel("About OpenStrand Studio information will be displayed here.")
        about_layout.addWidget(about_label)
        self.stacked_widget.addWidget(self.about_widget)

        # Add widgets to main layout
        main_layout.addWidget(self.categories_list)
        main_layout.addWidget(self.stacked_widget)

        # Set default category
        self.categories_list.setCurrentRow(0)
        self.stacked_widget.setCurrentIndex(0)

    def apply_general_settings(self):
        # Get the value from the spinbox
        new_grid_size = self.grid_size_spinbox.value()
        # Update the canvas grid size
        if self.canvas:
            self.canvas.set_grid_size(new_grid_size)
            self.canvas.update()  # Refresh the canvas to reflect changes
    def change_category(self, item):
        index = self.categories_list.row(item)
        self.stacked_widget.setCurrentIndex(index)