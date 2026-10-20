"""Drawing settings that travel with a project file.

The Settings dialog keeps its values in the global user_settings.txt, so a
project used to be redrawn with whatever settings happened to be active when it
was opened. The settings that change how the drawing itself looks (shadow,
curvature, extension lines, arrows and the defaults for new strands) are now
also written into the project JSON under PROJECT_SETTINGS_KEY and applied again
when that project is opened or its tab is shown.

App preferences (theme, language, sounds, highlights, snapping, warnings) stay
global: opening someone's file never switches your language.

The block is only added at the top level of a saved file. Undo/redo state files
never carry it, so undo does not touch the settings.
"""

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QSpinBox


PROJECT_SETTINGS_KEY = "project_settings"
PROJECT_SETTINGS_VERSION = 1

# Numbers and flags held on the canvas: settings key -> (canvas attribute,
# type, Settings dialog widget that shows it).
_CANVAS_VALUES = {
    "num_steps": ("num_steps", int, "num_steps_spinbox"),
    "max_blur_radius": ("max_blur_radius", float, "blur_radius_spinbox"),
    "control_point_base_fraction": ("control_point_base_fraction", float, "base_fraction_spinbox"),
    "distance_multiplier": ("distance_multiplier", float, "distance_mult_spinbox"),
    "curve_response_exponent": ("curve_response_exponent", float, "curve_response_spinbox"),
    "enable_third_control_point": ("enable_third_control_point", bool, "third_control_checkbox"),
    "enable_curvature_bias_control": ("enable_curvature_bias_control", bool, "curvature_bias_checkbox"),
    "extension_length": ("extension_length", float, "extension_length_spinbox"),
    "extension_dash_count": ("extension_dash_count", int, "extension_dash_count_spinbox"),
    "extension_dash_width": ("extension_dash_width", float, "extension_dash_width_spinbox"),
    "extension_dash_gap_length": ("extension_dash_gap_length", float, "extension_dash_gap_length_spinbox"),
    "arrow_head_length": ("arrow_head_length", float, "arrow_head_length_spinbox"),
    "arrow_head_width": ("arrow_head_width", float, "arrow_head_width_spinbox"),
    "arrow_head_stroke_width": ("arrow_head_stroke_width", int, "arrow_head_stroke_width_spinbox"),
    "arrow_gap_length": ("arrow_gap_length", float, "arrow_gap_length_spinbox"),
    "arrow_line_length": ("arrow_line_length", float, "arrow_line_length_spinbox"),
    "arrow_line_width": ("arrow_line_width", float, "arrow_line_width_spinbox"),
    "use_default_arrow_color": ("use_default_arrow_color", bool, "default_arrow_color_checkbox"),
    "default_strand_width": ("strand_width", int, None),
    "default_stroke_width": ("stroke_width", int, None),
}

# Colors held on the canvas: settings key -> (canvas attribute, dialog
# attribute, dialog method that repaints its swatch).
_CANVAS_COLORS = {
    "shadow_color": ("default_shadow_color", "shadow_color", "update_shadow_color_button"),
    "default_arrow_fill_color": ("default_arrow_fill_color", "default_arrow_fill_color", "update_default_arrow_color_button"),
    "default_strand_color": ("default_strand_color", "default_strand_color", "update_default_strand_color_button"),
    "default_stroke_color": ("default_stroke_color", "default_stroke_color", "update_default_stroke_color_button"),
}

# The Settings dialog attribute for each value it keeps a copy of. Its Apply
# button and user_settings.txt read these, so they must follow the canvas.
_DIALOG_ATTRIBUTES = {
    "num_steps": "num_steps",
    "max_blur_radius": "max_blur_radius",
    "enable_third_control_point": "enable_third_control_point",
    "enable_curvature_bias_control": "enable_curvature_bias_control",
    "extension_length": "extension_length",
    "extension_dash_count": "extension_dash_count",
    "extension_dash_width": "extension_dash_width",
    "extension_dash_gap_length": "extension_dash_gap_length",
    "arrow_head_length": "arrow_head_length",
    "arrow_head_width": "arrow_head_width",
    "arrow_head_stroke_width": "arrow_head_stroke_width",
    "arrow_gap_length": "arrow_gap_length",
    "arrow_line_length": "arrow_line_length",
    "arrow_line_width": "arrow_line_width",
    "use_default_arrow_color": "use_default_arrow_color",
    "default_strand_width": "default_strand_width",
    "default_stroke_width": "default_stroke_width",
}


def _color_to_json(color):
    color = QColor(color)
    return {"r": color.red(), "g": color.green(), "b": color.blue(), "a": color.alpha()}


def _color_from_json(value):
    if not isinstance(value, dict):
        return None
    try:
        color = QColor(int(value["r"]), int(value["g"]), int(value["b"]), int(value.get("a", 255)))
    except (KeyError, TypeError, ValueError):
        return None
    return color if color.isValid() else None


def _coerce(value, kind):
    if kind is bool:
        if isinstance(value, bool):
            return value
        raise ValueError("not a flag")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("not a number")
    return int(round(value)) if kind is int else float(value)


