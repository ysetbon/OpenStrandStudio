"""The language models the agent can run on, by provider, and a client for each.

Every client answers like the anthropic SDK (client.messages.create(...) gives a
message with content blocks, stop_reason and usage), so the agent's loop is the
same for every model:

- Anthropic (Claude): the Messages API, the anthropic SDK itself.
- Moonshot (Kimi), DeepSeek and Alibaba Cloud (Qwen): their Anthropic-compatible
  endpoints, the ones they run for Claude Code: the same SDK with their base URL;
  CompatClient leaves out what only Anthropic has (effort, adaptive thinking,
  Anthropic's server-side web tools).
- OpenAI (GPT) and xAI (Grok): the OpenAI Responses API (GPT-6 models call tools
  only there), through ResponsesClient, which speaks it over plain HTTPS (Python's
  urllib) and turns its answer into the same shape.

Model ids, endpoints and prices are as the providers published them in November
2026; PRICES are USD per million tokens: input, output, cache write, cache read.

A key only ever goes to its own provider (see "Safe requests" below): every
request is checked on its way out (HTTPS, to the host its endpoint names here),
no redirect is followed, and environment variables can neither move a client
(ANTHROPIC_BASE_URL) nor add another credential to its requests.
"""
import json
import os
import re
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field, replace
from types import SimpleNamespace
from urllib.parse import quote, urlsplit


@dataclass(frozen=True)
class Provider:
    key: str          # 'anthropic', 'openai', ...
    name: str         # shown in Settings > Models
    api: str          # 'anthropic', 'anthropic-compatible' or 'responses'
    env: str          # the environment variable that holds its API key
    base_url: str = None
    keys_url: str = ''  # where to make a key
    key_hint: str = ''  # what a key looks like (the key field's placeholder)
    models_url: str = ''  # where it lists the models a key can use (Refresh models)


@dataclass(frozen=True)
class Model:
    id: str
    label: str
    provider: str
    prices: tuple                     # input, output, cache write, cache read (USD per million tokens)
    vision: bool = True               # reads images (the reference image, render's picture)
    aliases: tuple = field(default=())
    new: bool = False                 # found by Refresh models, not in the built-in list
    retiring: str = ''                # the date (or 'soon') its provider stops it, when announced
    estimated: bool = False           # its price is an estimate (the provider does not publish it)


PROVIDERS = {p.key: p for p in (
    Provider('anthropic', 'Anthropic (Claude)', 'anthropic', 'ANTHROPIC_API_KEY', 'https://api.anthropic.com',
             keys_url='https://console.anthropic.com/settings/keys', key_hint='sk-ant-…',
             models_url='https://api.anthropic.com/v1/models'),
    Provider('openai', 'OpenAI (GPT)', 'responses', 'OPENAI_API_KEY', 'https://api.openai.com/v1',
             'https://platform.openai.com/api-keys', 'sk-…', 'https://api.openai.com/v1/models'),
    Provider('xai', 'xAI (Grok)', 'responses', 'XAI_API_KEY', 'https://api.x.ai/v1',
             'https://console.x.ai', 'xai-…', 'https://api.x.ai/v1/language-models'),
    Provider('moonshot', 'Moonshot AI (Kimi)', 'anthropic-compatible', 'MOONSHOT_API_KEY',
             'https://api.moonshot.ai/anthropic', 'https://platform.kimi.ai/console/api-keys', 'sk-…',
             'https://api.moonshot.ai/v1/models'),
    Provider('deepseek', 'DeepSeek', 'anthropic-compatible', 'DEEPSEEK_API_KEY',
             'https://api.deepseek.com/anthropic', 'https://platform.deepseek.com/api_keys', 'sk-…',
             'https://api.deepseek.com/models'),
    # Its model list is not in Alibaba's docs: Refresh tries the OpenAI-compatible one.
    Provider('qwen', 'Alibaba Cloud (Qwen)', 'anthropic-compatible', 'DASHSCOPE_API_KEY',
             'https://dashscope-intl.aliyuncs.com/apps/anthropic',
             'https://modelstudio.console.alibabacloud.com/?tab=playground#/api-key', 'sk-…',
             'https://dashscope-intl.aliyuncs.com/compatible-mode/v1/models'),
)}

