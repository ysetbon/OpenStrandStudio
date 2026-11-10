"""Settings: what the Settings dialog does, through its own widgets and the code
its OK button runs (SettingsDialog._perform_apply_settings), so the dialog shows
what the agent set and the person's next OK keeps it. Colors and the default strand
width go through the dialog's own choosers, their color (or width) dialog answered
unshown. Settings belong to the app, not to a tab: no undo step; the reply gives
the old values, to set them back.

settings_read   every setting: page, key, label, value, what it takes
settings        values {key: value, ...}
settings_show   page: Settings opened on that page, for the person
"""
from dataclasses import dataclass

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QColorDialog, QDialog

from .base import Action, BridgeError, patched
from .layers import qcolor

PAGES = ('general', 'layer_panel', 'selected_strand', 'language', 'save_load', 'tutorial', 'button_guide',
         'levels_masks', 'history', 'whats_new', 'samples', 'models', 'about')
PAGE_LABELS = ('General', 'Layer Panel', 'Selected Strand', 'Language', 'Save/Load', 'Tutorial', 'Button Guide',
               'Levels & Masks', 'History', "What's New", 'Samples', 'Models', 'About')


@dataclass(frozen=True)
class Setting:
    """One row of the Settings dialog.

    kind    check / spin / slider / combo (a widget of the dialog, applied by OK),
            color (the dialog's attribute and its chooser), level_color, width
    target  the widget's attribute, or (attribute, chooser) for a color
    """
    key: str
    page: str
    label: str
    kind: str
    target: object = None


