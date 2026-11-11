"""Knots as a person ties them: laid out loose, tied move by move, pulled tight.

A knot comes from a recipe: a rough path for the cord, from its standing end
to its working end, and whether the cord goes over (O) or under (U) at each
crossing it passes on the way. The library has the common stopper knots; any
other knot can be given as a path. Nothing is guessed afterwards:

- the knot the path makes is worked out from its crossings (invariants) and
  checked against the knot asked for;
- simulate.tighten() lays the path out evenly (a cord a few widths thick,
  pulled until it touches itself) and then pulls it tight with the real
  width. The cord never passes through itself, so every stage is the same
  knot, and the checks say so.

tie() gives the steps a tutorial needs: the cord laid move by move with an
arrow on the working end, then drawn up, then pulled tight, each a full
OpenStrand design (draw.build, over and under from the cord's heights).

    from openstrand import tying
    made = tying.tie('figure-eight', color='teal')
    for step in made['steps']:
        print(step['title'], step['caption'])
"""
import json
import math
import re
from pathlib import Path

import numpy as np

from . import draw, invariants, simulate
from .progress import picture as picture_of

LOOSE = 2.6          # widths between parts of a knot laid out loose
TAIL = 4.0           # widths of tail shown beyond the knot
MAX_MOVES = 4        # tying pictures before the knot is drawn up
CENTRE = (600.0, 400.0)
DEFAULT_WIDTH = 24
MIN_WIDTH = 16
SHAPES = Path(__file__).with_name('knot_shapes.json')
# A path whose crossings lie further apart along it than OVERSIZED widths (the
# median) is shrunk to SPACED first, a laid-out knot's spacing (5 to 6.5), never
# bringing two crossings closer than CLOSEST widths (see compact_scale).
OVERSIZED = 13.0
SPACED = 6.5
CLOSEST = 4.0
# Pulled tight, a knot has jammed once two of its crossings come nearer than
# this many widths (see simulate.tighten): the overhand, figure-eight and
# stevedore never get there (their crossings stay 1.1 widths apart and more
# while they are pulled), the twisted legs of a double or triple overhand do.
JAMMED = 0.85
# For the progress bar: the steps the two simulations usually take, the share
# of the simulation's time the loose layout takes, and the share of a whole
# tie() the simulation takes when there is one (drawing the steps is the rest).
LAYOUT_STEPS, TIGHTEN_STEPS, LAYOUT_SHARE = 400, 200, 0.75
SIMULATION_SHARE = 0.7

# The knots people tie in one cord, as 4-plats (see plat_layout). An overhand
# knot is a loop with the end passed through it; pass the end through again
# and its two legs twist round each other once more: the overhand, double and
# triple overhand are the two legs of a loop twisted 3, 5 and 7 half turns
# (the knots 3_1, 5_1 and 7_1, word 2 repeated). The figure-eight and the
# stevedore are twist knots instead: a clasp and 2 or 4 half twists (4_1, 6_1).
LIBRARY = {
    'overhand': dict(
        title='Overhand knot', word=(2, 1, 2), aliases=('thumb knot', 'simple knot', 'single knot'),
        about='The simplest stopper: a loop with the end passed through it once. Jams when loaded.'),
    'figure-eight': dict(
        title='Figure-eight knot', word=(2, 1, 2, 2), aliases=('figure 8', 'figure of eight', 'flemish knot',
                                                               'savoy knot', 'eight knot'),
        about='Stopper that is easy to untie after loading; the base of the figure-eight loop and bend.'),
    'double overhand': dict(
        title='Double overhand knot', word=(2, 2, 2, 2, 2), aliases=('double knot', 'double overhand stopper'),
        about='An overhand with the end passed through the loop twice: a bulkier stopper.'),
    'stevedore': dict(
        title='Stevedore knot', word=(2, 1, 1, 1, 2, 2), aliases=('stevedore stopper',),
        about='A figure-eight with an extra turn round the standing part: bulky, still easy to untie.'),
    'triple overhand': dict(
        title='Triple overhand knot', word=(2, 2, 2, 2, 2, 2, 2), aliases=('triple knot',),
        about='An overhand with three passes through the loop: a large, round stopper.'),
}


class TyingError(ValueError):
    """A knot that cannot be tied as asked; the message says what to change."""


