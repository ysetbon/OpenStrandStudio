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

    def _get_group_strands(self):
        """Get all strands (including attached strands) for the group."""
        if not hasattr(self.canvas, 'groups') or self.group_name not in self.canvas.groups:
            return []

        group_data = self.canvas.groups[self.group_name]
        layer_names = group_data.get('layers', [])

        strands = []
        for layer_name in layer_names:
            strand = self.canvas.find_strand_by_name(layer_name)
            if strand:
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

    def setup_ui(self):
        """Setup the user interface."""
        _ = translations[self.language_code]

        # Window setup
        self.setWindowTitle(f"{_['create_mask_grid']} - {self.group_name}")
        self.setModal(True)
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
            self.table.setRowHeight(i, 32)
            self.table.setColumnWidth(i, 50)  # Compact column width

        # First column and row should be slightly wider for labels
        self.table.setColumnWidth(0, 75)  # Header column width - compact
        self.table.setRowHeight(0, 70)  # Header row height for vertical layout (color, name, checkbox)

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

        if is_row:
            # Row headers (left column) - horizontal layout in one line
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(2, 2, 2, 2)
            layout.setSpacing(1)  # Minimal spacing

            # Color indicator
            color_hex = strand.color.name()
            color_label = QLabel("  ")
            color_label.setFixedSize(16, 16)
            color_label.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #888; border-radius: 2px;")
            layout.addWidget(color_label)

            # Layer name
            name_label = QLabel(strand.layer_name)
            name_label.setWordWrap(False)
            name_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            name_label.setStyleSheet("font-size: 9pt;")
            layout.addWidget(name_label)

            # Select all checkbox (no text label)
            select_all_checkbox = QCheckBox()
            select_all_checkbox.setChecked(False)

            # Apply custom styling from shadow editor
            self._apply_large_indicator(select_all_checkbox, indicator_size=16)
            self._setup_custom_checkmark(select_all_checkbox)

            select_all_checkbox.stateChanged.connect(
                lambda state, idx=index, row=is_row: self._on_header_checkbox_changed(idx, row, state)
            )
            layout.addWidget(select_all_checkbox)
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

            # Apply custom styling from shadow editor
            self._apply_large_indicator(select_all_checkbox, indicator_size=16)
            self._setup_custom_checkmark(select_all_checkbox)

            select_all_checkbox.stateChanged.connect(
                lambda state, idx=index, row=is_row: self._on_header_checkbox_changed(idx, row, state)
            )
            layout.addWidget(select_all_checkbox, alignment=Qt.AlignCenter)

        # Store reference
        if is_row:
            self.header_row_checkboxes[index] = select_all_checkbox
        else:
            self.header_col_checkboxes[index] = select_all_checkbox

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

        # Apply custom styling from shadow editor
        self._apply_large_indicator(checkbox, indicator_size=18)
        self._setup_custom_checkmark(checkbox)

        if is_disabled:
            # Gray out existing masks
            checkbox.setStyleSheet("QCheckBox { color: #808080; }")

        # Connect to update header checkboxes
        checkbox.stateChanged.connect(lambda: self._update_header_checkboxes())

        layout.addWidget(checkbox)

        # Store reference
        self.checkboxes[(row_idx, col_idx)] = checkbox

        return widget

    def _check_mask_exists(self, strand1_name, strand2_name):
        """Check if a mask layer already exists between two strands."""
        mask_name = f"{strand1_name}_{strand2_name}"

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

    def _refresh_table(self):
        """Refresh the table to reflect newly created masks."""
        for (row_idx, col_idx), checkbox in self.checkboxes.items():
            if checkbox.isEnabled():
                row_strand = self.strands[row_idx]
                col_strand = self.strands[col_idx]

                if self._check_mask_exists(row_strand.layer_name, col_strand.layer_name):
                    checkbox.setChecked(True)
                    checkbox.setEnabled(False)
                    checkbox.setStyleSheet("QCheckBox { color: #808080; }")

        # Update header checkboxes
        self._update_header_checkboxes()

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
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border: 2px solid #666;
                    border-radius: 3px;
                    background-color: #2C2C2C;
                }
                QCheckBox::indicator:checked {
                    background-color: #4A6FA5;
                    border: 2px solid #6A9FD5;
                }
                QCheckBox::indicator:disabled {
                    background-color: #404040;
                    border: 2px solid #555;
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
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border: 2px solid #999;
                    border-radius: 3px;
                    background-color: white;
                }
                QCheckBox::indicator:checked {
                    background-color: #A0C0E0;
                    border: 2px solid #7090C0;
                }
                QCheckBox::indicator:disabled {
                    background-color: #E0E0E0;
                    border: 2px solid #BBB;
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
