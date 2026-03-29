from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                             QListWidgetItem, QLabel, QPushButton,
                             QDialogButtonBox, QWidget, QFrame, QScrollArea,
                             QSizePolicy, QGridLayout, QSpacerItem, QLayout)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont
from translations import translations
from shadow_editor_dialog import ShadowListItem, get_shadow_help_alignment, get_shadow_help_text


class GroupShadowEditorDialog(QDialog):
    """Dialog for editing shadows of all strands in a group, combined into one view."""

    def __init__(self, canvas, group_name, group_strands, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.group_name = group_name
        self.group_strands = group_strands
        self.all_shadow_items = []
        self.section_items = {}          # casting_layer -> [(ShadowListItem, recv_layer)]
        self.section_toggles = {}        # casting_layer -> {type: button}
        self.global_toggles = {}

        self.language_code = canvas.language_code if hasattr(canvas, 'language_code') else 'en'
        _ = translations[self.language_code]

        self.setWindowTitle(f"{_['group_shadow_editor_title']} - {group_name}")
        self.setModal(False)
        self.setMinimumSize(750, 450)
        self.resize(800, 600)

        main_window = parent
        while main_window and not hasattr(main_window, 'current_theme'):
            main_window = main_window.parent()
        self.main_window = main_window
        self.theme = main_window.current_theme if main_window and hasattr(main_window, 'current_theme') else 'light'

        self._apply_theme()

        if self.language_code == 'he':
            self.setLayoutDirection(Qt.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LeftToRight)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Info label
        self.info_label = QLabel(_['group_shadow_editor_info'].format(group_name))
        layout.addWidget(self.info_label)

        # Global toggle row
        self.global_toggle_row = self._create_global_toggle_row()
        layout.addWidget(self.global_toggle_row)

        # Scrollable area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._style_scroll_area()

        self.scroll_content = QWidget()
        self.scroll_content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(4, 4, 4, 4)
        self.scroll_layout.setSpacing(4)
        self.scroll_layout.setSizeConstraint(QLayout.SetMinAndMaxSize)

        self._populate_all_strands()

        self.scroll_layout.addStretch()
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)

        self.help_label = QLabel(get_shadow_help_text(self.language_code))
        self.help_label.setWordWrap(True)
        self.help_label.setTextFormat(Qt.RichText)
        self.help_label.setFont(self.info_label.font())
        self.help_label.setLayoutDirection(Qt.RightToLeft if self.language_code == 'he' else Qt.LeftToRight)
        self.help_label.setAlignment(get_shadow_help_alignment(self.language_code))
        self.help_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        layout.addWidget(self.help_label)

        # Sync widths and row heights after the scroll area has laid out its children.
        QTimer.singleShot(0, self._finalize_initial_layout)

        # Button box
        self.button_box = QDialogButtonBox(QDialogButtonBox.Close)
        self.button_box.rejected.connect(self.close)
        close_button = self.button_box.button(QDialogButtonBox.Close)
        if close_button:
            close_button.setText(_['close'])
        layout.addWidget(self.button_box)

        if hasattr(canvas, 'language_changed'):
            canvas.language_changed.connect(self.update_translations)

    # ── Column width sync ──────────────────────────────────────────────

    def _finalize_initial_layout(self):
        """Apply the initial column sizing and row heights once widgets are shown."""
        self._sync_column_widths()
        self._refresh_scroll_layout()

    def _sync_column_widths(self):
        """
        Keep names and controls aligned across the group editor while allowing
        long mask layer names and subtract-layer entries to remain fully visible.
        """
        toggle_rows = []
        if self.global_toggles:
            toggle_rows.append(self.global_toggles)
        toggle_rows.extend(self.section_toggles.values())

        if not self.all_shadow_items and not toggle_rows:
            return

        name_w = 0
        vis_w = 0
        full_w = 0
        sub_w = 0
        show_w = 0

        for item in self.all_shadow_items:
            name_w = max(name_w, item.name_label.sizeHint().width())
            vis_w = max(vis_w, item.visibility_checkbox.sizeHint().width())
            full_w = max(full_w, item.allow_full_shadow_checkbox.sizeHint().width())
            sub_w = max(sub_w, item.get_subtract_column_width())
            show_w = max(show_w, item.show_shadow_button.sizeHint().width())

        for toggles in toggle_rows:
            row_widget = toggles.get('_row_widget')
            if row_widget:
                name_label = row_widget.findChild(QLabel, 'toggle_name_label')
                if name_label:
                    name_w = max(name_w, name_label.sizeHint().width())
            vis_w = max(vis_w, toggles['visible'].sizeHint().width())
            full_w = max(full_w, toggles['full'].sizeHint().width())
            sub_w = max(sub_w, toggles['subtract'].sizeHint().width())
            show_w = max(show_w, toggles['shadow'].sizeHint().width())

        # Add a small buffer so exact glyph bounds do not clip on Windows/Qt.
        name_w += 12
        sub_w += 6

        for item in self.all_shadow_items:
            item.name_label.setFixedWidth(name_w)
            item.set_subtract_column_width(sub_w)

        def apply_to_toggles(toggles):
            row_widget = toggles.get('_row_widget')
            if row_widget:
                name_label = row_widget.findChild(QLabel, 'toggle_name_label')
                if name_label:
                    name_label.setFixedWidth(name_w)
            toggles['visible'].setFixedWidth(vis_w)
            toggles['full'].setFixedWidth(full_w)
            toggles['subtract'].setFixedWidth(sub_w)
            toggles['shadow'].setFixedWidth(show_w)

        for toggles in toggle_rows:
            apply_to_toggles(toggles)

    def _refresh_scroll_layout(self, ensure_widget_visible=None):
        """
        Recompute row heights so expanded subtract sections push the rows below
        downward and the scroll area updates its vertical scrollbar range.
        """
        self.scroll_layout.invalidate()

        for item in self.all_shadow_items:
            item.updateGeometry()
            item.adjustSize()
            target_height = max(48, item.sizeHint().height(), item.minimumSizeHint().height())
            item.setFixedHeight(target_height)

        self.scroll_layout.activate()
        self.scroll_content.adjustSize()
        self.scroll_content.updateGeometry()
        self.scroll_area.updateGeometry()
        self.scroll_area.viewport().update()

        if ensure_widget_visible is not None:
            QTimer.singleShot(
                0,
                lambda widget=ensure_widget_visible: self.scroll_area.ensureWidgetVisible(widget, 0, 24)
            )

    def _on_item_size_changed(self, widget):
        """Refresh the group layout when one row expands or collapses."""
        self._refresh_scroll_layout(ensure_widget_visible=widget)

    # ── Global toggle row ──────────────────────────────────────────────

    def _create_global_toggle_row(self):
        """Create the global toggle row matching ShadowListItem column layout."""
        _ = translations[self.language_code]
        return self._build_toggle_row(
            label_html=f"{self.group_name} - All",
            color=None,
            toggles_out=None,
            is_global=True
        )

    def _build_toggle_row(self, label_html, color, toggles_out, is_global=False, casting_layer=None):
        """
        Build a toggle row widget with the same HBoxLayout column structure
        as ShadowListItem: [color][name][visible][full][subtract][shadow_path]
        """
        _ = translations[self.language_code]

        row = QWidget()
        lay = QHBoxLayout(row)
        lay.setContentsMargins(3, 3, 3, 3)
        lay.setSpacing(1)

        if self.language_code == 'he':
            row.setLayoutDirection(Qt.RightToLeft)
        else:
            row.setLayoutDirection(Qt.LeftToRight)

        row.setMinimumHeight(42)
        row.setMinimumWidth(650)

        # Col 1: Color indicator (matches ShadowListItem.color_indicator 20x20)
        color_box = QLabel("  ")
        color_box.setFixedSize(20, 20)
        if color:
            color_box.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #888; border-radius: 3px;")
        else:
            color_box.setStyleSheet("background-color: transparent; border: none;")
        lay.addWidget(color_box)

        # Col 2: Name label (matches ShadowListItem.name_label)
        name_label = QLabel(label_html)
        name_label.setObjectName('toggle_name_label')
        name_label.setTextFormat(Qt.PlainText)
        name_label.setMinimumWidth(10)
        name_label.setWordWrap(False)
        name_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        name_label.setToolTip(label_html)
        font = name_label.font()
        font.setBold(True)
        name_label.setFont(font)
        if self.theme == 'dark':
            name_label.setStyleSheet("color: #DDD; background-color: transparent;")
        else:
            name_label.setStyleSheet("color: #333; background-color: transparent;")
        lay.addWidget(name_label)

        # Col 3: Visible toggle (matches visibility_checkbox position)
        vis_btn = self._create_toggle_button(_['shadow_visible_on'], _['shadow_visible_off'])
        vis_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        lay.addWidget(vis_btn)

        # Col 4: Full shadow toggle (matches allow_full_shadow_checkbox position)
        full_btn = self._create_toggle_button(_['shadow_full_on'], _['shadow_full_off'])
        full_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        lay.addWidget(full_btn)

        # Col 5: Subtract toggle (matches subtract_container position)
        sub_btn = self._create_toggle_button(_['shadow_subtract_on'], _['shadow_subtract_off'])
        sub_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        lay.addWidget(sub_btn, stretch=0)

        # Col 6: Shadow path toggle (matches show_shadow_button position)
        shd_btn = self._create_toggle_button(_['shadow_show_all'], _['shadow_hide_all'])
        shd_btn.setMinimumWidth(80)
        shd_btn.setMinimumHeight(36)
        shd_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        lay.addWidget(shd_btn, stretch=0)

        toggles = {
            'visible': vis_btn,
            'full': full_btn,
            'subtract': sub_btn,
            'shadow': shd_btn,
            '_row_widget': row,
        }

        if is_global:
            vis_btn.toggled.connect(self._toggle_all_visible)
            full_btn.toggled.connect(self._toggle_all_full_shadow)
            sub_btn.toggled.connect(self._toggle_all_subtract)
            shd_btn.toggled.connect(self._toggle_all_shadows)
            self.global_toggles = toggles
        else:
            vis_btn.toggled.connect(
                lambda chk, cl=casting_layer: self._toggle_section_visible(cl, chk))
            full_btn.toggled.connect(
                lambda chk, cl=casting_layer: self._toggle_section_full_shadow(cl, chk))
            sub_btn.toggled.connect(
                lambda chk, cl=casting_layer: self._toggle_section_subtract(cl, chk))
            shd_btn.toggled.connect(
                lambda chk, cl=casting_layer: self._toggle_section_shadows(cl, chk))
            self.section_toggles[casting_layer] = toggles

        # Row background
        if self.theme == 'dark':
            row.setStyleSheet(
                "QWidget { background-color: #353535; border-radius: 3px; }"
                "QLabel { background-color: transparent; border: none; }")
        else:
            row.setStyleSheet(
                "QWidget { background-color: #EAEAEA; border-radius: 3px; }"
                "QLabel { background-color: transparent; border: none; }")

        return row

    # ── Toggle button factory ──────────────────────────────────────────

    def _create_toggle_button(self, on_text, off_text):
        btn = QPushButton(on_text)
        btn.setCheckable(True)
        btn.setChecked(False)
        btn.setMinimumHeight(28)
        btn.setProperty('on_text', on_text)
        btn.setProperty('off_text', off_text)
        self._style_toggle_button(btn)
        btn.toggled.connect(lambda checked, b=btn: self._update_toggle_text(b, checked))
        return btn

    def _update_toggle_text(self, btn, checked):
        btn.setText(btn.property('off_text') if checked else btn.property('on_text'))

    def _style_toggle_button(self, btn):
        if self.theme == 'dark':
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #252525; color: white; border: 1px solid #555;
                    padding: 4px 10px; border-radius: 3px; min-width: 60px;
                    font-weight: bold; font-size: 9pt;
                }
                QPushButton:hover { background-color: #505050; }
                QPushButton:checked { background-color: #4A6FA5; border: 1px solid #6A9FD5; }
                QPushButton:checked:hover { background-color: #5A7FB5; }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #F0F0F0; color: black; border: 1px solid #BBB;
                    padding: 4px 10px; border-radius: 3px; min-width: 60px;
                    font-weight: bold; font-size: 9pt;
                }
                QPushButton:hover { background-color: #E0E0E0; }
                QPushButton:checked { background-color: #A0C0E0; border: 1px solid #7090C0; }
                QPushButton:checked:hover { background-color: #B0D0F0; }
            """)

    # ── Global toggle handlers ─────────────────────────────────────────

    def _toggle_all_shadows(self, checked):
        _ = translations[self.language_code]
        for casting_layer, items in self.section_items.items():
            for item_widget, recv_layer in items:
                item_widget.show_shadow_button.setChecked(checked)
                item_widget.show_shadow_button.setText(
                    _['shadow_path_hide'] if checked else _['shadow_path_button'])
                item_widget.is_shadow_visible = checked
                if checked:
                    if hasattr(self.canvas, 'add_visible_shadow_path'):
                        self.canvas.add_visible_shadow_path(casting_layer, recv_layer)
                else:
                    if hasattr(self.canvas, 'remove_visible_shadow_path'):
                        self.canvas.remove_visible_shadow_path(casting_layer, recv_layer)
        for cl in self.section_toggles:
            btn = self.section_toggles[cl]['shadow']
            btn.blockSignals(True)
            btn.setChecked(checked)
            self._update_toggle_text(btn, checked)
            btn.blockSignals(False)
        self.canvas.update()

    def _toggle_all_visible(self, checked):
        for items in self.section_items.values():
            for item_widget, _ in items:
                item_widget.visibility_checkbox.setChecked(checked)
        for cl in self.section_toggles:
            btn = self.section_toggles[cl]['visible']
            btn.blockSignals(True)
            btn.setChecked(checked)
            self._update_toggle_text(btn, checked)
            btn.blockSignals(False)

    def _toggle_all_full_shadow(self, checked):
        for items in self.section_items.values():
            for item_widget, _ in items:
                item_widget.allow_full_shadow_checkbox.setChecked(checked)
        for cl in self.section_toggles:
            btn = self.section_toggles[cl]['full']
            btn.blockSignals(True)
            btn.setChecked(checked)
            self._update_toggle_text(btn, checked)
            btn.blockSignals(False)

    def _toggle_all_subtract(self, checked):
        for items in self.section_items.values():
            for item_widget, _ in items:
                for cb in item_widget.subtract_checkboxes.values():
                    cb.setChecked(checked)
        for cl in self.section_toggles:
            btn = self.section_toggles[cl]['subtract']
            btn.blockSignals(True)
            btn.setChecked(checked)
            self._update_toggle_text(btn, checked)
            btn.blockSignals(False)

    # ── Per-section toggle handlers ────────────────────────────────────

    def _toggle_section_shadows(self, casting_layer, checked):
        _ = translations[self.language_code]
        if casting_layer not in self.section_items:
            return
        for item_widget, recv_layer in self.section_items[casting_layer]:
            item_widget.show_shadow_button.setChecked(checked)
            item_widget.show_shadow_button.setText(
                _['shadow_path_hide'] if checked else _['shadow_path_button'])
            item_widget.is_shadow_visible = checked
            if checked:
                if hasattr(self.canvas, 'add_visible_shadow_path'):
                    self.canvas.add_visible_shadow_path(casting_layer, recv_layer)
            else:
                if hasattr(self.canvas, 'remove_visible_shadow_path'):
                    self.canvas.remove_visible_shadow_path(casting_layer, recv_layer)
        self.canvas.update()

    def _toggle_section_visible(self, casting_layer, checked):
        if casting_layer not in self.section_items:
            return
        for item_widget, _ in self.section_items[casting_layer]:
            item_widget.visibility_checkbox.setChecked(checked)

    def _toggle_section_full_shadow(self, casting_layer, checked):
        if casting_layer not in self.section_items:
            return
        for item_widget, _ in self.section_items[casting_layer]:
            item_widget.allow_full_shadow_checkbox.setChecked(checked)

    def _toggle_section_subtract(self, casting_layer, checked):
        if casting_layer not in self.section_items:
            return
        for item_widget, _ in self.section_items[casting_layer]:
            for cb in item_widget.subtract_checkboxes.values():
                cb.setChecked(checked)

    # ── Scroll area styling ────────────────────────────────────────────

    def _style_scroll_area(self):
        if self.theme == 'dark':
            self.scroll_area.setStyleSheet("""
                QScrollArea { background-color: #3D3D3D; border: 1px solid #555; border-radius: 3px; }
                QScrollBar:vertical { background-color: #2C2C2C; width: 14px; border: none; }
                QScrollBar::handle:vertical { background-color: #666; min-height: 30px; border-radius: 4px; margin: 2px; }
                QScrollBar::handle:vertical:hover { background-color: #888; }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
                QScrollBar:horizontal { background-color: #2C2C2C; height: 14px; border: none; }
                QScrollBar::handle:horizontal { background-color: #666; min-width: 30px; border-radius: 4px; margin: 2px; }
                QScrollBar::handle:horizontal:hover { background-color: #888; }
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
            """)
        else:
            self.scroll_area.setStyleSheet("""
                QScrollArea { background-color: white; border: 1px solid #CCC; border-radius: 3px; }
                QScrollBar:vertical { background-color: #F0F0F0; width: 14px; border: none; }
                QScrollBar::handle:vertical { background-color: #BBB; min-height: 30px; border-radius: 4px; margin: 2px; }
                QScrollBar::handle:vertical:hover { background-color: #999; }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
                QScrollBar:horizontal { background-color: #F0F0F0; height: 14px; border: none; }
                QScrollBar::handle:horizontal { background-color: #BBB; min-width: 30px; border-radius: 4px; margin: 2px; }
                QScrollBar::handle:horizontal:hover { background-color: #999; }
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
            """)

    # ── Populate ───────────────────────────────────────────────────────

    def _populate_all_strands(self):
        if not hasattr(self.canvas, 'layer_state_manager'):
            return

        layer_order = self.canvas.layer_state_manager.getOrder()

        all_available_layers = []
        for layer_name in layer_order:
            strand = self._find_strand_by_name(layer_name)
            if strand and not getattr(strand, 'is_hidden', False):
                all_available_layers.append(layer_name)

        first_section = True
        for strand in self.group_strands:
            casting_layer = strand.layer_name

            try:
                casting_index = layer_order.index(casting_layer)
            except ValueError:
                continue

            layers_below = layer_order[:casting_index]

            receiving_layers = []
            for layer_name in layers_below:
                recv_strand = self._find_strand_by_name(layer_name)
                if recv_strand and not getattr(recv_strand, 'is_hidden', False):
                    receiving_layers.append((layer_name, recv_strand))

            if not receiving_layers:
                continue

            if not first_section:
                self._add_separator()
            first_section = False

            self.section_items[casting_layer] = []

            # Per-section toggle row (first row, column-aligned with items below)
            toggle_row = self._build_toggle_row(
                label_html=casting_layer,
                color=strand.color,
                toggles_out=None,
                is_global=False,
                casting_layer=casting_layer
            )
            self.scroll_layout.addWidget(toggle_row)

            # Shadow data rows
            for layer_name, recv_strand in receiving_layers:
                override = self.canvas.layer_state_manager.get_shadow_override(casting_layer, layer_name)
                is_visible = self.canvas.layer_state_manager.get_shadow_visibility(casting_layer, layer_name)
                allow_full_shadow = override.get('allow_full_shadow', False) if override else False
                subtracted_layers = self.canvas.layer_state_manager.get_subtracted_layers(casting_layer, layer_name)

                available_for_this_shadow = [l for l in all_available_layers if l != layer_name]

                item_widget = ShadowListItem(
                    layer_name, recv_strand.color.name(), is_visible, allow_full_shadow,
                    available_for_this_shadow, subtracted_layers, self.language_code
                )
                item_widget.set_theme(self.theme)

                item_widget.visibility_changed.connect(
                    lambda recv, vis, caster=casting_layer: self._on_visibility_changed(caster, recv, vis))
                item_widget.allow_full_shadow_changed.connect(
                    lambda recv, allow, caster=casting_layer: self._on_allow_full_shadow_changed(caster, recv, allow))
                item_widget.show_shadow_requested.connect(
                    lambda recv, enabled, caster=casting_layer: self._on_show_shadow_requested(caster, recv, enabled))
                item_widget.subtracted_layers_changed.connect(
                    lambda recv, layers, caster=casting_layer: self._on_subtracted_layers_changed(caster, recv, layers))
                item_widget.size_changed.connect(lambda w=item_widget: self._on_item_size_changed(w))

                self.all_shadow_items.append(item_widget)
                self.section_items[casting_layer].append((item_widget, layer_name))
                self.scroll_layout.addWidget(item_widget)

    def _add_separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setFixedHeight(2)
        if self.theme == 'dark':
            sep.setStyleSheet("QFrame { background-color: #666; color: #666; margin: 6px 0px; }")
        else:
            sep.setStyleSheet("QFrame { background-color: #BBB; color: #BBB; margin: 6px 0px; }")
        self.scroll_layout.addWidget(sep)

    # ── Data handlers ──────────────────────────────────────────────────

    def _find_strand_by_name(self, layer_name):
        for strand in self.canvas.strands:
            if strand.layer_name == layer_name:
                return strand
        return None

    def _on_visibility_changed(self, casting_layer, receiving_layer, is_visible):
        override = self.canvas.layer_state_manager.get_shadow_override(casting_layer, receiving_layer)
        if not override:
            override = {'visibility': is_visible}
        else:
            override['visibility'] = is_visible
        self.canvas.layer_state_manager.set_shadow_override(casting_layer, receiving_layer, override)
        self.canvas.update()

    def _on_allow_full_shadow_changed(self, casting_layer, receiving_layer, allow_full):
        override = self.canvas.layer_state_manager.get_shadow_override(casting_layer, receiving_layer)
        if not override:
            override = {
                'visibility': self.canvas.layer_state_manager.get_shadow_visibility(
                    casting_layer, receiving_layer),
                'allow_full_shadow': allow_full
            }
        else:
            override['allow_full_shadow'] = allow_full
        self.canvas.layer_state_manager.set_shadow_override(casting_layer, receiving_layer, override)
        self.canvas.update()

    def _on_subtracted_layers_changed(self, casting_layer, receiving_layer, subtracted_layers):
        self.canvas.layer_state_manager.set_subtracted_layers(
            casting_layer, receiving_layer, subtracted_layers)
        self.canvas.update()

    def _on_show_shadow_requested(self, casting_layer, receiving_layer, enabled):
        if enabled:
            if hasattr(self.canvas, 'add_visible_shadow_path'):
                self.canvas.add_visible_shadow_path(casting_layer, receiving_layer)
        else:
            if hasattr(self.canvas, 'remove_visible_shadow_path'):
                self.canvas.remove_visible_shadow_path(casting_layer, receiving_layer)

    # ── Theme ──────────────────────────────────────────────────────────

    def _apply_theme(self):
        if self.theme == 'dark':
            self.setStyleSheet("""
                QDialog { background-color: #2C2C2C; color: white; }
                QLabel { color: white; }
                QPushButton, QDialogButtonBox QPushButton {
                    background-color: #252525; color: white; font-weight: bold;
                    border: 2px solid #000000; padding: 10px; border-radius: 4px; min-width: 80px;
                }
                QPushButton:hover, QDialogButtonBox QPushButton:hover { background-color: #505050; }
                QPushButton:pressed, QDialogButtonBox QPushButton:pressed { background-color: #151515; }
            """)
        elif self.theme == 'light':
            self.setStyleSheet("""
                QDialog { background-color: #F5F5F5; color: black; }
                QLabel { color: black; }
                QPushButton, QDialogButtonBox QPushButton {
                    background-color: #F0F0F0; color: black; border: 1px solid #BBBBBB;
                    border-radius: 5px; padding: 10px; min-width: 80px; font-weight: bold;
                }
                QPushButton:hover, QDialogButtonBox QPushButton:hover { background-color: #E0E0E0; }
                QPushButton:pressed, QDialogButtonBox QPushButton:pressed { background-color: #D0D0D0; }
            """)

    # ── Translations ───────────────────────────────────────────────────

    def update_translations(self):
        self.language_code = self.canvas.language_code if hasattr(self.canvas, 'language_code') else 'en'
        _ = translations[self.language_code]

        if self.language_code == 'he':
            self.setLayoutDirection(Qt.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LeftToRight)

        self.setWindowTitle(f"{_['group_shadow_editor_title']} - {self.group_name}")
        self.info_label.setText(_['group_shadow_editor_info'].format(self.group_name))
        self.help_label.setText(get_shadow_help_text(self.language_code))
        self.help_label.setLayoutDirection(Qt.RightToLeft if self.language_code == 'he' else Qt.LeftToRight)
        self.help_label.setAlignment(get_shadow_help_alignment(self.language_code))

        for toggles in [self.global_toggles] + list(self.section_toggles.values()):
            self._update_toggle_labels(toggles['shadow'], _['shadow_show_all'], _['shadow_hide_all'])
            self._update_toggle_labels(toggles['visible'], _['shadow_visible_on'], _['shadow_visible_off'])
            self._update_toggle_labels(toggles['full'], _['shadow_full_on'], _['shadow_full_off'])
            self._update_toggle_labels(toggles['subtract'], _['shadow_subtract_on'], _['shadow_subtract_off'])

        close_button = self.button_box.button(QDialogButtonBox.Close)
        if close_button:
            close_button.setText(_['close'])

        for item in self.all_shadow_items:
            if isinstance(item, ShadowListItem):
                item.update_translations(self.language_code)

        # Re-sync widths and heights after translation change
        QTimer.singleShot(0, self._finalize_initial_layout)

    def _update_toggle_labels(self, btn, on_text, off_text):
        btn.setProperty('on_text', on_text)
        btn.setProperty('off_text', off_text)
        btn.setText(off_text if btn.isChecked() else on_text)

    # ── Close ──────────────────────────────────────────────────────────

    def closeEvent(self, event):
        if hasattr(self.canvas, 'clear_visible_shadow_paths'):
            self.canvas.clear_visible_shadow_paths()
        if hasattr(self.canvas, 'set_highlighted_shadow'):
            self.canvas.set_highlighted_shadow(None, None)
        self.canvas.update()

        if hasattr(self.canvas, 'undo_redo_manager') and self.canvas.undo_redo_manager:
            self.canvas.undo_redo_manager._last_save_time = 0
            self.canvas.undo_redo_manager.save_state()

        super().closeEvent(event)