# ------------------------------------------------------------- the library
def find(name):
    """The library key for a knot name or alias, or None."""
    key = re.sub(r'[^a-z0-9]+', ' ', str(name or '').lower()).strip()
    key = re.sub(r'\b(knot|stopper)\b', '', key).strip() or key
    for k, recipe in LIBRARY.items():
        names = [k, recipe['title']] + list(recipe['aliases'])
        for n in names:
            m = re.sub(r'[^a-z0-9]+', ' ', n.lower()).strip()
            if key in (m, re.sub(r'\b(knot|stopper)\b', '', m).strip()):
                return k
    return None


def library():
    """[(key, title, crossings, knot name, aliases, about)] for every library knot."""
    out = []
    for key, recipe in LIBRARY.items():
        n = len(recipe['word'])
        out.append((key, recipe['title'], n, _knot_of(key), recipe['aliases'], recipe['about']))
    return out


def _knot_of(key):
    return {'overhand': 'trefoil (3_1)', 'figure-eight': 'figure-eight (4_1)', 'double overhand': 'cinquefoil (5_1)',
            'stevedore': '6_1', 'triple overhand': '7_1'}[key]


def plat_layout(word, unit=DEFAULT_WIDTH):
    """A rough path for the knot whose 4-plat is word (generators 1-3, each
    swapping two neighbouring columns), opened at its lower left cap into a
    standing end on the left and a working end on the right."""
    col = row = 3.5 * unit
    xs = [(c - 1.5) * col for c in range(4)]
    ys = [row * r for r in range(len(word) + 1)]
    pos = list(range(4))
    tracks = [[(xs[c], ys[0])] for c in range(4)]
    for g in word:
        i = int(g) - 1
        if not 0 <= i <= 2:
            raise TyingError('plat generators are 1, 2 or 3')
        pos = [i + 1 if p == i else i if p == i + 1 else p for p in pos]
        for t in range(4):
            tracks[t].append((xs[pos[t]], ys[len(tracks[t])]))
    cap = {0: 1, 1: 0, 2: 3, 3: 2}
    ends = {pos[t]: t for t in range(4)}
    walk, t, down = [], 0, True
    for _ in range(8):
        if down:
            walk.append(('down', t))
            walk.append(('bottom', pos[t], cap[pos[t]]))
            t, down = ends[cap[pos[t]]], False
        else:
            walk.append(('up', t))
            walk.append(('top', t, cap[t]))
            t, down = cap[t], True
        if t == 0 and down:
            break
    if sum(1 for w in walk if w[0] in ('up', 'down')) != 4:
        raise TyingError('this plat closes into more than one cord: it is a link, not a knot')
    k = next(i for i, w in enumerate(walk) if w[0] == 'bottom' and {w[1], w[2]} == {0, 1})
    walk = walk[k + 1:] + walk[:k]
    pts = []
    for w in walk:
        if w[0] == 'down':
            piece = tracks[w[1]]
        elif w[0] == 'up':
            piece = tracks[w[1]][::-1]
        else:
            a, b = xs[w[1]], xs[w[2]]
            y = ys[0] if w[0] == 'top' else ys[-1]
            out = -1 if w[0] == 'top' else 1
            piece = [(a + (b - a) * 0.1, y + out * 0.55 * row), ((a + b) / 2, y + out * 0.85 * row),
                     (b + (a - b) * 0.1, y + out * 0.55 * row)]
        for p in piece:
            if not pts or math.dist(pts[-1], p) > 1e-6:
                pts.append(p)
    start, end = pts[0], pts[-1]
    if start[0] > end[0]:
        pts.reverse()
        start, end = end, start
    low = ys[-1] + 0.95 * row
    pts = ([(xs[0] - 7 * unit, low), (start[0] - 0.6 * unit, ys[-1] + 0.6 * row)] + pts
           + [(end[0] + 0.6 * unit, ys[-1] + 0.6 * row), (xs[3] + 7 * unit, low)])
    return [list(p) for p in pts]


def alternating(points):
    """Over, under, over... along the cord: the pattern that makes the fewest
    crossings show the knot (every library knot is alternating)."""
    n = len(invariants.crossings([_dense(points)], [False]))
    return 'OU' * n


