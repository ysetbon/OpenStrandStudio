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

Knots tied in a cord (overhand, figure-eight, stevedore and the like):
- To show how a knot is tied, or a knot pulled tight, use tie_knot. It works
  the steps out by simulating a real cord and checks every step is the right
  knot, so never draw tying steps or a tightened knot by hand.
- A knot not in knot_library: research how it is tied, then give tie_knot its
  path (rough points from the standing end, crossing itself where the knot
  does, a few cord widths between parts) and its over/under pattern. Read the
  checks: they name the knot the path makes. If it is not the knot you meant,
  fix the path or the pattern and try again.
- For the knot in a design the person already has (in the app: read_tab it
  first), call tie_knot with from_design: it keeps that knot's over and under.
- tie_knot pulls the two ends apart, as for stopper knots. For a loop knot
  (bowline) or a bend joining two cords, say it is not supported yet and draw
  it with draw_design.
- To check any design is the knot it should be, call identify_knot rather than
  judging the picture.

Masks (which strand is on top at a crossing) in tight and crowded designs:
- A tight knot's parts touch and its joints sit inside crossings, so a mask
  can paint over a strand beside its crossing, or a crossing can show half one
  way, half the other. tie_knot already fixes what is safe and lists what is
  left per step ("masks fixed", "masks left"). The same happens in any crowded
  design: stretched MxN stitches, Turk's heads with a small inner radius,
  designs whose cords lie close together.
- After tie_knot (and after drawing or loading anything crowded), call
  check_masks. For each problem it lists, call the edit_mask it names, with
  preview: true first when unsure; use its coordinates and names, never guess
  them. Prefer covers (uncover a strand) and around (one crossing) over a box:
  the tool shapes those along the strand's outline. Then render and look
  closely at each place you changed. Stop when check_masks finds nothing, or
  say what is left and why (some places need the strands moved apart).
- Where a problem says neither the design nor a mask says which strand goes
  over, the check reads it from what most of the crossing shows: compare with
  the render and with what the person asked before you change it.

Drawing takes a few seconds to a minute; making a Turk's head size that is not
published, or a heart, about a minute. Call it once and wait.

