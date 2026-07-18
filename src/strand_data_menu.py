"""Layer-panel menu integration for selective strand data copy/paste."""

from functools import partial

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)


def _keep_menu_on_screen(menu):
    """Shift an already-open menu back inside the screen after it grew.

    Expanding a dropdown panel inline makes the menu taller in place; Qt only
    auto-positions menus when they open, so a low menu would grow past the
    bottom of the screen. Mirrors the flip-up behavior of normal menus.
    """
    try:
        screen_geometry = menu.screen().availableGeometry()
    except AttributeError:
        screen_geometry = QApplication.desktop().availableGeometry(menu)
    pos = menu.pos()
    x = max(min(pos.x(), screen_geometry.right() - menu.width() + 1),
            screen_geometry.left())
    y = max(min(pos.y(), screen_geometry.bottom() - menu.height() + 1),
            screen_geometry.top())
    if (x, y) != (pos.x(), pos.y()):
        menu.move(x, y)

from masked_strand import MaskedStrand
from numbered_layer_button import HoverLabel, build_menu_stylesheet
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

    def _strand_data_is_hebrew(self):
        return getattr(self, "language_code", "en") == "he"

    def _configure_strand_data_menu_label(self, label):
        """Apply the same RTL handling every other menu row uses."""
        if self._strand_data_is_hebrew():
            label.setLayoutDirection(Qt.RightToLeft)
            label.setAlignment(Qt.AlignLeft)

    def _disabled_strand_data_menu_label(self, label, theme):
        background = "#333333" if theme == "dark" else "#F0F0F0"
        label.setStyleSheet(
            f"background-color: {background}; color: #909090; "
            "padding: 5px 25px 5px 5px;"
        )
        label.setEnabled(False)

    def add_strand_data_menu_actions(self, menu, source_index, strings, theme):
        """Append collapsed Paste and Copy dropdowns to the batch menu.

        Paste sits above Copy so expanding the Copy panel (the taller of the
        two) never pushes the Paste row around.
        """
        source = (
            self.canvas.strands[source_index]
            if 0 <= source_index < len(self.canvas.strands)
            else None
        )
        copy_title = strings.get("copy_strand_data", "Copy Strand Data")
        paste_title = strings.get("paste_copied_data", "Paste Copied Data")

        clipboard = getattr(self.canvas, "strand_clipboard", None)
        paste_label = ClickableHoverLabel(f"{paste_title}  ▾", menu, theme)
        self._configure_strand_data_menu_label(paste_label)
        paste_action = QWidgetAction(menu)
        paste_action.setDefaultWidget(paste_label)
        menu.addAction(paste_action)

        paste_panel = self._build_strand_paste_panel(menu, strings, theme)
        paste_panel_action = QWidgetAction(menu)
        paste_panel_action.setDefaultWidget(paste_panel)
        paste_panel_action.setVisible(False)
        menu.addAction(paste_panel_action)

        menu.addSeparator()

        copy_label = ClickableHoverLabel(f"{copy_title}  ▾", menu, theme)
        self._configure_strand_data_menu_label(copy_label)
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

        copy_allowed = source is not None and not isinstance(source, MaskedStrand)
        if not copy_allowed:
            self._disabled_strand_data_menu_label(copy_label, theme)
        if clipboard is None:
            self._disabled_strand_data_menu_label(paste_label, theme)

        def remember_home_position():
            if not hasattr(menu, "_strand_data_home_pos"):
                menu._strand_data_home_pos = menu.pos()

        def toggle_copy_panel():
            remember_home_position()
            expanded = not copy_panel_action.isVisible()
            paste_panel_action.setVisible(False)
            paste_label.setText(f"{paste_title}  ▾")
            copy_panel_action.setVisible(expanded)
            copy_label.setText(f"{copy_title}  {'▴' if expanded else '▾'}")
            if expanded:
                refresh_copy_panel()
            menu.adjustSize()
            if not expanded:
                menu.move(menu._strand_data_home_pos)
            _keep_menu_on_screen(menu)

        def toggle_paste_panel():
            remember_home_position()
            expanded = not paste_panel_action.isVisible()
            copy_panel_action.setVisible(False)
            copy_label.setText(f"{copy_title}  ▾")
            paste_panel_action.setVisible(expanded)
            paste_label.setText(f"{paste_title}  {'▴' if expanded else '▾'}")
            menu.adjustSize()
            if not expanded:
                menu.move(menu._strand_data_home_pos)
            _keep_menu_on_screen(menu)

        copy_label.clicked.connect(toggle_copy_panel)
        paste_label.clicked.connect(toggle_paste_panel)

    def _build_strand_copy_panel(self, menu, source_index, strings, theme):
        """Toggle panel embedded exactly like the Arrow Customization block."""
        is_hebrew = self._strand_data_is_hebrew()
        foreground = "#ffffff" if theme == "dark" else "#000000"

        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)

        labels = {
            "start_point": strings.get("strand_data_start_point", "Start Point"),
            "end_point": strings.get("strand_data_end_point", "End Point"),
            "control_points": strings.get("strand_data_control_points", "Control Points"),
            "width": strings.get("strand_data_width", "Width"),
            "strand_color": strings.get("strand_data_strand_color", "Strand Color"),
            "stroke_color": strings.get("strand_data_stroke_color", "Stroke Color"),
        }

        def add_toggle_row(text):
            row = QHBoxLayout()
            label = QLabel(text)
            if is_hebrew:
                label.setLayoutDirection(Qt.RightToLeft)
                label.setAlignment(Qt.AlignRight)
            label.setStyleSheet(f"color: {foreground}; padding: 5px;")
            checkbox = QCheckBox()
            row.addWidget(label)
            row.addStretch()
            row.addWidget(checkbox)
            layout.addLayout(row)
            return checkbox

        select_all = add_toggle_row(strings.get("select_all", "Select All"))
        select_all.setTristate(True)

        checkboxes = {}
        for key in COPY_PROPERTIES:
            checkbox = add_toggle_row(labels[key])
            checkbox.setChecked(self.strand_data_copy_options.get(key, True))
            checkboxes[key] = checkbox

        copy_button = QPushButton()
        copy_button.setFlat(True)
        copy_button.setMinimumHeight(30)
        if theme == "dark":
            copy_button.setStyleSheet(
                "QPushButton { background-color: transparent; border: none; color: white; }"
                "QPushButton:hover { background-color: #F0F0F0; color: black; }"
                "QPushButton:disabled { color: #909090; }"
            )
        else:
            copy_button.setStyleSheet(
                "QPushButton { background-color: transparent; border: none; color: black; }"
                "QPushButton:hover { background-color: #333333; color: white; }"
                "QPushButton:disabled { color: #909090; }"
            )
        layout.addWidget(copy_button)

        panel.setLayout(layout)
        panel.setStyleSheet(
            f"background-color: {'#333333' if theme == 'dark' else '#F0F0F0'}; "
            "border-radius: 5px;"
        )

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
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(0)
        clipboard = getattr(self.canvas, "strand_clipboard", None)
        hint = QLabel(self._strand_data_clipboard_hint_text(strings))
        self._configure_strand_data_menu_label(hint)
        background = "#333333" if theme == "dark" else "#F0F0F0"
        hint.setStyleSheet(
            f"background-color: {background}; color: #909090; "
            "padding: 5px 25px 5px 5px;"
        )
        hint.setIndent(10)
        layout.addWidget(hint)

        for anchor, key, fallback in (
            ("start", "angle_from_start_point", "Angle from Start Point"),
            ("end", "angle_from_end_point", "Angle from End Point"),
        ):
            label = ClickableHoverLabel(strings.get(key, fallback), panel, theme)
            self._configure_strand_data_menu_label(label)
            label.setIndent(20)
            if clipboard is None:
                self._disabled_strand_data_menu_label(label, theme)
            label.clicked.connect(
                lambda chosen=anchor: self._paste_strand_data_from_menu(menu, chosen)
            )
            layout.addWidget(label)
        panel.setLayout(layout)
        return panel

    def _strand_data_clipboard_hint_text(self, strings):
        clipboard = getattr(self.canvas, "strand_clipboard", None)
        template = strings.get(
            "strand_data_clipboard_hint", "{count} properties from {source}"
        )
        return template.format(
            count=clipboard_property_count(clipboard),
            source=clipboard.get("source_layer_name", "") if clipboard else "",
        )

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
        self._refresh_strand_data_indicators()
        return True

    def clear_strand_data_clipboard(self):
        self.canvas.strand_clipboard = None
        self._refresh_strand_data_indicators()

    def _refresh_strand_data_indicators(self):
        """Repaint layer buttons so copy badges and paste chips follow the clipboard."""
        for button in self.layer_buttons:
            if getattr(button, "strand_chip_hover", None) is not None:
                button.strand_chip_hover = None
            if getattr(button, "strand_badge_hover", False):
                button.strand_badge_hover = False
            button.update()

    def is_strand_data_copy_source(self, button):
        """Whether ``button`` is the source of the current clipboard snapshot."""
        clipboard = getattr(self.canvas, "strand_clipboard", None)
        return (
            clipboard is not None
            and clipboard.get("source_layer_name") == button.layer_name
        )

    def is_strand_data_paste_target(self, index):
        """Whether the layer at ``index`` can receive a paste right now."""
        clipboard = getattr(self.canvas, "strand_clipboard", None)
        return (
            clipboard is not None
            and 0 <= index < len(self.canvas.strands)
            and index not in self.locked_layers
            and not isinstance(self.canvas.strands[index], MaskedStrand)
        )

    def show_strand_data_badge_popup(self, button, global_pos):
        """Small popup on the source layer's copy badge: hint text + Clear."""
        from translations import translations

        strings = translations.get(self.language_code, translations["en"])
        theme = getattr(self, "current_theme", "light")

        popup = QMenu(self)
        if self._strand_data_is_hebrew():
            popup.setLayoutDirection(Qt.RightToLeft)
        popup.setStyleSheet(build_menu_stylesheet(theme))

        hint = QLabel(self._strand_data_clipboard_hint_text(strings))
        self._configure_strand_data_menu_label(hint)
        self._disabled_strand_data_menu_label(hint, theme)
        hint_action = QWidgetAction(popup)
        hint_action.setDefaultWidget(hint)
        popup.addAction(hint_action)

        popup.addSeparator()

        clear_label = ClickableHoverLabel(
            strings.get("clear", "Clear"), popup, theme
        )
        self._configure_strand_data_menu_label(clear_label)
        clear_action = QWidgetAction(popup)
        clear_action.setDefaultWidget(clear_label)
        popup.addAction(clear_action)

        def perform_clear():
            popup.close()
            self.clear_strand_data_clipboard()

        clear_label.clicked.connect(perform_clear)
        # Backup path: if the menu routes the click to the action instead of
        # the embedded label (mouse-grab edge cases), still clear.
        clear_action.triggered.connect(perform_clear)
        popup.exec_(global_pos)

    def paste_strand_data_via_chip(self, index, anchor):
        """One-click chip paste: all ticked layers, or this layer alone if unticked."""
        if index in self.multi_selected_layers:
            targets = None
        else:
            targets = [index]
        return self.paste_copied_strand_data(anchor, targets)

    def _eligible_paste_indices(self, indices=None):
        candidates = self.multi_selected_layers if indices is None else indices
        return [
            index for index in sorted(candidates) if self.is_strand_data_paste_target(index)
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