# ------------------------------------------------------------------ shapes
def _dense(points, spacing=4.0):
    from sample_geometry import spline
    return np.array(spline([tuple(p[:2]) for p in points], spacing=spacing))


def shapes(points, pattern, width, expect=None, cord=None, progress=None):
    """Lay a rough path out loose, then pull it tight: (loose, history, tight, checks).
    cord: a ready path of (x, y, height) instead of points and pattern.
    progress(fraction, stage, cords) hears how far it has got: stage
    'lay_out' or 'tighten', cords a function giving the cords then."""
    rough = _rough(points, pattern, width, cord)
    knot = invariants.describe(rough)
    if expect is not None and tuple(knot['alexander']) != tuple(expect):
        raise TyingError(f"the path makes {knot['knot'] or 'a knot with Alexander polynomial ' + str(knot['alexander'])}, "
                         'not the knot asked for')
    scale = compact_scale(rough, width)
    if scale < 1:
        try:
            return _lay_out(_rough(points, pattern, width, cord, scale), width, knot, progress)
        except (TyingError, simulate.SimulationError):
            pass        # the smaller path would not lay out: the path as given, as before
    return _lay_out(rough, width, knot, progress)


def _rough(points, pattern, width, cord=None, scale=1.0):
    """The path as (x, y, height) every 4 px, over and under as heights;
    scale (< 1) shrinks it about its middle first."""
    if cord is not None:
        rough = simulate.resample(_scaled(np.asarray(cord, dtype=float), scale), 4.0)
        rough[:, 2] = np.sign(rough[:, 2]) * np.minimum(np.abs(rough[:, 2]), 1.0) * simulate.LEVEL * width
        return rough
    poly = _dense(_scaled(np.asarray(points, dtype=float)[:, :2], scale).tolist())
    z, _ = simulate.heights_from_pattern(poly, pattern, width)
    return np.c_[poly, z]


def _scaled(path, scale):
    if scale == 1:
        return path
    out = np.array(path, dtype=float)
    middle = (out[:, :2].min(0) + out[:, :2].max(0)) / 2
    out[:, :2] = middle + (out[:, :2] - middle) * scale
    return out


def compact_scale(rough, width):
    """How much to shrink an oversized path before laying it out: 1.0 for a
    path of the right size.

    Paths often come in canvas pixels, with loops many cord widths across. Laying
    such a path out pulls a huge loop in by a fraction of a pixel a step, for
    thousands of steps (minutes), and still leaves it sprawling. Scaling never
    changes the knot, and the loose layout respaces the cord anyway, so a
    path whose crossings lie much further apart along it than a laid-out knot's
    is shrunk to that spacing first; never so far that two crossings come
    closer than CLOSEST widths."""
    coarse = simulate.resample(np.asarray(rough, dtype=float), width / 2)
    passes = sorted(p for c in invariants.crossings([coarse[:, :2]], [False]) for p in c['positions'])
    if len(passes) < 2:
        return 1.0
    gaps = np.diff(passes) / width
    median = float(np.median(gaps))
    if median <= OVERSIZED:
        return 1.0
    return min(1.0, max(SPACED / median, CLOSEST / max(float(gaps.min()), 1e-9)))


def _lay_out(rough, width, knot, progress=None):
    pulls = [(0, 0, (-1, 0)), (0, 1, (1, 0))]
    lay = pull = None
    if progress is not None:
        lay = lambda f, cords: progress(LAYOUT_SHARE * f, 'lay_out', cords)
        pull = lambda f, cords: progress(LAYOUT_SHARE + (1 - LAYOUT_SHARE) * f, 'tighten', cords)
    loose, info = simulate.tighten([rough], width * LOOSE, pulls, grow_from=width, max_steps=1500,
                                   progress=lay, expected=LAYOUT_STEPS)
    tight, tinfo = simulate.tighten(loose, width, pulls, max_steps=2500, progress=pull, expected=TIGHTEN_STEPS,
                                    closest=JAMMED)
    checks = []
    for label, cord in (('laid out', loose[0]), ('pulled tight', tight[0])):
        d = invariants.describe(cord)
        checks.append(dict(stage=label, crossings=d['crossings'], alexander=d['alexander'], knot=d['knot']))
        if tuple(d['alexander']) != tuple(knot['alexander']):
            raise TyingError(f'the knot changed when {label}: the simulation let the cord pass through itself')
    return loose[0], tinfo['history'], tight[0], dict(knot=knot, checks=checks, tight=tinfo, loose=info)


