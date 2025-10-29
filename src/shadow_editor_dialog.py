from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                             QListWidgetItem, QLabel, QPushButton, QCheckBox,
                             QDialogButtonBox, QWidget, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPalette
from masked_strand import MaskedStrand


class ShadowListItem(QWidget):
    """Custom widget for each shadow entry in the list."""

    visibility_changed = pyqtSignal(str, bool)  # Signal when visibility is changed (layer_name, visible)
    show_shadow_requested = pyqtSignal(str, bool)  # Signal when show shadow is toggled (layer_name, enabled)
    allow_full_shadow_changed = pyqtSignal(str, bool)  # Signal when allow full shadow is toggled (layer_name, enabled)

    def __init__(self, receiving_layer_name, receiving_layer_color, is_visible=True, allow_full_shadow=False, parent=None):
        super().__init__(parent)
        self.receiving_layer_name = receiving_layer_name
        self.is_shadow_visible = False

        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        # Layer name label with color indicator
        self.color_indicator = QLabel("  ")
        self.color_indicator.setFixedSize(20, 20)
        self.color_indicator.setStyleSheet(f"background-color: {receiving_layer_color}; border: 1px solid #888; border-radius: 3px;")
        layout.addWidget(self.color_indicator)

        self.name_label = QLabel(receiving_layer_name)
        self.name_label.setMinimumWidth(100)
        layout.addWidget(self.name_label)

        layout.addStretch()

        # Visibility checkbox
        self.visibility_checkbox = QCheckBox("Visible")
        self.visibility_checkbox.setChecked(is_visible)
        self.visibility_checkbox.stateChanged.connect(self._on_visibility_changed)
        layout.addWidget(self.visibility_checkbox)

        # Allow full shadow checkbox
        self.allow_full_shadow_checkbox = QCheckBox("Allow Complete Shadow")
        self.allow_full_shadow_checkbox.setChecked(allow_full_shadow)
        self.allow_full_shadow_checkbox.stateChanged.connect(self._on_allow_full_shadow_changed)
        layout.addWidget(self.allow_full_shadow_checkbox)

        # Show Current Shadow button
        self.show_shadow_button = QPushButton("Show Current Shadow")
        self.show_shadow_button.setCheckable(True)
        self.show_shadow_button.clicked.connect(self._on_show_shadow_clicked)
        layout.addWidget(self.show_shadow_button)

    def _on_visibility_changed(self, state):
        """Handle visibility checkbox change."""
        is_visible = (state == Qt.Checked)
        self.visibility_changed.emit(self.receiving_layer_name, is_visible)

    def _on_allow_full_shadow_changed(self, state):
        """Handle allow full shadow checkbox change."""
        allow_full = (state == Qt.Checked)
        self.allow_full_shadow_changed.emit(self.receiving_layer_name, allow_full)

    def _on_show_shadow_clicked(self, checked):
        """Handle show shadow button toggle."""
        self.is_shadow_visible = checked
        if checked:
            self.show_shadow_button.setText("Hide Current Shadow")
        else:
            self.show_shadow_button.setText("Show Current Shadow")
        self.show_shadow_requested.emit(self.receiving_layer_name, checked)

    def set_theme(self, theme):
        """Apply theme styling to the item."""
        if theme == 'dark':
            self.setStyleSheet("""
                QWidget {
                    background-color: #3D3D3D;
                    color: white;
                    border-radius: 3px;
                }
                QLabel {
                    color: white;
                }
                QCheckBox {
                    color: white;
                }
                QPushButton {
                    background-color: #252525;
                    color: white;
                    border: 1px solid #555;
                    padding: 5px 10px;
                    border-radius: 3px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
                QPushButton:pressed {
                    background-color: #151515;
                }
                QPushButton:checked {
                    background-color: #4A6FA5;
                    border: 1px solid #6A9FD5;
                }
            """)
        elif theme == 'light':
            self.setStyleSheet("""
                QWidget {
                    background-color: white;
                    color: black;
                    border: 1px solid #DDD;
                    border-radius: 3px;
                }
                QLabel {
                    color: black;
                }
                QCheckBox {
                    color: black;
                }
                QPushButton {
                    background-color: #F0F0F0;
                    color: black;
                    border: 1px solid #BBB;
                    padding: 5px 10px;
                    border-radius: 3px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #E0E0E0;
                }
                QPushButton:pressed {
                    background-color: #D0D0D0;
                }
                QPushButton:checked {
                    background-color: #A0C0E0;
                    border: 1px solid #7090C0;
                }
            """)


