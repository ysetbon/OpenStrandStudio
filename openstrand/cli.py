"""The openstrand command: python -m openstrand <command> ...

Every command prints one short line per result, or "error: ..." on stderr
with exit status 1, so a person or an agent can read the outcome directly.
"""
import argparse
import contextlib
import json
import re
import os
import sys
import time
from pathlib import Path

from . import __version__, colors, project


@contextlib.contextmanager
def quiet(enabled=True):
    """Hide the app's own console chatter (Qt, audio, debug prints) while it works."""
    if not enabled:
        yield
        return
    sys.stdout.flush()
    sys.stderr.flush()
    saved = os.dup(1), os.dup(2)
    null = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(null, 1)
        os.dup2(null, 2)
        yield
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        os.dup2(saved[0], 1)
        os.dup2(saved[1], 2)
        for fd in (*saved, null):
            os.close(fd)


def preload():
    """Load numpy for the knot tools now, before anything reads stdin. On
    Windows its DLLs look at the standard handles as they load, and wait
    for any read left on them (see AppClient)."""
    try:
        import numpy  # noqa: F401
    except ImportError:
        pass  # the knot tools say how to install it when one is used


def event_stream():
    """Where the agent's events go: the real stdout, kept apart from it. A
    tool runs inside quiet(), which points stdout at nothing to hide the
    app's chatter; its progress events must still get out while it works."""
    try:
        sys.stdout.flush()
        return os.fdopen(os.dup(sys.stdout.fileno()), 'w', encoding='utf-8', newline='\n', buffering=1)
    except (AttributeError, OSError, ValueError):  # no real stdout (a test capturing it)
        return sys.stdout


def _write_design(args, data, warnings, source, default_name):
    out = Path(args.out or default_name)
    project.write(data, out)
    origin = f' · from the published sample {source}' if source else ''
    print(f'wrote {out} · {project.summary(data)}{origin}')
    for warning in warnings:
        print('warning:', ' '.join(map(str, warning)))


def cmd_make(args):
    from . import generators
    color = colors.parse(args.color) if getattr(args, 'color', None) else None
    with quiet(not args.verbose):
        if args.design == 'turks_head':
            data, warnings, source = generators.turks_head(args.leads, args.bights, color or colors.NAMES['teal'],
                                                   width=args.width, inner=args.inner)
            name = f'turks_head_{args.leads}x{args.bights}.json'
        elif args.design == 'heart':
            data, warnings, source = generators.heart(color or colors.NAMES['crimson'], width=args.width or 26)
            name = 'heart.json'
        elif args.design == 'mxn':
            data, warnings, source = generators.mxn(args.m, args.n, args.hand, args.stretch)
            name = f"mxn_{args.hand}{'_stretch' if args.stretch else ''}_{args.m}x{args.n}.json"
        else:
            data, warnings, source = generators.sample(args.name)
            name = f'{args.name}.json'
    _write_design(args, data, warnings, source, name)


def cmd_draw(args):
    from . import draw
    text = sys.stdin.read() if args.spec == '-' else Path(args.spec).read_text(encoding='utf-8')
    try:
        spec = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f'{args.spec}: not valid JSON ({e.msg}, line {e.lineno})') from None
    with quiet(not args.verbose):
        data, report = draw.build(spec)
    out = Path(args.out or 'drawn.json')
    project.write(data, out)
    print(f'wrote {out} · {project.summary(data)}')
    print(report)


def cmd_draw_steps(args):
    """openstrand draw-steps: each step written as a project, and one picture of all of them."""
    from . import storyboard
    text = sys.stdin.read() if args.spec == '-' else Path(args.spec).read_text(encoding='utf-8')
    try:
        spec = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f'{args.spec}: not valid JSON ({e.msg}, line {e.lineno})') from None
    out = Path(args.out_dir or '.')
    with quiet(not args.verbose):
        made = storyboard.build(spec)
        paths = [project.write(step['data'], out / f'step_{n}.json') for n, step in enumerate(made, start=1)]
        sheet = None
        if not args.no_sheet:
            from . import render
            sheet = render.step_sheet([step['data'] for step in made], [step['title'] for step in made],
                                      out / 'steps.png')
    for path, step in zip(paths, made):
        print(f'wrote {path} · {step["title"]} · {project.summary(step["data"])}')
    if sheet:
        print(f'rendered {sheet} · all {len(made)} steps side by side')
    print(storyboard.summary(made))


