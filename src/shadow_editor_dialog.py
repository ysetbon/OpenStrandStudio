from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                             QListWidgetItem, QLabel, QPushButton, QCheckBox,
                             QDialogButtonBox, QWidget, QGroupBox, QComboBox, QSizePolicy, QStyleOptionButton,
                             QProxyStyle, QStyle)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QRect
from PyQt5.QtGui import QColor, QPalette, QPainter, QPen, QPainterPath
from masked_strand import MaskedStrand
from translations import translations


class LargeIndicatorStyle(QProxyStyle):
    """Proxy style that enforces a specific checkbox indicator size."""

    def __init__(self, base_style, indicator_size=20):
        super().__init__(base_style)
        self._indicator_size = indicator_size

    def pixelMetric(self, metric, option=None, widget=None):
        if metric in (QStyle.PM_IndicatorWidth, QStyle.PM_IndicatorHeight):
            return self._indicator_size
        return super().pixelMetric(metric, option, widget)


class ShadowListItem(QWidget):
    """Custom widget for each shadow entry in the list."""

    visibility_changed = pyqtSignal(str, bool)  # Signal when visibility is changed (layer_name, visible)
    show_shadow_requested = pyqtSignal(str, bool)  # Signal when show shadow is toggled (layer_name, enabled)
    allow_full_shadow_changed = pyqtSignal(str, bool)  # Signal when allow full shadow is toggled (layer_name, enabled)
    subtracted_layers_changed = pyqtSignal(str, list)  # Signal when subtracted layers are changed (receiving_layer, list of subtracted_layers)
    size_changed = pyqtSignal()  # Signal when widget size needs to be updated

    def __init__(self, receiving_layer_name, receiving_layer_color, is_visible=True, allow_full_shadow=False, available_layers=None, subtracted_layers=None, language_code='en', parent=None):
        super().__init__(parent)
        self.receiving_layer_name = receiving_layer_name
        self.is_shadow_visible = False
        self.subtract_checkboxes = {}  # Dictionary to track checkboxes by layer name
        self.language_code = language_code
        self.available_layers = available_layers
        self.subtracted_layers = subtracted_layers
        self.no_layers_label = None  # Reference to no layers label for translation updates

        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(1)

        # Set RTL layout direction for Hebrew
        if self.language_code == 'he':
            self.setLayoutDirection(Qt.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LeftToRight)

        # Set minimum dimensions for the row
        self.setMinimumHeight(48)
        self.setMinimumWidth(650)  # Ensure enough space for all widgets

        # Layer name label with color indicator
        self.color_indicator = QLabel("  ")
        self.color_indicator.setFixedSize(20, 20)
        self.color_indicator.setStyleSheet(f"background-color: {receiving_layer_color}; border: 1px solid #888; border-radius: 3px;")
        layout.addWidget(self.color_indicator)

        self.name_label = QLabel(receiving_layer_name)
        self.name_label.setMinimumWidth(10)
        self.name_label.setWordWrap(False)
        self.name_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(self.name_label)

        # Visibility checkbox
        _ = translations[self.language_code]
        self.visibility_checkbox = QCheckBox(_['shadow_visible'])
        self.visibility_checkbox.setChecked(is_visible)
        self.visibility_checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.visibility_checkbox.stateChanged.connect(self._on_visibility_changed)
        self._apply_large_indicator(self.visibility_checkbox)
        self._setup_custom_checkmark(self.visibility_checkbox)
        self._set_checkbox_min_width(self.visibility_checkbox)
        self._style_shadow_checkbox(self.visibility_checkbox, is_dark_mode=False)
        layout.addWidget(self.visibility_checkbox)

        # Allow full shadow checkbox
        self.allow_full_shadow_checkbox = QCheckBox(_['shadow_full'])
        self.allow_full_shadow_checkbox.setChecked(allow_full_shadow)
        self.allow_full_shadow_checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.allow_full_shadow_checkbox.stateChanged.connect(self._on_allow_full_shadow_changed)
        self._apply_large_indicator(self.allow_full_shadow_checkbox)
        self._setup_custom_checkmark(self.allow_full_shadow_checkbox)
        self._set_checkbox_min_width(self.allow_full_shadow_checkbox)
        self._style_shadow_checkbox(self.allow_full_shadow_checkbox, is_dark_mode=False)
        layout.addWidget(self.allow_full_shadow_checkbox)

        # Subtract layers collapsible section
        subtract_container = QWidget()
        subtract_container_layout = QVBoxLayout(subtract_container)
        subtract_container_layout.setContentsMargins(0, 0, 0, 0)
        subtract_container_layout.setSpacing(0)

        # Toggle button with arrow
        # For RTL (Hebrew), put arrow after text; for LTR, put arrow before text
        if self.language_code == 'he':
            button_text = f"{_['shadow_subtract_layers']} ◀"
            text_align = "right"
        else:
            button_text = f"▶ {_['shadow_subtract_layers']}"
            text_align = "left"

        self.subtract_toggle_button = QPushButton(button_text)
        self.subtract_toggle_button.setCheckable(True)
        self.subtract_toggle_button.setFlat(True)
        self.subtract_toggle_button.setStyleSheet(f"""
            QPushButton {{
                text-align: {text_align};
                padding: 3px;
                border: none;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(128, 128, 128, 0.2);
            }}
        """)
        self.subtract_toggle_button.clicked.connect(self._toggle_subtract_section)
        subtract_container_layout.addWidget(self.subtract_toggle_button)

        # Collapsible content
        self.subtract_content = QWidget()
        self.subtract_content.setVisible(False)
        subtract_layout = QVBoxLayout(self.subtract_content)
        subtract_layout.setContentsMargins(15, 2, 0, 2)
        subtract_layout.setSpacing(2)

        if available_layers and len(available_layers) > 0:
            for layer in available_layers:
                checkbox = QCheckBox(layer)
                # Check if this layer is in the subtracted layers list
                if subtracted_layers and layer in subtracted_layers:
                    checkbox.setChecked(True)
                checkbox.stateChanged.connect(self._on_subtracted_layers_changed)
                self._apply_large_indicator(checkbox)
                self._setup_custom_checkmark(checkbox)
                self._style_shadow_checkbox(checkbox, is_dark_mode=False)
                self.subtract_checkboxes[layer] = checkbox
                subtract_layout.addWidget(checkbox)
        else:
            self.no_layers_label = QLabel(_['shadow_no_layers'])
            self.no_layers_label.setStyleSheet("color: gray; font-style: italic;")
            subtract_layout.addWidget(self.no_layers_label)

        subtract_container_layout.addWidget(self.subtract_content)
        subtract_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        layout.addWidget(subtract_container, stretch=0)

        # Auto-expand if there are any subtracted layers
        if subtracted_layers and len(subtracted_layers) > 0:
            self.subtract_toggle_button.setChecked(True)
            self.subtract_content.setVisible(True)
            if self.language_code == 'he':
                self.subtract_toggle_button.setText(f"{_['shadow_subtract_layers']} ▼")
            else:
                self.subtract_toggle_button.setText(f"▼ {_['shadow_subtract_layers']}")

        # Show Current Shadow button
        self.show_shadow_button = QPushButton(_['shadow_path_button'])
        self.show_shadow_button.setCheckable(True)
        self.show_shadow_button.setMinimumWidth(80)
        self.show_shadow_button.setMinimumHeight(36)
        self.show_shadow_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.show_shadow_button.clicked.connect(self._on_show_shadow_clicked)
        layout.addWidget(self.show_shadow_button, stretch=0)

    def _apply_large_indicator(self, checkbox, indicator_size=20):
        """Apply a proxy style so the checkbox indicator uses a crisp fixed size."""
        base_style = checkbox.style()
        if isinstance(base_style, LargeIndicatorStyle):
            base_style = base_style.baseStyle()
        checkbox.setStyle(LargeIndicatorStyle(base_style, indicator_size))
        checkbox.setMinimumHeight(max(checkbox.minimumHeight(), indicator_size + 6))

    def _setup_custom_checkmark(self, checkbox):
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

                # Use Qt's style system to get the ACTUAL indicator position
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

                # Set pen for white checkmark with proportional thickness
                pen_width = max(1.6, indicator_rect.height() * 0.16)
                pen = QPen(QColor(255, 255, 255), pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.setPen(pen)

                left = indicator_rect.left()
                top = indicator_rect.top()
                width = indicator_rect.width()
                height = indicator_rect.height()

                start_x = left + width * 0.25
                start_y = top + height * 0.55
                mid_x = left + width * 0.42
                mid_y = top + height * 0.72
                end_x = left + width * 0.78
                end_y = top + height * 0.28

                check_path = QPainterPath()
                check_path.moveTo(start_x, start_y)
                check_path.lineTo(mid_x, mid_y)
                check_path.lineTo(end_x, end_y)

                painter.drawPath(check_path)

                painter.end()

        # Replace the paintEvent method
        checkbox.paintEvent = custom_paintEvent

    def _set_checkbox_min_width(self, checkbox):
        """Ensure checkbox text is fully visible while preventing it from stretching."""
        checkbox.setMinimumWidth(checkbox.sizeHint().width())
        checkbox.updateGeometry()

    def _style_shadow_checkbox(self, checkbox, is_dark_mode, is_enabled=None):
        """Apply the shared large-indicator styling for this dialog's checkboxes."""
        if is_enabled is None:
            is_enabled = checkbox.isEnabled()

        if is_dark_mode:
            text_color = "#FFFFFF" if is_enabled else "#808080"
            indicator_border = "#666666"
            indicator_background = "#2A2A2A"
            hover_border = "#888888"
            hover_background = "#454545"
            checked_background = "#4A6FA5"
            checked_border = "#6A9FD5"
            checked_hover_background = "#5A7FB5"
            checked_hover_border = "#7AAFF5"
            disabled_indicator = "#1F1F1F"
            disabled_border = "#444444"
        else:
            text_color = "#000000" if is_enabled else "#AAAAAA"
            indicator_border = "#AAAAAA"
            indicator_background = "#FFFFFF"
            hover_border = "#888888"
            hover_background = "#F8F8F8"
            checked_background = "#A0C0E0"
            checked_border = "#7090C0"
            checked_hover_background = "#B0D0F0"
            checked_hover_border = "#8AA0D0"
            disabled_indicator = "#F0F0F0"
            disabled_border = "#BBBBBB"

        checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {text_color};
                spacing: 8px;
                font-size: 11pt;
                background-color: transparent;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                min-width: 20px;
                min-height: 20px;
                border: 2px solid {indicator_border};
                border-radius: 4px;
                background-color: {indicator_background};
            }}
            QCheckBox::indicator:hover {{
                border: 2px solid {hover_border};
                background-color: {hover_background};
            }}
            QCheckBox::indicator:checked {{
                background-color: {checked_background};
                border: 2px solid {checked_border};
            }}
            QCheckBox::indicator:checked:hover {{
                background-color: {checked_hover_background};
                border: 2px solid {checked_hover_border};
            }}
            QCheckBox::indicator:disabled {{
                background-color: {disabled_indicator};
                border: 2px solid {disabled_border};
            }}
        """)

    def _restyle_all_checkboxes(self, is_dark_mode):
        """Update every checkbox to the correct theme colors."""
        self._style_shadow_checkbox(self.visibility_checkbox, is_dark_mode, self.visibility_checkbox.isEnabled())
        self._style_shadow_checkbox(self.allow_full_shadow_checkbox, is_dark_mode, self.allow_full_shadow_checkbox.isEnabled())
        for checkbox in self.subtract_checkboxes.values():
            self._style_shadow_checkbox(checkbox, is_dark_mode, checkbox.isEnabled())

    def _on_visibility_changed(self, state):
        """Handle visibility checkbox change."""
        is_visible = (state == Qt.Checked)
        self.visibility_changed.emit(self.receiving_layer_name, is_visible)

    def _on_allow_full_shadow_changed(self, state):
        """Handle allow full shadow checkbox change."""
        allow_full = (state == Qt.Checked)
        self.allow_full_shadow_changed.emit(self.receiving_layer_name, allow_full)

    def _toggle_subtract_section(self, checked):
        """Toggle the visibility of the subtract layers section."""
        _ = translations[self.language_code]
        self.subtract_content.setVisible(checked)

        # Handle arrow direction and position based on language direction
        if self.language_code == 'he':
            # RTL: arrow after text
            if checked:
                self.subtract_toggle_button.setText(f"{_['shadow_subtract_layers']} ▼")
            else:
                self.subtract_toggle_button.setText(f"{_['shadow_subtract_layers']} ◀")
        else:
            # LTR: arrow before text
            if checked:
                self.subtract_toggle_button.setText(f"▼ {_['shadow_subtract_layers']}")
            else:
                self.subtract_toggle_button.setText(f"▶ {_['shadow_subtract_layers']}")

        if checked:
            # Remove maximum height constraint when expanding
            self.setMaximumHeight(16777215)  # Qt's QWIDGETSIZE_MAX
        else:
            # Set maximum height to minimum when collapsing
            collapsed_height = max(self.sizeHint().height(), self.minimumHeight())
            self.setMaximumHeight(collapsed_height)

        # Update geometry and emit signal to resize list item
        self.subtract_content.adjustSize()
        self.adjustSize()
        self.updateGeometry()

        # Use QTimer to ensure signal is emitted after geometry is updated
        QTimer.singleShot(0, self.size_changed.emit)

    def _on_subtracted_layers_changed(self, state):
        """Handle subtracted layers checkbox changes."""
        # Collect all checked layers
        subtracted_layers = [layer for layer, checkbox in self.subtract_checkboxes.items() if checkbox.isChecked()]
        self.subtracted_layers_changed.emit(self.receiving_layer_name, subtracted_layers)

    def _on_show_shadow_clicked(self, checked):
        """Handle show shadow button toggle."""
        _ = translations[self.language_code]
        self.is_shadow_visible = checked
        if checked:
            self.show_shadow_button.setText(_['shadow_path_hide'])
        else:
            self.show_shadow_button.setText(_['shadow_path_button'])
        self.show_shadow_requested.emit(self.receiving_layer_name, checked)

    def set_theme(self, theme):
        """Apply theme styling to the item."""
        self.current_theme = theme
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
                    spacing: 10px;
                    font-size: 11pt;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    min-width: 20px;
                    min-height: 20px;
                    border: 2px solid #666;
                    border-radius: 4px;
                    background-color: #2A2A2A;
                }
                QCheckBox::indicator:hover {
                    border: 2px solid #888;
                    background-color: #454545;
                }
                QCheckBox::indicator:checked {
                    background-color: #4A6FA5;
                    border: 2px solid #6A9FD5;
                }
                QCheckBox::indicator:checked:hover {
                    background-color: #5A7FB5;
                    border: 2px solid #7AAFF5;
                }
                QPushButton {
                    background-color: #252525;
                    color: white;
                    border: 1px solid #555;
                    padding: 5px 10px;
                    border-radius: 3px;
                    min-width: 100px;
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
                QPushButton[flat="true"] {
                    background-color: transparent;
                    border: none;
                    text-align: left;
                    font-weight: bold;
                    padding: 3px;
                }
                QPushButton[flat="true"]:hover {
                    background-color: rgba(128, 128, 128, 0.3);
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
                    spacing: 10px;
                    font-size: 11pt;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    min-width: 20px;
                    min-height: 20px;
                    border: 2px solid #AAA;
                    border-radius: 4px;
                    background-color: white;
                }
                QCheckBox::indicator:hover {
                    border: 2px solid #888;
                    background-color: #F8F8F8;
                }
                QCheckBox::indicator:checked {
                    background-color: #A0C0E0;
                    border: 2px solid #7090C0;
                }
                QCheckBox::indicator:checked:hover {
                    background-color: #B0D0F0;
                    border: 2px solid #8AA0D0;
                }
                QPushButton {
                    background-color: #F0F0F0;
                    color: black;
                    border: 1px solid #BBB;
                    padding: 5px 10px;
                    border-radius: 3px;
                    min-width: 100px;
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
                QPushButton[flat="true"] {
                    background-color: transparent;
                    border: none;
                    text-align: left;
                    font-weight: bold;
                    padding: 3px;
                }
                QPushButton[flat="true"]:hover {
                    background-color: rgba(0, 0, 0, 0.1);
                }
            """)
        self._restyle_all_checkboxes(theme == 'dark')

    def update_translations(self, language_code):
        """Update all text elements with new language."""
        self.language_code = language_code
        _ = translations[language_code]

        # Update layout direction for RTL/LTR
        if language_code == 'he':
            self.setLayoutDirection(Qt.RightToLeft)
            text_align = "right"
        else:
            self.setLayoutDirection(Qt.LeftToRight)
            text_align = "left"

        # Update checkbox labels
        self.visibility_checkbox.setText(_['shadow_visible'])
        self.allow_full_shadow_checkbox.setText(_['shadow_full'])
        self._set_checkbox_min_width(self.visibility_checkbox)
        self._set_checkbox_min_width(self.allow_full_shadow_checkbox)

        # Update toggle button (preserve expanded/collapsed state and handle RTL arrow positioning)
        is_expanded = self.subtract_toggle_button.isChecked()
        if language_code == 'he':
            # RTL: arrow after text
            if is_expanded:
                self.subtract_toggle_button.setText(f"{_['shadow_subtract_layers']} ▼")
            else:
                self.subtract_toggle_button.setText(f"{_['shadow_subtract_layers']} ◀")
        else:
            # LTR: arrow before text
            if is_expanded:
                self.subtract_toggle_button.setText(f"▼ {_['shadow_subtract_layers']}")
            else:
                self.subtract_toggle_button.setText(f"▶ {_['shadow_subtract_layers']}")

        # Update button stylesheet for text alignment
        self.subtract_toggle_button.setStyleSheet(f"""
            QPushButton {{
                text-align: {text_align};
                padding: 3px;
                border: none;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(128, 128, 128, 0.2);
            }}
        """)

        # Update no layers label if it exists
        if self.no_layers_label:
            self.no_layers_label.setText(_['shadow_no_layers'])

        # Update shadow path button (preserve checked state)
        if self.show_shadow_button.isChecked():
            self.show_shadow_button.setText(_['shadow_path_hide'])
        else:
            self.show_shadow_button.setText(_['shadow_path_button'])


