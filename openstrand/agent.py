"""A Claude agent that builds OpenStrand Studio projects with the openstrand tools.

The agent loop is ours: Claude reads the request (and any reference image),
researches it on the web when it needs to, plans a structure, builds it from
samples, generators or its own drawing, looks at each render, and stops when
the design is right. Everything it does is reported through on_event, one
dict per step, so a terminal or the app's Claude panel can show progress.

Runs with the user's own Anthropic API key (ANTHROPIC_API_KEY).
"""
import base64
import contextlib
import json
import mimetypes
from pathlib import Path

from . import ROOT, colors, edit, generators, project

MODELS = {'sonnet': 'claude-sonnet-5-5', 'haiku': 'claude-haiku-5-5'}
DEFAULT_MODEL = MODELS['sonnet']
EFFORTS = ('low', 'medium', 'high', 'xhigh', 'max')

# USD per million tokens: input, output, cache write (5 min), cache read.
# Haiku 5.5's prices are for prompts up to 100K tokens, which these stay under.
PRICES = {
    'claude-sonnet-5-5': (2.00, 10.00, 2.50, 0.20),
    'claude-haiku-5-5': (0.10, 0.50, 0.125, 0.01),
}
WEB_SEARCH_PRICE = 0.01  # USD per search ($10 per 1,000)

# Server-side fallback re-runs a declined Sonnet request on another model;
# Haiku has none.
FALLBACK_BETA = 'server-side-fallback-2026-07-01'

# Web tools run on Anthropic's servers. Sonnet 5.5 has the versions that
# filter results before they reach the context; Haiku 5.5 the basic ones.
WEB_TOOLS = {
    'claude-sonnet-5-5': [{'type': 'web_search_20260209', 'name': 'web_search', 'max_uses': 6},
                          {'type': 'web_fetch_20260209', 'name': 'web_fetch', 'max_uses': 6}],
    'claude-haiku-5-5': [{'type': 'web_search_20250305', 'name': 'web_search', 'max_uses': 6},
                         {'type': 'web_fetch_20250910', 'name': 'web_fetch', 'max_uses': 6}],
}

SKILL = ROOT / '.claude' / 'skills' / 'openstrand-designer'
GUIDE = SKILL / 'guide.md'
DRAWING = SKILL / 'drawing.md'

INSTRUCTIONS = """You design OpenStrand Studio projects for the person you are talking to.
OpenStrand Studio is a desktop app for drawing knots, mats, stitches and other
woven strand designs. Every design you make goes through the tools, so it opens
in the app with real strands, masks and groups.

How to work:
1. Understand the request from the words and any reference image. Describe an
   image in the guide's terms first (kind of design, loops, crossings, colors).
2. If a published sample or a make_ tool fits, use it: it is the fastest and
   cleanest result.
3. Otherwise design it yourself:
   - Research: when you do not know exactly what the thing is or how it is
     tied or woven, search the web (web_search) and read a good page
     (web_fetch): its structure, how many strands, how they cross, what it
     looks like when finished.
   - If the web has nothing useful, reason it out from first principles: what
     the name suggests, how similar knots and stitches are built. Say what you
     assumed.
   - Plan the structure in OpenStrand terms: how many cords, where each runs,
     where they cross, which goes over.
   - Draw it with draw_design, using the drawing guide below. Read the report:
     crossings, conflicts and warnings.
4. Call render and look at the picture. Compare it with the request and with
   what you learned: counts, shape, colors, over and under. Fix what is off and
   draw or render again. Stop after five renders.
5. Finish with two or three short sentences: what you made, how it is built,
   and anything you could not do or had to assume. Plain words, no markdown.

Drawing takes a few seconds to a minute; making a Turk's head size that is not
published, or a heart, about a minute. Call it once and wait.

"""