class ShadowEditorDialog(QDialog):
    """Dialog for editing shadow casting from a specific strand."""

    def __init__(self, canvas, strand, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.strand = strand
        self.casting_layer = strand.layer_name
        self.shadow_visible_layer = None  # Track which layer's shadow is being visualized

        self.setWindowTitle(f"Shadow Editor - {self.casting_layer}")
        self.setModal(False)  # Allow interaction with canvas
        self.setMinimumSize(700, 400)
        self.resize(800, 500)

        # Find the main window to inherit its theme
        main_window = parent
        while main_window and not hasattr(main_window, 'current_theme'):
            main_window = main_window.parent()

        self.main_window = main_window
        self.theme = main_window.current_theme if main_window and hasattr(main_window, 'current_theme') else 'light'

        # Apply theme styling
        self._apply_theme()

        # Create layout
        layout = QVBoxLayout(self)

        # Info label
        info_label = QLabel(f"Shadows cast by <b>{self.casting_layer}</b> onto layers below:")
        layout.addWidget(info_label)

        # Shadows list
        self.shadows_list_widget = QListWidget()
        self.shadows_list_widget.setSpacing(2)
        self.shadows_list_widget.currentItemChanged.connect(self._on_selection_changed)
        layout.addWidget(self.shadows_list_widget)

        # Populate the list
        self._populate_shadow_list()

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.close)
        layout.addWidget(button_box)

        # Connect canvas update signal to refresh when canvas changes
        if hasattr(canvas, 'canvas_updated'):
            canvas.canvas_updated.connect(self._on_canvas_updated)

    def _apply_theme(self):
        """Apply theme styling to the dialog."""
        if self.theme == 'dark':
            self.setStyleSheet("""
                QDialog {
                    background-color: #2C2C2C;
                    color: white;
                }
                QLabel {
                    color: white;
                }
                QListWidget {
                    background-color: #3D3D3D;
                    color: white;
                    border: 1px solid #555;
                    border-radius: 3px;
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
                }
            """)
        elif self.theme == 'light':
            self.setStyleSheet("""
                QDialog {
                    background-color: #F5F5F5;
                    color: black;
                }
                QLabel {
                    color: black;
                }
                QListWidget {
                    background-color: white;
                    color: black;
                    border: 1px solid #CCC;
                    border-radius: 3px;
                }
                QPushButton, QDialogButtonBox QPushButton {
                    background-color: #F0F0F0;
                    color: black;
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
            """)

    def _populate_shadow_list(self):
        """Populate the list with layers that receive shadows from this strand."""
        self.shadows_list_widget.clear()

        # Get layer order from canvas
        if not hasattr(self.canvas, 'layer_state_manager'):
            return

        layer_order = self.canvas.layer_state_manager.getOrder()

        # Find position of casting strand
        try:
            casting_index = layer_order.index(self.casting_layer)
        except ValueError:
            return

        # Get layers below (lower indices = below in Z-order)
        layers_below = layer_order[:casting_index]

        # Filter out masked strands and hidden strands
        receiving_layers = []
        for layer_name in layers_below:
            strand = self._find_strand_by_name(layer_name)
            if strand and not isinstance(strand, MaskedStrand) and not getattr(strand, 'is_hidden', False):
                receiving_layers.append((layer_name, strand))

        # Create list items for each receiving layer
        for layer_name, strand in receiving_layers:
            # Get shadow override if exists
            override = self.canvas.layer_state_manager.get_shadow_override(self.casting_layer, layer_name)
            is_visible = override.get('visibility', True) if override else True
            allow_full_shadow = override.get('allow_full_shadow', False) if override else False

            # Create custom widget
            item_widget = ShadowListItem(layer_name, strand.color.name(), is_visible, allow_full_shadow)
            item_widget.set_theme(self.theme)

            # Connect signals
            item_widget.visibility_changed.connect(self._on_visibility_changed)
            item_widget.allow_full_shadow_changed.connect(self._on_allow_full_shadow_changed)
            item_widget.show_shadow_requested.connect(self._on_show_shadow_requested)

            # Add to list
            list_item = QListWidgetItem(self.shadows_list_widget)
            list_item.setSizeHint(item_widget.sizeHint())
            self.shadows_list_widget.addItem(list_item)
            self.shadows_list_widget.setItemWidget(list_item, item_widget)

    def _find_strand_by_name(self, layer_name):
        """Find a strand by its layer name."""
        for strand in self.canvas.strands:
            if strand.layer_name == layer_name:
                return strand
        return None

    def _on_selection_changed(self, current, previous):
        """Handle selection change in the list - highlight shadow on canvas."""
        if current:
            widget = self.shadows_list_widget.itemWidget(current)
            if widget:
                receiving_layer = widget.receiving_layer_name
                # Emit signal to canvas to highlight this shadow
                if hasattr(self.canvas, 'set_highlighted_shadow'):
                    self.canvas.set_highlighted_shadow(self.casting_layer, receiving_layer)

    def _on_visibility_changed(self, receiving_layer, is_visible):
        """Handle visibility change."""
        # Update shadow override
        override = self.canvas.layer_state_manager.get_shadow_override(self.casting_layer, receiving_layer)
        if not override:
            override = {'visibility': is_visible}
        else:
            override['visibility'] = is_visible

        self.canvas.layer_state_manager.set_shadow_override(self.casting_layer, receiving_layer, override)

        # Refresh canvas
        self.canvas.update()

    def _on_allow_full_shadow_changed(self, receiving_layer, allow_full):
        """Handle allow full shadow change."""
        # Update shadow override
        override = self.canvas.layer_state_manager.get_shadow_override(self.casting_layer, receiving_layer)
        if not override:
            override = {'visibility': True, 'allow_full_shadow': allow_full}
        else:
            override['allow_full_shadow'] = allow_full

        self.canvas.layer_state_manager.set_shadow_override(self.casting_layer, receiving_layer, override)

        # Refresh canvas
        self.canvas.update()

    def _on_show_shadow_requested(self, receiving_layer, enabled):
        """Handle show shadow request."""
        # Track which layer's shadow is being visualized
        self.shadow_visible_layer = receiving_layer if enabled else None

        # Set the visible shadow on canvas
        if hasattr(self.canvas, 'set_visible_shadow_path'):
            self.canvas.set_visible_shadow_path(self.casting_layer, receiving_layer if enabled else None)

        # Refresh canvas
        self.canvas.update()

    def _on_canvas_updated(self):
        """Handle canvas updates."""
        # Refresh the shadow list if needed
        pass

    def closeEvent(self, event):
        """Handle dialog close - clean up visualizations."""
        # Hide shadow visualization
        if self.shadow_visible_layer:
            if hasattr(self.canvas, 'set_visible_shadow_path'):
                self.canvas.set_visible_shadow_path(None, None)

        # Clear highlighted shadow
        if hasattr(self.canvas, 'set_highlighted_shadow'):
            self.canvas.set_highlighted_shadow(None, None)

        self.canvas.update()

        # Save state for undo/redo when dialog closes
        if hasattr(self.canvas, 'undo_redo_manager') and self.canvas.undo_redo_manager:
            self.canvas.undo_redo_manager._last_save_time = 0
            self.canvas.undo_redo_manager.save_state()

        super().closeEvent(event)
