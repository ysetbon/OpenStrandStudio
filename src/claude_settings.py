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
    try:
        value = float(value)
    except (TypeError, ValueError):
        return DEFAULT_MAX_COST
    return min(max(value, MAX_COST_RANGE[0]), MAX_COST_RANGE[1])


def _money(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.0
    return value if value > 0 and value == value and value != float('inf') else 0.0


def load():
    """{'api_key', 'model', 'web', 'max_cost', 'spent', 'spent_since'}; empty key when none is saved.

    spent is what every request has cost in all, in USD, since spent_since
    (an ISO date, empty before the first request)."""
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
            'spent': _money(data.get('spent')), 'spent_since': str(data.get('spent_since') or '')}


def save(api_key=None, model=None, web=None, max_cost=None):
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
               'spent': current['spent'], 'spent_since': current['spent_since']}
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