TOOLS = [
    {
        'name': 'search_samples',
        'description': 'List published ready-made designs whose names contain the text '
                       '(knots, Turk\'s heads, links, MxN stitches). Empty text lists all.',
        'input_schema': {'type': 'object', 'properties': {
            'text': {'type': 'string', 'description': 'part of a name, e.g. "turks", "ring", "mxn_rh"'}},
            'required': ['text']},
    },
    {
        'name': 'load_sample',
        'description': 'Start from a published design by its exact name (from search_samples).',
        'input_schema': {'type': 'object', 'properties': {'name': {'type': 'string'}}, 'required': ['name']},
    },
    {
        'name': 'make_turks_head',
        'description': "Make a woven Turk's head ring knot. Leads (2-7) and bights (2-13) must share "
                       "no common factor. Published sizes are instant; others take about a minute.",
        'input_schema': {'type': 'object', 'properties': {
            'leads': {'type': 'integer', 'description': 'turns around the ring'},
            'bights': {'type': 'integer', 'description': 'loops on the rim'},
            'color': {'type': 'string', 'description': 'color name or hex; default teal'}},
            'required': ['leads', 'bights']},
    },
    {
        'name': 'make_mxn',
        'description': 'Make an MxN stitch: m vertical and n horizontal ribbons (each 1-8). '
                       'Each ribbon is its own set.',
        'input_schema': {'type': 'object', 'properties': {
            'm': {'type': 'integer'}, 'n': {'type': 'integer'},
            'hand': {'type': 'string', 'enum': ['lh', 'rh'], 'description': 'left or right hand; default lh'},
            'stretch': {'type': 'boolean', 'description': 'ribbons packed closer together'}},
            'required': ['m', 'n']},
    },
    {
        'name': 'make_heart',
        'description': 'Make a ribbon heart from one cord, its ends crossing below the tip. Takes about a minute.',
        'input_schema': {'type': 'object', 'properties': {
            'color': {'type': 'string', 'description': 'color name or hex; default crimson'}}},
    },
    {
        'name': 'draw_design',
        'description': 'Draw your own design from cord centerlines; it replaces the current design. '
                       'Each cord is points it passes through ({"points": [[x, y], ...]}), a parametric '
                       'curve ({"x": "...t...", "y": "...t...", "t0": 0, "t1": "2*pi"}) or a shape '
                       '({"shape": "circle", "center": [x, y], "radius": r}; also ellipse, polygon, heart, '
                       'turks_head), plus optional closed, color, width, label, second_color, tucked. '
                       'Every crossing gets over and under, alternating along each cord. Send the whole '
                       'design every time. Returns a report: crossings, which cord is on top, conflicts '
                       'and warnings. See "Drawing your own designs" in the guide.',
        'input_schema': {'type': 'object', 'properties': {
            'name': {'type': 'string', 'description': 'what the design is'},
            'weave': {'type': 'string', 'enum': ['alternate', 'alternate_under_first']},
            'cords': {'type': 'array', 'minItems': 1, 'maxItems': 12,
                      'items': {'type': 'object', 'description': 'one cord: points, x/y, or shape, '
                                                                 'plus style'}}},
            'required': ['cords']},
    },
    {
        'name': 'describe',
        'description': 'Describe the current design: each set with its color and which way it runs '
                       '(vertical, horizontal), strands, masks, size.',
        'input_schema': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'recolor',
        'description': 'Give the listed sets one color (name or hex). Masks follow their sets.',
        'input_schema': {'type': 'object', 'properties': {
            'sets': {'type': 'array', 'items': {'type': 'integer'}, 'description': 'set numbers, e.g. [1, 2, 3]'},
            'color': {'type': 'string'}},
            'required': ['sets', 'color']},
    },
    {
        'name': 'validate',
        'description': "Load the current design with the app's own loader and list problems.",
        'input_schema': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'render',
        'description': "Draw the current design with the app's real canvas and return the picture to look at.",
        'input_schema': {'type': 'object', 'properties': {}},
    },
]


class ToolError(Exception):
    """A tool call that cannot be done; its message goes back to Claude."""


def image_block(path):
    """A user-message image block for a PNG, JPEG, GIF or WebP file."""
    path = Path(path)
    media = mimetypes.guess_type(path.name)[0]
    if media not in ('image/png', 'image/jpeg', 'image/gif', 'image/webp'):
        raise ValueError(f'{path}: use a PNG, JPEG, GIF or WebP image')
    data = base64.standard_b64encode(path.read_bytes()).decode('ascii')
    return {'type': 'image', 'source': {'type': 'base64', 'media_type': media, 'data': data}}


def _searches(usage):
    server = getattr(usage, 'server_tool_use', None)
    return (getattr(server, 'web_search_requests', 0) or 0) if server is not None else 0


