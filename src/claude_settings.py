"""The model settings (Settings > Models): the user's API key for each provider
(Anthropic, OpenAI, xAI, Moonshot, DeepSeek, Alibaba Cloud), the model to use,
whether what Claude makes is shared with the developer, and what the requests
have cost in all on this computer.

Kept in claude.json in the OpenStrand Studio settings folder, on this computer
only, and never in project files or user_settings.txt. The API keys go in the
system's own password store when there is one (macOS Keychain, Windows
Credential Manager, the Secret Service on Linux, through the keyring package):
claude.json then only says which providers have a key there. Without one they
stay in claude.json, which is readable by the user alone on macOS and Linux.
"""
import datetime
import importlib.util
import json
import os
import sys
import tempfile


def _providers():
    """openstrand/providers.py, the one list of models and providers the agent uses too:
    the agent's own module when it runs here, else loaded on its own (not the openstrand
    package, which puts scripts/ on the path)."""
    if 'openstrand.providers' in sys.modules:
        return sys.modules['openstrand.providers']
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'openstrand', 'providers.py')
    spec = importlib.util.spec_from_file_location('openstrand_providers', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


try:
    providers = _providers()
except (OSError, ImportError, AttributeError):  # a build without the source folder: Claude only
    providers = None

if providers is not None:
    MODELS = [(m.id, m.label) for m in providers.MODELS.values()]  # (model id, its name)
    PROVIDERS = providers.PROVIDERS
else:
    MODELS = [('claude-sonnet-5-5', 'Claude Sonnet 5.5'), ('claude-haiku-5-5', 'Claude Haiku 5.5')]
    PROVIDERS = {}
DEFAULT_MODEL = MODELS[0][0]


def catalog():
    """What the last Refresh models found ({} before the first): see providers.use_catalog."""
    try:
        with open(settings_path(), 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    found = data.get('catalog') if isinstance(data, dict) else None
    return found if isinstance(found, dict) else {}


def models():
    """[(model id, name)] offered now: the built-in models, with what the last Refresh
    found (new ones added, ones a provider no longer offers hidden)."""
    if providers is None:
        return list(MODELS)
    providers.use_catalog(catalog())
    return [(m.id, m.label) for m in providers.MODELS.values()]


def model_info(model):
    """The model's entry (new, retiring, estimated price), or None."""
    return providers.MODELS.get(model) if providers is not None else None


def fetch_catalog():
    """Ask each provider with a saved key (or its environment variable) which models it
    offers now. Network only, nothing changes: call it off the main thread, then hand
    the answer to apply_catalog."""
    keys = dict(load()['keys'])
    for key, spec in PROVIDERS.items():
        if not keys.get(key):
            keys[key] = os.environ.get(spec.env, '').strip()
    return providers.refresh({k: v for k, v in keys.items() if v})


def refresh_due(hours=24):
    """Whether the automatic Refresh models should run: some provider has a key, and the
    last refresh (by hand or not) is older than hours, or there was none."""
    current = load()
    keyed = any(current['keys'].get(k) or os.environ.get(spec.env, '').strip() for k, spec in PROVIDERS.items())
    if not keyed or providers is None:
        return False
    stamp = (current.get('catalog') or {}).get('refreshed') or ''
    try:
        last = datetime.datetime.strptime(stamp, '%Y-%m-%d %H:%M')
    except ValueError:
        return True
    return datetime.datetime.now() - last >= datetime.timedelta(hours=hours)


def apply_catalog(found):
    """Keep what fetch_catalog found and offer it; move off the saved model if it is no
    longer offered. A provider that failed this time keeps what it said last time.
    Returns {'hidden': ids, 'new': ids, 'retiring': ids, 'switched': id or None}."""
    current = load()
    before = (current.get('catalog') or {}).get('providers') or {}
    found = dict(found, providers=dict(found.get('providers') or {}))
    for provider, answer in list(found['providers'].items()):
        if answer.get('error') and isinstance((before.get(provider) or {}).get('models'), list):
            found['providers'][provider] = dict(before[provider], error=answer['error'])
    hidden = providers.use_catalog(found)
    switched = None
    if current['model'] not in providers.MODELS:
        same = [m.id for m in providers.MODELS.values() if m.provider == provider_of_any(current['model'])]
        switched = (same or list(providers.MODELS) or [DEFAULT_MODEL])[0]
        current['model'] = switched
    current['catalog'] = found
    _write(current)
    offered = providers.MODELS.values()
    return {'hidden': hidden, 'new': [m.id for m in offered if m.new],
            'retiring': [m.id for m in offered if m.retiring], 'switched': switched}


def provider_of_any(model):
    """The provider of a model, offered now or built in."""
    if providers is not None:
        for table in (providers.MODELS, providers.BUILTIN):
            if model in table:
                return table[model].provider
    return 'anthropic'


def provider_of(model):
    """The provider key of a model ('anthropic' when unknown)."""
    if providers is not None and model in providers.MODELS:
        return providers.MODELS[model].provider
    return 'anthropic'
DEFAULT_MAX_COST = 2.00     # USD one request may spend before it stops
MAX_COST_RANGE = (0.10, 20.00)
DEFAULT_SESSION_LIMIT = 10.00  # USD all requests may spend before the app is restarted
SESSION_LIMIT_RANGE = (0.50, 500.00)
EFFORTS = ('low', 'medium', 'high', 'xhigh', 'max')  # how long Claude may think
DEFAULT_EFFORT = 'high'
MODES = ('ask', 'auto')  # ask before opening a design, or open it at once (plan mode is never kept)
DEFAULT_MODE = 'auto'
FILE_NAME = 'claude.json'
KEYCHAIN_SERVICE = 'OpenStrandStudio'  # the keys' entries in the password store: this, and the provider


# ------------------------------------------------------------ the password store
_found = []  # [the keyring backend to use, or None], once looked for
_cache = {}  # provider -> its key as read from (or written to) the store by this process


def keychain():
    """The system's password store, or None: keyring not installed, no secure store on this
    computer (keyring's 'fail' backend, or one that keeps its own files), or
    OPENSTRAND_KEYCHAIN=off (the tests, which must never touch the real one)."""
    if os.environ.get('OPENSTRAND_KEYCHAIN', '').strip().lower() in ('off', '0', 'no', 'false'):
        return None
    if not _found:
        _found.append(_find_keychain())
    return _found[0]


def _find_keychain():
    try:
        import keyring
        from keyring.backends import chainer, fail
        backend = keyring.get_keyring()
        first = backend
        if isinstance(backend, chainer.ChainerBackend):
            chained = list(backend.backends)
            first = chained[0] if chained else fail.Keyring()
        if isinstance(first, fail.Keyring) or float(getattr(first, 'priority', 0) or 0) < 1:
            return None
        if type(first).__module__.startswith('keyrings.alt'):  # plain files of its own: no better than ours
            return None
        return backend
    except Exception:  # noqa: BLE001 - no keyring, or a store that cannot be reached
        return None


def key_storage():
    """'keychain' when the keys go in the system's password store, else 'file'."""
    return 'keychain' if keychain() is not None else 'file'


def _stored_key(store, provider):
    if provider not in _cache:
        try:
            _cache[provider] = str(store.get_password(KEYCHAIN_SERVICE, provider) or '').strip()
        except Exception:  # noqa: BLE001 - locked, or access refused: as if there were none
            return ''
    return _cache[provider]


def _store_key(store, provider, key):
    """Put the key in the store (when it is not there already); False if that failed."""
    if _cache.get(provider) == key:
        return True
    try:
        store.set_password(KEYCHAIN_SERVICE, provider, key)
    except Exception:  # noqa: BLE001
        _cache.pop(provider, None)
        return False
    _cache[provider] = key
    return True


def _forget_key(store, provider):
    _cache.pop(provider, None)
    try:
        store.delete_password(KEYCHAIN_SERVICE, provider)
    except Exception:  # noqa: BLE001 - not there: nothing to remove
        pass


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


def _read():
    try:
        with open(settings_path(), 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def load():
    """{'api_key', 'keys', 'model', 'web', 'max_cost', 'spent', 'spent_since', 'show_button',
    'share', ...}; empty key when none is saved.

    spent is what every request has cost in all, in USD, since spent_since
    (an ISO date, empty before the first request). show_button is False when
    Settings > Claude hides Claude altogether. Claude itself always starts closed.
    share: whether what Claude makes goes to the developer (claude_sharing): None until
    the person is asked, then True or False. Keys saved in claude.json by an earlier
    version move to the password store here, once there is one."""
    data = _read()
    model = data.get('model')
    offered = [m for m, _ in models()]
    if model not in offered:
        model = DEFAULT_MODEL if DEFAULT_MODEL in offered else (offered or [DEFAULT_MODEL])[0]
    keys = {str(k): str(v).strip() for k, v in (data.get('api_keys') or {}).items()
            if isinstance(data.get('api_keys'), dict) and str(v or '').strip()}
    if str(data.get('api_key') or '').strip():
        keys['anthropic'] = str(data.get('api_key')).strip()
    in_file = bool(keys)
    stored = [str(p) for p in data.get('keychain') or [] if isinstance(data.get('keychain'), list)]
    store = keychain() if (stored or in_file) else None
    for provider in stored if store is not None else ():
        key = _stored_key(store, provider)
        if key:
            keys.setdefault(provider, key)
    current = {'api_key': keys.get('anthropic', ''), 'keys': keys, 'model': model,
               'catalog': data.get('catalog') if isinstance(data.get('catalog'), dict) else {},
               'web': data.get('web', True) is not False,
               'max_cost': _cost(data.get('max_cost', DEFAULT_MAX_COST)),
               'spent': _money(data.get('spent')), 'spent_since': str(data.get('spent_since') or ''),
               'show_button': data.get('show_button', True) is not False,
               'effort': data.get('effort') if data.get('effort') in EFFORTS else DEFAULT_EFFORT,
               'session_limit': _range(data.get('session_limit', DEFAULT_SESSION_LIMIT), SESSION_LIMIT_RANGE,
                                       DEFAULT_SESSION_LIMIT),
               'mode': data.get('mode') if data.get('mode') in MODES else DEFAULT_MODE,
               'share': data.get('share') if data.get('share') in (True, False) else None}
    if in_file and store is not None:
        _write(current)  # keys an earlier version kept in claude.json: into the store
    return current


def save(api_key=None, model=None, web=None, max_cost=None, show_button=None,
         effort=None, session_limit=None, mode=None, provider_key=None, share=None):
    """Update the saved settings given. api_key is Anthropic's; provider_key is
    (provider, key) for any provider. An empty key removes it. share: True or False."""
    current = load()
    if api_key is not None:
        provider_key = ('anthropic', api_key)
    if provider_key is not None:
        provider, key = provider_key
        key = (key or '').strip()
        if key:
            current['keys'][provider] = key
        else:
            current['keys'].pop(provider, None)
        current['api_key'] = current['keys'].get('anthropic', '')
    if model is not None:
        if model not in [m for m, _ in models()]:
            raise ValueError(f'unknown model {model}')
        current['model'] = model
    if web is not None:
        current['web'] = bool(web)
    if max_cost is not None:
        current['max_cost'] = _cost(max_cost)
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
    if share is not None:
        current['share'] = bool(share)
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
               'show_button': current['show_button'],
               'effort': current['effort'], 'session_limit': current['session_limit'], 'mode': current['mode']}
    if current.get('share') is not None:
        payload['share'] = bool(current['share'])
    if current.get('catalog'):
        payload['catalog'] = current['catalog']
    # Each key in the password store, else (none, or it refused this one) in the file.
    store = keychain()
    stored, plain = [], {}
    for provider, key in current['keys'].items():
        if key and store is not None and _store_key(store, provider, key):
            stored.append(provider)
        elif key:
            plain[provider] = key
    if store is not None:
        before = _read().get('keychain')
        for provider in before if isinstance(before, list) else []:
            if provider not in stored:
                _forget_key(store, str(provider))  # removed in Settings, or kept in the file now
    if stored:
        payload['keychain'] = sorted(stored)
    if plain.get('anthropic'):
        payload['api_key'] = plain['anthropic']
    others = {k: v for k, v in plain.items() if k != 'anthropic'}
    if others:
        payload['api_keys'] = others
    _write_private(path, payload)
    return current


def _write_private(path, payload):
    """Write the file whole or not at all (a crash halfway cannot lose the settings), and
    readable by its owner only (mkstemp makes it so, before anything is in it)."""
    fd, temp = tempfile.mkstemp(prefix='.claude-', suffix='.json', dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)
        try:
            os.replace(temp, path)
            return
        except PermissionError:  # Windows: another process has the file open this instant
            pass
    except BaseException:
        os.unlink(temp)
        raise
    os.unlink(temp)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)


def masked(key):
    """'sk-ant-…a1b2' for showing which key is saved without showing it."""
    key = key or ''
    return f'{key[:7]}…{key[-4:]}' if len(key) > 12 else ('•' * len(key))