SETTINGS = (
    Setting('theme', 'general', 'Theme', 'combo', 'theme_combobox'),
    Setting('shadow_color', 'general', 'Shadow color', 'color', ('shadow_color', 'choose_shadow_color')),
    Setting('draw_only_affected_strand', 'general', 'Draw only affected strand when dragging', 'check',
            'affected_strand_checkbox'),
    Setting('third_control_point', 'general', 'Enable third control point at center', 'check',
            'third_control_checkbox'),
    Setting('curvature_bias', 'general', 'Enable curvature bias controls (needs the third control point)', 'check',
            'curvature_bias_checkbox'),
    Setting('snap_to_grid', 'general', 'Snap to grid in move mode', 'check', 'snap_to_grid_checkbox'),
    Setting('snap_to_grid_attach', 'general', 'Snap to grid when attaching or drawing a strand', 'check',
            'snap_to_grid_attach_checkbox'),
    Setting('show_move_highlights', 'general', 'Show selection indicators in move/attach modes', 'check',
            'show_highlights_checkbox'),
    Setting('show_hover_highlights', 'general', 'Show hover highlights', 'check', 'show_hover_highlights_checkbox'),
    Setting('skip_close_tab_warning', 'general', "Don't ask to save when closing a tab", 'check',
            'skip_close_tab_warning_checkbox'),
    Setting('skip_quit_warning', 'general', "Don't ask to save when quitting", 'check', 'skip_quit_warning_checkbox'),
    Setting('shadow_blur_steps', 'general', 'Shadow blur steps', 'spin', 'num_steps_spinbox'),
    Setting('shadow_blur_radius', 'general', 'Shadow blur radius', 'spin', 'blur_radius_spinbox'),
    Setting('control_point_pull', 'general', 'Control point influence (pull strength)', 'spin',
            'base_fraction_spinbox'),
    Setting('distance_boost', 'general', 'Distance boost (magnifies curves)', 'spin', 'distance_mult_spinbox'),
    Setting('curve_shape', 'general', 'Curve shape (1 sharp, 3 smooth)', 'spin', 'curve_response_spinbox'),
    Setting('sounds', 'general', 'Play interface sounds', 'check', 'sound_enabled_checkbox'),
    Setting('sound_volume', 'general', 'Sound volume', 'slider', 'sound_volume_slider'),
    Setting('hover_sounds', 'general', 'Play hover sounds', 'check', 'sound_hover_checkbox'),
    Setting('extension_length', 'layer_panel', 'Extension length', 'spin', 'extension_length_spinbox'),
    Setting('extension_dash_count', 'layer_panel', 'Extension dash count', 'spin', 'extension_dash_count_spinbox'),
    Setting('extension_dash_width', 'layer_panel', 'Extension dash width', 'spin', 'extension_dash_width_spinbox'),
    Setting('extension_dash_gap', 'layer_panel', 'Gap between strand end and the dashes', 'spin',
            'extension_dash_gap_length_spinbox'),
    Setting('arrow_head_length', 'layer_panel', 'Arrow head length', 'spin', 'arrow_head_length_spinbox'),
    Setting('arrow_head_width', 'layer_panel', 'Arrow head width', 'spin', 'arrow_head_width_spinbox'),
    Setting('arrow_head_stroke_width', 'layer_panel', 'Arrow head stroke width', 'spin',
            'arrow_head_stroke_width_spinbox'),
    Setting('arrow_gap_length', 'layer_panel', 'Arrow gap length', 'spin', 'arrow_gap_length_spinbox'),
    Setting('arrow_line_length', 'layer_panel', 'Arrow line length', 'spin', 'arrow_line_length_spinbox'),
    Setting('arrow_line_width', 'layer_panel', 'Arrow line width', 'spin', 'arrow_line_width_spinbox'),
    Setting('use_default_arrow_color', 'layer_panel', 'Use the default arrow color (the stroke color)', 'check',
            'default_arrow_color_checkbox'),
    Setting('default_arrow_color', 'layer_panel', 'Arrow color when not the default', 'color',
            ('default_arrow_fill_color', 'choose_default_arrow_color')),
    Setting('default_strand_color', 'layer_panel', 'Default strand color (new sets)', 'color',
            ('default_strand_color', 'choose_default_strand_color')),
    Setting('default_stroke_color', 'layer_panel', 'Stroke color (also recolors every stroke now)', 'color',
            ('default_stroke_color', 'choose_default_stroke_color')),
    Setting('default_level_color', 'layer_panel', 'Default level color (null: the theme\'s)', 'level_color'),
    Setting('default_strand_width', 'layer_panel', 'Default strand width (new strands)', 'width'),
    Setting('view_hide_control_points', 'layer_panel', 'In view mode, hide the control points', 'check',
            'view_hide_control_points_checkbox'),
    Setting('unfolded_start_edge', 'layer_panel', 'Unfolded start edge by default', 'check',
            'default_transparent_start_circle_checkbox'),
    Setting('move_selected_only', 'selected_strand', 'In move mode, move only the selected strand', 'check',
            'move_selected_only_checkbox'),
    Setting('control_points_selected_only', 'selected_strand', 'Show control points only for the selected strand',
            'check', 'show_cp_selected_only_checkbox'),
    Setting('shadow_selected_only', 'selected_strand', 'Cast shadow only for the selected strand', 'check',
            'shadow_selected_only_checkbox'),
    Setting('view_hide_highlight', 'selected_strand', 'In view mode, hide the selection highlight', 'check',
            'view_hide_highlight_checkbox'),
    Setting('highlight_color', 'selected_strand', 'Selection highlight color', 'color',
            ('highlight_color', 'choose_highlight_color')),
    Setting('language', 'language', 'Language', 'combo', 'language_combobox'),
)
SPEC = {s.key: s for s in SETTINGS}
GRID_UNIT = 23  # px per grid square in the Default Strand Width dialog


def hex_color(color):
    if color is None or not QColor(color).isValid():
        return None
    color = QColor(color)
    text = color.name()
    return text if color.alpha() == 255 else f'{text}{color.alpha():02x}'


