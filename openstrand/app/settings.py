"""The person's Settings (the gear button's dialog): read them, change them with
the dialog's own code (its widgets and what its OK button runs), or open a page
for the person (src/claude_bridge/settings.py). Settings belong to the app, not
to a tab: changing one makes no undo step."""
from ..errors import ToolError
from .layers import color_value
from .tabs import read_into_workspace

PAGES = ('general', 'layer_panel', 'selected_strand', 'language', 'save_load', 'tutorial', 'button_guide',
         'levels_masks', 'history', 'whats_new', 'samples', 'models', 'about')
COLOR_KEYS = {'shadow_color', 'default_arrow_color', 'default_strand_color', 'default_stroke_color',
              'default_level_color', 'highlight_color'}

TOOLS = [
    {
        'name': 'read_settings',
        'description': ("The person's Settings (the gear button's dialog), page by page: each setting's key, "
                        'label, value and what it takes. Nothing changes.'),
        'input_schema': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'app_settings',
        'description': (
            "Change the person's Settings with the dialog's own code (as if they set them and pressed OK: the "
            'dialog then shows the new values), or open a page of Settings for them. Settings belong to the app, '
            'not to a tab: no undo step; the reply gives the old values, to set them back. In ask mode the person '
            'allows a change first. ops:\n'
            '- set: values {key: value} with keys from read_settings, e.g. {"theme": "dark"} (dark mode; "light", '
            '"default"), {"control_points_selected_only": true}, {"language": "fr"}. Colors: a name or "#rrggbb" '
            '("#rrggbbaa" with alpha).\n'
            '- show: page, one of ' + ', '.join(PAGES) + ': Settings opened there, for the person to see.'),
        'input_schema': {'type': 'object', 'properties': {
            'op': {'type': 'string', 'enum': ['set', 'show']},
            'values': {'type': 'object', 'description': '{key: value}, keys from read_settings'},
            'page': {'type': 'string', 'enum': list(PAGES)},
        }, 'required': ['op']},
    },
]
LOOK_ONLY = {'read_settings'}

INSTRUCTIONS = """- Settings (theme and dark mode, language, control points, snapping, shadows,
  highlights, arrows, default colors and widths) go through read_settings and
  app_settings; set what the person asks for on their app.
- When control points crowd (many strands' handles close together) and the
  person needs to see or move one strand's, set control_points_selected_only
  true and select that layer with app_window (or hide them all with app_window
  points false). Say what you toggled, so they can turn it back.
"""


def settings_text(rows):
    lines, page = [], None
    for row in rows:
        if row.get('page') != page:
            page = row.get('page')
            lines.append(f'[{page}]')
        lines.append(f"- {row['key']} = {row['value']!r} ({row['label']}; takes {row['takes']})")
    return '\n'.join(lines)


def app_value(key, value):
    """Claude's value with its colors made exact for the app."""
    if key not in COLOR_KEYS or value is None:
        return value
    try:
        return color_value(value)
    except ToolError as e:
        raise ToolError(f'{key}: {e}') from None


def read_settings(agent, args):
    result = agent.app.call('settings_read', {})
    rows = result.get('settings') or []
    return f'Settings · {len(rows)} settings', settings_text(rows)


def app_settings(agent, args):
    op = str(args.get('op', ''))
    if op == 'show':
        result = agent.app.call('settings_show', {'page': str(args.get('page') or 'general')})
        return f"Settings · {result.get('note', 'open')}", result.get('note') or 'open'
    if op != 'set':
        raise ToolError('op is "set" or "show"')
    values = args.get('values')
    if not isinstance(values, dict) or not values:
        raise ToolError('set: values {key: value}, keys from read_settings')
    values = {str(k): app_value(str(k), v) for k, v in values.items()}
    result = agent.app.call('settings', {'values': values})
    if 'new' not in result:  # ask mode: the person decides; nothing changed yet
        return 'Settings · waiting for the person', result.get('note') or 'shown to the person'
    lines = [f"{result.get('note', 'done')}.", f"Old values (to set them back): {result.get('old')}."]
    ws = agent.workspace
    tab = result.get('tab_id')
    if tab and ws.tab == tab and result.get('version') and result.get('version') != ws.tab_version:
        fresh, _ = read_into_workspace(agent, tab)  # the setting reshaped or recolored the strands
        lines.append(f"The setting changed the strands of the tab showing: read again (version {fresh.get('version')}).")
    return f"Settings · {result.get('note', 'done')[:70]}", '\n'.join(lines)


HANDLERS = {'read_settings': read_settings, 'app_settings': app_settings}