BUILTIN = {m.id: m for m in (
    Model('claude-sonnet-5-5', 'Claude Sonnet 5.5', 'anthropic', (2.00, 10.00, 2.50, 0.20), aliases=('sonnet',)),
    Model('claude-haiku-5-5', 'Claude Haiku 5.5', 'anthropic', (0.10, 0.50, 0.125, 0.01), aliases=('haiku',)),
    Model('gpt-6.1-terra', 'GPT-6.1 Terra', 'openai', (1.00, 5.00, 1.00, 0.05), aliases=('gpt', 'terra')),
    Model('gpt-6.1-sol', 'GPT-6.1 Sol', 'openai', (2.00, 10.00, 2.00, 0.10), aliases=('sol',)),
    Model('gpt-6-astra', 'GPT-6 Astra', 'openai', (10.00, 50.00, 10.00, 1.00), aliases=('astra',)),
    Model('grok-4.7', 'Grok 4.7', 'xai', (2.00, 6.00, 2.00, 0.50), aliases=('grok',)),
    Model('kimi-k3.1-pro', 'Kimi K3.1 Pro', 'moonshot', (2.00, 10.00, 2.00, 0.20), aliases=('kimi',)),
    # DeepSeek's peak-hour price (off-peak is half): a limit never runs over.
    Model('deepseek-flash', 'DeepSeek V4.1 Flash', 'deepseek', (0.30, 1.20, 0.30, 0.006),
          aliases=('deepseek', 'deepseek-v4-flash')),
    # Its cache price is not published for this endpoint: counted at the input price.
    Model('qwen3.8-max', 'Qwen3.8 Max', 'qwen', (2.00, 6.00, 2.00, 2.00), aliases=('qwen',)),
)}
# The models offered: the built-in ones, and what Refresh models found (use_catalog
# changes these in place, so the agent's PRICES follows).
MODELS = dict(BUILTIN)
DEFAULT_MODEL = 'claude-sonnet-5-5'
PRICES = {m.id: m.prices for m in MODELS.values()}
ALIASES = {alias: m.id for m in MODELS.values() for alias in m.aliases}

# Thinking budget on the Anthropic-compatible endpoints, by the person's effort.
BUDGETS = {'low': 4000, 'medium': 8000, 'high': 12000, 'xhigh': 16000, 'max': 16000}
# Reasoning effort on the Responses API (it has no 'max').
REASONING = {'low': 'low', 'medium': 'medium', 'high': 'high', 'xhigh': 'xhigh', 'max': 'xhigh'}


def resolve(name):
    """A model id from an id or an alias ('sonnet', 'grok', 'kimi', ...)."""
    name = str(name or '').strip()
    model = ALIASES.get(name.lower(), name)
    if model not in MODELS:
        known = ', '.join(sorted(set(MODELS) | set(ALIASES)))
        raise ValueError(f'unknown model {name}: use one of {known}')
    return model


def provider_of(model):
    return PROVIDERS[MODELS[resolve(model)].provider]


def api_key(provider, saved=None):
    """The provider's key: its environment variable, else the one saved in the app's
    settings (saved: {provider: key}), else an error that says where to add it."""
    p = PROVIDERS[provider]
    key = os.environ.get(p.env, '').strip() or str((saved or {}).get(provider) or '').strip()
    if not key:
        raise ValueError(f'no {p.name} API key: set {p.env}, or add it in OpenStrand Studio under '
                         f'Settings > Models')
    return key


def client_for(model, key):
    """A client for the model's provider, answering like anthropic.Anthropic()."""
    p = provider_of(model)
    stand_in = os.environ.get(TEST_API, '').strip()
    if stand_in:  # the tests' local stand-in for the provider's API, never another computer
        if host_of(stand_in) not in LOOPBACK:
            raise UnsafeRequest(f'{TEST_API} must be on this computer (127.0.0.1 or localhost), '
                                f'not {host_of(stand_in) or stand_in}')
        p = replace(p, base_url=stand_in.rstrip('/'))
    if p.api == 'responses':
        return ResponsesClient(p, key)
    import anthropic
    if p.api == 'anthropic':
        return sdk_client(anthropic, p.base_url, key)
    return CompatClient(compatible_sdk(anthropic, key, p.base_url))


def compatible_sdk(anthropic, key, base_url):
    """The anthropic SDK on a compatible endpoint. Their docs for Claude Code give the key
    as a Bearer token (ANTHROPIC_AUTH_TOKEN); some read x-api-key: send it both ways."""
    return sdk_client(anthropic, base_url, key, bearer=True)