class SettingsActions:
    ACTIONS = {
        'settings_read': Action(run='settings_read'),
        'settings': Action(run='settings_set', change=True, check='check_settings', card='settings_card'),
        'settings_show': Action(run='settings_show', check='check_settings_show'),
    }

    # ---------------------------------------------------------- lookups
    @property
    def settings_dialog(self):
        dialog = getattr(self.window, 'settings_dialog', None)
        if dialog is None:
            raise BridgeError('this window has no Settings dialog')
        return dialog

    def widget(self, spec):
        return getattr(self.settings_dialog, spec.target)

    def setting_value(self, key):
        spec, dialog = SPEC[key], self.settings_dialog
        if spec.kind == 'check':
            return self.widget(spec).isChecked()
        if spec.kind in ('spin', 'slider'):
            return self.widget(spec).value()
        if spec.kind == 'combo':
            return self.widget(spec).currentData()
        if spec.kind == 'color':
            return hex_color(getattr(dialog, spec.target[0]))
        if spec.kind == 'level_color':
            return hex_color(dialog.default_level_color)
        color, stroke = dialog.default_strand_width, dialog.default_stroke_width
        total = color + 2 * stroke
        return {'squares': dialog.default_width_grid_units, 'color_percent': round(100 * color / total) if total else 50,
                'color_px': color, 'stroke_px': stroke}

    def takes(self, spec):
        """What a setting takes, as the agent reads it."""
        if spec.kind == 'check':
            return 'true/false'
        if spec.kind in ('spin', 'slider'):
            widget = self.widget(spec)
            whole = not hasattr(widget, 'decimals')
            low, high = widget.minimum(), widget.maximum()
            return f"{low:g}..{high:g}" + (' (whole)' if whole else '')
        if spec.kind == 'combo':
            widget = self.widget(spec)
            return ' / '.join(str(widget.itemData(i)) for i in range(widget.count()))
        if spec.kind == 'color':
            return '"#rrggbb" or "#rrggbbaa"'
        if spec.kind == 'level_color':
            return '"#rrggbb", or null for the theme\'s'
        return ('{"squares": total thickness in grid squares, even 2..20, "color_percent": 10..90 of it the color} '
                'as the dialog offers, or exact {"color_px", "stroke_px"} (stroke: each side)')

    def setting_input(self, key, value):
        """The agent's value made what the dialog takes, or a BridgeError saying what it takes."""
        spec = SPEC[key]
        wrong = BridgeError(f'{key}: {self.takes(spec)}')
        if spec.kind == 'check':
            if not isinstance(value, bool):
                raise wrong
            return value
        if spec.kind in ('spin', 'slider'):
            widget = self.widget(spec)
            whole = not hasattr(widget, 'decimals')
            if isinstance(value, bool) or not isinstance(value, (int, float)) or (whole and value != int(value)):
                raise wrong
            if not widget.minimum() <= value <= widget.maximum():
                raise wrong
            return int(value) if whole else float(value)
        if spec.kind == 'combo':
            widget = self.widget(spec)
            choices = [widget.itemData(i) for i in range(widget.count())]
            if value not in choices:
                raise wrong
            return value
        if spec.kind == 'color':
            return qcolor(value)
        if spec.kind == 'level_color':
            return None if value is None else qcolor(value)
        keys = {'squares', 'color_percent', 'color_px', 'stroke_px'}
        if not isinstance(value, dict) or not value or set(value) - keys:
            raise wrong
        whole = lambda v: isinstance(v, int) and not isinstance(v, bool)  # noqa: E731
        now = self.setting_value(key)
        if 'color_px' in value or 'stroke_px' in value:
            color, stroke = value.get('color_px', now['color_px']), value.get('stroke_px', now['stroke_px'])
            if not (whole(color) and whole(stroke) and color >= 1 and stroke >= 0 and color + 2 * stroke <= 20 * GRID_UNIT):
                raise wrong
            squares = value.get('squares')
            if squares is None:  # the dialog's own rounding: the nearest even count, 2..20
                squares = max(2, min(20, round((color + 2 * stroke) / GRID_UNIT)))
                squares += squares % 2
            if not (whole(squares) and squares % 2 == 0 and 2 <= squares <= 20):
                raise wrong
            return 'px', squares, color, stroke
        squares, percent = value.get('squares', now['squares']), value.get('color_percent', now['color_percent'])
        if not (whole(squares) and squares % 2 == 0 and 2 <= squares <= 20 and isinstance(percent, (int, float))
                and not isinstance(percent, bool) and 10 <= percent <= 90):
            raise wrong
        return 'share', squares, int(round(percent))

    def showing_session(self):
        try:
            return self.tabs.get_active()
        except BridgeError:
            return None

    # ------------------------------------------------------------ cards
    def settings_card(self, args, session):
        what = ', '.join(f'{k} {v}' for k, v in (args.get('values') or {}).items())
        return 'settings', '', what

    # ----------------------------------------------------------- checks
    def check_settings(self, args, session):
        values = args.get('values')
        if not isinstance(values, dict) or not values:
            raise BridgeError('values: {setting: value}, e.g. {"theme": "dark"}; read_settings lists them')
        unknown = [k for k in values if k not in SPEC]
        if unknown:
            raise BridgeError(f'no setting {", ".join(map(str, unknown))}: read_settings lists them')
        for key, value in values.items():
            self.setting_input(key, value)
        third = values.get('third_control_point', self.setting_value('third_control_point'))
        if values.get('curvature_bias') and not third:
            raise BridgeError('curvature_bias needs third_control_point on (the dialog greys it out otherwise)')

    def check_settings_show(self, args, session):
        page = args.get('page', 'general')
        if page not in PAGES:
            raise BridgeError(f'page is one of {", ".join(PAGES)}')

    # -------------------------------------------------------------- run
    def settings_read(self, args, session):
        rows = [{'key': s.key, 'page': s.page, 'label': s.label, 'value': self.setting_value(s.key),
                 'takes': self.takes(s)} for s in SETTINGS]
        return {'settings': rows, 'pages': list(PAGES)}

    def settings_set(self, args, session):
        dialog, values = self.settings_dialog, args['values']
        old = {key: self.setting_value(key) for key in values}
        dialog.sync_language_with_parent()  # as opening it does: its widgets show the app as it is
        widgets = False
        for spec in SETTINGS:  # the dialog's order: the third control point before the bias it enables
            if spec.key not in values:
                continue
            value = self.setting_input(spec.key, values[spec.key])
            if spec.kind == 'check':
                self.widget(spec).setChecked(value)
            elif spec.kind in ('spin', 'slider'):
                self.widget(spec).setValue(value)
            elif spec.kind == 'combo':
                widget = self.widget(spec)
                widget.setCurrentIndex(widget.findData(value))
            elif spec.kind == 'color':
                self.choose_color(getattr(dialog, spec.target[1]), value)
                continue
            elif spec.kind == 'level_color':
                dialog.set_default_level_color(value)  # the swatch's chooser, or its reset button for null
                continue
            else:
                self.choose_width(*value)
                continue
            widgets = True
        if widgets:
            dialog._perform_apply_settings()  # what OK runs: every widget applied, the settings file written
            if 'theme' in values and getattr(self.window, '_settings_dialog', None) is None:
                # The window hears the dialog's theme only once Settings has been opened.
                self.window.apply_theme(values['theme'])
        new = {key: self.setting_value(key) for key in values}
        changed = [f'{key} {new[key]}' for key in values if new[key] != old[key]]
        result = {'note': ('set ' + ', '.join(changed)) if changed else 'nothing to change: already so',
                  'old': old, 'new': new}
        session = self.showing_session()
        if session is not None:  # some settings reshape or recolor the strands
            result.update(tab_id=session.id, version=self.version(session))
        return result

    def choose_color(self, chooser, color):
        """The dialog's chooser, its color dialog answered with the color."""
        def answered(color_dialog):
            color_dialog.setCurrentColor(color)
            return QDialog.Accepted
        with patched(QColorDialog, 'exec_', answered):
            chooser()

    def choose_width(self, kind, squares, *amount):
        """Default Strand Width, its dialog answered: the thickness and the color share, as the
        dialog offers them, or (to set an old value back) the exact widths."""
        import settings_dialog as module

        def answered(width_dialog):
            width_dialog.thickness_spinbox.setValue(squares)
            if kind == 'share':
                width_dialog.color_slider.setValue(amount[0])
            return QDialog.Accepted
        with patched(module.DefaultWidthConfigDialog, 'exec_', answered):
            if kind == 'share':
                self.settings_dialog.open_default_width_dialog()
            else:
                with patched(module.DefaultWidthConfigDialog, 'get_values', lambda width_dialog: tuple(amount)):
                    self.settings_dialog.open_default_width_dialog()

    def settings_show(self, args, session):
        page = args.get('page', 'general')
        self.window.open_settings_dialog()
        self.settings_dialog.categories_list.setCurrentRow(PAGES.index(page))
        return {'note': f'Settings is open on {PAGE_LABELS[PAGES.index(page)]}'}