class ShadowEditorDialog(QDialog):
    """Dialog for editing shadow casting from a specific strand."""

    def __init__(self, canvas, strand, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.strand = strand
        self.casting_layer = strand.layer_name
        self.shadow_visible_layer = None  # Track which layer's shadow is being visualized
        self.widget_to_item = {}  # Map widgets to their list items

        # Get language code from canvas
        self.language_code = canvas.language_code if hasattr(canvas, 'language_code') else 'en'
        _ = translations[self.language_code]

        self.setWindowTitle(f"{_['shadow_editor_title']} - {self.casting_layer}")
        self.setModal(False)  # Allow interaction with canvas
        self.setMinimumSize(700, 400)
        self.resize(750, 500)

        # Find the main window to inherit its theme
        main_window = parent
        while main_window and not hasattr(main_window, 'current_theme'):
            main_window = main_window.parent()

        self.main_window = main_window
        self.theme = main_window.current_theme if main_window and hasattr(main_window, 'current_theme') else 'light'

        # Apply theme styling
        self._apply_theme()

        # Set RTL layout direction for Hebrew
        if self.language_code == 'he':
            self.setLayoutDirection(Qt.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LeftToRight)

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)  # Compact margins on all sides

        # Info label
        self.info_label = QLabel(_['shadow_editor_info'].format(self.casting_layer))
        layout.addWidget(self.info_label)

        # Shadows list
        self.shadows_list_widget = QListWidget()
        self.shadows_list_widget.setSpacing(5)
        self.shadows_list_widget.setUniformItemSizes(False)
        self.shadows_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.shadows_list_widget.currentItemChanged.connect(self._on_selection_changed)
        layout.addWidget(self.shadows_list_widget)

        # Populate the list
        self._populate_shadow_list()

        # Button box
        self.button_box = QDialogButtonBox(QDialogButtonBox.Close)
        self.button_box.rejected.connect(self.close)

        # Set translated text for Close button
        close_button = self.button_box.button(QDialogButtonBox.Close)
        if close_button:
            close_button.setText(_['close'])

        layout.addWidget(self.button_box)

        # Connect canvas update signal to refresh when canvas changes
        if hasattr(canvas, 'canvas_updated'):
            canvas.canvas_updated.connect(self._on_canvas_updated)

        # Connect to language change signal
        if hasattr(canvas, 'language_changed'):
            canvas.language_changed.connect(self.update_translations)

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

        # Get all available layers for subtraction (all layers except casting layer and masked strands)
        available_layers = []
        for layer_name in layer_order:
            if layer_name != self.casting_layer:
                strand = self._find_strand_by_name(layer_name)
                if strand and not isinstance(strand, MaskedStrand) and not getattr(strand, 'is_hidden', False):
                    available_layers.append(layer_name)

        # Create list items for each receiving layer
        for layer_name, strand in receiving_layers:
            # Get shadow override if exists
            override = self.canvas.layer_state_manager.get_shadow_override(self.casting_layer, layer_name)
            is_visible = override.get('visibility', True) if override else True
            allow_full_shadow = override.get('allow_full_shadow', False) if override else False

            # Get subtracted layers
            subtracted_layers = self.canvas.layer_state_manager.get_subtracted_layers(self.casting_layer, layer_name)

            # Create custom widget - exclude the receiving layer from available layers
            available_for_this_shadow = [l for l in available_layers if l != layer_name]
            item_widget = ShadowListItem(layer_name, strand.color.name(), is_visible, allow_full_shadow,
                                        available_for_this_shadow, subtracted_layers, self.language_code)
            item_widget.set_theme(self.theme)

            # Connect signals
            item_widget.visibility_changed.connect(self._on_visibility_changed)
            item_widget.allow_full_shadow_changed.connect(self._on_allow_full_shadow_changed)
            item_widget.show_shadow_requested.connect(self._on_show_shadow_requested)
            item_widget.subtracted_layers_changed.connect(self._on_subtracted_layers_changed)
            item_widget.size_changed.connect(lambda w=item_widget: self._on_item_size_changed(w))

            # Add to list
            list_item = QListWidgetItem(self.shadows_list_widget)
            # Ensure proper size for the item
            size_hint = item_widget.sizeHint()
            if size_hint.height() < 50:
                size_hint.setHeight(50)
            list_item.setSizeHint(size_hint)
            self.shadows_list_widget.addItem(list_item)
            self.shadows_list_widget.setItemWidget(list_item, item_widget)

            # Store widget to item mapping
            self.widget_to_item[item_widget] = list_item

    def _on_item_size_changed(self, widget):
        """Handle when an item widget's size changes (e.g., expand/collapse)."""
        if widget in self.widget_to_item:
            list_item = self.widget_to_item[widget]
            # Force widget to recalculate size
            widget.updateGeometry()
            # Update the list item's size hint to match the widget's new size
            new_size_hint = widget.sizeHint()
            if new_size_hint.height() < 50:
                new_size_hint.setHeight(50)
            list_item.setSizeHint(new_size_hint)
            # Force the list widget to update its layout immediately
            self.shadows_list_widget.scheduleDelayedItemsLayout()
            self.shadows_list_widget.updateGeometry()

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

    def _on_subtracted_layers_changed(self, receiving_layer, subtracted_layers):
        """Handle subtracted layers change."""
        # Update subtracted layers in layer_state_manager
        self.canvas.layer_state_manager.set_subtracted_layers(
            self.casting_layer, receiving_layer, subtracted_layers
        )

        # Refresh canvas to show updated shadow
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

    def update_translations(self):
        """Update all text elements when language changes."""
        # Get new language code from canvas
        self.language_code = self.canvas.language_code if hasattr(self.canvas, 'language_code') else 'en'
        _ = translations[self.language_code]

        # Update layout direction for RTL/LTR
        if self.language_code == 'he':
            self.setLayoutDirection(Qt.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LeftToRight)

        # Update window title
        self.setWindowTitle(f"{_['shadow_editor_title']} - {self.casting_layer}")

        # Update info label
        self.info_label.setText(_['shadow_editor_info'].format(self.casting_layer))

        # Update Close button text
        close_button = self.button_box.button(QDialogButtonBox.Close)
        if close_button:
            close_button.setText(_['close'])

        # Update all list items
        for i in range(self.shadows_list_widget.count()):
            item = self.shadows_list_widget.item(i)
            widget = self.shadows_list_widget.itemWidget(item)
            if widget and isinstance(widget, ShadowListItem):
                widget.update_translations(self.language_code)

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