def library_shapes(key, width):
    """Loose, snug and tight cords of a library knot at this width: from the
    shapes shipped with the package (made by scripts/build_knot_shapes.py),
    scaled, or worked out now when missing."""
    try:
        stored = json.loads(SHAPES.read_text(encoding='utf-8')).get(key)
    except (OSError, ValueError):
        stored = None
    if stored:
        scale = lambda c: np.array(c, dtype=float) * width
        return scale(stored['loose']), scale(stored['snug']), scale(stored['tight'])
    recipe = LIBRARY[key]
    loose, history, tight, _ = shapes(plat_layout(recipe['word'], width), 'OU' * len(recipe['word']), width)
    return loose, _snug(history, tight), tight


def _snug(history, tight, fraction=0.55):
    """The cord part of the way from laid out to tight, by length given up."""
    if not history:
        return tight
    start, end = history[0][0], simulate.length(tight)
    target = start - fraction * (start - end)
    return min(history, key=lambda h: abs(h[0] - target))[1][0]


# ------------------------------------------------------------------ frames
def _arc(cord):
    return np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(cord[:, :2], axis=0).T))])


def _passes(cord):
    """Crossing passes along the cord: (position, crossing, first time there, over)."""
    found = invariants.crossings([cord], [False])
    out = []
    for k, c in enumerate(found):
        for side in (0, 1):
            out.append((c['positions'][side], k, c['over'] == side))
    out.sort()
    seen, passes = set(), []
    for s, k, over in out:
        passes.append((s, k, k not in seen, over))
        seen.add(k)
    return passes, found


def _cut(cord, lo, hi):
    """The part of the cord between arc positions lo and hi, ends interpolated."""
    s = _arc(cord)
    lo, hi = max(lo, 0.0), min(hi, s[-1])
    inside = (s > lo) & (s < hi)
    first = np.array([np.interp(lo, s, cord[:, k]) for k in range(cord.shape[1])])
    last = np.array([np.interp(hi, s, cord[:, k]) for k in range(cord.shape[1])])
    return np.vstack([first, cord[inside], last])


def _trimmed(cord, width, tail=TAIL):
    passes, _ = _passes(cord)
    if not passes:
        return cord
    return _cut(cord, passes[0][0] - tail * width, passes[-1][0] + tail * width)


def _centred(cords, centre=CENTRE):
    pts = np.vstack([c[:, :2] for c in cords])
    mid = (pts.min(0) + pts.max(0)) / 2
    shift = np.array([centre[0] - mid[0], centre[1] - mid[1], 0.0])
    return [c + shift for c in cords]


def _who(position, total):
    if position < total * 0.25:
        return 'the standing part'
    return 'the cord laid before'


def moves(loose, width, count=None):
    """Where each tying move ends along the loose cord, with what it does.

    A move ends just after the working end crosses a part already laid; with
    more such crossings than MAX_MOVES they are grouped."""
    passes, _ = _passes(loose)
    actions = [p for p in passes if not p[2]]
    if not actions:
        raise TyingError('the cord never crosses itself: there is no knot to tie')
    count = min(count or MAX_MOVES, len(actions))
    groups = [list(g) for g in np.array_split(np.arange(len(actions)), count)]
    first_of = {k: s for s, k, first, _ in passes if first}
    total = _arc(loose)[-1]
    out = []
    for n, g in enumerate(groups):
        acts = [actions[i] for i in g]
        words = []
        for s, k, _, over in acts:
            words.append(f"{'over' if over else 'under'} {_who(first_of[k], total)}")
        what = ', then '.join(words)
        out.append(dict(until=acts[-1][0] + 1.6 * width, caption=f'Take the working end {what}.'))
    return out