class ProviderError(Exception):
    """An error a provider's API returned: status_code and its message."""

    def __init__(self, provider, status_code, message):
        super().__init__(f'{provider} API returned {status_code}: {message}')
        self.provider, self.status_code, self.message = provider, status_code, message


# --------------------------------------------------------------- safe requests
# The endpoints above are the only places a key goes. Each request is checked as it
# leaves: HTTPS to the host its endpoint names (plain HTTP only to this computer itself,
# where the tests stand in for the APIs), with the certificate and its host name
# verified. A redirect is never followed, since following one could carry the key to
# another host. What the environment says cannot change this: the SDK would otherwise
# take its endpoint from ANTHROPIC_BASE_URL (set for Claude Code by people who use
# DeepSeek's or Kimi's endpoint, it would send the Claude key and the whole request
# there), and credentials from ANTHROPIC_AUTH_TOKEN or ANTHROPIC_CUSTOM_HEADERS.
LOOPBACK = ('127.0.0.1', 'localhost', '::1')
CREDENTIAL_HEADERS = ('authorization', 'x-api-key')
# For the tests only: the URL of a stand-in for every provider's API, which must be on this
# computer itself (so, unlike ANTHROPIC_BASE_URL, it can never take a key anywhere else).
TEST_API = 'OPENSTRAND_TEST_API'


class UnsafeRequest(ValueError):
    """A request that would have taken a key where it does not belong. It was not sent."""


def host_of(url):
    return (urlsplit(str(url)).hostname or '').lower()


def check_url(url, host):
    """Raise UnsafeRequest unless url is on host, over HTTPS (HTTP only to this computer)."""
    parts = urlsplit(str(url))
    name = (parts.hostname or '').lower()
    if name != host or not (parts.scheme == 'https' or (parts.scheme == 'http' and name in LOOPBACK)):
        raise UnsafeRequest(f'refused to send a request to {parts.scheme}://{name}: '
                            f'the key for {host} goes to https://{host} only')


def sdk_client(anthropic, base_url, key, bearer=False):
    """anthropic.Anthropic held to one endpoint: base_url and key are given here, so the
    SDK reads neither from the environment; it follows no redirect, and each request is
    checked on its way out: its host, and its credentials, which are this key exactly as
    the SDK sends it (whatever else an environment variable put there is replaced)."""
    host = host_of(base_url)
    wanted = {}  # header name (lowercase) -> its one value; filled once the client exists

    def guard(request):
        check_url(request.url, host)
        for name in CREDENTIAL_HEADERS:
            mine = [wanted[name]] if name in wanted else []
            if request.headers.get_list(name) != mine:
                if name in request.headers:
                    del request.headers[name]
                for value in mine:
                    request.headers[name] = value

    http = anthropic.DefaultHttpxClient(follow_redirects=False, event_hooks={'request': [guard]})
    if bearer:
        client = anthropic.Anthropic(auth_token=key, base_url=base_url, http_client=http,
                                     default_headers={'x-api-key': key})
    else:
        client = anthropic.Anthropic(api_key=key, base_url=base_url, http_client=http)
    wanted.update({name.lower(): value for name, value in (client.auth_headers or {'x-api-key': key}).items()})
    if bearer:
        wanted['x-api-key'] = key
    return client


class _NoRedirects(urllib.request.HTTPRedirectHandler):
    """A redirect ends the request: its 3xx comes back as the answer (an HTTPError)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def tls_context():
    """The certificate and its host name checked, TLS 1.2 or newer."""
    context = ssl.create_default_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context


def open_url(request, host, timeout):
    """urllib's urlopen for a request that carries a key for host: checked, never redirected."""
    check_url(request.full_url, host)
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=tls_context()), _NoRedirects)
    return opener.open(request, timeout=timeout)


# ------------------------------------------------- Anthropic-compatible endpoints
def _compatible(params):
    """The request as the compatible endpoints take it: no effort setting or adaptive
    thinking (thinking with a budget instead), no Anthropic server tools."""
    params = dict(params)
    effort = (params.pop('output_config', None) or {}).get('effort', 'high')
    if params.get('thinking'):
        budget = BUDGETS.get(effort, 12000)
        params['thinking'] = {'type': 'enabled', 'budget_tokens': min(budget, int(params.get('max_tokens', 20000)) - 1000)}
    params['tools'] = [t for t in params.get('tools') or [] if 'input_schema' in t]
    if not params['tools']:
        params.pop('tools')
    for key in ('betas', 'fallbacks'):
        params.pop(key, None)
    return params


