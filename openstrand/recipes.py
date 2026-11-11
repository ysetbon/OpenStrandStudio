"""Knot recipes of the craft library: a knot as data, tied in steps by bends.tie.

A recipe is one JSON file, craft_library/<craft>/recipes/<name>.json: every
cord as the points it passes through, the reference (for each cord, O or U
at every crossing it passes, in order), and the tying steps (how far each
cord is drawn, which end carries the arrow, what to do). It is the same
thing as a knot of bends.LIBRARY, written down instead of programmed, and
goes through the same checks: the drawing must pass its crossings as the
reference says, and every step, read back from its strands, masks and
layers, must be the part of the knot it shows.

    {"name": "half_hitch", "craft": "macrame", "title": "Half hitch",
     "also": ["single half hitch"], "about": "One or two sentences.",
     "kind": "hitch", "width": 24,
     "cords": [{"label": "Holding cord", "color": "gold", "smooth": false,
                "points": [[200, 400], [1000, 400]]},
               {"label": "Working cord", "color": "teal",
                "points": [[480, 720], [480, 400, "over"], ...]}],
     "patterns": ["UO", "UOUO"],
     "steps": [{"shown": ["all", null], "caption": "Stretch the holding cord."},
               {"shown": ["all", "over"], "arrow": 1, "caption": "..."},
               {"shown": ["all", "all"], "caption": "..."}]}

"shown" says, for every cord, how far a step draws it: null (not yet), "all"
(the whole cord), {"after": 3} (past its third crossing, half way to its
fourth; {"after": 0} stops half way to its first), or the name of one of its
points (a point may carry a name as its third item).
"""
import json
import math
import re

import numpy as np

from . import ROOT

FOLDER = ROOT / 'craft_library'
KINDS = {'hitch': 'tied round a holding cord', 'macrame': 'tied round filler cords',
         'bend': 'joins two cords', 'loop': 'a loop in one cord', 'decorative': 'a decorative knot',
         'braid': 'cords plaited together', 'sennit': 'the same knot tied again and again'}
STEP = 3                    # every STEP-th sample of a cord's centreline becomes a point of its layout
FLAT = 10.0                 # px either side of a crossing where a cord keeps that crossing's height
START = 96.0                # px of a cord a step shows at least, before its first crossing


class RecipeError(ValueError):
    """A recipe that cannot be read or does not pass its own reference; the message says what to change."""


def _need(spec, key, kind, what):
    value = spec.get(key)
    if not isinstance(value, kind) or (kind in (str, list) and not value):
        raise RecipeError(f'{what}: "{key}" is missing or empty')
    return value


