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
"""
import json
import os
import time
from dataclasses import dataclass, field
from types import SimpleNamespace


@dataclass(frozen=True)
class Provider:
    key: str          # 'anthropic', 'openai', ...
    name: str         # shown in Settings > Models
    api: str          # 'anthropic', 'anthropic-compatible' or 'responses'
    env: str          # the environment variable that holds its API key
    base_url: str = None
    keys_url: str = ''  # where to make a key
    key_hint: str = ''  # what a key looks like (the key field's placeholder)


@dataclass(frozen=True)
class Model:
    id: str
    label: str
    provider: str
    prices: tuple                     # input, output, cache write, cache read (USD per million tokens)
    vision: bool = True               # reads images (the reference image, render's picture)
    aliases: tuple = field(default=())


PROVIDERS = {p.key: p for p in (
    Provider('anthropic', 'Anthropic (Claude)', 'anthropic', 'ANTHROPIC_API_KEY',
             keys_url='https://console.anthropic.com/settings/keys', key_hint='sk-ant-…'),
    Provider('openai', 'OpenAI (GPT)', 'responses', 'OPENAI_API_KEY', 'https://api.openai.com/v1',
             'https://platform.openai.com/api-keys', 'sk-…'),
    Provider('xai', 'xAI (Grok)', 'responses', 'XAI_API_KEY', 'https://api.x.ai/v1',
             'https://console.x.ai', 'xai-…'),
    Provider('moonshot', 'Moonshot AI (Kimi)', 'anthropic-compatible', 'MOONSHOT_API_KEY',
             'https://api.moonshot.ai/anthropic', 'https://platform.kimi.ai/console/api-keys', 'sk-…'),
    Provider('deepseek', 'DeepSeek', 'anthropic-compatible', 'DEEPSEEK_API_KEY',
             'https://api.deepseek.com/anthropic', 'https://platform.deepseek.com/api_keys', 'sk-…'),
    Provider('qwen', 'Alibaba Cloud (Qwen)', 'anthropic-compatible', 'DASHSCOPE_API_KEY',
             'https://dashscope-intl.aliyuncs.com/apps/anthropic',
             'https://modelstudio.console.alibabacloud.com/?tab=playground#/api-key', 'sk-…'),
)}

MODELS = {m.id: m for m in (
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
    if p.api == 'responses':
        return ResponsesClient(p, key)
    import anthropic
    if p.api == 'anthropic':
        return anthropic.Anthropic(api_key=key)
    return CompatClient(compatible_sdk(anthropic, key, p.base_url))


def compatible_sdk(anthropic, key, base_url):
    """The anthropic SDK on a compatible endpoint. Their docs for Claude Code give the key
    as a Bearer token (ANTHROPIC_AUTH_TOKEN); some read x-api-key: send it both ways."""
    return anthropic.Anthropic(auth_token=key, base_url=base_url, default_headers={'x-api-key': key})


class ProviderError(Exception):
    """An error a provider's API returned: status_code and its message."""

    def __init__(self, provider, status_code, message):
        super().__init__(f'{provider} API returned {status_code}: {message}')
        self.provider, self.status_code, self.message = provider, status_code, message


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
        import urllib.error
        import urllib.request
        request = urllib.request.Request(
            f'{self.provider.base_url}/responses', data=json.dumps(body).encode('utf-8'), method='POST',
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self.key}'})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as answer:
                status, headers, raw = answer.status, dict(answer.headers), answer.read()
        except urllib.error.HTTPError as e:
            status, headers, raw = e.code, dict(e.headers or {}), e.read()
        try:
            return status, headers, json.loads(raw.decode('utf-8') or 'null')
        except ValueError:
            return status, headers, raw.decode('utf-8', 'replace')[:500]

    def create(self, **params):
        import urllib.error
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
            if status < 400 and isinstance(data, dict):
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