class CompatClient:
    """anthropic.Anthropic on a provider's Anthropic-compatible endpoint."""

    def __init__(self, client):
        self._client = client
        self.messages = SimpleNamespace(create=lambda **params: client.messages.create(**_compatible(params)))
        self.beta = SimpleNamespace(messages=self.messages)


# ------------------------------------------------------------ the Responses API
def _image_part(block):
    source = block.get('source') or {}
    if source.get('type') == 'base64':
        url = f"data:{source.get('media_type', 'image/png')};base64,{source.get('data', '')}"
    else:
        url = source.get('url', '')
    return {'type': 'input_image', 'image_url': url}


def _get(block, name, default=None):
    return block.get(name, default) if isinstance(block, dict) else getattr(block, name, default)


def responses_input(messages, vision=True):
    """Anthropic-style messages as Responses API input items."""
    items = []
    for message in messages:
        role, content = message['role'], message['content']
        if isinstance(content, str):
            content = [{'type': 'text', 'text': content}]
        if role == 'assistant':
            raw = next((_get(b, 'items') for b in content if _get(b, 'type') == 'provider_items'), None)
            if raw is not None:  # our own answer: its items back as they came, reasoning included
                # (a reasoning item without its encrypted content cannot be sent back: nothing is stored)
                items.extend(i for i in raw if i.get('type') != 'reasoning' or i.get('encrypted_content'))
                continue
            for block in content:
                kind = _get(block, 'type')
                if kind == 'text' and _get(block, 'text'):
                    items.append({'role': 'assistant', 'content': _get(block, 'text')})
                elif kind == 'tool_use':
                    items.append({'type': 'function_call', 'call_id': _get(block, 'id'), 'name': _get(block, 'name'),
                                  'arguments': json.dumps(_get(block, 'input') or {})})
            continue
        parts, pictures = [], []
        for block in content:
            kind = _get(block, 'type')
            if kind == 'text':
                parts.append({'type': 'input_text', 'text': _get(block, 'text') or ''})
            elif kind == 'image':
                parts.append(_image_part(block) if vision else
                             {'type': 'input_text', 'text': '[a picture: this model cannot see images]'})
            elif kind == 'tool_result':
                result = _get(block, 'content')
                if isinstance(result, str):
                    text = result
                else:
                    texts = []
                    for part in result or []:
                        if _get(part, 'type') == 'text':
                            texts.append(_get(part, 'text') or '')
                        elif _get(part, 'type') == 'image':
                            if vision:
                                pictures.append(_image_part(part))
                            texts.append('(the picture follows in the next message)' if vision else
                                         '(a picture: this model cannot see images)')
                    text = '\n'.join(texts)
                if _get(block, 'is_error'):
                    text = 'Error: ' + text
                items.append({'type': 'function_call_output', 'call_id': _get(block, 'tool_use_id'), 'output': text})
        if pictures:  # a tool's output is text only: its pictures come as the next message
            parts = [{'type': 'input_text', 'text': 'The pictures the tools returned:'}] + pictures + parts
        if parts:
            items.append({'role': 'user', 'content': parts})
    return items


def responses_request(params, model, include_reasoning=True):
    system = params.get('system') or ''
    if isinstance(system, list):
        system = '\n\n'.join(b.get('text', '') for b in system)
    tools = [{'type': 'function', 'name': t['name'], 'description': t.get('description', ''),
              'parameters': t['input_schema']} for t in params.get('tools') or [] if 'input_schema' in t]
    effort = (params.get('output_config') or {}).get('effort', 'high')
    request = {'model': params['model'], 'instructions': system,
               'input': responses_input(params['messages'], MODELS[model].vision),
               'max_output_tokens': int(params.get('max_tokens', 20000)),
               'reasoning': {'effort': REASONING.get(effort, 'high'), 'summary': 'auto'}, 'store': False}
    if tools:
        request['tools'] = tools
    if include_reasoning:  # stateless: the reasoning comes back encrypted, to send it on with the next turn
        request['include'] = ['reasoning.encrypted_content']
    return request