def parse(spec, source='recipe'):
    """A recipe as bends.tie takes it, from its JSON: checked for shape here,
    for its crossings when its layout is first asked for."""
    if not isinstance(spec, dict):
        raise RecipeError(f'{source}: a recipe is a JSON object')
    name = _need(spec, 'name', str, source)
    if not re.fullmatch(r'[a-z0-9]+(_[a-z0-9]+)*', name):
        raise RecipeError(f'{source}: "name" is lower case words joined by underscores, e.g. "half_hitch"')
    what = f'{source} ({name})'
    kind = spec.get('kind', 'decorative')
    if kind not in KINDS:
        raise RecipeError(f'{what}: "kind" is one of {", ".join(KINDS)}')
    cords = _need(spec, 'cords', list, what)
    patterns = _need(spec, 'patterns', list, what)
    if len(patterns) != len(cords) or not all(isinstance(p, str) and set(p) <= set('OU') for p in patterns):
        raise RecipeError(f'{what}: "patterns" lists one string of O and U for each of the {len(cords)} cords')
    names = []
    for k, cord in enumerate(cords):
        points = cord.get('points') if isinstance(cord, dict) else None
        if not isinstance(points, list) or len(points) < 2 or not cord.get('label') or not cord.get('color'):
            raise RecipeError(f'{what}: cord {k + 1} needs "label", "color" and at least two "points"')
        for p in points:
            if not (isinstance(p, list) and len(p) in (2, 3) and all(isinstance(v, (int, float)) for v in p[:2])
                    and (len(p) == 2 or isinstance(p[2], str))):
                raise RecipeError(f'{what}: cord {k + 1} has a point that is not [x, y] or [x, y, "name"]: {p}')
        names.append({p[2] for p in points if len(p) == 3})
    steps = _need(spec, 'steps', list, what)
    if len(steps) < 2:
        raise RecipeError(f'{what}: a tutorial has at least two steps')
    plan = []
    afters = [set() for _ in cords]             # per cord: the crossing counts some step stops after
    for n, step in enumerate(steps, start=1):
        shown = step.get('shown') if isinstance(step, dict) else None
        if not isinstance(shown, list) or len(shown) != len(cords) or not step.get('caption'):
            raise RecipeError(f'{what}: step {n} needs "shown" (one entry per cord) and a "caption"')
        shown = list(shown)
        for k, stop in enumerate(shown):
            if isinstance(stop, dict):
                after = stop.get('after')
                if set(stop) != {'after'} or not isinstance(after, int) or not 0 <= after < len(patterns[k]):
                    raise RecipeError(f'{what}: step {n} cord {k + 1}: {{"after": n}} takes a number of crossings '
                                      f'passed, from 0 to {len(patterns[k]) - 1} for this cord ("all" for the '
                                      'whole cord)')
                shown[k] = f'after {after}'
                afters[k].add(after)
            elif stop not in (None, 'all') and stop not in names[k]:
                raise RecipeError(f'{what}: step {n} draws cord {k + 1} as far as "{stop}", but none of its points '
                                  f'has that name ({", ".join(sorted(names[k])) or "it has no named points"})')
        arrow = step.get('arrow')
        if arrow is not None and not (isinstance(arrow, int) and 0 <= arrow < len(cords) and shown[arrow]):
            raise RecipeError(f'{what}: step {n} "arrow" is the number (from 0) of a cord that step shows')
        plan.append(((tuple(shown), arrow), str(step['caption'])))
    if any(stop != 'all' for stop in plan[-1][0][0]):
        raise RecipeError(f'{what}: the last step shows every cord whole ("all")')
    cache = []

    def layout():
        if not cache:
            cache.append(_layout(cords, patterns, what, afters))
        return cache[0]
    return dict(name=name, craft=_need(spec, 'craft', str, what), title=_need(spec, 'title', str, what),
                aliases=tuple(spec.get('also') or ()), about=_need(spec, 'about', str, what), kind=kind,
                width=float(spec.get('width', 24)), layout=layout, patterns=tuple(patterns),
                cords=tuple((str(c['label']), str(c['color'])) for c in cords), steps=tuple(plan), alone=())


def passes(cords, what='recipe'):
    """Where the cords of a recipe cross: (polylines, per cord its passes in
    order: (arc length, crossing number, the other cord, point))."""
    from . import bends, draw, invariants
    polys, named = [], []
    for k, cord in enumerate(cords):
        try:
            poly, _, _ = draw.centerline({'points': [list(p[:2]) for p in cord['points']],
                                          'smooth': cord.get('smooth', True)}, k, with_heights=True)
        except draw.DrawError as e:
            raise RecipeError(f'{what}: {e}') from None
        poly = np.asarray(poly, dtype=float)
        polys.append(poly)
        named.append({bends._sample_of(cord['points'], poly, n): p[2]
                      for n, p in enumerate(cord['points']) if len(p) == 3})
    found = invariants.crossings([np.c_[p, np.zeros(len(p))] for p in polys])
    along = [[] for _ in cords]
    for number, c in enumerate(found):
        for side in (0, 1):
            along[c['cords'][side]].append((c['positions'][side], number, c['cords'][1 - side], c['point']))
    return polys, named, [sorted(a) for a in along], found


def listing(cords, along):
    """Every cord's passes in order, in words: what a pattern has a letter for."""
    lines = []
    for k, visits in enumerate(along):
        said = ', '.join(f"{n} {'itself' if other == k else f'cord {other + 1}'} ({x:.0f}, {y:.0f})"
                         for n, (_, _, other, (x, y)) in enumerate(visits, start=1))
        lines.append(f'  cord {k + 1} ({cords[k]["label"]}) passes {len(visits)}: {said or "nothing"}')
    return '\n'.join(lines)