def cost_of(model, usage):
    """USD for one response's usage, web searches included."""
    p_in, p_out, p_write, p_read = PRICES.get(model, PRICES[DEFAULT_MODEL])
    get = lambda name: getattr(usage, name, 0) or 0
    return ((get('input_tokens') * p_in + get('output_tokens') * p_out
             + get('cache_creation_input_tokens') * p_write
             + get('cache_read_input_tokens') * p_read) / 1_000_000
            + _searches(usage) * WEB_SEARCH_PRICE)


class Workspace:
    """The design being built, saved to out_dir after every change."""

    def __init__(self, out_dir):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.project_path = self.out_dir / 'design.json'
        self.png_path = self.out_dir / 'design.png'
        self.data = None
        self.version = 0
        self.rendered_version = -1
        self._preview = None

    def need(self):
        if self.data is None:
            raise ToolError('there is no design yet: make, draw or load one first')
        return self.data

    def store(self, data):
        self.data = data
        self.version += 1
        project.write(data, self.project_path)

    def render(self):
        from generate_creative_samples import AppPreview
        generators.application()
        if self._preview is None:
            self._preview = AppPreview()
        self._preview.capture(self.need(), self.png_path)
        self.rendered_version = self.version
        return self.png_path

    def close(self):
        if self._preview is not None:
            self._preview.close()
            self._preview = None

    def run(self, name, args):
        """Do one tool call. Returns (summary for people, content for Claude)."""
        if name == 'search_samples':
            text = str(args.get('text', '')).lower()
            names = [n for n in generators.samples() if text in n.lower()]
            shown = ', '.join(names[:60]) + (f' (and {len(names) - 60} more)' if len(names) > 60 else '')
            return f'{len(names)} samples', shown or 'no sample matches; try a shorter word'
        if name == 'load_sample':
            data, _, source = generators.sample(str(args.get('name', '')))
            self.store(data)
            return f'{source} · {project.summary(data)}', f'loaded {source}: {project.summary(data)}'
        if name == 'make_turks_head':
            color = colors.parse(args.get('color') or 'teal')
            data, warnings, source = generators.turks_head(int(args['leads']), int(args['bights']), color)
            self.store(data)
            note = f' (from the published sample {source})' if source else ''
            text = f"Turk's head {args['leads']}x{args['bights']}: {project.summary(data)}{note}"
            if warnings:
                text += '; warnings: ' + '; '.join(' '.join(map(str, w)) for w in warnings)
            return f"Turk's head {args['leads']}×{args['bights']} · {project.summary(data)}", text
        if name == 'make_mxn':
            data, _, source = generators.mxn(int(args['m']), int(args['n']), args.get('hand') or 'lh',
                                             bool(args.get('stretch')))
            self.store(data)
            return f"Stitch {args['m']}×{args['n']} {args.get('hand') or 'lh'} · {project.summary(data)}", \
                f'made {source}: {project.summary(data)}'
        if name == 'make_heart':
            data, warnings, _ = generators.heart(colors.parse(args.get('color') or 'crimson'))
            self.store(data)
            return f'Heart · {project.summary(data)}', f'made a ribbon heart: {project.summary(data)}'
        if name == 'draw_design':
            from . import draw
            data, report = draw.build(args)
            self.store(data)
            title = str(args.get('name') or 'drawing')[:40]
            return f'{title} · {project.summary(data)}', report + '\nNow render it and look at the result.'
        if name == 'describe':
            info = project.describe(self.need())
            lines = [f"{info['strands']} strands, {info['masks']} masks, size {info['size'][0]}x{info['size'][1]}"]
            for n, s in info['sets'].items():
                lines.append(f"set {n}: {s['strands']} strands, {' '.join(s['colors'])}"
                             + (f", runs {s['runs']}" if s['runs'] else ''))
            return project.summary(self.need()), '\n'.join(lines)
        if name == 'recolor':
            sets = [int(n) for n in args.get('sets') or []]
            if not sets:
                raise ToolError('list at least one set number')
            color = colors.parse(str(args.get('color', '')))
            data = self.need()
            edit.recolor(data, {n: color for n in sets})
            self.store(data)
            return f"Sets {', '.join(map(str, sets))} → {color}", f"recolored sets {sets} to {color}"
        if name == 'validate':
            from . import check
            found = check.problems(self.need())
            if found:
                return f'{len(found)} problems', 'problems:\n' + '\n'.join(found)
            return 'valid', f'valid: {project.summary(self.data)}'
        if name == 'render':
            path = self.render()
            data = base64.standard_b64encode(path.read_bytes()).decode('ascii')
            return 'picture', [{'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': data}}]
        raise ToolError(f'unknown tool {name}')