def responses_message(data, model):
    """A Responses API answer as an Anthropic-style message."""
    content, calls = [], False
    output = data.get('output') or []
    for item in output:
        kind = item.get('type')
        if kind == 'reasoning':
            summary = '\n'.join(s.get('text', '') for s in item.get('summary') or [] if s.get('text'))
            if summary.strip():
                content.append(SimpleNamespace(type='thinking', thinking=summary, signature=''))
        elif kind == 'message':
            for part in item.get('content') or []:
                text = part.get('text') or part.get('refusal') or ''
                if text:
                    content.append(SimpleNamespace(type='text', text=text))
        elif kind == 'function_call':
            calls = True
            try:
                args = json.loads(item.get('arguments') or '{}')
            except ValueError:
                args = {}
            content.append(SimpleNamespace(type='tool_use', id=item.get('call_id'), name=item.get('name'),
                                           input=args if isinstance(args, dict) else {}))
    # The items themselves, to send back unchanged with the next request.
    content.append(SimpleNamespace(type='provider_items', items=output))
    if calls:
        stop = 'tool_use'
    elif data.get('status') == 'incomplete' and (data.get('incomplete_details') or {}).get('reason') == 'max_output_tokens':
        stop = 'max_tokens'
    else:
        stop = 'end_turn'
    usage = data.get('usage') or {}
    cached = (usage.get('input_tokens_details') or {}).get('cached_tokens') or 0
    return SimpleNamespace(
        id=data.get('id'), model=data.get('model', model), role='assistant', content=content, stop_reason=stop,
        usage=SimpleNamespace(input_tokens=max(0, (usage.get('input_tokens') or 0) - cached),
                              output_tokens=usage.get('output_tokens') or 0, cache_read_input_tokens=cached,
                              cache_creation_input_tokens=0, server_tool_use=None))


class ResponsesClient:
    """The OpenAI Responses API (OpenAI, xAI), answering like anthropic.Anthropic().
    Plain HTTPS with Python's own urllib: nothing more to install."""

    RETRY = (429, 500, 502, 503, 504)

    def __init__(self, provider, key, timeout=600.0):
        self.provider, self.key, self.timeout = provider, key, timeout
        self.include_reasoning = True
        self.messages = SimpleNamespace(create=self.create)
        self.beta = SimpleNamespace(messages=self.messages)

    def post(self, body):
        """(status, headers, parsed body or text) of one POST to /responses."""
        request = urllib.request.Request(
            f'{self.provider.base_url}/responses', data=json.dumps(body).encode('utf-8'), method='POST',
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self.key}'})
        try:
            with open_url(request, host_of(self.provider.base_url), self.timeout) as answer:
                status, headers, raw = answer.status, dict(answer.headers), answer.read()
        except urllib.error.HTTPError as e:
            status, headers, raw = e.code, dict(e.headers or {}), e.read()
        try:
            return status, headers, json.loads(raw.decode('utf-8') or 'null')
        except ValueError:
            return status, headers, raw.decode('utf-8', 'replace')[:500]

    def create(self, **params):
        model = params['model']
        request = responses_request(params, model, self.include_reasoning)
        status, data = 0, None
        for attempt in range(4):
            try:
                status, headers, data = self.post(request)
            except (urllib.error.URLError, OSError) as e:  # no connection, or no answer in time
                if attempt < 3 and 'timed out' not in str(e):
                    time.sleep(2 ** (attempt + 1))
                    continue
                raise ProviderError(self.provider.name, 0, f'cannot reach {self.provider.base_url}: {e}') from None
            if 200 <= status < 300 and isinstance(data, dict):  # a redirect (3xx) is no answer
                return responses_message(data, model)
            message = self.error_text(data)
            if status == 400 and 'include' in request and 'include' in message.lower():
                # This endpoint will not send reasoning back: go on without it.
                self.include_reasoning = False
                request.pop('include')
                continue
            if status == 400 and request['reasoning']['effort'] != 'high' and 'effort' in message.lower():
                request['reasoning']['effort'] = 'high'  # an effort this model does not take
                continue
            if status in self.RETRY and attempt < 3:
                wait = str(headers.get('retry-after') or headers.get('Retry-After') or '')
                time.sleep(min(30.0, float(wait)) if wait.replace('.', '', 1).isdigit() else 2 ** (attempt + 1))
                continue
            raise ProviderError(self.provider.name, status, message)
        raise ProviderError(self.provider.name, status, self.error_text(data))

    @staticmethod
    def error_text(data):
        if isinstance(data, dict):
            error = data.get('error')
            if isinstance(error, dict):
                return str(error.get('message') or error)
            return str(error or data)
        return str(data)


