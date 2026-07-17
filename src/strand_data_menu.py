"""Layer-panel menu integration for selective strand data copy/paste."""

from functools import partial

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QCheckBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from masked_strand import MaskedStrand
from numbered_layer_button import HoverLabel
from strand_data_clipboard import (
    COPY_PROPERTIES,
    apply_strand_data,
    clipboard_property_count,
    snapshot_strand_data,
)


class ClickableHoverLabel(HoverLabel):
    """HoverLabel variant used for expandable and actionable menu rows."""

    clicked = pyqtSignal()

    def mouseReleaseEvent(self, event):
        if self.isEnabled() and event.button() == Qt.LeftButton:
            self.clicked.emit()
            event.accept()
            return
        super().mouseReleaseEvent(event)


class StrandDataClipboardMixin:
    """Adds strand-data clipboard state and menu actions to ``LayerPanel``."""

    def _initialize_strand_data_clipboard(self):
        self.strand_data_copy_options = {key: True for key in COPY_PROPERTIES}
        if not hasattr(self.canvas, "strand_clipboard"):
            self.canvas.strand_clipboard = None

    def strand_data_menu_texts(self, strings):
        """Texts included when calculating the batch menu's dynamic width."""
        return [
            strings.get("copy_strand_data", "Copy Strand Data") + "  ▾",
            strings.get("paste_copied_data", "Paste Copied Data") + "  ▾",
            strings.get("angle_from_start_point", "Angle from Start Point"),
            strings.get("angle_from_end_point", "Angle from End Point"),
        ]

    def _disabled_strand_data_menu_label(self, label):
        background = (
            "#333333" if getattr(self, "current_theme", "light") == "dark" else "#F0F0F0"
        )
        label.setStyleSheet(
            f"background-color: {background}; color: #909090; "
            "padding: 5px 25px 5px 5px;"
        )
        label.setEnabled(False)

    def add_strand_data_menu_actions(self, menu, source_index, strings, theme):
        """Append collapsed Copy and Paste dropdowns to the batch menu."""
        source = (
            self.canvas.strands[source_index]
            if 0 <= source_index < len(self.canvas.strands)
            else None
        )
        copy_title = strings.get("copy_strand_data", "Copy Strand Data")
        paste_title = strings.get("paste_copied_data", "Paste Copied Data")

        copy_label = ClickableHoverLabel(f"{copy_title}  ▾", menu, theme)
        copy_action = QWidgetAction(menu)
        copy_action.setDefaultWidget(copy_label)
        menu.addAction(copy_action)

        copy_panel, refresh_copy_panel = self._build_strand_copy_panel(
            menu, source_index, strings, theme
        )
        copy_panel_action = QWidgetAction(menu)
        copy_panel_action.setDefaultWidget(copy_panel)
        copy_panel_action.setVisible(False)
        menu.addAction(copy_panel_action)

        menu.addSeparator()

        clipboard = getattr(self.canvas, "strand_clipboard", None)
        paste_label = ClickableHoverLabel(f"{paste_title}  ▾", menu, theme)
        paste_action = QWidgetAction(menu)
        paste_action.setDefaultWidget(paste_label)
        menu.addAction(paste_action)

        paste_panel = self._build_strand_paste_panel(menu, strings, theme)
        paste_panel_action = QWidgetAction(menu)
        paste_panel_action.setDefaultWidget(paste_panel)
        paste_panel_action.setVisible(False)
        menu.addAction(paste_panel_action)

        copy_allowed = source is not None and not isinstance(source, MaskedStrand)
        paste_allowed = clipboard is not None and bool(self._eligible_paste_indices())
        if not copy_allowed:
            self._disabled_strand_data_menu_label(copy_label)
        if not paste_allowed:
            self._disabled_strand_data_menu_label(paste_label)

        def toggle_copy_panel():
            expanded = not copy_panel_action.isVisible()
            paste_panel_action.setVisible(False)
            paste_label.setText(f"{paste_title}  ▾")
            copy_panel_action.setVisible(expanded)
            copy_label.setText(f"{copy_title}  {'▴' if expanded else '▾'}")
            if expanded:
                refresh_copy_panel()
            menu.adjustSize()

        def toggle_paste_panel():
            expanded = not paste_panel_action.isVisible()
            copy_panel_action.setVisible(False)
            copy_label.setText(f"{copy_title}  ▾")
            paste_panel_action.setVisible(expanded)
            paste_label.setText(f"{paste_title}  {'▴' if expanded else '▾'}")
            menu.adjustSize()

        copy_label.clicked.connect(toggle_copy_panel)
        paste_label.clicked.connect(toggle_paste_panel)

    def _build_strand_copy_panel(self, menu, source_index, strings, theme):
        panel = QWidget(menu)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 6, 8, 8)
        layout.setSpacing(3)
        background = "#333333" if theme == "dark" else "#F0F0F0"
        foreground = "#FFFFFF" if theme == "dark" else "#000000"
        panel.setStyleSheet(
            f"QWidget {{ background-color: {background}; color: {foreground}; }}"
            "QPushButton { padding: 5px 12px; border-radius: 3px; }"
        )

        select_all = QCheckBox(strings.get("select_all", "Select All"), panel)
        select_all.setTristate(True)
        layout.addWidget(select_all)

        labels = {
            "start_point": strings.get("strand_data_start_point", "Start Point"),
            "end_point": strings.get("strand_data_end_point", "End Point"),
            "control_points": strings.get("strand_data_control_points", "Control Points"),
            "width": strings.get("strand_data_width", "Width"),
            "strand_color": strings.get("strand_data_strand_color", "Strand Color"),
            "stroke_color": strings.get("strand_data_stroke_color", "Stroke Color"),
        }
        checkboxes = {}
        for key in COPY_PROPERTIES:
            checkbox = QCheckBox(labels[key], panel)
            checkbox.setChecked(self.strand_data_copy_options.get(key, True))
            layout.addWidget(checkbox)
            checkboxes[key] = checkbox

        copy_button = QPushButton(panel)
        layout.addWidget(copy_button)
        updating = {"value": False}

        def refresh():
            count = sum(checkbox.isChecked() for checkbox in checkboxes.values())
            state = (
                Qt.Checked
                if count == len(checkboxes)
                else Qt.PartiallyChecked
                if count
                else Qt.Unchecked
            )
            updating["value"] = True
            select_all.setCheckState(state)
            updating["value"] = False
            copy_button.setText(f"{strings.get('copy', 'Copy')} ({count})")
            copy_button.setEnabled(count > 0)

        def option_changed(key, checked):
            self.strand_data_copy_options[key] = bool(checked)
            refresh()

        for key, checkbox in checkboxes.items():
            checkbox.toggled.connect(partial(option_changed, key))

        def toggle_all(state):
            if updating["value"]:
                return
            checked = state != Qt.Unchecked
            updating["value"] = True
            for key, checkbox in checkboxes.items():
                checkbox.setChecked(checked)
                self.strand_data_copy_options[key] = checked
            updating["value"] = False
            refresh()

        select_all.stateChanged.connect(toggle_all)

        def perform_copy():
            selected = [
                key for key, checkbox in checkboxes.items() if checkbox.isChecked()
            ]
            if self.copy_strand_data(source_index, selected):
                menu.close()

        copy_button.clicked.connect(perform_copy)
        refresh()
        return panel, refresh

    def _build_strand_paste_panel(self, menu, strings, theme):
        panel = QWidget(menu)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(0)
        clipboard = getattr(self.canvas, "strand_clipboard", None)
        count = clipboard_property_count(clipboard)
        source_name = clipboard.get("source_layer_name", "") if clipboard else ""
        hint_template = strings.get(
            "strand_data_clipboard_hint", "{count} properties from {source}"
        )
        hint = QLabel(hint_template.format(count=count, source=source_name), panel)
        background = "#333333" if theme == "dark" else "#F0F0F0"
        hint.setStyleSheet(
            f"background-color: {background}; color: #909090; "
            "padding: 5px 25px 5px 15px;"
        )
        layout.addWidget(hint)

        for anchor, key, fallback in (
            ("start", "angle_from_start_point", "Angle from Start Point"),
            ("end", "angle_from_end_point", "Angle from End Point"),
        ):
            label = ClickableHoverLabel("      " + strings.get(key, fallback), panel, theme)
            label.clicked.connect(
                lambda chosen=anchor: self._paste_strand_data_from_menu(menu, chosen)
            )
            layout.addWidget(label)
        return panel

    def _paste_strand_data_from_menu(self, menu, anchor):
        if self.paste_copied_strand_data(anchor):
            menu.close()

    def copy_strand_data(self, source_index, selected_properties=None):
        """Snapshot selected properties from one ordinary or attached strand."""
        if not 0 <= source_index < len(self.canvas.strands):
            return False
        source = self.canvas.strands[source_index]
        if isinstance(source, MaskedStrand):
            return False
        try:
            self.canvas.strand_clipboard = snapshot_strand_data(
                source, selected_properties
            )
        except ValueError:
            return False
        return True

    def clear_strand_data_clipboard(self):
        self.canvas.strand_clipboard = None
        for button in self.layer_buttons:
            button.update()

    def _eligible_paste_indices(self, indices=None):
        candidates = self.multi_selected_layers if indices is None else indices
        return [
            index
            for index in sorted(candidates)
            if 0 <= index < len(self.canvas.strands)
            and index not in self.locked_layers
            and not isinstance(self.canvas.strands[index], MaskedStrand)
        ]

    def paste_copied_strand_data(self, anchor="start", target_indices=None):
        """Paste onto all eligible ticked layers and create one undo state."""
        clipboard = getattr(self.canvas, "strand_clipboard", None)
        if clipboard is None:
            return 0
        changed = []
        for index in self._eligible_paste_indices(target_indices):
            strand = self.canvas.strands[index]
            if apply_strand_data(clipboard, strand, anchor):
                changed.append(index)
                if index < len(self.layer_buttons):
                    self.layer_buttons[index].set_color(QColor(strand.color))

        if not changed:
            return 0
        self.canvas.update()
        manager = getattr(self.canvas, "undo_redo_manager", None)
        if manager is not None:
            manager._last_save_time = 0
            manager.save_state()
        return len(changed)