def cmd_tie(args):
    from . import bends, tying
    if args.list:
        print('stopper knots, tied in one cord (simulated: laid out, drawn up, pulled tight):')
        for key, title, crossings, kind, aliases, about in tying.library():
            print(f'  {key:<16} {title}: {crossings} crossings, {kind}; also {", ".join(aliases)}')
        print('knots that join cords or make a loop (from a checked drawing, shown loose):')
        for key, title, kind, _, crossings, aliases, about in bends.library():
            print(f'  {key:<16} {title}: {kind}, {crossings} crossings; also {", ".join(aliases)}')
        return
    points = None
    if args.path:
        text = Path(args.path).read_text(encoding='utf-8')
        try:
            points = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f'{args.path}: not valid JSON ({e.msg}, line {e.lineno})') from None
        if isinstance(points, dict):
            args.pattern = args.pattern or points.get('pattern')
            points = points.get('points')
    if not args.knot and points is None:
        raise ValueError('name a knot (see: openstrand tie --list) or give --path with its points')
    out = Path(args.out_dir or '.')
    if args.knot and points is None and tying.find(args.knot) is None and bends.find(args.knot) is not None:
        return tie_drawn(args, out)
    if args.colors:
        raise ValueError('--colors is for a knot of several cords; use --color for a knot in one cord')
    color = colors.parse(args.color) if args.color else colors.NAMES['teal']
    with quiet(not args.verbose):
        made = tying.tie(knot=args.knot, points=points, pattern=args.pattern, width=args.width or 24,
                         color=color, count=args.moves)
    out.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r'[^a-z0-9]+', '_', made['title'].lower()).strip('_') or 'knot'
    print(f"{made['title']}: {made['knot'] or made['alexander']}, {made['crossings']} crossings")
    print('checks: ' + '; '.join(f"{c['stage']}: {c['knot'] or c['alexander']}" for c in made['checks']))
    for n, step in enumerate(made['steps'], start=1):
        path = out / f'{stem}_step_{n}.json'
        project.write(step['data'], path)
        print(f'wrote {path} · {step["caption"]}')
        for line in mask_lines(step.get('masks')):
            print('  ' + line)
    if not made['ok']:
        raise SystemExit('error: not every stage is the same knot (see the checks above)')


def cmd_recipe(args):
    """Try a knot recipe (openstrand/recipes.py): its crossings, its reference, every tying step."""
    from . import bends, recipes, render
    path = Path(args.file)
    try:
        spec = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        raise ValueError(f'{path}: not valid JSON ({e.msg}, line {e.lineno})') from None
    with quiet(not args.verbose):
        _, _, along, _ = recipes.passes(spec.get('cords') or [], str(path))
    print('crossings each cord passes, in order from its first point:')
    print(recipes.listing(spec['cords'], along))
    if args.alternate:
        with quiet(not args.verbose):
            found = recipes.alternating(spec['cords'])
        if found is None:
            raise ValueError('this drawing cannot go over, under, over along every cord: write its patterns by hand')
        print('over, under, over along every cord gives "patterns": ' + json.dumps(found))
        return
    recipe = recipes.parse(spec, str(path))
    bends.EXTRA[recipe['name']] = recipe
    out = Path(args.out_dir or path.parent)
    with quiet(not args.verbose):
        made = bends.tie(recipe['name'])
    out.mkdir(parents=True, exist_ok=True)
    print(f"{made['title']}: {bends.KINDS[made['kind']]}, {made['crossings']} crossings, "
          f"{len(made['steps'])} steps")
    for c in made['checks']:
        print(f"  {'ok  ' if c['ok'] else 'FAIL'} {c['stage']}: {c['note']}")
    pictures = []
    for n, step in enumerate(made['steps'], start=1):
        file = out / f"{recipe['name']}_step_{n}.json"
        project.write(step['data'], file)
        print(f'wrote {file} · {step["caption"]}')
        for line in mask_lines(step.get('masks')):
            print('  ' + line)
        if not args.no_pictures:
            with quiet(not args.verbose):
                pictures.append(render.render(step['data'], file.with_suffix('.png')))
    if pictures:
        sheet = out / f"{recipe['name']}_steps.png"
        _contact_sheet(pictures, sheet)
        print(f'pictures: {sheet} (every step, in order), and one PNG per step beside its project')
    if not made['ok']:
        raise SystemExit('error: FAIL: not every step is the knot (see the checks above)')
    print('PASS: the drawing passes its reference, and every step is the part of the knot it shows')