# ------------------------------------------------------------- Refresh models
# What a provider lists that the assistant can use: chat models that call tools,
# not its embedding, speech, image or dated snapshot ids.
SKIP_WORDS = ('embed', 'audio', 'realtime', 'transcribe', 'tts', 'whisper', 'image', 'imagine', 'dall', 'vision-exp',
              'moderation', 'search', 'instruct', 'asr', 'omni', '-vl', 'math', 'mt-', 'rerank', 'video', 'ocr')
FAMILIES = {'anthropic': ('claude-',), 'openai': ('gpt-',), 'xai': ('grok-',), 'moonshot': ('kimi-',),
            'deepseek': ('deepseek-',), 'qwen': ('qwen3', 'qwen4')}
SNAPSHOT = re.compile(r'-(\d{4}-\d{2}-\d{2}|\d{8}|\d{4})$')  # gpt-6.1-terra-2026-10-26, qwen3.8-max-0902
OPUS_FACTOR = 2.5  # an Opus model not in the built-in list: estimated at 2.5 times Sonnet


def usable(provider, model_id):
    model_id = str(model_id or '').lower()
    return (model_id.startswith(FAMILIES.get(provider, ('',))) and not SNAPSHOT.search(model_id)
            and not any(word in model_id for word in SKIP_WORDS))


def pretty(model_id):
    """A name for a model only known by its id: 'gpt-6.2-terra' -> 'GPT-6.2 Terra'."""
    words = str(model_id).split('-')
    names = {'gpt': 'GPT', 'deepseek': 'DeepSeek', 'grok': 'Grok', 'kimi': 'Kimi', 'claude': 'Claude'}
    out = []
    for i, word in enumerate(words):
        if word in names:
            out.append(names[word])
        elif word[:1].isalpha() and word[1:2].isdigit():  # k3.1, v5
            out.append(word.upper())
        elif word[:1].isdigit() and out and out[-1] == 'GPT':
            out[-1] = f'GPT-{word}'
        elif word.isdigit() and out and out[-1].split('-')[-1].replace('.', '').isdigit():
            out[-1] += '.' + word  # opus-5-5 -> Opus 5.5
        else:
            out.append(word[:1].upper() + word[1:])
    return ' '.join(out)


def _get_json(url, headers, timeout, host):
    """GET url (with a key in headers, for host only) as parsed JSON."""
    request = urllib.request.Request(url, headers=headers, method='GET')
    try:
        with open_url(request, host, timeout) as answer:
            return json.loads(answer.read().decode('utf-8') or 'null')
    except UnsafeRequest as e:
        raise ProviderError(url.split('/')[2], 0, str(e)) from None
    except urllib.error.HTTPError as e:
        try:
            data = json.loads(e.read().decode('utf-8') or 'null')
        except ValueError:
            data = None
        raise ProviderError(url.split('/')[2], e.code, ResponsesClient.error_text(data) if data else e.reason) from None
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise ProviderError(url.split('/')[2], 0, f'cannot reach it: {e}') from None


