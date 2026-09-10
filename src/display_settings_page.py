"""
The "Display" page of the settings dialog.

Zoom the whole app like a browser (Ctrl + / Ctrl - / Ctrl 0), fine-tune one
kind of control on top of the zoom, choose the cursor size, and see a preview
made of real widgets.  Every change applies immediately.
"""

from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QCheckBox, QGroupBox, QFrame, QSizePolicy, QScrollArea, QMenu, QToolButton,
)

import ui_zoom
import display_settings

# English fallbacks for every string on the page.  translations.py carries the
# same keys; a language that lacks one falls back to these.
DEFAULTS = {
    'display': 'Display',
    'display_your_screen': 'Your screen',
    'display_platform': 'Platform',
    'display_resolution': 'Resolution',
    'display_os_scale': 'OS scale',
    'display_diagonal': 'Diagonal',
    'display_suggested_zoom': 'Suggested zoom',
    'display_detect_again': 'Detect again',
    'display_detect_hint': 'Read at every launch from the screen the window is on.',
    'display_zoom': 'Zoom',
    'display_fit_my_screen': 'Fit my screen',
    'display_zoom_shortcuts': 'Also Ctrl + / Ctrl − / Ctrl 0 anywhere in the app, and Ctrl + mouse wheel over the side panel.',
    'display_zoom_shortcuts_mac': 'Also Cmd + / Cmd − / Cmd 0 anywhere in the app, and Cmd + mouse wheel over the side panel.',
    'display_auto_zoom': 'Start at the suggested zoom for the screen the app opens on',
    'display_auto_zoom_hint': 'A laptop docked to a different monitor gets the right size without asking.',
    'display_zoom_is_suggested': 'This is the suggested zoom for your screen. Changes apply immediately.',
    'display_zoom_not_suggested': 'Suggested for this screen: {zoom} %. Changes apply immediately.',
    'display_preset_small': 'Small',
    'display_preset_default': 'Default',
    'display_preset_large': 'Large',
    'display_preset_larger': 'Larger',
    'display_preset_extra_large': 'Extra large',
    'display_fine_tune': 'Fine-tune one area',
    'display_fine_tune_hint': 'Each row is a percentage on top of the zoom. 100 % means "just follow the zoom". Use it when one thing is still too small, for example the right-click menus, without making everything else bigger.',
    'display_fine_tune_all_follow': 'All areas follow the zoom',
    'display_fine_tune_show': 'Show',
    'display_fine_tune_hide': 'Hide',
    'display_fine_tune_reset': 'Set every area back to 100 %',
    'display_cursor': 'Mouse cursor',
    'display_cursor_grow': 'Grow with zoom',
    'display_cursor_hint': 'The app draws its own arrow, cross and hand cursors, so their size does not depend on the operating system.',
    'display_preview': 'Preview',
    'display_preview_hint': 'Real controls at the current zoom. Right-click menu rows are {menu} px tall, layer buttons {lw} × {lh} px, toolbar buttons {tb} px.',
    'display_reset': 'Reset to detected',
    'display_saved_hint': 'Saved with the other settings.',
    'zoom_area_text': 'Text',
    'zoom_area_text_desc': 'Every label, button caption, menu entry, layer name and tab title.',
    'zoom_area_toolbar': 'Toolbar',
    'zoom_area_toolbar_desc': 'The mode buttons at the top, State, Tabs and the settings gear.',
    'zoom_area_icons': 'Side icon buttons',
    'zoom_area_icons_desc': 'The round buttons: home, undo, redo, zoom in and out, pan, refresh, centre, multi-select.',
    'zoom_area_layers': 'Layer buttons',
    'zoom_area_layers_desc': 'The coloured layer buttons in the list, their green strip, lock badge and copy chips.',
    'zoom_area_groups': 'Groups',
    'zoom_area_groups_desc': 'Create Group, the group column and rail, group buttons and the group dialogs.',
    'zoom_area_actions': 'Panel action buttons',
    'zoom_area_actions_desc': 'Draw Names, Lock Layers, New Strand, Delete Strand, Deselect All, Delete All.',
    'zoom_area_menus': 'Right-click menus',
    'zoom_area_menus_desc': 'Layer and group context menus, their submenus, the colour dialog and the arrow panel.',
    'zoom_area_dialogs': 'Dialogs and settings',
    'zoom_area_dialogs_desc': 'This dialog and every other dialog: spin boxes, combos, checkboxes, buttons.',
    'zoom_area_tabs': 'Tabs',
    'zoom_area_tabs_desc': 'The floating tab bar and its tabs.',
    'zoom_area_canvas': 'Canvas handles',
    'zoom_area_canvas_desc': 'Selection squares, control points and hit areas over the drawing. Strands, grid and canvas zoom are not touched.',
    'zoom_area_chrome': 'Tooltips, scrollbars, splitter',
    'zoom_area_chrome_desc': 'The small things around the edges.',
}