def _contact_sheet(pictures, out, size=340, columns=4):
    """Every step's picture in one, in order, each with its number."""
    from PIL import Image, ImageDraw
    rows = (len(pictures) + columns - 1) // columns
    sheet = Image.new('RGB', (min(columns, len(pictures)) * size, rows * size), 'white')
    pen = ImageDraw.Draw(sheet)
    for n, picture in enumerate(pictures):
        x, y = (n % columns) * size, (n // columns) * size
        sheet.paste(Image.open(picture).convert('RGB').resize((size, size)), (x, y))
        pen.rectangle([x, y, x + size - 1, y + size - 1], outline='#c8c8c8')
        pen.text((x + 10, y + 8), f'step {n + 1}', fill='black')
    sheet.save(out)


def tie_drawn(args, out):
    """tie for a knot that joins cords or makes a loop: its steps from the checked drawing."""
    from . import bends
    given = [c for c in (args.colors or '').split(',') if c.strip()] or ([args.color] if args.color else None)
    with quiet(not args.verbose):
        made = bends.tie(args.knot, colors=given, width=args.width)
    out.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r'[^a-z0-9]+', '_', bends.recipe_of(made['key'])['title'].lower().replace("'", '')).strip('_')
    print(f"{made['title']}: {bends.KINDS[made['kind']]}, {made['crossings']} crossings")
    print('checks: ' + bends.checked(made))
    for n, step in enumerate(made['steps'], start=1):
        path = out / f'{stem}_step_{n}.json'
        project.write(step['data'], path)
        print(f'wrote {path} · {step["caption"]}')
        for line in mask_lines(step.get('masks')):
            print('  ' + line)
    if not made['ok']:
        raise SystemExit('error: not every step is the knot (see the checks above)')


def mask_lines(found):
    """What tie's mask check fixed and left in one step, as lines."""
    if not found:
        return []
    lines = [f'masks: fixed: {text}' for text in found['fixed']]
    lines += [f"masks: left: {p['text']}" for p in found['left']]
    return lines


def cmd_masks(args):
    from . import masks
    data = project.read(args.file)
    done = None
    with quiet(not args.verbose):
        if args.repair:
            data, done, _left = masks.repair(data, create_masks=args.create)
        report = masks.check(data)
    if done is not None:
        out = Path(args.out or args.file)
        project.write(data, out)
        print(f"wrote {out} · {len(done)} fixed, {len(report['problems'])} left")
        for text in done:
            print('fixed: ' + text)
    if args.json:
        print(json.dumps({'masks': report['masks'], 'problems': report['problems']}, indent=2))
    else:
        print(report['text'])


def cmd_edit_mask(args):
    from . import identify, masks
    data = project.read(args.file)
    numbers = lambda text, what: _numbers(text, what)
    box = numbers(args.box, '--box') if args.box else None
    around = numbers(args.around, '--around') if args.around else None
    at = numbers(args.at, '--at') if args.at else None
    if box is not None and len(box) not in (4, 8):
        raise ValueError('--box is x0,y0,x1,y1 or the four corners x,y,x,y,x,y,x,y')
    if box is not None and len(box) == 8:
        box = [box[k:k + 2] for k in range(0, 8, 2)]
    if around is not None and len(around) != 2:
        raise ValueError('--around is x,y')
    if at is not None and len(at) != 2:
        raise ValueError('--at is x,y')
    with quiet(not args.verbose):
        new, done = masks.edit(data, args.op, mask=args.mask, first=args.first, second=args.second,
                               box=box, covers=args.covers, around=around, at=at, trim=not args.no_trim)
        report = masks.check(new)
        knot = identify.summary(new)
    if args.preview:
        print(f'preview (nothing written): {done}')
    else:
        out = Path(args.out or args.file)
        project.write(new, out)
        print(f'wrote {out} · {done}')
    print(knot)
    print(report['text'])


def _numbers(text, what):
    try:
        return [float(v) for v in str(text).split(',')]
    except ValueError:
        raise ValueError(f'{what} takes numbers separated by commas, like 600,400') from None


def cmd_identify(args):
    from . import identify
    data = project.read(args.file)
    with quiet(not args.verbose):
        text = identify.summary(data, unknown=True)
    print(text)