def list_models(provider, key, timeout=30.0):
    """The models a provider offers to this key, as dicts {id, label, vision, prices,
    retiring, retired}; prices only where the provider says them (xAI), else None."""
    p = PROVIDERS[provider]
    host = host_of(p.models_url)  # every page of the list from there, whatever an answer says
    found = []
    if provider == 'anthropic':
        url, after = p.models_url + '?limit=100', None
        while True:
            data = _get_json(url + (f'&after_id={quote(str(after), safe="")}' if after else ''),
                             {'x-api-key': key, 'anthropic-version': '2023-06-01'}, timeout, host) or {}
            for m in data.get('data') or []:
                state = str(m.get('lifecycle') or m.get('status') or '').lower()
                found.append({'id': m.get('id'), 'label': m.get('display_name') or pretty(m.get('id')),
                              'vision': True, 'prices': None, 'retired': state == 'retired',
                              'retiring': str(m.get('deprecated_at') or '')[:10] or ('soon' if state == 'deprecated'
                                                                                    else '')})
            if not data.get('has_more') or not data.get('last_id'):
                break
            after = data['last_id']
    else:
        data = _get_json(p.models_url, {'Authorization': f'Bearer {key}'}, timeout, host) or {}
        rows = data.get('models') if provider == 'xai' else data.get('data')
        today = time.strftime('%Y-%m-%d')
        for m in rows or []:
            if not isinstance(m, dict):
                continue
            modalities = [str(x).lower() for x in m.get('input_modalities') or []]
            vision = ('image' in modalities) if modalities else bool(m.get('supports_image_in', True))
            if provider == 'xai' and 'text' not in [str(x).lower() for x in m.get('output_modalities') or ['text']]:
                continue
            prices = None
            if provider == 'xai' and m.get('prompt_text_token_price') is not None:
                per_million = lambda v: round(float(v or 0) / 10000.0, 6)  # noqa: E731 (cents per 100M tokens)
                cin = per_million(m['prompt_text_token_price'])
                prices = (cin, per_million(m.get('completion_text_token_price')), cin,
                          per_million(m.get('cached_prompt_text_token_price', m['prompt_text_token_price'])))
            shutdown = str(m.get('shutdown_date') or '')[:10]
            found.append({'id': m.get('id'), 'label': pretty(m.get('id')), 'vision': vision, 'prices': prices,
                          'retired': bool(shutdown) and shutdown <= today, 'retiring': shutdown})
    return [f for f in found if f['id'] and usable(provider, f['id'])]


def estimate(provider, model_id):
    """A price for a model its provider does not price: the dearest built-in model of the
    provider (an Opus at OPUS_FACTOR times that), so a spending limit is never run past."""
    known = [m.prices for m in BUILTIN.values() if m.provider == provider]
    if not known:
        return BUILTIN[DEFAULT_MODEL].prices
    dearest = max(known, key=lambda prices: prices[1])
    if provider == 'anthropic' and 'opus' in model_id:
        return tuple(round(v * OPUS_FACTOR, 6) for v in dearest)
    return dearest


def use_catalog(catalog):
    """The models offered, from the built-in ones and a Refresh (catalog: {'providers':
    {provider: {'models': [list_models rows]} or {'error': text}}}). A provider that
    answered decides: what it no longer lists or retired is hidden, what it newly lists
    is added. MODELS, PRICES and ALIASES change in place. Returns the hidden ids."""
    listed = {k: v.get('models') for k, v in ((catalog or {}).get('providers') or {}).items()
              if isinstance(v, dict) and isinstance(v.get('models'), list)}
    offered, hidden = {}, []
    for provider in PROVIDERS:
        rows = {r['id']: r for r in listed.get(provider) or [] if isinstance(r, dict) and r.get('id')}
        answered = provider in listed
        for m in BUILTIN.values():
            if m.provider != provider:
                continue
            row = rows.get(m.id)
            if answered and (row is None or row.get('retired')):
                hidden.append(m.id)
                continue
            offered[m.id] = replace(m, retiring=(row or {}).get('retiring') or '')
        for model_id, row in rows.items():
            if model_id in BUILTIN or row.get('retired') or model_id in offered:
                continue
            prices = tuple(row['prices']) if row.get('prices') else estimate(provider, model_id)
            offered[model_id] = Model(model_id, row.get('label') or pretty(model_id), provider, prices,
                                      vision=row.get('vision', True) is not False, new=True,
                                      retiring=row.get('retiring') or '', estimated=not row.get('prices'))
    MODELS.clear()
    MODELS.update(offered)
    PRICES.clear()
    PRICES.update({m.id: m.prices for m in offered.values()})
    ALIASES.clear()
    ALIASES.update({alias: m.id for m in offered.values() for alias in m.aliases})
    return hidden


def refresh(keys, timeout=30.0):
    """Ask every provider with a key which models it offers: a catalog for use_catalog."""
    catalog = {'refreshed': time.strftime('%Y-%m-%d %H:%M'), 'providers': {}}
    for provider, key in keys.items():
        if provider not in PROVIDERS or not key:
            continue
        try:
            catalog['providers'][provider] = {'models': list_models(provider, key, timeout)}
        except ProviderError as e:
            catalog['providers'][provider] = {'error': e.message if e.status_code else str(e.message)}
    return catalog