# The settings dialog's theme gives every QPushButton a 120 px minimum width
# and generous padding; the page's own small buttons opt out of that.
COMPACT_BUTTON_QSS = "QPushButton { min-width: 0px; padding: 2px 8px; }"
GROUP_QSS = ("QGroupBox { margin-top: 22px; padding-top: 8px; } "
             "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 0px; padding: 0px 2px; }")

PRESETS = [('display_preset_small', 75), ('display_preset_default', 100), ('display_preset_large', 125),
           ('display_preset_larger', 150), ('display_preset_extra_large', 200)]


def tr(language_code, key):
    try:
        from translations import translations
        table = translations.get(language_code) or {}
        if key in table:
            return table[key]
        en = translations.get('en') or {}
        if key in en:
            return en[key]
    except Exception:
        pass
    return DEFAULTS.get(key, key)


class _StepControl(QWidget):
    """[ − ] value [ + ]"""

    def __init__(self, on_step, parent=None, big=False):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.minus = QPushButton('−')
        self.plus = QPushButton('+')
        self.value = QLabel('')
        self.value.setAlignment(Qt.AlignCenter)
        for b in (self.minus, self.plus):
            b.setAutoRepeat(True)
            b.setAutoRepeatDelay(400)
            b.setAutoRepeatInterval(120)
            b.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            b.setStyleSheet(COMPACT_BUTTON_QSS)
        if big:
            self.minus.setFixedSize(40, 36)
            self.plus.setFixedSize(40, 36)
            self.value.setMinimumWidth(84)
            f = self.value.font()
            f.setBold(True)
            f.setPointSize(14)
            self.value.setFont(f)
        else:
            self.minus.setFixedSize(30, 28)
            self.plus.setFixedSize(30, 28)
            self.value.setMinimumWidth(64)
        lay.addWidget(self.minus)
        lay.addWidget(self.value)
        lay.addWidget(self.plus)
        self.minus.clicked.connect(lambda: on_step(-1))
        self.plus.clicked.connect(lambda: on_step(+1))

    def set_text(self, text):
        self.value.setText(text)