def cmd_samples(args):
    from . import generators, library
    entries = library.search(args.filter) if args.filter else library.entries()
    for entry in entries:
        print(library.line(entry, cli=True))
    names = [n for n in generators.samples() if not args.filter or args.filter.lower() in n.lower()]
    for n in names:
        print(n)
    print(f'{len(entries) + len(names)} samples', file=sys.stderr)


def cmd_info(args):
    data = project.read(args.file)
    info = project.describe(data)
    if args.json:
        print(json.dumps(info, indent=2))
        return
    print(f'file     {args.file}')
    print(f"strands  {info['strands']} (+{info['masks']} masks for over/under)")
    for n, s in info['sets'].items():
        runs = f"  {s['runs']}" if s['runs'] else ''
        print(f"set {n:<4} {s['strands']} strands  {' '.join(s['colors'])}{runs}")
    if info['groups']:
        print(f"groups   {', '.join(info['groups'])}")
    print(f"size     {info['size'][0]} x {info['size'][1]}")


def cmd_validate(args):
    from . import check
    data = project.read(args.file)
    with quiet(not args.verbose):
        found = check.problems(data)
    if found:
        for p in found:
            print('problem:', p)
        raise SystemExit(f'error: {args.file} has {len(found)} problem{"s" if len(found) != 1 else ""}')
    print(f'valid · {project.summary(data)}')


def cmd_recolor(args):
    from . import edit
    data = project.read(args.file)
    if args.colors:
        by_set = {k + 1: colors.parse(c) for k, c in enumerate(args.colors.split(','))}
    else:
        try:
            numbers = [int(n) for n in args.set.split(',')]
        except ValueError:
            raise ValueError(f'--set takes set numbers like 1 or 1,2,3, not "{args.set}"') from None
        by_set = {n: colors.parse(args.color) for n in numbers}
    edit.recolor(data, by_set)
    out = Path(args.out or args.file)
    project.write(data, out)
    left = sorted(set(project.describe(data)['sets']) - set(by_set))
    note = f" · sets {', '.join(map(str, left))} unchanged" if left else ''
    print(f"recolored {', '.join(f'set {n} → {c}' for n, c in by_set.items())}{note} · wrote {out}")


def cmd_render(args):
    from . import render
    data = project.read(args.file)
    out = Path(args.out or Path(args.file).with_suffix('.png'))
    with quiet(not args.verbose):
        render.render(data, out)
    from PyQt5.QtGui import QImage
    image = QImage(str(out))
    print(f'rendered {out} · {image.width()}x{image.height()}')


def api_key(provider='anthropic'):
    """The provider's API key: its environment variable (ANTHROPIC_API_KEY, OPENAI_API_KEY,
    XAI_API_KEY, MOONSHOT_API_KEY, DEEPSEEK_API_KEY, DASHSCOPE_API_KEY), else the one saved
    in the app's Settings > Models."""
    from . import providers
    if os.environ.get(providers.PROVIDERS[provider].env, '').strip():
        return providers.api_key(provider)  # the app passes it this way: the saved keys stay unread
    try:
        import agent_settings
        saved = agent_settings.load().get('keys', {})
    except Exception:
        saved = {}
    return providers.api_key(provider, saved)


def _anthropic():
    """The anthropic package, or an error that says how to install it for this Python."""
    install = f'"{sys.executable}" -m pip install --upgrade "anthropic>=2.4"'
    try:
        import anthropic
    except ImportError:
        raise ValueError(f'the anthropic package is not installed for this Python; install it with: {install}') from None
    version = tuple(int(p) for p in anthropic.__version__.split('.')[:2] if p.isdigit())
    if version < (2, 4):
        raise ValueError(f'anthropic {anthropic.__version__} is too old (needs 2.4 or newer); '
                         f'upgrade it with: {install}')
    return anthropic