class Agent:
    """Runs one request: the loop of Claude calls and tool calls."""

    def __init__(self, client, out_dir, model=DEFAULT_MODEL, on_event=None, max_rounds=24, max_cost=2.00,
                 quiet=None, web=True, effort='high'):
        if model not in PRICES:
            raise ValueError(f"model must be one of {', '.join(PRICES)}")
        if effort not in EFFORTS:
            raise ValueError(f"effort must be one of {', '.join(EFFORTS)}")
        self.client = client
        # Wraps every tool call; the CLI passes one that hides the app's own
        # console output, so it cannot mix with the events.
        self.quiet = quiet or contextlib.nullcontext
        self.model = model
        self.web = web
        self.effort = effort
        self.workspace = Workspace(out_dir)
        self.on_event = on_event or (lambda event: None)
        self.max_rounds = max_rounds
        self.max_cost = max_cost
        self.cost = 0.0
        self.searches = 0
        self.usage = {'input_tokens': 0, 'output_tokens': 0,
                      'cache_creation_input_tokens': 0, 'cache_read_input_tokens': 0}

    def system(self):
        text = (INSTRUCTIONS + 'The guide:\n\n' + GUIDE.read_text(encoding='utf-8')
                + '\n\n' + DRAWING.read_text(encoding='utf-8'))
        return [{'type': 'text', 'text': text, 'cache_control': {'type': 'ephemeral'}}]

    def tools(self):
        return TOOLS + (WEB_TOOLS[self.model] if self.web else [])

    def call(self, messages):
        params = dict(model=self.model, max_tokens=20000, system=self.system(), tools=self.tools(),
                      messages=messages, thinking={'type': 'adaptive', 'display': 'summarized'},
                      output_config={'effort': self.effort})
        try:
            if self.model == MODELS['sonnet']:
                return self.client.beta.messages.create(betas=[FALLBACK_BETA], fallbacks='default', **params)
            return self.client.messages.create(**params)
        except Exception as e:
            # An organization can switch the web tools off for its API keys:
            # carry on without them rather than fail the request.
            text = str(e)
            if self.web and getattr(e, 'status_code', None) == 400 and ('web_search' in text or 'web_fetch' in text):
                self.web = False
                self.on_event({'type': 'note', 'text': 'Web search is not available for this API key '
                                                        '(an organization setting in the Anthropic Console); '
                                                        'continuing without it.'})
                return self.call(messages)
            raise

    def count(self, response):
        for key in self.usage:
            self.usage[key] += getattr(response.usage, key, 0) or 0
        self.searches += _searches(response.usage)
        self.cost += cost_of(self.model, response.usage)
        self.on_event({'type': 'usage', 'cost': round(self.cost, 4), 'searches': self.searches, **self.usage})

    def report(self, block):
        """Events for the parts of a response people want to follow."""
        kind = block.type
        if kind == 'thinking' and (getattr(block, 'thinking', '') or '').strip():
            self.on_event({'type': 'thinking', 'text': block.thinking.strip()})
        elif kind == 'server_tool_use':
            args = block.input if isinstance(block.input, dict) else {}
            self.on_event({'type': 'search', 'name': block.name,
                           'query': args.get('query') or args.get('url') or ''})
        elif kind in ('web_search_tool_result', 'web_fetch_tool_result'):
            content = getattr(block, 'content', None)
            error = getattr(content, 'error_code', None) if not isinstance(content, list) else None
            found = len(content) if isinstance(content, list) else None
            self.on_event({'type': 'search_result', 'name': kind.replace('_tool_result', ''),
                           'ok': error is None, 'error': error, 'results': found})

    def run(self, prompt, images=(), start=None):
        """Build what prompt asks for. Returns the 'done' event.

        start is a project dict to begin from, such as what is on the
        person's canvas; the agent can describe, change or replace it.
        """
        if start is not None:
            self.workspace.store(start)
            prompt = ('The design on my canvas right now is already loaded as the current design '
                      f'({project.summary(start)}). Change it if my request is about it; '
                      'make a new one if I ask for something new.\n\n' + prompt)
        content = [image_block(p) for p in images] + [{'type': 'text', 'text': prompt}]
        messages = [{'role': 'user', 'content': content}]
        said = []
        try:
            for _ in range(self.max_rounds):
                response = self.call(messages)
                self.count(response)
                # Append the whole turn, thinking blocks included: the API
                # needs them back unchanged.
                messages.append({'role': 'assistant', 'content': response.content})
                for block in response.content:
                    if block.type == 'text' and block.text.strip():
                        said.append(block.text.strip())
                        self.on_event({'type': 'text', 'text': block.text.strip()})
                    else:
                        self.report(block)
                if response.stop_reason == 'refusal':
                    return self.finish(said, error='Claude declined this request.')
                if response.stop_reason == 'max_tokens':
                    return self.finish(said, error='Claude ran out of room for its answer.')
                if response.stop_reason == 'pause_turn':
                    continue  # a long server-side search: send the turn back to resume it
                if response.stop_reason != 'tool_use':
                    return self.finish(said)
                results = [self.tool(block) for block in response.content if block.type == 'tool_use']
                messages.append({'role': 'user', 'content': results})
                if self.cost > self.max_cost:
                    return self.finish(said, error=f'Stopped at the ${self.max_cost:.2f} limit for one request.')
            return self.finish(said, error=f'Stopped after {self.max_rounds} rounds without finishing.')
        finally:
            with self.quiet():
                self.workspace.close()

    def tool(self, block):
        args = block.input if isinstance(block.input, dict) else {}
        self.on_event({'type': 'tool_start', 'name': block.name, 'input': args})
        try:
            with self.quiet():
                summary, content = self.workspace.run(block.name, args)
        except (ToolError, ValueError, KeyError, TypeError) as e:
            message = str(e) if not isinstance(e, KeyError) else f'missing argument {e}'
            self.on_event({'type': 'tool_end', 'name': block.name, 'ok': False, 'summary': message})
            return {'type': 'tool_result', 'tool_use_id': block.id, 'content': message, 'is_error': True}
        except Exception as e:  # a crash inside the app's code: tell Claude, keep going
            message = f'{type(e).__name__}: {e}'
            self.on_event({'type': 'tool_end', 'name': block.name, 'ok': False, 'summary': message})
            return {'type': 'tool_result', 'tool_use_id': block.id, 'content': message, 'is_error': True}
        self.on_event({'type': 'tool_end', 'name': block.name, 'ok': True, 'summary': summary})
        return {'type': 'tool_result', 'tool_use_id': block.id, 'content': content}

    def finish(self, said, error=None):
        ws = self.workspace
        event = {'type': 'done', 'ok': error is None, 'error': error,
                 'text': said[-1] if said else '',
                 'project': str(ws.project_path) if ws.data is not None else None,
                 'png': str(ws.png_path) if ws.rendered_version == ws.version and ws.data is not None else None,
                 'cost': round(self.cost, 4), 'model': self.model, 'searches': self.searches, **self.usage}
        self.on_event(event)
        return event