def alternating(cords):
    """The patterns that make every cord go over, under, over along its whole
    length, cord 1 over first; None when the drawing cannot alternate."""
    _, _, along, found = passes(cords)
    where = [{} for _ in cords]                 # crossing number -> its place(s) in the cord's order
    for k, visits in enumerate(along):
        for n, (_, number, _, _) in enumerate(visits):
            where[k].setdefault(number, []).append(n)
    first = {}                                  # cord -> True when its first pass is over

    def top(k, n):
        return first[k] == (n % 2 == 0)
    for start in range(len(cords)):
        if start in first:
            continue
        first[start] = True
        todo = [start]
        while todo:
            k = todo.pop()
            for n, (_, number, other, _) in enumerate(along[k]):
                mine = top(k, n)
                if other == k:
                    a, b = where[k][number]
                    if top(k, a) == top(k, b):
                        return None
                    continue
                theirs = where[other][number][0]
                want = (not mine) == (theirs % 2 == 0)      # the other cord's first letter, so that it is opposite here
                if other not in first:
                    first[other] = want
                    todo.append(other)
                elif first[other] != want:
                    return None
    return [''.join('O' if top(k, n) else 'U' for n in range(len(along[k]))) for k in range(len(cords))]


def _layout(cords, patterns, what, afters=None):
    """Each cord as (x, y, height[, name]) points: its own curve, with a
    height at every crossing that puts the cord on top where its pattern
    says O and underneath where it says U."""
    polys, named, along, found = passes(cords, what)
    told = {}                                   # crossing number -> {cord pass: on top}
    for k, visits in enumerate(along):
        if len(visits) != len(patterns[k]):
            raise RecipeError(f'{what}: cord {k + 1} passes {len(visits)} crossings, but its pattern '
                              f'"{patterns[k]}" has {len(patterns[k])} letters. The drawing passes:\n'
                              + listing(cords, along))
        for letter, (_, number, _, _) in zip(patterns[k], visits):
            told.setdefault(number, []).append(letter)
    for number, letters in told.items():
        if sorted(letters) != ['O', 'U']:
            x, y = found[number]['point']
            raise RecipeError(f'{what}: at ({x:.0f}, {y:.0f}) both parts are "{letters[0]}": where two parts '
                              'cross, one pattern letter is O and the other U. The drawing passes:\n'
                              + listing(cords, along))
    out = []
    for k, poly in enumerate(polys):
        arc = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(poly, axis=0).T))])
        at = [v[0] for v in along[k]]
        xs, hs = [], []
        for n, (position, letter) in enumerate(zip(at, patterns[k])):
            before = position - at[n - 1] if n else math.inf
            after = at[n + 1] - position if n + 1 < len(at) else math.inf
            reach = min(FLAT, 0.4 * before, 0.4 * after)
            xs += [position - reach, position + reach]
            hs += [1.0 if letter == 'O' else -1.0] * 2
        heights = np.interp(arc, xs, hs) if xs else np.zeros(len(arc))
        for after in sorted((afters or [set()] * len(cords))[k]):
            # Half way from the crossing passed last to the next one (from the start, for none).
            here = at[after - 1] if after else 0.0
            there = at[after] if after < len(at) else arc[-1]
            stop = (here + there) / 2
            if not after:
                # A cord not yet crossing anything is still long enough to read as a cord.
                stop = min(max(stop, START), max(stop, there - 14))
            i = int(np.argmin(np.abs(arc - stop)))
            while i in named[k]:
                i += 1
            named[k][i] = f'after {after}'
        # Few enough points for draw (400 a cord), however long the cord is.
        every = max(STEP, math.ceil(len(poly) / 300))
        keep = set(range(0, len(poly), every)) | {len(poly) - 1} | set(named[k])
        keep |= {int(np.argmin(np.abs(arc - position))) for position in at}
        points = []
        for i in sorted(keep):
            if points and math.dist(points[-1][:2], poly[i]) < 1:
                if i in named[k]:
                    points[-1] = points[-1][:3] + (named[k][i],)
                continue
            point = (float(poly[i][0]), float(poly[i][1]), float(heights[i]))
            points.append(point + ((named[k][i],) if i in named[k] else ()))
        out.append(points)
    return out


# ------------------------------------------------------------------ the library
_LOADED = {}


def files():
    return sorted(FOLDER.glob('*/recipes/*.json'))


def read(path):
    try:
        spec = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        raise RecipeError(f'{path}: not valid JSON ({e.msg}, line {e.lineno})') from None
    return parse(spec, str(path))


def library():
    """{name: recipe} for every recipe of the craft library, read once (again when a file changes)."""
    stamp = tuple((str(p), p.stat().st_mtime_ns) for p in files())
    if _LOADED.get('stamp') != stamp:
        found = {}
        for path in files():
            recipe = read(path)
            if recipe['name'] != path.stem:
                raise RecipeError(f'{path}: its "name" is "{recipe["name"]}"; a recipe is named as its file is')
            found[recipe['name']] = recipe
        _LOADED.update(stamp=stamp, recipes=found)
    return _LOADED['recipes']