def cmd_agent(args):
    from . import providers
    try:  # the app's settings, when the app is here: they decide what this command may do
        import agent_settings
    except ImportError:
        agent_settings = None
    # The agent turned off in the app (Settings > Models): this command does nothing at all,
    # before any package is loaded, any key read or any model looked up.
    providers.check_allowed(None)
    anthropic = _anthropic()
    from . import agent
    try:  # the models Settings > Models offers: the built-in ones and what Refresh models found
        providers.use_catalog(agent_settings.catalog())
    except Exception:
        pass
    model = providers.resolve(args.model)
    provider = providers.provider_of(model)
    providers.check_allowed(provider.key)  # Settings > Models may forbid it: then nothing is sent
    client = providers.client_for(model, api_key(provider.key))
    start = project.read(args.start) if args.start else None
    for image in args.image or []:
        if not Path(image).is_file():
            raise ValueError(f'{image}: no such image')
    out_dir = Path(args.out_dir or 'designs')
    if not args.max_cost > 0:
        raise ValueError('--max-cost must be more than 0')
    app = None
    events = event_stream()
    out_dir.mkdir(parents=True, exist_ok=True)
    from .debuglog import Log
    log = Log(out_dir / 'agent.log', to_stderr=args.log)
    log(f'agent starts: model {model}, effort {args.effort}, web {not args.no_web}, plan {args.plan}, '
        f'app {args.app}, max ${args.max_cost:.2f}, folder {out_dir.resolve()}')
    log(f'python {sys.version.split()[0]} on {sys.platform}, {sys.executable}')
    if args.app:  # started by OpenStrand Studio: its tabs are tools, answered on stdin
        began = time.monotonic()
        preload()
        log(f'numpy loaded in {time.monotonic() - began:.1f}s (before stdin is read)')
        from .app import AppClient
        args.json_events = True
        app = AppClient(lambda e: agent.print_events(e, True, out=events), log=log)
    runner = agent.Agent(client, out_dir, model=model, max_cost=args.max_cost, web=not args.no_web,
                         effort=args.effort, plan=args.plan, app=app,
                         on_event=lambda e: agent.print_events(e, args.json_events, out=events),
                         quiet=lambda: quiet(not args.verbose), log=log)
    try:
        history = json.loads(Path(args.history).read_text(encoding='utf-8')) if args.history else None
        result = runner.run(args.prompt, images=args.image or [], start=start, history=history)
    except (anthropic.AuthenticationError, anthropic.PermissionDeniedError):
        raise ValueError(f'the {provider.name} API key was refused: check it in Settings > Models') from None
    except anthropic.APIConnectionError as e:
        if isinstance(e.__cause__, providers.UnsafeRequest):  # stopped before it left: say why
            raise ValueError(str(e.__cause__)) from None
        raise ValueError(f'cannot reach the {provider.name} API: check the internet connection') from None
    except anthropic.RateLimitError:
        raise ValueError(f'the {provider.name} API is busy (rate limit): try again in a minute') from None
    except anthropic.APIStatusError as e:
        raise ValueError(f'the {provider.name} API returned {e.status_code}: {e.message}') from None
    except providers.ProviderError as e:
        if e.status_code in (401, 403):
            raise ValueError(f'the {provider.name} API key was refused ({e.message}): check it in '
                             'Settings > Models') from None
        raise ValueError(str(e)) from None

    if not result['ok']:
        raise SystemExit(1)  # the 'done' event already said why