def print_events(event, as_json=False):
    """Show agent events in a terminal: JSON lines for programs, short lines for people."""
    if as_json:
        print(json.dumps(event), flush=True)
        return
    kind = event['type']
    if kind == 'text':
        print(f"claude: {event['text']}", flush=True)
    elif kind == 'thinking':
        print(f"  (thinking) {event['text']}", flush=True)
    elif kind == 'search':
        print(f"  … {event['name']} {event['query']}".rstrip(), flush=True)
    elif kind == 'search_result':
        found = f"{event['results']} results" if event['results'] is not None else 'done'
        print(f"  {'✓' if event['ok'] else '✗'} {event['name']}: {found if event['ok'] else event['error']}", flush=True)
    elif kind == 'note':
        print(f"note: {event['text']}", flush=True)
    elif kind == 'tool_start':
        args = ' '.join(f'{k}={v}' for k, v in event['input'].items())
        print(f"  … {event['name']} {args[:200]}".rstrip(), flush=True)
    elif kind == 'tool_end':
        print(f"  {'✓' if event['ok'] else '✗'} {event['summary']}", flush=True)
    elif kind == 'done':
        if event['error']:
            print(f"error: {event['error']}", flush=True)
        if event['project']:
            print(f"wrote {event['project']}", flush=True)
        searches = f" · {event['searches']} web searches" if event.get('searches') else ''
        print(f"cost ${event['cost']:.4f} · {event['model']}{searches}", flush=True)
