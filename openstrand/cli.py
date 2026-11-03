"""The openstrand command: python -m openstrand <command> ...

Every command prints one short line per result, or "error: ..." on stderr
with exit status 1, so a person or an agent can read the outcome directly.
"""
import argparse
import contextlib
import json
import os
import sys
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


def cmd_samples(args):
    from . import generators
    names = [n for n in generators.samples() if not args.filter or args.filter.lower() in n.lower()]
    for n in names:
        print(n)
    print(f'{len(names)} samples', file=sys.stderr)


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


def build_parser():
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

    samples = command('samples', 'list the ready-made designs', cmd_samples)
    samples.add_argument('filter', nargs='?', help='only names containing this text')

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