def frames(loose, snug, tight, width, count=None, titles=None):
    """[(title, caption, cord, tip)] for the tutorial: tying moves, drawn up, tight.
    tip is where the arrow goes (the working end), or None."""
    loose = _trimmed(loose, width)
    plan = moves(loose, width, count)
    passes, _ = _passes(loose)
    out = []
    for n, move in enumerate(plan, start=1):
        last = n == len(plan)
        cord = loose if last else _cut(loose, 0.0, move['until'])
        caption = move['caption']
        if n == 1:
            caption = 'Lay the cord out and ' + caption[0].lower() + caption[1:]
        out.append((f'Step {n}', caption, cord, None if last else cord[-1, :2]))
    out.append((f'Step {len(out) + 1}', 'Draw the knot up: pull both ends a little at a time, keeping its shape.',
                _trimmed(snug, width), None))
    out.append((f'Step {len(out) + 1}', 'Pull both ends hard: the knot is tight when the cord jams against itself.',
                _trimmed(tight, width), None))
    if titles:
        out = [(t or o[0], o[1], o[2], o[3]) for t, o in zip(list(titles) + [None] * len(out), out)]
    return out


# ----------------------------------------------------------------- designs
def design(cord, width, color, name):
    cord = np.asarray(cord, dtype=float)
    kept = [cord[0]]
    for p in cord[1:]:                  # draw wants points at least a pixel apart
        if math.dist(p[:2], kept[-1][:2]) >= 2.0:
            kept.append(p)
    if math.dist(cord[-1][:2], kept[-1][:2]) > 0:
        if len(kept) > 1 and math.dist(cord[-1][:2], kept[-1][:2]) < 2.0:
            kept[-1] = cord[-1]
        else:
            kept.append(cord[-1])
    cord = np.array(kept)
    step = max(1, int(math.ceil(len(cord) / 380)))
    picked = cord[::step]
    if step > 1 and not np.allclose(picked[-1], cord[-1]):
        picked = np.vstack([picked[:-1], cord[-1]]) if math.dist(picked[-1][:2], cord[-1][:2]) < 2.0 \
            else np.vstack([picked, cord[-1]])
    return {'name': name, 'cords': [{'points': np.round(picked[:, :2], 2).tolist(),
                                     'heights': np.round(picked[:, 2], 3).tolist(),
                                     'width': width, 'color': color, 'label': 'Cord'}]}


def _arrow(data, tip):
    """An arrow on the strand that ends at the working end."""
    best = None
    for s in data['strands']:
        if s['type'] == 'MaskedStrand':
            continue
        for side, key in ((1, 'end'), (0, 'start')):
            d = math.dist((s[key]['x'], s[key]['y']), tip)
            if best is None or d < best[0]:
                best = (d, s, side)
    if best is None:
        return
    _, s, side = best
    s['end_arrow_visible' if side else 'start_arrow_visible'] = True
    circles = list(s.get('has_circles', [False, False]))
    circles[side] = False
    s['has_circles'] = circles