class DisplaySettingsPage(QWidget):
    """Widget placed in the settings dialog's stacked widget at index 1."""

    def __init__(self, dialog, parent=None):
        super().__init__(parent)
        self.dialog = dialog
        self.language_code = getattr(dialog, 'current_language', 'en')
        self._building = True
        self._info = getattr(ui_zoom.state, 'screen_info', None) or display_settings.detect()
        self._build()
        self._building = False
        ui_zoom.state.changed.connect(self._refresh)
        self._refresh()

    # ------------------------------------------------------------------ build
    def _t(self, key):
        return tr(self.language_code, key)

    def _group(self, title_key):
        box = QGroupBox(self._t(title_key))
        box.setObjectName('display_group_' + title_key)
        f = box.font()
        f.setBold(True)
        box.setFont(f)
        box.setStyleSheet(GROUP_QSS)
        return box

    def _hint(self, text):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setObjectName('display_hint')
        f = lbl.font()
        f.setBold(False)
        with ui_zoom.raw():   # relative to the (already zoomed) app font
            f.setPointSizeF(max(6.0, f.pointSizeF() * 0.9))
        lbl.setFont(f)
        return lbl

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        # The dialog widens itself to the widest page; a scroll area reports a
        # tiny hint, so ask for the width the rows need (zoomed by the setter).
        self.setMinimumWidth(800)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        body = QWidget()
        self.scroll.setWidget(body)
        outer.addWidget(self.scroll)
        lay = QVBoxLayout(body)
        lay.setSpacing(12)

        # --- Your screen -------------------------------------------------
        self.screen_box = self._group('display_your_screen')
        g = QGridLayout(self.screen_box)
        g.setHorizontalSpacing(18)
        self.info_labels = {}
        keys = ['display_platform', 'display_resolution', 'display_os_scale', 'display_diagonal', 'display_suggested_zoom']
        for col, key in enumerate(keys):
            k = QLabel(self._t(key))
            k.setObjectName('display_info_key')
            kf = k.font()
            kf.setBold(False)
            with ui_zoom.raw():
                kf.setPointSizeF(max(6.0, kf.pointSizeF() * 0.85))
            k.setFont(kf)
            v = QLabel('')
            vf = v.font()
            vf.setBold(True)
            v.setFont(vf)
            g.addWidget(k, 0, col)
            g.addWidget(v, 1, col)
            self.info_labels[key] = (k, v)
        row = QHBoxLayout()
        self.detect_button = QPushButton(self._t('display_detect_again'))
        self.detect_button.setStyleSheet(COMPACT_BUTTON_QSS)
        self.detect_button.clicked.connect(self.detect_again)
        row.addWidget(self.detect_button)
        self.detect_hint = self._hint(self._t('display_detect_hint'))
        row.addWidget(self.detect_hint, 1)
        g.addLayout(row, 2, 0, 1, len(keys))
        lay.addWidget(self.screen_box)

        # --- Zoom --------------------------------------------------------
        self.zoom_box = self._group('display_zoom')
        zl = QVBoxLayout(self.zoom_box)
        row = QHBoxLayout()
        self.zoom_ctl = _StepControl(self._step_zoom, big=True)
        row.addWidget(self.zoom_ctl)
        self.fit_button = QPushButton(self._t('display_fit_my_screen'))
        self.fit_button.setStyleSheet(COMPACT_BUTTON_QSS)
        self.fit_button.clicked.connect(self.fit_my_screen)
        row.addWidget(self.fit_button)
        self.hundred_button = QPushButton('100 %')
        self.hundred_button.setStyleSheet(COMPACT_BUTTON_QSS)
        self.hundred_button.clicked.connect(lambda: ui_zoom.set_zoom(100))
        row.addWidget(self.hundred_button)
        row.addStretch(1)
        zl.addLayout(row)
        presets = QGridLayout()
        presets.setHorizontalSpacing(6)
        presets.setVerticalSpacing(6)
        self.preset_buttons = []
        for i, (key, value) in enumerate(PRESETS):
            b = QPushButton(f"{self._t(key)} · {value} %")
            b.setCheckable(True)
            b.setProperty('displayPreset', True)
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            b.setStyleSheet(COMPACT_BUTTON_QSS)
            b.clicked.connect(lambda _c, v=value: ui_zoom.set_zoom(v))
            presets.addWidget(b, i // 3, i % 3)
            self.preset_buttons.append((b, value))
        zl.addLayout(presets)
        self.auto_check = QCheckBox(self._t('display_auto_zoom'))
        self.auto_check.setChecked(ui_zoom.state.auto)
        self.auto_check.toggled.connect(self._auto_toggled)
        zl.addWidget(self.auto_check)
        self.auto_hint = self._hint(self._t('display_auto_zoom_hint'))
        zl.addWidget(self.auto_hint)
        import sys
        self.shortcut_hint = self._hint(self._t('display_zoom_shortcuts_mac' if sys.platform.startswith('darwin') else 'display_zoom_shortcuts'))
        zl.addWidget(self.shortcut_hint)
        self.zoom_note = self._hint('')
        zl.addWidget(self.zoom_note)
        lay.addWidget(self.zoom_box)

        # --- Fine-tune (collapsed by default) ----------------------------
        self.fine_box = self._group('display_fine_tune')
        fl = QVBoxLayout(self.fine_box)
        head = QHBoxLayout()
        self.fine_toggle = QToolButton()
        self.fine_toggle.setCheckable(True)
        self.fine_toggle.setChecked(False)
        self.fine_toggle.setArrowType(Qt.RightArrow)
        self.fine_toggle.setText(self._t('display_fine_tune_show'))
        self.fine_toggle.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.fine_toggle.toggled.connect(self._toggle_fine)
        head.addWidget(self.fine_toggle)
        self.fine_summary = self._hint('')
        head.addWidget(self.fine_summary, 1)
        fl.addLayout(head)
        self.fine_body = QWidget()
        fb = QVBoxLayout(self.fine_body)
        fb.setContentsMargins(0, 0, 0, 0)
        fb.addWidget(self._hint(self._t('display_fine_tune_hint')))
        rows = QVBoxLayout()
        rows.setSpacing(4)
        self.area_controls = {}
        self.area_samples = {}
        for area in ui_zoom.AREAS:
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 6, 0, 6)
            rl.setSpacing(14)
            text_col = QVBoxLayout()
            text_col.setSpacing(2)
            name = QLabel(self._t('zoom_area_' + area))
            nf = name.font()
            nf.setBold(True)
            name.setFont(nf)
            desc = self._hint(self._t('zoom_area_' + area + '_desc'))
            text_col.addWidget(name)
            text_col.addWidget(desc)
            rl.addLayout(text_col, 1)
            sample = self._make_sample(area)
            if sample is not None:
                holder = QWidget()
                holder.setFixedWidth(150)
                hl = QHBoxLayout(holder)
                hl.setContentsMargins(0, 0, 0, 0)
                hl.addStretch(1)
                hl.addWidget(sample)
                hl.addStretch(1)
                rl.addWidget(holder, 0, Qt.AlignVCenter)
            ctl = _StepControl(lambda d, a=area: self._step_area(a, d))
            rl.addWidget(ctl, 0, Qt.AlignVCenter)
            rows.addWidget(row)
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setObjectName('display_rule')
            rows.addWidget(line)
            self.area_controls[area] = ctl
            self.area_samples[area] = sample
        fb.addLayout(rows)
        self.fine_reset = QPushButton(self._t('display_fine_tune_reset'))
        self.fine_reset.setStyleSheet(COMPACT_BUTTON_QSS)
        self.fine_reset.clicked.connect(lambda: ui_zoom.reset_fine_tune())
        fb.addWidget(self.fine_reset, 0, Qt.AlignLeft)
        self.fine_body.setVisible(False)
        fl.addWidget(self.fine_body)
        lay.addWidget(self.fine_box)

        # --- Mouse cursor ------------------------------------------------
        self.cursor_box = self._group('display_cursor')
        cl = QHBoxLayout(self.cursor_box)
        self.cursor_ctl = _StepControl(self._step_cursor)
        cl.addWidget(self.cursor_ctl)
        self.cursor_grow = QCheckBox(self._t('display_cursor_grow'))
        self.cursor_grow.setChecked(ui_zoom.state.cursor_follows_zoom)
        self.cursor_grow.toggled.connect(lambda on: ui_zoom.set_cursor(follows=on))
        cl.addWidget(self.cursor_grow)
        self.cursor_preview = QLabel()
        self.cursor_preview.setProperty('zoomRaw', True)
        cl.addWidget(self.cursor_preview)
        self.cursor_hint = self._hint(self._t('display_cursor_hint'))
        cl.addWidget(self.cursor_hint, 1)
        lay.addWidget(self.cursor_box)

        # --- Preview -----------------------------------------------------
        self.preview_box = self._group('display_preview')
        pl = QVBoxLayout(self.preview_box)
        self.preview_strip = QWidget()
        self.preview_strip.setObjectName('display_preview_strip')
        ps = QHBoxLayout(self.preview_strip)
        ps.setSpacing(14)
        self.preview_widgets = {}
        for area in ('toolbar', 'icons', 'layers', 'actions', 'menus'):
            w = self._make_sample(area, big=True)
            if w is not None:
                ps.addWidget(w, 0, Qt.AlignVCenter)
                self.preview_widgets[area] = w
        self.preview_cursor = QLabel()
        self.preview_cursor.setProperty('zoomRaw', True)
        ps.addWidget(self.preview_cursor, 0, Qt.AlignVCenter)
        ps.addStretch(1)
        pl.addWidget(self.preview_strip)
        self.preview_hint = self._hint('')
        pl.addWidget(self.preview_hint)
        lay.addWidget(self.preview_box)

        # --- Bottom row --------------------------------------------------
        bottom = QHBoxLayout()
        self.reset_button = QPushButton(self._t('display_reset'))
        self.reset_button.setStyleSheet(COMPACT_BUTTON_QSS)
        self.reset_button.clicked.connect(self.reset_to_detected)
        bottom.addWidget(self.reset_button)
        bottom.addStretch(1)
        self.saved_hint = self._hint(self._t('display_saved_hint'))
        bottom.addWidget(self.saved_hint)
        lay.addLayout(bottom)
        self.ok_button = QPushButton(self._t('ok'))
        self.ok_button.clicked.connect(self._ok)
        lay.addWidget(self.ok_button)
        lay.addStretch(1)

    # --------------------------------------------------------------- samples
    def _main_window(self):
        w = self.dialog
        while w is not None and type(w).__name__ != 'MainWindow':
            w = w.parent()
        return w

    def _copy_style(self, source_attr_chain, default=''):
        mw = self._main_window()
        obj = mw
        for attr in source_attr_chain:
            obj = getattr(obj, attr, None) if obj is not None else None
        if obj is None:
            return default
        try:
            return obj.styleSheet() or default
        except Exception:
            return default

    def _make_sample(self, area, big=False):
        """A real widget of that kind, tagged so the area multiplier reaches it."""
        w = None
        if area == 'text':
            w = QLabel('Select')
            f = w.font()
            f.setBold(True)
            w.setFont(f)
            w.setStyleSheet('font-size: 14px; font-weight: bold;')
        elif area == 'toolbar':
            w = QPushButton('Rotate')
            w.setFixedHeight(32)
            w.setMaximumWidth(90)
            w.setStyleSheet(self._copy_style(('rotate_button',),
                                             'QPushButton { background-color: #2E86D6; color: white; font-size: 14px; font-weight: bold; border-radius: 6px; padding: 0px 4px; }'))
        elif area == 'icons':
            w = QPushButton('🔍')
            w.setFixedSize(40, 40)
            w.setStyleSheet(self._copy_style(('layer_panel', 'zoom_in_button'),
                                             'QPushButton { background-color: #FFD400; border-radius: 20px; font-size: 20px; }'))
        elif area == 'layers':
            try:
                from numbered_layer_button import NumberedLayerButton
                from PyQt5.QtGui import QColor
                w = NumberedLayerButton('1_2', 0, QColor(107, 91, 123))
                w.setEnabled(False)
                w.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            except Exception:
                w = QPushButton('1_2')
                w.setFixedSize(146, 40)
        elif area == 'groups':
            w = QPushButton('Create Group')
            w.setFixedSize(140 if big else 100, 50 if big else 30)
            w.setStyleSheet(self._copy_style(('layer_panel', 'group_layer_manager', 'create_group_button'),
                                             'QPushButton { background-color: #8a8a8a; color: white; font-weight: bold; padding: 10px; }'))
        elif area == 'actions':
            w = QPushButton('New Strand')
            w.setStyleSheet(self._copy_style(('layer_panel', 'add_new_strand_button'),
                                             'QPushButton { background-color: #8FE88F; font-size: 14px; font-weight: bold; border: 1px solid #888; border-radius: 4px; padding: 5px 10px; }'))
        elif area == 'menus':
            w = QLabel()
            w.setProperty('zoomRaw', True)
            w.setObjectName('display_menu_sample_' + ('big' if big else 'small'))
        elif area == 'dialogs':
            w = QCheckBox('')
            w.setChecked(True)
            w.setEnabled(False)
        elif area == 'tabs':
            w = QPushButton('Tab')
            w.setFixedHeight(40)
            w.setStyleSheet('QPushButton { background: white; border: 1px solid #9a9a9a; border-bottom: 0; border-radius: 6px 6px 0 0; font-weight: bold; padding: 0 11px; }')
        elif area == 'canvas':
            w = QLabel()
            w.setFixedSize(24, 24)
            w.setStyleSheet('background: rgba(255, 220, 0, 140); border: 2px solid #c9a000;')
        elif area == 'chrome':
            w = QLabel()
            w.setFixedSize(12, 40)
            w.setStyleSheet('background: #c9c9c9; border-radius: 6px;')
        if w is not None:
            w.setProperty('zoomArea', area)
            w.setFocusPolicy(Qt.NoFocus)
        return w

    def _menu_pixmap(self, rows):
        """Render a real QMenu with the layer menu's stylesheet to a pixmap."""
        menu = QMenu(self)
        try:
            from numbered_layer_button import build_menu_stylesheet
            mw = self._main_window()
            theme = getattr(mw, 'current_theme', 'default') if mw else 'default'
            menu.setStyleSheet(build_menu_stylesheet(theme))
        except Exception:
            pass
        for text in rows:
            if text is None:
                menu.addSeparator()
            else:
                menu.addAction(text)
        menu.adjustSize()
        menu.setAttribute(Qt.WA_DontShowOnScreen, True)
        menu.show()
        pm = menu.grab()
        menu.hide()
        menu.deleteLater()
        return pm

    # -------------------------------------------------------------- actions
    def _step_zoom(self, direction):
        ui_zoom.step(direction)

    def _step_area(self, area, direction):
        ui_zoom.set_multiplier(area, ui_zoom.state.multipliers[area] + 10 * direction)

    def _step_cursor(self, direction):
        ui_zoom.set_cursor(size=ui_zoom.state.cursor_size + 8 * direction)

    def _auto_toggled(self, on):
        ui_zoom.state.auto = bool(on)
        ui_zoom.schedule_save()

    def _toggle_fine(self, on):
        self.fine_body.setVisible(on)
        self.fine_toggle.setArrowType(Qt.DownArrow if on else Qt.RightArrow)
        self.fine_toggle.setText(self._t('display_fine_tune_hide' if on else 'display_fine_tune_show'))

    def fit_my_screen(self):
        ui_zoom.set_zoom(ui_zoom.state.suggested)

    def detect_again(self):
        mw = self._main_window()
        screen = None
        try:
            screen = (mw or self).screen()
        except Exception:
            screen = None
        self._info = display_settings.detect(screen)
        ui_zoom.state.screen_info = self._info
        ui_zoom.state.suggested = display_settings.suggested_zoom(self._info)
        if ui_zoom.state.auto:
            ui_zoom.set_zoom(ui_zoom.state.suggested)
        self._refresh()
        ui_zoom.schedule_save()

    def reset_to_detected(self):
        ui_zoom.state.auto = True
        self.auto_check.setChecked(True)
        for a in ui_zoom.AREAS:
            ui_zoom.state.multipliers[a] = 100
        ui_zoom.state.cursor_size = 32
        ui_zoom.state.cursor_follows_zoom = True
        self.cursor_grow.setChecked(True)
        ui_zoom.state.zoom = ui_zoom.state.suggested
        ui_zoom.apply_all()

    def _ok(self):
        if hasattr(self.dialog, 'apply_all_settings'):
            self.dialog.apply_all_settings()

    # -------------------------------------------------------------- refresh
    def set_language(self, language_code):
        self.language_code = language_code
        self.screen_box.setTitle(self._t('display_your_screen'))
        self.zoom_box.setTitle(self._t('display_zoom'))
        self.fine_box.setTitle(self._t('display_fine_tune'))
        self.cursor_box.setTitle(self._t('display_cursor'))
        self.preview_box.setTitle(self._t('display_preview'))
        for key, (k, _v) in self.info_labels.items():
            k.setText(self._t(key))
        self.detect_button.setText(self._t('display_detect_again'))
        self.detect_hint.setText(self._t('display_detect_hint'))
        self.fit_button.setText(self._t('display_fit_my_screen'))
        for (b, value), (key, _v) in zip(self.preset_buttons, PRESETS):
            b.setText(f"{self._t(key)} · {value} %")
        self.auto_check.setText(self._t('display_auto_zoom'))
        self.auto_hint.setText(self._t('display_auto_zoom_hint'))
        self.fine_reset.setText(self._t('display_fine_tune_reset'))
        self.cursor_grow.setText(self._t('display_cursor_grow'))
        self.cursor_hint.setText(self._t('display_cursor_hint'))
        self.reset_button.setText(self._t('display_reset'))
        self.saved_hint.setText(self._t('display_saved_hint'))
        self.ok_button.setText(self._t('ok'))
        self._toggle_fine(self.fine_toggle.isChecked())
        self._refresh()

    def _refresh(self):
        if self._building:
            return
        st = ui_zoom.state
        info = self._info or {}
        # screen
        vals = {
            'display_platform': info.get('platform', ''),
            'display_resolution': f"{info.get('width', 0)} × {info.get('height', 0)} px",
            'display_os_scale': (f"Retina ×{info.get('device_pixel_ratio', 1):.2f}" if info.get('platform') == 'macOS'
                                 else f"{info.get('os_scale', 100)} %  ({int(round(info.get('logical_dpi', 96)))} dpi)"),
            'display_diagonal': (f"{info.get('diagonal_in', 0):.1f}″  ({int(round(info.get('ppi', 0)))} ppi)" if info.get('diagonal_in') else '—'),
            'display_suggested_zoom': f"{st.suggested} %",
        }
        for key, (_k, v) in self.info_labels.items():
            v.setText(vals.get(key, ''))
        # zoom
        self.zoom_ctl.set_text(f"{st.zoom} %")
        for b, value in self.preset_buttons:
            b.blockSignals(True)
            b.setChecked(value == st.zoom)
            b.blockSignals(False)
        self.auto_check.blockSignals(True)
        self.auto_check.setChecked(st.auto)
        self.auto_check.blockSignals(False)
        if st.zoom == st.suggested:
            self.zoom_note.setText(self._t('display_zoom_is_suggested'))
        else:
            self.zoom_note.setText(self._t('display_zoom_not_suggested').format(zoom=st.suggested))
        # fine-tune
        changed = [f"{self._t('zoom_area_' + a)} {st.multipliers[a]} %" for a in ui_zoom.AREAS if st.multipliers[a] != 100]
        self.fine_summary.setText(' · '.join(changed) if changed else self._t('display_fine_tune_all_follow'))
        for a, ctl in self.area_controls.items():
            ctl.set_text(f"{st.multipliers[a]} %")
        # cursor
        eff = ui_zoom.cursor_pixel_size()
        self.cursor_ctl.set_text(f"{st.cursor_size} px" + (f" → {eff}" if eff != st.cursor_size else ''))
        self.cursor_grow.blockSignals(True)
        self.cursor_grow.setChecked(st.cursor_follows_zoom)
        self.cursor_grow.blockSignals(False)
        pm = ui_zoom.cursor_preview_pixmap()
        self.cursor_preview.setPixmap(pm)
        self.preview_cursor.setPixmap(pm)
        # menus samples
        small = self.area_samples.get('menus')
        if small is not None:
            small.setPixmap(self._menu_pixmap(['Hide Layer']))
        big = self.preview_widgets.get('menus')
        if big is not None:
            big.setPixmap(self._menu_pixmap(['Hide Layer', 'Shadow Only', None, 'Change Color', 'Change Width']))
        # preview hint
        menu_row = ui_zoom.S(35, 'menus')
        self.preview_hint.setText(self._t('display_preview_hint').format(
            menu=menu_row, lw=ui_zoom.S(146, 'layers'), lh=ui_zoom.S(40, 'layers'), tb=ui_zoom.S(32, 'toolbar')))