def build_parser():
    """The command line: one sub-command per tool (make, draw, tie, masks, agent, render...),
    each with its options and the function that runs it."""
    p = argparse.ArgumentParser(prog='openstrand', description='Make, check, recolor and render OpenStrand Studio projects.')
    p.add_argument('--version', action='version', version=f'openstrand {__version__}')
    sub = p.add_subparsers(dest='command', required=True, metavar='command')

    def command(name, help_text, func):
        c = sub.add_parser(name, help=help_text, description=help_text)
        c.add_argument('--verbose', action='store_true', help="show the app's own console output")
        c.set_defaults(func=func)
        return c

    make = command('make', 'make a new design and save it as a project file', cmd_make)
    designs = make.add_subparsers(dest='design', required=True, metavar='design')
    t = designs.add_parser('turks_head', help="a Turk's head ring knot")
    t.add_argument('--leads', type=int, required=True, help='turns around the ring (2-7)')
    t.add_argument('--bights', type=int, required=True, help='loops on the rim (2-13), no common factor with leads')
    t.add_argument('--color', help='name or hex (default teal)')
    t.add_argument('--width', type=int, help='cord width in px')
    t.add_argument('--inner', type=int, help='inner radius in px (outer is 290)')
    h = designs.add_parser('heart', help='a ribbon heart from one cord')
    h.add_argument('--color', help='name or hex (default crimson)')
    h.add_argument('--width', type=int, help='cord width in px (default 26)')
    x = designs.add_parser('mxn', help='an MxN stitch: m vertical and n horizontal ribbons')
    x.add_argument('--m', type=int, required=True, help='vertical ribbons (1-8)')
    x.add_argument('--n', type=int, required=True, help='horizontal ribbons (1-8)')
    x.add_argument('--hand', choices=['lh', 'rh'], default='lh', help='left or right hand (default lh)')
    x.add_argument('--stretch', action='store_true', help='the stretched variant, ribbons packed closer')
    s = designs.add_parser('sample', help='a ready-made design by name (see: openstrand samples)')
    s.add_argument('name')
    for d in (t, h, x, s):
        d.add_argument('--out', help='project file to write (default: a name from the design)')
        d.add_argument('--verbose', action='store_true', help=argparse.SUPPRESS)

    recipe = command('recipe', 'try a knot recipe of the craft library: its crossings, its reference and every '
                               'tying step, with pictures', cmd_recipe)
    recipe.add_argument('file', help='the recipe, a JSON file (see openstrand/recipes.py)')
    recipe.add_argument('--out-dir', help='folder for the step projects and pictures (default: beside the recipe)')
    recipe.add_argument('--alternate', action='store_true',
                        help='only list the crossings and print the patterns that go over, under, over')
    recipe.add_argument('--no-pictures', action='store_true', help='do not render the steps')

    drawn = command('draw', 'draw a design from your own cords (points, x(t)/y(t) curves or shapes)', cmd_draw)
    drawn.add_argument('spec', help='a JSON file with {"cords": [...]}, or - to read it from stdin')
    drawn.add_argument('--out', help='project file to write (default drawn.json)')

    steps = command('draw-steps', 'draw a tutorial step by step: each step its own picture, with hooks, '
                                  'needles and arrows', cmd_draw_steps)
    steps.add_argument('spec', help='a JSON file with {"steps": [{"title", "keep", "cords", "arrows"}, ...]}, '
                                    'or - to read it from stdin')
    steps.add_argument('--out-dir', help='folder for step_1.json, step_2.json, ... and steps.png (default: here)')
    steps.add_argument('--no-sheet', action='store_true', help='do not render steps.png, the picture of all steps')

    tie = command('tie', 'tying steps for a knot, each checked to be that knot: stopper knots simulated with a '
                         'real cord, bends and loop knots from a checked drawing', cmd_tie)
    tie.add_argument('knot', nargs='?', help='a library knot, e.g. figure-eight, bowline, "square knot" (see --list)')
    tie.add_argument('--list', action='store_true', help='list the library knots')
    tie.add_argument('--path', help='a JSON file with the path of a knot not in the library: '
                                    '[[x, y], ...] or {"points": [...], "pattern": "OUOU..."}')
    tie.add_argument('--pattern', help='over (O) / under (U) at each crossing along the path (default alternating)')
    tie.add_argument('--color', help='name or hex (default teal)')
    tie.add_argument('--colors', help='a knot of several cords: one color per cord, e.g. teal,gold')
    tie.add_argument('--width', type=float, help='cord width in px: 16-60 for a knot in one cord (default 24), '
                                                 '14-30 for a knot of several cords')
    tie.add_argument('--moves', type=int, help='tying pictures before the knot is drawn up (default up to 4)')
    tie.add_argument('--out-dir', help='folder for the step files (default: here)')

    masks_cmd = command('masks', "list a project's masks and what is wrong with them, with coordinates", cmd_masks)
    masks_cmd.add_argument('file')
    masks_cmd.add_argument('--repair', action='store_true',
                           help='fix what is safe (erase a mask where it hides a strand that should show)')
    masks_cmd.add_argument('--create', action='store_true',
                           help='with --repair, also make masks the design calls for')
    masks_cmd.add_argument('--out', help='with --repair, write here instead of changing the file')
    masks_cmd.add_argument('--json', action='store_true', help='print the masks and problems as JSON')

    edit_mask = command('edit-mask', "change one mask with the app's own code, then check again", cmd_edit_mask)
    edit_mask.add_argument('file')
    edit_mask.add_argument('op', choices=['erase', 'reset', 'swap', 'delete', 'create'])
    edit_mask.add_argument('--mask', help='the mask (as "openstrand masks" lists it)')
    edit_mask.add_argument('--at', help='erase: the place x,y where "openstrand masks" listed a problem of it')
    edit_mask.add_argument('--covers', help='erase: where the mask paints over this strand')
    edit_mask.add_argument('--around', help='erase: the mask\'s piece at the crossing nearest x,y')
    edit_mask.add_argument('--box', help='erase: x0,y0,x1,y1 or four corners x,y,x,y,x,y,x,y')
    edit_mask.add_argument('--first', help='create: the strand on top')
    edit_mask.add_argument('--second', help='create: the strand under it')
    edit_mask.add_argument('--no-trim', action='store_true',
                           help='create, swap: keep the new mask whole (by default it is erased where it would '
                                'paint the wrong way)')
    edit_mask.add_argument('--preview', action='store_true', help='show the result, write nothing')
    edit_mask.add_argument('--out', help='write here instead of changing the file')

    identify_cmd = command('identify', 'which knot a project shows, read from its strands and masks', cmd_identify)
    identify_cmd.add_argument('file')

    samples = command('samples', 'list the ready-made designs', cmd_samples)
    samples.add_argument('filter', nargs='?', help='a craft or any name people use (boondoggle, "cobra knot"), or part of a file name')

    info = command('info', 'describe a project: sets, colors, strands, size', cmd_info)
    info.add_argument('file')
    info.add_argument('--json', action='store_true', help='print the description as JSON')

    validate = command('validate', "load a project with the app's loader and report problems", cmd_validate)
    validate.add_argument('file')

    recolor = command('recolor', 'change the color of one set or of every set', cmd_recolor)
    recolor.add_argument('file')
    which = recolor.add_mutually_exclusive_group(required=True)
    which.add_argument('--colors', help='one color per set in order, e.g. red,gold')
    which.add_argument('--set', help='the sets to recolor with --color, e.g. 1 or 1,2,3')
    recolor.add_argument('--color', help='the color for --set')
    recolor.add_argument('--out', help='write here instead of changing the file')

    agent_cmd = command('agent', 'ask the OpenStrand agent to build or change a design (needs an API key for the model)', cmd_agent)
    agent_cmd.add_argument('prompt', help='what to make, in plain words')
    agent_cmd.add_argument('--image', action='append',
                           help='a reference image (PNG, JPEG, GIF, WebP); repeat it for more, up to 10 with one '
                                'request (6 with haiku)')
    agent_cmd.add_argument('--model', default='sonnet',
                           help='a model id or alias: sonnet (Claude Sonnet 5.5, default), haiku, gpt (GPT-6.1 Terra), '
                                'gpt-6.1-sol, gpt-6-astra, grok (Grok 4.7), kimi (Kimi K3.1 Pro), deepseek '
                                '(DeepSeek V4.1 Flash), qwen (Qwen3.8 Max); each provider\'s key comes from its '
                                'environment variable or Settings > Models')
    agent_cmd.add_argument('--start', help='a project to start from, such as the current canvas')
    agent_cmd.add_argument('--out-dir', help='folder for design.json and design.png (default designs/)')
    agent_cmd.add_argument('--max-cost', type=float, default=2.00, help='stop when one request has cost this many USD (default 2.00)')
    agent_cmd.add_argument('--no-web', action='store_true', help='do not let the agent search or read the web')
    agent_cmd.add_argument('--effort', default='high', choices=['low', 'medium', 'high', 'xhigh', 'max'],
                           help='how hard the model thinks (default high; higher costs more)')
    agent_cmd.add_argument('--history', help="the session so far, a JSON list of {user, agent, design}")
    agent_cmd.add_argument('--app', action='store_true',
                           help="started by OpenStrand Studio: its tabs become tools, answered on stdin")
    agent_cmd.add_argument('--plan', action='store_true',
                           help='plan mode: research and write a plan, build nothing')
    agent_cmd.add_argument('--json-events', action='store_true', help='print one JSON event per line (for the app)')
    agent_cmd.add_argument('--log', action='store_true',
                           help="print the step-by-step log on stderr (it is always in the folder's agent.log)")

    render = command('render', "draw a project to PNG with the app's real canvas", cmd_render)
    render.add_argument('file')
    render.add_argument('--out', help='PNG to write (default: the project name with .png)')
    return p


def main(argv=None):
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == 'recolor' and args.set is not None and not args.color:
        parser.error('recolor --set needs --color')
    try:
        args.func(args)
    except ValueError as e:
        print(f'error: {e}', file=sys.stderr)
        return 1
    except SystemExit as e:
        if isinstance(e.code, str):
            print(e.code, file=sys.stderr)
            return 1
        raise
    return 0
