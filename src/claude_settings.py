"""The Claude settings: the user's Anthropic API key, the model to use, and
what Claude has cost in all on this computer.

Kept in claude.json in the OpenStrand Studio settings folder, on this computer
only, and never in project files or user_settings.txt. On macOS and Linux the
file is readable by the user alone.
"""
import datetime
import json
import os
import sys

MODELS = [
    # (model id, translation key of its label)
    ('claude-sonnet-5-5', 'claude_model_sonnet'),
    ('claude-haiku-5-5', 'claude_model_haiku'),
]
DEFAULT_MODEL = MODELS[0][0]
DEFAULT_MAX_COST = 2.00     # USD one request may spend before it stops
MAX_COST_RANGE = (0.10, 20.00)
DEFAULT_SESSION_LIMIT = 10.00  # USD all requests may spend before the app is restarted
SESSION_LIMIT_RANGE = (0.50, 500.00)
EFFORTS = ('low', 'medium', 'high', 'xhigh', 'max')  # how long Claude may think
DEFAULT_EFFORT = 'high'
MODES = ('ask', 'auto')  # ask before opening a design, or open it at once (plan mode is never kept)
DEFAULT_MODE = 'auto'
FILE_NAME = 'claude.json'


def settings_directory():
    """The OpenStrand Studio settings folder (as main.get_settings_directory)."""
    app_name = 'OpenStrandStudio'
    if sys.platform.startswith('darwin'):
        return os.path.join(os.path.expanduser('~/Library/Application Support'), app_name)
    appdata = os.environ.get('APPDATA', '')
    if appdata or sys.platform.startswith('win'):
        return os.path.join(appdata, app_name)
    return os.path.join(os.path.expanduser('~/.config'), app_name)


def settings_path():
    return os.path.join(settings_directory(), FILE_NAME)


def _cost(value):
    return _range(value, MAX_COST_RANGE, DEFAULT_MAX_COST)


def _range(value, limits, default):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default
    if value != value:  # NaN
        return default
    return min(max(value, limits[0]), limits[1])


def _money(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.0
    return value if value > 0 and value == value and value != float('inf') else 0.0


def load():
    """{'api_key', 'model', 'web', 'max_cost', 'spent', 'spent_since', 'panel_open', 'show_button'};
    empty key when none is saved.

    spent is what every request has cost in all, in USD, since spent_since
    (an ISO date, empty before the first request). panel_open is whether
    Claude was showing when the app last closed; show_button is False when
    Settings > Claude hides Claude altogether."""
    data = {}
    try:
        with open(settings_path(), 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    model = data.get('model')
    if model not in [m for m, _ in MODELS]:
        model = DEFAULT_MODEL
    return {'api_key': str(data.get('api_key') or '').strip(), 'model': model,
            'web': data.get('web', True) is not False,
            'max_cost': _cost(data.get('max_cost', DEFAULT_MAX_COST)),
            'spent': _money(data.get('spent')), 'spent_since': str(data.get('spent_since') or ''),
            'panel_open': data.get('panel_open') is True, 'show_button': data.get('show_button', True) is not False,
            'effort': data.get('effort') if data.get('effort') in EFFORTS else DEFAULT_EFFORT,
            'session_limit': _range(data.get('session_limit', DEFAULT_SESSION_LIMIT), SESSION_LIMIT_RANGE,
                                    DEFAULT_SESSION_LIMIT),
            'mode': data.get('mode') if data.get('mode') in MODES else DEFAULT_MODE}


def save(api_key=None, model=None, web=None, max_cost=None, panel_open=None, show_button=None,
         effort=None, session_limit=None, mode=None):
    """Update the saved settings given. An empty key removes the key."""
    current = load()
    if api_key is not None:
        current['api_key'] = api_key.strip()
    if model is not None:
        if model not in [m for m, _ in MODELS]:
            raise ValueError(f'unknown model {model}')
        current['model'] = model
    if web is not None:
        current['web'] = bool(web)
    if max_cost is not None:
        current['max_cost'] = _cost(max_cost)
    if panel_open is not None:
        current['panel_open'] = bool(panel_open)
    if show_button is not None:
        current['show_button'] = bool(show_button)
    if effort is not None:
        if effort not in EFFORTS:
            raise ValueError(f'unknown effort {effort}')
        current['effort'] = effort
    if session_limit is not None:
        current['session_limit'] = _range(session_limit, SESSION_LIMIT_RANGE, DEFAULT_SESSION_LIMIT)
    if mode is not None and mode in MODES:
        current['mode'] = mode
    return _write(current)


def add_spending(amount):
    """Add what one request cost to the running total; returns the new total."""
    current = load()
    amount = _money(amount)
    if amount:
        current['spent'] = round(current['spent'] + amount, 6)
        current['spent_since'] = current['spent_since'] or datetime.date.today().isoformat()
        _write(current)
    return current['spent']


def reset_spending():
    """Start the running total again from today."""
    current = load()
    current['spent'], current['spent_since'] = 0.0, datetime.date.today().isoformat()
    return _write(current)


def _write(current):
    path = settings_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {'model': current['model'], 'web': current['web'], 'max_cost': current['max_cost'],
               'spent': current['spent'], 'spent_since': current['spent_since'],
               'panel_open': current['panel_open'], 'show_button': current['show_button'],
               'effort': current['effort'], 'session_limit': current['session_limit'], 'mode': current['mode']}
    if current['api_key']:
        payload['api_key'] = current['api_key']
    # Create the file readable by its owner only before writing the key.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
    return current


def masked(key):
    """'sk-ant-…a1b2' for showing which key is saved without showing it."""
    key = key or ''
    return f'{key[:7]}…{key[-4:]}' if len(key) > 12 else ('•' * len(key))