def tie(knot=None, points=None, pattern=None, width=DEFAULT_WIDTH, color='#d97757', count=None,
        titles=None, expect=None, build=True, cord=None, progress=None):
    """The steps to tie a knot: from the library by name, or from a rough path.

    Returns dict(title, knot, alexander, crossings, checks, steps) with
    steps [dict(title, caption, data, report)] (data is None when build is
    False). expect (Alexander coefficients) makes a path that turns out to
    be another knot an error. progress (see openstrand.progress) hears how
    far it has got, with a picture of the cord: laid out and pulled tight in
    the simulation, then each step as it is drawn."""
    width = float(width)
    tell = progress or (lambda *a, **k: None)
    picture = lambda get: lambda: picture_of(get(), width, color)    # made only when a picture is due
    drawn_from = 0.0
    if not MIN_WIDTH <= width <= draw.WIDTH_RANGE[1]:
        raise TyingError(f'width must be between {MIN_WIDTH} and {draw.WIDTH_RANGE[1]} px: a tight knot in a '
                         'thinner cord is too fine for its strands to follow')
    if knot is not None and points is None and cord is None:
        key = find(knot)
        if key is None:
            names = ', '.join(r['title'] for r in LIBRARY.values())
            raise TyingError(f'"{knot}" is not in the knot library ({names}). Give its path as points '
                             '(standing end first) with its over/under pattern instead.')
        recipe = LIBRARY[key]
        loose, snug, tight = library_shapes(key, width)
        d = invariants.describe(tight)
        checks = [dict(stage=label, **_check(c)) for label, c in (('laid out', loose), ('drawn up', snug),
                                                                  ('pulled tight', tight))]
        title = recipe['title']
    else:
        if cord is None and (not isinstance(points, list) or len(points) < 4):
            raise TyingError('points: the path of the cord, at least 4 [x, y] points from the standing end')
        if cord is None:
            pattern = pattern or alternating(points)
        simulated = None
        if progress is not None:
            drawn_from = SIMULATION_SHARE
            simulated = lambda f, stage, cords: tell(SIMULATION_SHARE * f, stage,
                                                     picture(lambda: [_trimmed(c, width) for c in cords()]))
        loose, history, tight, made = shapes(points, pattern, width, expect, cord=cord, progress=simulated)
        snug = _snug(history, tight)
        d = made['knot']
        checks = [dict(stage='as drawn', crossings=d['crossings'], alexander=d['alexander'], knot=d['knot'])]
        checks += [dict(stage=label, **_check(c)) for label, c in (('laid out', loose), ('drawn up', snug),
                                                                   ('pulled tight', tight))]
        title = (d['meaning'] or 'Knot').capitalize() if d['knot'] else 'Knot'
    knot_type = checks[-1]
    for c in checks:
        if tuple(c['alexander']) != tuple(knot_type['alexander']):
            raise TyingError(f"the knot is not the same at every stage ({c['stage']}: {c['knot']})")
    steps = []
    made = frames(loose, snug, tight, width, count, titles)
    # Drawing a step takes about as long as its cord is long.
    lengths = np.array([simulate.length(m[2]) for m in made])
    starts = drawn_from + (1 - drawn_from) * np.concatenate([[0.0], np.cumsum(lengths)])[:-1] / lengths.sum()
    for n, (step_title, caption, cord, tip) in enumerate(made, start=1):
        cords = _centred([cord])
        if build:
            tell(starts[n - 1], 'draw_step', picture(lambda: cords), step=n, steps=len(made))
        shift = cords[0][0, :2] - cord[0, :2]
        entry = dict(title=step_title, caption=caption, data=None, report='', masks=None)
        if build:
            # The finished steps are checked and fixed below, the others need no mask check.
            data, report = draw.build(design(cords[0], width, color, f'{title} step {n}'), mask_check=False)
            if tip is not None:
                _arrow(data, tuple(np.asarray(tip) + shift))
            entry.update(data=data, report=report)
            if n >= len(made) - 2:      # the finished knot, drawn up, tight: read back from the app's strands
                from . import identify, masks
                # Its parts touch and its joints sit in crossings, so a mask can
                # land on a strand beside its crossing, or a crossing can show
                # half one way: fix what is safe, keep what is left to report.
                fixed_data, fixed, left = masks.repair(data, create_masks=True)
                found = identify.cords(fixed_data)
                if fixed and (len(found) != 1 or tuple(found[0]['alexander']) != tuple(knot_type['alexander'])):
                    left = masks.check(data)['problems']     # a fix that changes the knot is no fix
                    fixed, found = [], identify.cords(data)
                else:
                    data = fixed_data
                entry.update(data=data, masks=dict(fixed=fixed, left=left))
                knot = found[0] if len(found) == 1 else dict(knot=None, alexander=None, crossings=None)
                checks.append(dict(stage=f'step {n} as drawn in the app', crossings=knot['crossings'],
                                   alexander=knot['alexander'], knot=knot['knot']))
        steps.append(entry)
    tell(1.0)
    wrong = [c for c in checks if tuple(c['alexander'] or ()) != tuple(knot_type['alexander'])]
    return dict(title=title, knot=knot_type['knot'], alexander=knot_type['alexander'],
                crossings=knot_type['crossings'], checks=checks, steps=steps, ok=not wrong)


def _check(cord):
    d = invariants.describe(cord)
    return dict(crossings=d['crossings'], alexander=d['alexander'], knot=d['knot'])


def make_library_shapes(width=DEFAULT_WIDTH):
    """{key: {loose, snug, tight}} in widths, for knot_shapes.json."""
    out = {}
    for key, recipe in LIBRARY.items():
        loose, history, tight, made = shapes(plat_layout(recipe['word'], width), 'OU' * len(recipe['word']), width)
        snug = _snug(history, tight)
        keep = lambda c: np.round(_trimmed(np.asarray(c), width, tail=8) / width, 4).tolist()
        out[key] = dict(loose=keep(loose), snug=keep(snug), tight=keep(tight),
                        checks=made['checks'])
    return out