"""

# Plan mode: research and plan, build nothing. Only tools that look are offered.
PLAN_TOOLS = ('search_samples', 'describe', 'knot_library', 'identify_knot', 'check_masks')
PLAN_INSTRUCTIONS = """Plan mode is on: the person wants a plan before anything is built. The
tools that build are not available, so do not try to build. Research as much as
you need (samples, the web, the current design), then answer with a short plan
in plain words, as a numbered list: what the design is and how it is built in
the real world; the cords and how each runs; where they cross and which goes
over; the colors; and how you will build it (which sample or make_ tool, or
draw_design and the curve for each cord). End with any question the person
should answer before you build. No markdown headings or bold.

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
        'name': 'tie_knot',
        'description': ('Steps to tie a knot, worked out by simulating a real cord: the cord laid out move by '
                        'move with an arrow on the working end, then drawn up, then pulled tight until it '
                        'touches itself, no gaps. Every stage is checked to be the knot asked for, from its '
                        'crossings, also as drawn in the app. Library knots by name (knot_library lists them); '
                        'any other knot from its path: rough [x, y] points from the standing end to the working '
                        'end, crossing itself where the knot does, and its over/under pattern; or the knot in '
                        'the current design (from_design, e.g. after read_tab). The knot is tightened by pulling '
                        'its two ends apart, as for stopper knots; not for loop knots (bowline) or bends that '
                        'join two cords. Saves the steps as "step 1", "step 2", ... (open them with '
                        'open_in_new_tab) and makes the tight knot the current design. Library knots take '
                        'seconds; a path or a design about half a minute.'),
        'input_schema': {'type': 'object', 'properties': {
            'knot': {'type': 'string', 'description': 'a library knot, e.g. "figure-eight", "overhand"'},
            'points': {'type': 'array', 'items': {'type': 'array', 'items': {'type': 'number'}},
                       'description': 'for a knot not in the library: its path, standing end first'},
            'pattern': {'type': 'string', 'description': 'with points: O or U for each crossing the path '
                                                         'passes, in order along it (default alternating)'},
            'from_design': {'type': 'boolean', 'description': 'tie the knot of the current design (one open '
                                                              'cord), keeping its over and under'},
            'color': {'type': 'string', 'description': 'color name or hex; default teal'},
            'width': {'type': 'number', 'description': 'cord width in px, 16-60; default 24'},
            'moves': {'type': 'integer', 'minimum': 1, 'maximum': 6,
                      'description': 'tying pictures before the knot is drawn up (default: up to 4)'}}},
    },
    {
        'name': 'knot_library',
        'description': 'The knots tie_knot knows by name: the names people use, crossings, what each is for.',
        'input_schema': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'identify_knot',
        'description': ('Which knot the current design shows, read from its strands, masks and layers the way '
                        'the app draws them: per cord its crossings and its knot type (an open cord is named '
                        'as if its ends were joined high above it, as for a tied rope). Use it to check that a '
                        'design really is the knot it should be, instead of judging by eye.'),
        'input_schema': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'check_masks',
        'description': ('Check the masks of the current design, measured with the app\'s own paths and clipping: '
                        'every mask (its two strands, which is on top, its centre, its erase boxes) and every '
                        'problem, located with canvas coordinates: a mask piece painting over a strand that should '
                        'show (covers_strand), part of a crossing showing the strand that should be under '
                        '(wrong_way), a mask covering two crossings of its strands where one should be the other way '
                        '(two_crossings), a crossing drawn the other way round from the design (wrong_crossing). '
                        'Each problem names the edit_mask call that fixes it. Changes nothing. Needed after '
                        'tie_knot (tight knots: parts touch, joints sit inside crossings) and for any crowded '
                        'design: tight knots, stretched MxN stitches, Turk\'s heads with small inner radius.'),
        'input_schema': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'edit_mask',
        'description': ('Change one mask of the current design with the app\'s own code, then check again '
                        '(identify and check_masks) and report. op: "erase" adds erase boxes, shaped by the tool '
                        'to follow a strand\'s outline; give one of: at [x, y] (a problem check_masks listed '
                        'there: just that place is erased), covers (a strand: the mask is erased where it paints '
                        'over it), around [x, y] (the mask\'s whole piece at that crossing), box ([x0, y0, x1, '
                        'y1] or four [x, y] corners) when you know the exact area. "reset" is Reset Mask (every '
                        'erase box gone). "swap" puts the other strand on top (delete and create reversed; its '
                        'erase boxes go). "delete" removes the mask. "create" masks two strands (first on top of '
                        'second). create and swap trim the new mask at once wherever it would paint the wrong '
                        'way. preview: true shows the result and the check after it without keeping it. '
                        'Otherwise the edited design becomes the current design.'),
        'input_schema': {'type': 'object', 'properties': {
            'op': {'type': 'string', 'enum': ['erase', 'reset', 'swap', 'delete', 'create']},
            'mask': {'type': 'string', 'description': 'the mask name, as check_masks lists it, e.g. "1_1_1_6"'},
            'at': {'type': 'array', 'items': {'type': 'number'},
                   'description': 'erase: [x, y] where check_masks listed a problem of this mask'},
            'covers': {'type': 'string', 'description': 'erase: the strand the mask should stop covering'},
            'around': {'type': 'array', 'items': {'type': 'number'}, 'description': 'erase: [x, y] of a crossing'},
            'box': {'type': 'array', 'description': 'erase: [x0, y0, x1, y1] or four [x, y] corners'},
            'first': {'type': 'string', 'description': 'create: the strand on top'},
            'second': {'type': 'string', 'description': 'create: the strand under it'},
            'preview': {'type': 'boolean', 'description': 'show what the edit would do, keep nothing'}},
            'required': ['op']},
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
    {
        'name': 'make_steps',
        'description': ('Turn the current design into tying steps: step k shows the cord drawn so far along its '
                        'path, every crossing with its finished over and under, and an arrow on the working end '
                        'showing where the cord goes next; the last step is the whole design. Each step is saved '
                        'as its own design ("step 1", "step 2", ...) that can open in its own tab. Default: one '
                        'step per strand, at most six.'),
        'input_schema': {'type': 'object', 'properties': {
            'count': {'type': 'integer', 'minimum': 2, 'maximum': 12, 'description': 'how many steps'},
            'arrows': {'type': 'boolean', 'description': 'arrow on the working end (default true)'},
        }},
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
        self.tab = None
        self.version = 0
        self.rendered_version = -1
        self._preview = None
        self.steps = []  # [(title, path)] from make_steps
        self.last_edit = None  # the design edit_mask made last (kept or previewed)

    def need(self):
        if self.data is None:
            raise ToolError('there is no design yet: make, draw or load one first')
        return self.data

    def store(self, data, tab=None):
        self.data = data
        self.tab = tab  # the tab this design was read from, while it is unchanged
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

    def edit_mask(self, args, store=True):
        """One mask edit on the current design: (summary, text); the edited
        design becomes the current one unless previewed (it is in last_edit)."""
        from . import identify, masks
        op = str(args.get('op') or '')
        try:
            new, done = masks.edit(self.need(), op, mask=args.get('mask'), first=args.get('first'),
                                   second=args.get('second'), box=args.get('box'), covers=args.get('covers'),
                                   around=args.get('around'), at=args.get('at'))
            found = masks.check(new)
        except masks.MaskError as e:
            raise ToolError(str(e)) from None
        preview = bool(args.get('preview'))
        if store and not preview:
            self.store(new)
        count = len(found['problems'])
        head = ('Preview, not kept: ' if preview else '') + done
        text = '\n'.join([head, 'Knot: ' + identify.summary(new), found['text']]
                         + ([] if preview else ['This is now the current design: render it and look.']))
        summary = f"{'Preview · ' if preview else ''}{done[:60]} · {count} problem{'s' if count != 1 else ''} left"
        self.last_edit = new
        return summary, text

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
        if name == 'tie_knot':
            from . import tying
            cord = None
            if args.get('from_design'):
                from . import identify
                try:
                    cord = identify.cord_of(self.need())
                except ValueError as e:
                    raise ToolError(str(e)) from None
            try:
                made = tying.tie(knot=args.get('knot') if cord is None else None, points=args.get('points'),
                                 pattern=args.get('pattern'), width=args.get('width') or tying.DEFAULT_WIDTH,
                                 color=colors.parse(args.get('color') or 'teal'), count=args.get('moves'),
                                 cord=cord)
            except (tying.TyingError, ImportError) as e:
                raise ToolError(str(e)) from None
            self.steps = []
            for number, step in enumerate(made['steps'], start=1):
                path = self.out_dir / f'step_{number}.json'
                project.write(step['data'], path)
                self.steps.append((step['title'], path))
            self.store(made['steps'][-1]['data'])
            name_ = made['knot'] or f"a knot with Alexander polynomial {made['alexander']}"
            lines = [f"{made['title']}: {name_}, {made['crossings']} crossings."]
            lines.append('Checks (knot type at each stage): ' + '; '.join(
                f"{c['stage']}: {c['knot'] or c['alexander']}" for c in made['checks']))
            if not made['ok']:
                lines.append('WARNING: not every stage is the same knot; tell the person which step is off.')
            for number, step in enumerate(made['steps'], start=1):
                lines.append(f"step {number}: {step['caption']}")
                found = step.get('masks')
                if found:
                    for text in found['fixed']:
                        lines.append(f'  masks fixed: {text}')
                    for p in found['left']:
                        lines.append(f"  masks left: {p['text']}")
                    if not found['fixed'] and not found['left']:
                        lines.append('  masks: no problems')
            lines.append(f'Saved as "step 1" to "step {len(made["steps"])}"; the current design is the tight '
                         'knot. In the app, open each step with open_in_new_tab, in order, titled by what it '
                         'does, e.g. "Step 1 · first loop".')
            return f"{made['title']} · {len(made['steps'])} steps", '\n'.join(lines)
        if name == 'check_masks':
            from . import masks
            try:
                found = masks.check(self.need())
            except masks.MaskError as e:
                raise ToolError(str(e)) from None
            count = len(found['problems'])
            return (f"{len(found['masks'])} masks · {count} problem{'s' if count != 1 else ''}", found['text'])
        if name == 'edit_mask':
            return self.edit_mask(args)
        if name == 'knot_library':
            from . import tying
            lines = [f'{title} ("{key}"): {crossings} crossings, {kind}; also called {", ".join(aliases)}. {about}'
                     for key, title, crossings, kind, aliases, about in tying.library()]
            return f'{len(lines)} knots', '\n'.join(lines)
        if name == 'identify_knot':
            from . import identify
            text = identify.summary(self.need())
            return text.splitlines()[0][:80], text
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
        if name == 'make_steps':
            from . import steps
            made = steps.make(self.need(), count=args.get('count'), arrows=args.get('arrows', True) is not False)
            self.steps = []
            for number, (title, data) in enumerate(made, start=1):
                path = self.out_dir / f'step_{number}.json'
                project.write(data, path)
                self.steps.append((title, path))
            names = ', '.join(f'step {n}' for n in range(1, len(made) + 1))
            return (f'{len(made)} steps',
                    f'made {len(made)} steps ({names}); the last is the whole design. Each can open in its own '
                    'tab with open_in_new_tab if you are running in the app.')
        if name == 'render':
            path = self.render()
            data = base64.standard_b64encode(path.read_bytes()).decode('ascii')
            return 'picture', [{'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': data}}]
        raise ToolError(f'unknown tool {name}')


class Agent:
    """Runs one request: the loop of Claude calls and tool calls."""

    def __init__(self, client, out_dir, model=DEFAULT_MODEL, on_event=None, max_rounds=24, max_cost=2.00,
                 quiet=None, web=True, effort='high', plan=False, app=None):
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
        self.plan = plan  # plan mode: research and plan, build nothing
        self.app = app  # an AppClient when the app started the agent: its tabs become tools
        self.opened_tabs = []  # titles of tabs opened by open_in_new_tab
        self.workspace = Workspace(out_dir)
        self.on_event = on_event or (lambda event: None)
        self.max_rounds = max_rounds
        self.max_cost = max_cost
        self.cost = 0.0
        self.searches = 0
        self.usage = {'input_tokens': 0, 'output_tokens': 0,
                      'cache_creation_input_tokens': 0, 'cache_read_input_tokens': 0}

    def system(self):
        from .app_tools import APP_INSTRUCTIONS
        text = (INSTRUCTIONS + (APP_INSTRUCTIONS if self.app else '') + (PLAN_INSTRUCTIONS if self.plan else '')
                + 'The guide:\n\n' + GUIDE.read_text(encoding='utf-8')
                + '\n\n' + DRAWING.read_text(encoding='utf-8'))
        return [{'type': 'text', 'text': text, 'cache_control': {'type': 'ephemeral'}}]

    def tools(self):
        from .app_tools import APP_TOOLS, LOOK_ONLY
        tools = [t for t in TOOLS if t['name'] in PLAN_TOOLS] if self.plan else list(TOOLS)
        if self.app is not None:
            tools += [t for t in APP_TOOLS if t['name'] in LOOK_ONLY] if self.plan else APP_TOOLS
        return tools + (WEB_TOOLS[self.model] if self.web else [])

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

    def run(self, prompt, images=(), start=None, history=None):
        """Build what prompt asks for. Returns the 'done' event.

        start is a project dict to begin from, such as what is on the
        person's canvas; the agent can describe, change or replace it.
        history is the session so far ([{'user', 'claude', 'design'}], oldest
        first), so the person can refer back to it; a new session sends none.
        """
        if history:
            prompt = with_history(prompt, history)
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
        from .app_tools import APP_TOOL_NAMES, AppError
        try:
            if block.name in APP_TOOL_NAMES:
                if self.app is None:
                    raise ToolError('this tool works only when OpenStrand Studio started you')
                summary, content = self.app_tool(block.name, args)
            else:
                with self.quiet():
                    summary, content = self.workspace.run(block.name, args)
        except (ToolError, AppError, ValueError, KeyError, TypeError) as e:
            message = str(e) if not isinstance(e, KeyError) else f'missing argument {e}'
            self.on_event({'type': 'tool_end', 'name': block.name, 'ok': False, 'summary': message})
            return {'type': 'tool_result', 'tool_use_id': block.id, 'content': message, 'is_error': True}
        except Exception as e:  # a crash inside the app's code: tell Claude, keep going
            message = f'{type(e).__name__}: {e}'
            self.on_event({'type': 'tool_end', 'name': block.name, 'ok': False, 'summary': message})
            return {'type': 'tool_result', 'tool_use_id': block.id, 'content': message, 'is_error': True}
        self.on_event({'type': 'tool_end', 'name': block.name, 'ok': True, 'summary': summary})
        return {'type': 'tool_result', 'tool_use_id': block.id, 'content': content}

    def app_tool(self, name, args):
        """A tool the running app does with its own code, through the bridge."""
        ws = self.workspace
        if name == 'open_in_new_tab':
            which = str(args.get('design', 'current')).strip().lower()
            title = str(args.get('title') or '').strip()[:60] or 'Claude design'
            if which in ('current', 'design', ''):
                ws.need()
                path = ws.project_path
            else:
                number = which.replace('step', '').strip()
                if not number.isdigit() or not 1 <= int(number) <= len(ws.steps):
                    raise ToolError(f'no {which}: make_steps made {len(ws.steps)} steps')
                path = ws.steps[int(number) - 1][1]
            result = self.app.call(name, {'path': str(path), 'title': title})
            if result.get('opened'):
                self.opened_tabs.append(title)
                return f'New tab · {title}', f'opened in a new tab titled "{title}"'
            return f'{title} · waiting for the person', result.get('note') or 'shown to the person to open'
        if name == 'read_tab':
            result = self.app.call(name, {'tab_id': str(args.get('tab_id', ''))})
            data = project.read(result['file'])
            ws.store(data, tab=str(args.get('tab_id', '')))
            return (f"Read tab {result.get('title', '')} · {project.summary(data)}",
                    f"tab \"{result.get('title', '')}\" is now the current design: {project.summary(data)}")
        if name == 'edit_mask_in_tab':
            return self.edit_mask_in_tab(args)
        if name in ('rename_tab', 'switch_tab'):
            call = {'tab_id': str(args.get('tab_id', ''))}
            if name == 'rename_tab':
                call['title'] = str(args.get('title') or '').strip()[:60]
            result = self.app.call(name, call)
            note = result.get('note') or 'done'
            return f"{name.replace('_', ' ').capitalize()} · {result.get('title', '')}", note
        result = self.app.call(name, {})
        tabs = result.get('tabs', [])
        return f'{len(tabs)} tabs', json.dumps(tabs)

    def edit_mask_in_tab(self, args):
        """Work the edit out on the copy read from the tab, then have the app do it there."""
        from . import masks
        ws = self.workspace
        tab = str(args.get('tab_id', ''))
        if ws.data is None or ws.tab != tab:
            raise ToolError('read_tab this tab first (and change nothing else before editing it)')
        before = ws.data
        with self.quiet():
            summary, text = ws.edit_mask(dict(args, preview=True), store=False)
        after = ws.last_edit
        call = {'tab_id': tab, 'op': args.get('op'), 'mask': args.get('mask'),
                'first': args.get('first'), 'second': args.get('second')}
        if args.get('op') == 'erase':
            call['boxes'] = _new_boxes(before, after, str(args.get('mask')))
            if not call['boxes']:
                raise ToolError('the erase added no box')
        elif args.get('op') in ('create', 'swap'):
            # The new mask is trimmed on Claude's copy: the same boxes go to the tab.
            made = (f"{args.get('first')}_{args.get('second')}" if args.get('op') == 'create'
                    else _swapped(before, str(args.get('mask'))))
            call['boxes'] = _new_boxes(before, after, made)
        result = self.app.call('edit_mask', call)
        ws.store(after, tab=tab)
        note = result.get('note') or 'done'
        return (f'In the tab · {note}',
                f"{note} in the tab (one undo step there).\n" + text.replace('Preview, not kept: ', '', 1))

    def finish(self, said, error=None):
        ws = self.workspace
        event = {'type': 'done', 'ok': error is None, 'error': error,
                 'text': said[-1] if said else '',
                 'project': str(ws.project_path) if ws.data is not None else None,
                 'png': str(ws.png_path) if ws.rendered_version == ws.version and ws.data is not None else None,
                 'cost': round(self.cost, 4), 'model': self.model, 'searches': self.searches,
                 'plan': self.plan, 'opened_tabs': self.opened_tabs, **self.usage}
        if self.plan:  # a plan builds nothing, whatever is in the workspace
            event['project'] = event['png'] = None
        if ws.tab is not None:
            # The design is the person's own tab (read, or changed in place
            # with edit_mask_in_tab): it is there already, not a new design.
            event['project'] = event['png'] = None
            event['in_tab'] = ws.tab
        self.on_event(event)
        return event


def _swapped(data, name):
    """The name a mask has once swapped: its two strands the other way round."""
    from .steps import mask_parts
    names = [s['layer_name'] for s in data['strands'] if s.get('type') != 'MaskedStrand']
    parts = mask_parts(name, names)
    return f'{parts[1]}_{parts[0]}' if len(parts) == 2 else name


def _new_boxes(before, after, name):
    """The erase boxes a mask has in after and not in before."""
    def boxes(data):
        for s in data['strands']:
            if s.get('type') == 'MaskedStrand' and s.get('layer_name') == name:
                return [{k: [float(v) for v in r[k]] for k in ('top_left', 'top_right', 'bottom_left', 'bottom_right')}
                        for r in s.get('deletion_rectangles') or [] if 'top_left' in r]
        return []
    old = boxes(before)
    return [b for b in boxes(after) if b not in old]


HISTORY_TURNS = 8


def with_history(prompt, history):
    """The request with the session's earlier turns before it, kept short."""
    lines = ['Earlier in this conversation, oldest first (the person may refer to it):']
    for turn in history[-HISTORY_TURNS:]:
        lines.append(f"- The person asked: {str(turn.get('user', ''))[:600]}")
        if turn.get('claude'):
            lines.append(f"  You answered: {str(turn['claude'])[:900]}")
        if turn.get('design'):
            lines.append(f"  The design: {turn['design']}")
    return '\n'.join(lines) + '\n\nNow the person asks:\n' + prompt


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