def capture_project_settings(canvas, settings_dialog=None):
    """The drawing settings in effect right now, as a JSON-ready dict."""
    settings = {"version": PROJECT_SETTINGS_VERSION}
    for key, (attribute, kind, _widget) in _CANVAS_VALUES.items():
        if hasattr(canvas, attribute):
            try:
                settings[key] = _coerce(getattr(canvas, attribute), kind)
            except ValueError:
                pass
    for key, (attribute, dialog_attribute, _repaint) in _CANVAS_COLORS.items():
        color = getattr(canvas, attribute, None)
        if color is None and settings_dialog is not None:
            color = getattr(settings_dialog, dialog_attribute, None)
        if color is not None:
            settings[key] = _color_to_json(color)
    if hasattr(canvas, 'default_level_color'):
        level_color = canvas.default_level_color
        # None means "follow the theme" and is saved as such.
        settings["default_level_color"] = _color_to_json(level_color) if level_color is not None else None
    if settings_dialog is not None and hasattr(settings_dialog, 'default_width_grid_units'):
        try:
            settings["default_width_grid_units"] = _coerce(settings_dialog.default_width_grid_units, int)
        except ValueError:
            pass
    return settings


def read_project_settings(data):
    """The settings block of a loaded project file, or None (older files)."""
    if not isinstance(data, dict):
        return None
    settings = data.get(PROJECT_SETTINGS_KEY)
    return settings if isinstance(settings, dict) else None


def apply_project_settings(canvas, settings, settings_dialog=None):
    """Make ``settings`` the active drawing settings.

    Updates the canvas, the strands already on it and the Settings dialog's
    copies and controls, so the dialog shows the project's values and its
    Apply button keeps them. Nothing is written to user_settings.txt. Keys that
    are missing or malformed keep their current value. Returns True when
    anything was applied.
    """
    if canvas is None or not isinstance(settings, dict):
        return False

    values = {}
    for key, (_attribute, kind, _widget) in _CANVAS_VALUES.items():
        if key in settings:
            try:
                values[key] = _coerce(settings[key], kind)
            except ValueError:
                pass
    colors = {}
    for key in _CANVAS_COLORS:
        color = _color_from_json(settings.get(key))
        if color is not None:
            colors[key] = color
    has_level_color = "default_level_color" in settings
    level_color = _color_from_json(settings.get("default_level_color")) if has_level_color else None
    if has_level_color and settings["default_level_color"] is not None and level_color is None:
        has_level_color = False  # malformed: keep the current one
    grid_units = None
    if "default_width_grid_units" in settings:
        try:
            grid_units = _coerce(settings["default_width_grid_units"], int)
        except ValueError:
            pass

    if not (values or colors or has_level_color or grid_units is not None):
        return False

    if settings_dialog is not None and getattr(settings_dialog, 'app_project_settings', None) is None:
        # Until now the app's own settings were in effect: keep them for new tabs.
        settings_dialog.app_project_settings = capture_project_settings(canvas, settings_dialog)

    for key, value in values.items():
        setattr(canvas, _CANVAS_VALUES[key][0], value)
    if not getattr(canvas, 'enable_third_control_point', True):
        # The dialog only allows curvature bias with a third control point.
        canvas.enable_curvature_bias_control = False
        values["enable_curvature_bias_control"] = False
    for key, color in colors.items():
        setattr(canvas, _CANVAS_COLORS[key][0], QColor(color))
    if has_level_color:
        canvas.default_level_color = QColor(level_color) if level_color is not None else None

    for strand in getattr(canvas, 'strands', []) or []:
        for key in ("control_point_base_fraction", "distance_multiplier", "curve_response_exponent"):
            if key in values:
                setattr(strand, key, values[key])
        if "shadow_color" in colors:
            strand.shadow_color = QColor(colors["shadow_color"])

    if settings_dialog is not None:
        _sync_settings_dialog(settings_dialog, values, colors,
                              has_level_color, level_color, grid_units)

    layer_panel = getattr(canvas, 'layer_panel', None)
    if has_level_color and layer_panel is not None and hasattr(layer_panel, 'restyle_level_rows'):
        layer_panel.restyle_level_rows()
    if hasattr(canvas, 'update'):
        canvas.update()
    return True


def _sync_settings_dialog(dialog, values, colors, has_level_color, level_color, grid_units):
    """Show the applied values in the dialog without running its change
    handlers: those would redraw and save to user_settings.txt on every value."""
    for key, value in values.items():
        dialog_attribute = _DIALOG_ATTRIBUTES.get(key)
        if dialog_attribute:
            setattr(dialog, dialog_attribute, value)
        widget = getattr(dialog, _CANVAS_VALUES[key][2] or '', None)
        if widget is None:
            continue
        widget.blockSignals(True)
        try:
            if hasattr(widget, 'setChecked'):
                widget.setChecked(bool(value))
            else:
                widget.setValue(int(value) if isinstance(widget, QSpinBox) else float(value))
        finally:
            widget.blockSignals(False)

    # Mirrors the third control point checkbox's own handler, blocked above.
    third = getattr(dialog, 'third_control_checkbox', None)
    bias = getattr(dialog, 'curvature_bias_checkbox', None)
    if third is not None and bias is not None:
        bias.setEnabled(third.isChecked())

    for key, color in colors.items():
        _attribute, dialog_attribute, repaint = _CANVAS_COLORS[key]
        setattr(dialog, dialog_attribute, QColor(color))
        if hasattr(dialog, repaint):
            try:
                getattr(dialog, repaint)()
            except Exception:
                pass

    if has_level_color:
        dialog.default_level_color = QColor(level_color) if level_color is not None else None
        if hasattr(dialog, 'default_level_color_button') and hasattr(dialog, 'update_default_level_color_button'):
            try:
                dialog.update_default_level_color_button()
            except Exception:
                pass

    if grid_units is not None:
        dialog.default_width_grid_units = grid_units
