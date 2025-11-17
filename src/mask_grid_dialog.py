from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QPushButton, QCheckBox, QWidget, QLabel,
                             QHeaderView, QTableWidgetItem, QSizePolicy, QStyleOptionButton,
                             QProxyStyle, QStyle)
from PyQt5.QtCore import Qt, pyqtSignal, QRect
from PyQt5.QtGui import QColor, QPainter, QPen, QPainterPath
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


class MaskGridDialog(QDialog):
    """
    Dialog for creating mask layers using an N×N grid interface.
    Each cell represents a potential mask between two strands.
    """

    masks_created = pyqtSignal(list)  # Emits list of (strand1_name, strand2_name) tuples

    def __init__(self, canvas, group_name, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.group_name = group_name
        self.language_code = canvas.language_code if hasattr(canvas, 'language_code') else 'en'
        # Strip the Windows context-help button so only the close button remains
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Get theme
        main_window = parent
        while main_window and not hasattr(main_window, 'current_theme'):
            main_window = main_window.parent()
        self.theme = main_window.current_theme if main_window else 'light'

        # Get strands for this group
        self.strands = self._get_group_strands()

        if not self.strands:
            # If no strands, we shouldn't show the dialog
            return

        # Track checkbox states
        self.checkboxes = {}  # {(row_idx, col_idx): QCheckBox}
        self.header_row_checkboxes = {}  # {row_idx: QCheckBox}
        self.header_col_checkboxes = {}  # {col_idx: QCheckBox}

        self.setup_ui()
        self._apply_theme()

        # Connect theme changes
        if hasattr(self.canvas, 'theme_changed'):
            self.canvas.theme_changed.connect(self._apply_theme)

        # Connect to canvas signals to auto-update when masks are added/deleted
        if hasattr(self.canvas, 'masked_layer_created'):
            self.canvas.masked_layer_created.connect(self._on_mask_layer_changed)
        if hasattr(self.canvas, 'strand_deleted'):
            self.canvas.strand_deleted.connect(self._on_mask_layer_changed)

        # Connect to undo/redo signals to catch all layer changes
        self._connect_undo_redo_signals()

    def _connect_undo_redo_signals(self):
        """Connect to undo/redo manager signals to catch all state changes."""
        # Try to get undo_redo_manager from parent (layer_panel)
        undo_redo_manager = None
        if hasattr(self.parent(), 'undo_redo_manager'):
            undo_redo_manager = self.parent().undo_redo_manager
        # Also check if canvas has it
        elif hasattr(self.canvas, 'undo_redo_manager'):
            undo_redo_manager = self.canvas.undo_redo_manager

        # Store reference for cleanup
        self.undo_redo_manager = undo_redo_manager

        if undo_redo_manager:
            if hasattr(undo_redo_manager, 'undo_performed'):
                undo_redo_manager.undo_performed.connect(self._on_mask_layer_changed)
            if hasattr(undo_redo_manager, 'redo_performed'):
                undo_redo_manager.redo_performed.connect(self._on_mask_layer_changed)

    def _get_group_strands(self):
        """
        Get all regular strands for the group, excluding MaskedStrand objects.

        Only regular strands should appear in the mask grid - MaskedStrand objects
        should be filtered out since they represent masks, not base layers.
        """
        if not hasattr(self.canvas, 'groups') or self.group_name not in self.canvas.groups:
            return []

        group_data = self.canvas.groups[self.group_name]
        layer_names = group_data.get('layers', [])

        strands = []
        for layer_name in layer_names:
            strand = self.canvas.find_strand_by_name(layer_name)
            # Only include regular strands, exclude MaskedStrand objects
            if strand and not isinstance(strand, MaskedStrand):
                strands.append(strand)

        # Sort by layer name for consistent ordering
        strands.sort(key=lambda s: s.layer_name)
        return strands

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

    def _style_mask_checkbox(self, checkbox, is_dark_mode, is_enabled=None, spacing=0):
        """Apply the shared large blue indicator styling per checkbox."""
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
                spacing: {spacing}px;
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

    def _restyle_all_checkboxes(self):
        """Reapply themed checkbox styling when the theme or enabled state changes."""
        is_dark_mode = (self.theme == 'dark')

        for checkbox in self.checkboxes.values():
            self._style_mask_checkbox(checkbox, is_dark_mode, checkbox.isEnabled())

        for checkbox in self.header_row_checkboxes.values():
            self._style_mask_checkbox(checkbox, is_dark_mode, checkbox.isEnabled())

        for checkbox in self.header_col_checkboxes.values():
            self._style_mask_checkbox(checkbox, is_dark_mode, checkbox.isEnabled())

    def setup_ui(self):
        """Setup the user interface."""
        _ = translations[self.language_code]

        # Window setup
        self.setWindowTitle(f"{_['create_mask_grid']} - {self.group_name}")
        self.setModal(False)
        self.setMinimumSize(600, 400)
        self.resize(800, 600)

        # Set RTL for Hebrew
        if self.language_code == 'he':
            self.setLayoutDirection(Qt.RightToLeft)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Info label
        info_text = _['mask_grid_info'].format(self.group_name, len(self.strands))
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)

        # Create table
        self.table = QTableWidget()
        self.table.setRowCount(len(self.strands) + 1)  # +1 for header row
        self.table.setColumnCount(len(self.strands) + 1)  # +1 for header column

        # Setup table properties
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)

        # Set fixed row/column sizes for compact display
        for i in range(len(self.strands) + 1):
            if i == 0:
                self.table.setRowHeight(i, 80)  # Header row height for vertical layout
            else:
                self.table.setRowHeight(i, 60)  # Data row height - allow room for large toggles
            self.table.setColumnWidth(i, 50)  # Compact column width

        # First column should be wider for labels
        self.table.setColumnWidth(0, 90)  # Header column width - enough space for color, name, and checkbox

        # Populate table
        self._populate_table()

        main_layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.apply_button = QPushButton(_['apply'])
        self.apply_button.clicked.connect(self.on_apply)
        self.apply_button.setMinimumWidth(80)
        button_layout.addWidget(self.apply_button)

        self.close_button = QPushButton(_['close'])
        self.close_button.clicked.connect(self.close)
        self.close_button.setMinimumWidth(80)
        button_layout.addWidget(self.close_button)

        main_layout.addLayout(button_layout)

    def _populate_table(self):
        """Populate the table with strand info and checkboxes."""
        _ = translations[self.language_code]

        # Top-left corner cell (empty)
        corner_widget = QWidget()
        self.table.setCellWidget(0, 0, corner_widget)

        # Column headers (top row) with select all checkboxes
        for col_idx, strand in enumerate(self.strands):
            header_widget = self._create_header_widget(strand, is_row=False, index=col_idx)
            self.table.setCellWidget(0, col_idx + 1, header_widget)

        # Row headers (left column) with select all checkboxes
        for row_idx, strand in enumerate(self.strands):
            header_widget = self._create_header_widget(strand, is_row=True, index=row_idx)
            self.table.setCellWidget(row_idx + 1, 0, header_widget)

        # Data cells with checkboxes
        for row_idx, row_strand in enumerate(self.strands):
            for col_idx, col_strand in enumerate(self.strands):
                # Skip diagonal (can't mask strand with itself)
                if row_idx == col_idx:
                    empty_widget = QWidget()
                    empty_widget.setStyleSheet("background-color: #404040;" if self.theme == 'dark' else "background-color: #E0E0E0;")
                    self.table.setCellWidget(row_idx + 1, col_idx + 1, empty_widget)
                    continue

                # Check if mask already exists
                mask_exists = self._check_mask_exists(row_strand.layer_name, col_strand.layer_name)

                # Create checkbox
                checkbox_widget = self._create_checkbox_widget(row_idx, col_idx, mask_exists)
                self.table.setCellWidget(row_idx + 1, col_idx + 1, checkbox_widget)

    def _create_header_widget(self, strand, is_row, index):
        """Create a header widget with color indicator, name, and select all checkbox."""
        _ = translations[self.language_code]

        widget = QWidget()
        indicator_size = 20
        is_dark_mode = (self.theme == 'dark')

        if is_row:
            # Row headers (left column) - vertical layout with checkbox on new line
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(2)
            layout.setAlignment(Qt.AlignHCenter)

            # Horizontal container for color and name
            top_container = QWidget()
            top_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            top_layout = QHBoxLayout(top_container)
            top_layout.setContentsMargins(0, 3, 0, 0)
            top_layout.setSpacing(6)
            top_layout.setAlignment(Qt.AlignCenter)

            top_layout.addStretch()

            # Color indicator
            color_hex = strand.color.name()
            color_label = QLabel("  ")
            color_label.setFixedSize(16, 16)
            color_label.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #888; border-radius: 2px;")
            color_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            top_layout.addWidget(color_label, 0, Qt.AlignVCenter)

            # Layer name
            name_label = QLabel(strand.layer_name)
            name_label.setWordWrap(False)
            name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            name_label.setStyleSheet("font-size: 9pt;")
            name_label.setAlignment(Qt.AlignCenter)
            top_layout.addWidget(name_label, 0, Qt.AlignVCenter)
            top_layout.addStretch()

            layout.addWidget(top_container)

            # Container for centered checkbox
            checkbox_container = QWidget()
            checkbox_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            checkbox_layout = QHBoxLayout(checkbox_container)
            checkbox_layout.setContentsMargins(0, 0, 0, 3)
            checkbox_layout.setSpacing(0)
            checkbox_layout.setAlignment(Qt.AlignCenter)

            # Select all checkbox (centered)
            select_all_checkbox = QCheckBox()
            select_all_checkbox.setChecked(False)
            select_all_checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            # Ensure the indicator itself is centered by removing label spacing
            # and constraining the widget width to the indicator width
            select_all_checkbox.setText("")

            # Apply custom styling from shadow editor
            self._apply_large_indicator(select_all_checkbox, indicator_size=indicator_size)
            self._setup_custom_checkmark(select_all_checkbox)
            select_all_checkbox.setFixedSize(indicator_size + 6, indicator_size + 6)

            select_all_checkbox.stateChanged.connect(
                lambda state, idx=index, row=is_row: self._on_header_checkbox_changed(idx, row, state)
            )

            checkbox_layout.addStretch()
            checkbox_layout.addWidget(select_all_checkbox)
            checkbox_layout.addStretch()

            layout.addWidget(checkbox_container)
        else:
            # Column headers (top row) - vertical layout stacked
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(2, 2, 2, 2)  # Same margins as row headers
            layout.setSpacing(2)
            layout.setAlignment(Qt.AlignCenter)

            # Color indicator (top)
            color_hex = strand.color.name()
            color_label = QLabel("  ")
            color_label.setFixedSize(16, 16)
            color_label.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #888; border-radius: 2px;")
            color_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(color_label, alignment=Qt.AlignCenter)

            # Layer name (middle)
            name_label = QLabel(strand.layer_name)
            name_label.setWordWrap(True)
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            name_label.setStyleSheet("font-size: 9pt;")
            layout.addWidget(name_label, alignment=Qt.AlignCenter)

            # Select all checkbox (bottom, no text label)
            select_all_checkbox = QCheckBox()
            select_all_checkbox.setChecked(False)
            select_all_checkbox.setText("")
            select_all_checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

            # Apply custom styling from shadow editor
            self._apply_large_indicator(select_all_checkbox, indicator_size=indicator_size)
            self._setup_custom_checkmark(select_all_checkbox)
            select_all_checkbox.setFixedSize(indicator_size + 6, indicator_size + 6)

            select_all_checkbox.stateChanged.connect(
                lambda state, idx=index, row=is_row: self._on_header_checkbox_changed(idx, row, state)
            )
            layout.addWidget(select_all_checkbox, alignment=Qt.AlignCenter)

        # Store reference
        if is_row:
            self.header_row_checkboxes[index] = select_all_checkbox
        else:
            self.header_col_checkboxes[index] = select_all_checkbox

        self._style_mask_checkbox(select_all_checkbox, is_dark_mode, select_all_checkbox.isEnabled())

        return widget

    def _create_checkbox_widget(self, row_idx, col_idx, is_disabled):
        """Create a checkbox widget for a table cell."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        checkbox = QCheckBox()
        checkbox.setChecked(is_disabled)
        checkbox.setEnabled(not is_disabled)

        indicator_size = 20

        # Apply custom styling from shadow editor
        self._apply_large_indicator(checkbox, indicator_size=indicator_size)
        self._setup_custom_checkmark(checkbox)
        # Remove internal spacing and fix size so indicator is truly centered
        checkbox.setText("")
        checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        checkbox.setFixedSize(indicator_size + 6, indicator_size + 6)

        # Connect to update header checkboxes
        checkbox.stateChanged.connect(lambda: self._update_header_checkboxes())

        layout.addWidget(checkbox)

        # Store reference
        self.checkboxes[(row_idx, col_idx)] = checkbox

        self._style_mask_checkbox(checkbox, self.theme == 'dark', checkbox.isEnabled())

        return widget

    def _check_mask_exists(self, strand1_name, strand2_name):
        """
        Check if a mask layer already exists between two strands.
        Uses LayerStateManager as the source of truth for mask state.
        """
        mask_name = f"{strand1_name}_{strand2_name}"

        # Use LayerStateManager's getMaskedLayers() as the source of truth
        if hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
            masked_layers = self.canvas.layer_state_manager.getMaskedLayers()
            return mask_name in masked_layers

        # Fallback to direct canvas.strands check if layer_state_manager not available
        for strand in self.canvas.strands:
            if isinstance(strand, MaskedStrand) and strand.layer_name == mask_name:
                return True

        return False

    def _on_header_checkbox_changed(self, index, is_row, state):
        """Handle select all checkbox change in header."""
        is_checked = (state == Qt.Checked)

        if is_row:
            # Select/deselect all in this row
            for col_idx in range(len(self.strands)):
                if (index, col_idx) in self.checkboxes:
                    checkbox = self.checkboxes[(index, col_idx)]
                    if checkbox.isEnabled():  # Only affect enabled checkboxes
                        checkbox.setChecked(is_checked)
        else:
            # Select/deselect all in this column
            for row_idx in range(len(self.strands)):
                if (row_idx, index) in self.checkboxes:
                    checkbox = self.checkboxes[(row_idx, index)]
                    if checkbox.isEnabled():  # Only affect enabled checkboxes
                        checkbox.setChecked(is_checked)

    def _update_header_checkboxes(self):
        """Update header checkboxes based on current checkbox states."""
        # Update row header checkboxes
        for row_idx in range(len(self.strands)):
            if row_idx in self.header_row_checkboxes:
                all_checked = True
                any_checked = False
                for col_idx in range(len(self.strands)):
                    if (row_idx, col_idx) in self.checkboxes:
                        checkbox = self.checkboxes[(row_idx, col_idx)]
                        if checkbox.isEnabled():
                            if checkbox.isChecked():
                                any_checked = True
                            else:
                                all_checked = False

                # Update header checkbox state (block signals to avoid recursion)
                header_checkbox = self.header_row_checkboxes[row_idx]
                header_checkbox.blockSignals(True)
                header_checkbox.setChecked(all_checked)
                header_checkbox.blockSignals(False)

        # Update column header checkboxes
        for col_idx in range(len(self.strands)):
            if col_idx in self.header_col_checkboxes:
                all_checked = True
                any_checked = False
                for row_idx in range(len(self.strands)):
                    if (row_idx, col_idx) in self.checkboxes:
                        checkbox = self.checkboxes[(row_idx, col_idx)]
                        if checkbox.isEnabled():
                            if checkbox.isChecked():
                                any_checked = True
                            else:
                                all_checked = False

                # Update header checkbox state (block signals to avoid recursion)
                header_checkbox = self.header_col_checkboxes[col_idx]
                header_checkbox.blockSignals(True)
                header_checkbox.setChecked(all_checked)
                header_checkbox.blockSignals(False)

    def on_apply(self):
        """Create masks for all checked cells."""
        mask_pairs = []

        # Collect all checked cells
        for (row_idx, col_idx), checkbox in self.checkboxes.items():
            if checkbox.isEnabled() and checkbox.isChecked():
                row_strand = self.strands[row_idx]
                col_strand = self.strands[col_idx]
                mask_pairs.append((row_strand.layer_name, col_strand.layer_name))

        if not mask_pairs:
            return

        # Create masks
        self._create_masks(mask_pairs)

        # Refresh table to show newly created masks as disabled
        self._refresh_table()

    def _create_masks(self, mask_pairs):
        """Create mask layers for the given pairs."""
        # Get undo_redo_manager to set batch operation flags
        undo_redo_manager = None
        if hasattr(self.canvas, 'layer_panel') and hasattr(self.canvas.layer_panel, 'undo_redo_manager'):
            undo_redo_manager = self.canvas.layer_panel.undo_redo_manager
        elif hasattr(self.canvas, 'undo_redo_manager'):
            undo_redo_manager = self.canvas.undo_redo_manager

        # Set flags to prevent intermediate state saves during batch operation
        if undo_redo_manager:
            setattr(undo_redo_manager, '_skip_save', True)
            setattr(undo_redo_manager, '_mask_save_in_progress', True)

        try:
            # Create all masks in the batch
            for strand1_name, strand2_name in mask_pairs:
                # Find strand objects
                strand1 = self.canvas.find_strand_by_name(strand1_name)
                strand2 = self.canvas.find_strand_by_name(strand2_name)

                if not strand1 or not strand2:
                    continue

                # Check if mask already exists (safety check)
                if self._check_mask_exists(strand1_name, strand2_name):
                    continue

                # Create mask directly using canvas's create_masked_layer method
                # This handles everything: creates MaskedStrand, adds button, updates UI
                if hasattr(self.canvas, 'create_masked_layer'):
                    self.canvas.create_masked_layer(strand1, strand2)
        finally:
            # Clear flags and save state once for the entire batch operation
            if undo_redo_manager:
                setattr(undo_redo_manager, '_skip_save', False)
                setattr(undo_redo_manager, '_mask_save_in_progress', False)
                # Save state once for all masks created
                undo_redo_manager.save_state()

    def _refresh_table(self):
        """Refresh the table to reflect current mask state (both created and deleted masks)."""
        is_dark_mode = (self.theme == 'dark')
        for (row_idx, col_idx), checkbox in self.checkboxes.items():
            row_strand = self.strands[row_idx]
            col_strand = self.strands[col_idx]

            mask_exists = self._check_mask_exists(row_strand.layer_name, col_strand.layer_name)

            if mask_exists:
                # Mask exists - disable and check the checkbox
                checkbox.setChecked(True)
                checkbox.setEnabled(False)
            else:
                # Mask doesn't exist - enable and uncheck if it was previously disabled
                if not checkbox.isEnabled():
                    checkbox.setEnabled(True)
                    checkbox.setChecked(False)

            self._style_mask_checkbox(checkbox, is_dark_mode, checkbox.isEnabled())

        # Update header checkboxes
        self._update_header_checkboxes()

    def _on_mask_layer_changed(self, *args):
        """
        Called when a mask layer is created or deleted outside the dialog.
        Refreshes the table to reflect the current state of masks.
        """
        self._refresh_table()

    def closeEvent(self, event):
        """Clean up signal connections when dialog is closed."""
        # Disconnect signals to prevent memory leaks
        if hasattr(self.canvas, 'theme_changed'):
            try:
                self.canvas.theme_changed.disconnect(self._apply_theme)
            except:
                pass
        if hasattr(self.canvas, 'masked_layer_created'):
            try:
                self.canvas.masked_layer_created.disconnect(self._on_mask_layer_changed)
            except:
                pass
        if hasattr(self.canvas, 'strand_deleted'):
            try:
                self.canvas.strand_deleted.disconnect(self._on_mask_layer_changed)
            except:
                pass

        # Disconnect undo/redo signals
        if hasattr(self, 'undo_redo_manager') and self.undo_redo_manager:
            try:
                self.undo_redo_manager.undo_performed.disconnect(self._on_mask_layer_changed)
            except:
                pass
            try:
                self.undo_redo_manager.redo_performed.disconnect(self._on_mask_layer_changed)
            except:
                pass

        # Call parent closeEvent
        super().closeEvent(event)

    def _apply_theme(self):
        """Apply theme-based styling to the dialog."""
        # Update theme from canvas
        main_window = self.parent()
        while main_window and not hasattr(main_window, 'current_theme'):
            main_window = main_window.parent()
        if main_window:
            self.theme = main_window.current_theme

        if self.theme == 'dark':
            self.setStyleSheet("""
                QDialog {
                    background-color: #2C2C2C;
                    color: white;
                }
                QLabel {
                    color: white;
                }
                QTableWidget {
                    background-color: #3D3D3D;
                    color: white;
                    gridline-color: #555;
                    border: 1px solid #555;
                }
                QTableWidget::item {
                    background-color: #3D3D3D;
                }
                QHeaderView::section {
                    background-color: #2C2C2C;
                    color: white;
                    border: 1px solid #555;
                }
                QCheckBox {
                    color: white;
                    spacing: 2px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    min-width: 20px;
                    min-height: 20px;
                    border: 2px solid #666666;
                    border-radius: 4px;
                    background-color: #2A2A2A;
                }
                QCheckBox::indicator:hover {
                    border: 2px solid #888888;
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
                QCheckBox::indicator:disabled {
                    background-color: #1F1F1F;
                    border: 2px solid #444444;
                }
                QPushButton {
                    background-color: #252525;
                    color: white;
                    border: 2px solid #000000;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #353535;
                    border: 2px solid #4A6FA5;
                }
                QPushButton:pressed {
                    background-color: #1A1A1A;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: #F5F5F5;
                    color: black;
                }
                QLabel {
                    color: black;
                }
                QTableWidget {
                    background-color: white;
                    color: black;
                    gridline-color: #CCC;
                    border: 1px solid #CCC;
                }
                QTableWidget::item {
                    background-color: white;
                }
                QHeaderView::section {
                    background-color: #E0E0E0;
                    color: black;
                    border: 1px solid #CCC;
                }
                QCheckBox {
                    color: black;
                    spacing: 2px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    min-width: 20px;
                    min-height: 20px;
                    border: 2px solid #AAAAAA;
                    border-radius: 4px;
                    background-color: #FFFFFF;
                }
                QCheckBox::indicator:hover {
                    border: 2px solid #888888;
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
                QCheckBox::indicator:disabled {
                    background-color: #F0F0F0;
                    border: 2px solid #BBBBBB;
                }
                QPushButton {
                    background-color: #FFFFFF;
                    color: black;
                    border: 2px solid #CCCCCC;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #E8E8E8;
                    border: 2px solid #A0C0E0;
                }
                QPushButton:pressed {
                    background-color: #D0D0D0;
                }
            """)

        self._restyle_all_checkboxes()
