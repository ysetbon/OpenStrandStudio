"""Draw a design from cords: any geometry, made into real woven strands.

A design is a list of cords. Each cord is a centerline, given as points the
cord passes through, as a parametric curve x(t), y(t), or as a ready shape.
The sample generators' fitter turns each centerline into a chain of attached
strands, and every crossing gets over and under: alternating along each cord
by default; as a cord's "pattern" says (a letter per crossing the cord
passes, O over or U under, in order from its start), for knots that do not
alternate, such as a square knot or a sheet bend; or, for cords given
"heights" (one number per point, how high the cord lies there), the higher
part on top, the way a real cord lies. This is what lets a person, or the
agent, design something no template covers.

A cord can also be a tool, a hook or a needle the cord is worked with: a
straight stick with a shaped tip, woven with the cords like any other. Arrows
("arrows": the move to make next) are not cords: each is drawn on top of
everything and never crosses or masks anything (in the app, a hidden strand
showing its full arrow).

Every design carries the curve settings it was fitted for (project_settings),
so it opens the same whatever the person's own Settings are.

    {"cords": [
        {"points": [[300, 400], [600, 250], [900, 400]], "color": "teal"},
        {"points": [[300, 250], [600, 400], [900, 250]], "heights": [0, 30, 0]},
        {"points": [[300, 500], [600, 300], [900, 500]], "pattern": "UO"},
        {"x": "600 + 200*cos(t)", "y": "400 + 200*sin(t)", "t1": "2*pi", "closed": true},
        {"shape": "circle", "center": [600, 400], "radius": 150, "color": "gold"},
        {"tool": "hook", "from": [200, 300], "to": [700, 380], "height": 10}
    ], "arrows": [{"points": [[700, 300], [780, 240], [860, 300]]}]}
"""
import ast
import itertools
import math
import operator
import time

from . import colors

MAX_CORDS = 12
MAX_POINTS = 400
MAX_LENGTH = 30000          # px of centerline over all cords, so a fit stays in minutes
BOUNDS = (-1000, 4000)      # every coordinate stays in this range
WIDTH_RANGE = (8, 60)
FLAT_ANGLE = 8              # crossings flatter than this are cords lying on each other
DEFAULT_WIDTH = 24
SPACING = 4.0               # px between centerline samples (the samples use 2; 4 fits about 4x faster)

# Tools a cord is worked with: a straight stick from its handle ("from") to its
# tip ("to"). Per tool, the end style (see src/end_style.py) of the handle and
# of the tip: shape, depth (a share of the width), tilt (degrees).
TOOLS = {
    'hook': (('rounded', 0.5, 0), ('rounded', 1.0, 45)),      # a crochet hook: a round head with a barb
    'needle': (('rounded', 0.5, 0), ('pointed', 1.0, 0)),     # a knitting needle: a point
    'stick': (('rounded', 0.4, 0), ('rounded', 0.4, 0)),      # a rod, a finger, a peg
}
TOOL_WIDTH = 34
TOOL_COLOR = 'grey'

# Arrows: the move to make next. Never woven, always on top.
MAX_ARROWS = 8
ARROW_POINTS = 12
ARROW_COLOR = 'red'
ARROW_WIDTH = 10            # the hidden strand that carries the arrow
ARROW_TOLERANCE = 3.0       # px an arrow's curve may stray from its points
# How the app draws full arrows in a design with arrows: a thin shaft, a clear head.
ARROW_SETTINGS = dict(arrow_line_width=7.0, arrow_head_length=30.0, arrow_head_width=26.0,
                      arrow_head_stroke_width=2)

_FUNCTIONS = {
    'sin': math.sin, 'cos': math.cos, 'tan': math.tan, 'asin': math.asin, 'acos': math.acos,
    'atan': math.atan, 'atan2': math.atan2, 'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh,
    'sqrt': math.sqrt, 'exp': math.exp, 'log': math.log, 'abs': abs, 'floor': math.floor,
    'ceil': math.ceil, 'min': min, 'max': max, 'hypot': math.hypot, 'radians': math.radians,
    'sign': lambda v: (v > 0) - (v < 0), 'pow': math.pow,
}
_CONSTANTS = {'pi': math.pi, 'tau': math.tau, 'e': math.e}
_BINARY = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
           ast.Div: operator.truediv, ast.Mod: math.fmod, ast.Pow: math.pow}
_UNARY = {ast.USub: operator.neg, ast.UAdd: operator.pos}


class DrawError(ValueError):
    """A design that cannot be drawn; the message says what to change."""


# ------------------------------------------------------------------ math
def expression(text, variables=('t',)):
    """A safe arithmetic expression as a function of the variables.

    Numbers, + - * / % **, parentheses, pi, tau, e and the functions in
    _FUNCTIONS; nothing else (no names, attributes or calls outside those).
    """
    if isinstance(text, (int, float)) and not isinstance(text, bool):
        value = float(text)
        return lambda **_: value
    if not isinstance(text, str) or not text.strip():
        raise DrawError('an expression must be a number or text like "300*cos(t)"')
    if len(text) > 500:
        raise DrawError('an expression may be at most 500 characters')
    try:
        tree = ast.parse(text.strip(), mode='eval')
    except SyntaxError:
        raise DrawError(f'cannot read the expression "{text}"') from None

    def check(node):
        if isinstance(node, ast.Expression):
            return check(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
                and not isinstance(node.value, bool):
            return
        if isinstance(node, ast.Name) and (node.id in _CONSTANTS or node.id in variables):
            return
        if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
            check(node.left)
            check(node.right)
            return
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
            check(node.operand)
            return
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCTIONS \
                and not node.keywords and 1 <= len(node.args) <= 4:
            for arg in node.args:
                check(arg)
            return
        name = getattr(node, 'id', None) or type(node).__name__
        raise DrawError(f'"{text}" uses {name}, which is not allowed: use numbers, '
                        f'{", ".join(sorted(variables))}, pi, + - * / % ** and '
                        f'{", ".join(sorted(_FUNCTIONS))}')
    check(tree)

    def value(node, env):
        if isinstance(node, ast.Expression):
            return value(node.body, env)
        if isinstance(node, ast.Constant):
            return float(node.value)
        if isinstance(node, ast.Name):
            return env[node.id] if node.id in env else _CONSTANTS[node.id]
        if isinstance(node, ast.BinOp):
            return _BINARY[type(node.op)](value(node.left, env), value(node.right, env))
        if isinstance(node, ast.UnaryOp):
            return _UNARY[type(node.op)](value(node.operand, env))
        return float(_FUNCTIONS[node.func.id](*[value(a, env) for a in node.args]))

    def run(**env):
        try:
            result = value(tree, env)
        except (ArithmeticError, ValueError, TypeError) as e:
            where = ', '.join(f'{k}={v:.4g}' for k, v in env.items())
            raise DrawError(f'"{text}" cannot be computed at {where}: {e}') from None
        if not math.isfinite(result):
            raise DrawError(f'"{text}" is not a finite number at {env}')
        return result
    return run


def _number(value, what):
    if isinstance(value, bool) or value is None:
        raise DrawError(f'{what} must be a number')
    return expression(value, variables=())()


def _flag(value, what):
    """A yes/no setting: true/false, also written as text or 0/1."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str) and value.strip().lower() in ('true', 'false', 'yes', 'no'):
        return value.strip().lower() in ('true', 'yes')
    raise DrawError(f'{what} must be true or false')


def _point(p, what):
    if not isinstance(p, (list, tuple)) or len(p) != 2:
        raise DrawError(f'{what} must be [x, y]')
    return _number(p[0], what), _number(p[1], what)


# --------------------------------------------------------------- centerlines
def centerline(cord, index, with_heights=False):
    """The cord's centerline as a polyline sampled every SPACING px and whether
    it is closed; with_heights adds its heights along the polyline (None when
    the cord gives none)."""
    from sample_geometry import parametric, resample, spline
    what = f'cord {index + 1}'
    closed = _flag(cord.get('closed', False), f'{what} "closed"')
    kinds = [k for k in ('points', 'x', 'shape', 'tool') if k in cord]
    if len(kinds) != 1:
        raise DrawError(f'{what} needs exactly one of "points", "x" and "y", "shape" or "tool"')
    kind = kinds[0]
    if kind == 'points':
        points = cord['points']
        if not isinstance(points, list) or not (2 <= len(points) <= MAX_POINTS):
            raise DrawError(f'{what}: "points" must list 2 to {MAX_POINTS} [x, y] points')
        pts = [_point(p, f'{what} point {k + 1}') for k, p in enumerate(points)]
        if closed and len(pts) < 3:
            raise DrawError(f'{what}: a closed cord needs at least 3 points')
        if closed and math.dist(pts[0], pts[-1]) < 1:
            pts = pts[:-1]  # the closing point is implied
        for a, b in zip(pts, pts[1:]):
            if math.dist(a, b) < 1:
                raise DrawError(f'{what}: two points in a row are the same ({a[0]:g}, {a[1]:g})')
        if _flag(cord.get('smooth', True), f'{what} "smooth"'):
            poly = spline(pts, closed=closed, spacing=SPACING)
        else:
            corners = pts + ([pts[0]] if closed else [])
            poly = resample(corners, SPACING)
        heights = _heights(cord, what, cord['points'], pts, poly, closed)
    elif kind == 'x':
        heights = None
        if 'y' not in cord:
            raise DrawError(f'{what}: a parametric cord needs both "x" and "y"')
        fx, fy = expression(cord['x']), expression(cord['y'])
        t0 = _number(cord.get('t0', 0), f'{what} t0')
        t1 = _number(cord.get('t1', 'tau'), f'{what} t1')
        if not t1 > t0:
            raise DrawError(f'{what}: t1 must be larger than t0')
        steps = int(_number(cord.get('steps', 4000), f'{what} steps'))
        if not 100 <= steps <= 20000:
            raise DrawError(f'{what}: steps must be between 100 and 20000')
        poly = parametric(lambda t: (fx(t=t), fy(t=t)), t0, t1, closed=closed, steps=steps, spacing=SPACING)
    elif kind == 'tool':
        heights = None
        tool_of(cord, what)
        if 'from' not in cord or 'to' not in cord:
            raise DrawError(f'{what}: a {cord["tool"]} needs "from" (its handle end) and "to" (its tip), each [x, y]')
        a, b = _point(cord['from'], f'{what} "from"'), _point(cord['to'], f'{what} "to"')
        if math.dist(a, b) < 1:
            raise DrawError(f'{what}: "from" and "to" are the same point')
        poly, closed = resample([a, b], SPACING), False
        if 'heights' in cord:       # a stick that dips: its height at the handle and at the tip
            ends = cord['heights']
            if not isinstance(ends, list) or len(ends) != 2:
                raise DrawError(f'{what}: a tool\'s "heights" are two numbers, at its handle and at its tip')
            h0, h1 = (_number(h, f'{what} height {k + 1}') for k, h in enumerate(ends))
            heights = [h0 + (h1 - h0) * k / (len(poly) - 1) for k in range(len(poly))]
    else:
        heights = None
        poly = _shape(cord, what)
        closed = True
    if heights is None and 'heights' in cord:
        raise DrawError(f'{what}: "heights" go with "points" (one height per point); '
                        'use "height" (one number) for the whole cord')
    if 'height' in cord:
        if heights is not None:
            raise DrawError(f'{what}: give "height" (one number for the whole cord) or "heights" '
                            '(one per point), not both')
        heights = [_number(cord['height'], f'{what} height')] * len(poly)
    for x, y in poly:
        if not (BOUNDS[0] <= x <= BOUNDS[1] and BOUNDS[0] <= y <= BOUNDS[1]):
            raise DrawError(f'{what} goes to ({x:.0f}, {y:.0f}); keep every point between '
                            f'{BOUNDS[0]} and {BOUNDS[1]} (the samples use about 0-1200 by 0-800)')
    return (poly, closed, heights) if with_heights else (poly, closed)


def tool_of(cord, what='the cord'):
    """The cord's tool ("hook", "needle", "stick"), or None for a cord."""
    if 'tool' not in cord:
        return None
    name = str(cord['tool']).strip().lower()
    if name not in TOOLS:
        raise DrawError(f'{what}: unknown tool "{cord["tool"]}"; use {", ".join(TOOLS)}')
    return name


def _heights(cord, what, given, pts, poly, closed):
    """Heights at every sample of the polyline, from one height per point."""
    if 'heights' not in cord:
        return None
    heights = cord['heights']
    if not isinstance(heights, list) or len(heights) != len(given):
        raise DrawError(f'{what}: "heights" must list one number per point ({len(given)})')
    values = [_number(h, f'{what} height {k + 1}') for k, h in enumerate(heights)]
    if closed and len(values) == len(pts) + 1:
        values = values[:-1]        # the closing point was dropped above
    # Where each point lies along the polyline: the curve passes through them in order.
    found, start = [], 0
    for k, (x, y) in enumerate(pts):
        reach = 12 + (math.dist(pts[k - 1], (x, y)) * 3 / SPACING if k else 12)
        stop = min(len(poly), start + int(reach))
        best = min(range(start, max(stop, start + 1)), key=lambda i: (poly[i][0] - x) ** 2 + (poly[i][1] - y) ** 2)
        found.append(best)
        start = best
    if closed:
        found.append(len(poly) - 1)
        values.append(values[0])
    out, j = [], 0
    for i in range(len(poly)):
        while j < len(found) - 2 and found[j + 1] <= i:
            j += 1
        a, b = found[j], found[j + 1] if j + 1 < len(found) else found[j]
        t = 0.0 if b == a else min(1.0, max(0.0, (i - a) / (b - a)))
        out.append(values[j] + (values[min(j + 1, len(values) - 1)] - values[j]) * t)
    return out


def by_height(fallback):
    """Over/under from the cords' heights: at each crossing the part lying
    higher goes over. Crossings of cords without heights, or at the same
    height, follow the fallback rule."""
    def rule(scene, hits):
        base = fallback(scene, hits)
        out, decided = [], 0
        for k, h in enumerate(hits):
            z = []
            for side in (0, 1):
                c = h['cords'][side]
                heights = scene.cords[c].get('heights')
                if heights is None:
                    break
                position = h['positions'][side]
                if 'strands' in h:
                    position = scene.poly_index(c, position)
                n = len(heights) - 1
                position = min(max(position, 0.0), n)
                i = min(int(position), n - 1)
                z.append(heights[i] + (heights[i + 1] - heights[i]) * (position - i))
            if len(z) == 2 and abs(z[0] - z[1]) > 1e-6:
                out.append(z[0] > z[1])
                decided += 1
            else:
                out.append(base[k])
        if decided == len(hits):
            scene.woven_conflicts = 0
        return out
    return rule


def _shape(cord, what):
    from sample_geometry import parametric, resample
    shape = cord['shape']
    cx, cy = _point(cord.get('center', [600, 400]), f'{what} center')
    turn = math.radians(_number(cord.get('rotation', 0), f'{what} rotation'))

    def rotated(points):
        c, s = math.cos(turn), math.sin(turn)
        return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in points]

    def positive(key, default=None):
        value = _number(cord.get(key, default), f'{what} {key}') if key in cord or default is not None else None
        if value is None or value <= 0:
            raise DrawError(f'{what}: the {shape} needs a positive "{key}"')
        return value
    if shape == 'circle':
        r = positive('radius')
        return parametric(lambda t: (cx + r * math.cos(t), cy + r * math.sin(t)), 0, math.tau, closed=True,
                          steps=3600, spacing=SPACING)
    if shape == 'ellipse':
        rx, ry = positive('rx'), positive('ry')
        return rotated(parametric(lambda t: (cx + rx * math.cos(t), cy + ry * math.sin(t)), 0, math.tau,
                                  closed=True, steps=3600, spacing=SPACING))
    if shape == 'polygon':
        from generate_knot_samples import rounded_polygon
        sides = int(positive('sides'))
        if not 3 <= sides <= 12:
            raise DrawError(f'{what}: a polygon has 3 to 12 sides')
        reach = positive('radius')
        rounding = _number(cord.get('rounding', reach * 0.2), f'{what} rounding')
        if not 0 < rounding < reach:
            raise DrawError(f'{what}: "rounding" must be between 0 and the radius')
        return resample(rounded_polygon((cx, cy), sides, reach, rounding, turn=turn - math.pi / 2), SPACING)
    if shape == 'heart':
        import generate_creative_samples as g
        size = positive('size', 520) / 520
        ring = g.heart_outline((0, 0), lobe_gap=125 * size, lobe=135 * size, depth=320 * size,
                               tip=78 * size, dip=74 * size)
        top = min(y for _, y in ring)
        bottom = max(y for _, y in ring)
        middle = (top + bottom) / 2
        return rotated(resample([(cx + x, cy + y - middle) for x, y in ring], SPACING))
    if shape == 'turks_head':
        from generate_knot_samples import turks_head
        leads, bights = int(positive('leads')), int(positive('bights'))
        if math.gcd(leads, bights) != 1:
            raise DrawError(f'{what}: leads and bights must share no factor')
        inner, outer = positive('inner'), positive('outer')
        if not inner < outer:
            raise DrawError(f'{what}: "inner" must be smaller than "outer"')
        return rotated(resample(turks_head(leads, bights, inner, outer, centre=(cx, cy)), SPACING))
    raise DrawError(f'{what}: unknown shape "{shape}"; use circle, ellipse, polygon, heart or turks_head')


# ----------------------------------------------------------------- building
_BUILDS = itertools.count(1)


def build(spec, mask_check=True, progress=None):
    """Fit and weave a design. Returns (project dict, report text). A design
    with heights gets the mask check at the end of its report (mask_check).
    progress (see openstrand.progress) is shown the design while it works."""
    from .generators import application, _serialize
    if not isinstance(spec, dict):
        raise DrawError('the design must be an object with a "cords" list')
    cords = spec.get('cords')
    if not isinstance(cords, list) or not 1 <= len(cords) <= MAX_CORDS:
        raise DrawError(f'"cords" must list 1 to {MAX_CORDS} cords')
    weave = spec.get('weave') or 'alternate'
    if weave not in ('alternate', 'alternate_under_first'):
        raise DrawError('"weave" is "alternate" (default; each cord starts over) or "alternate_under_first"')
    application()
    import generate_creative_samples as g

    started = time.monotonic()
    arrows = _arrows(spec.get('arrows'))
    tucked, made, patterns, tools = set(), [], {}, {}
    # Arrows are fitted too: they count toward the same limit as the cords.
    lengths = sum(math.dist(a, b) for poly, _, _ in arrows for a, b in zip(poly, poly[1:]))
    for k, cord in enumerate(cords):
        if not isinstance(cord, dict):
            raise DrawError(f'cord {k + 1} must be an object')
        poly, closed, heights = centerline(cord, k, with_heights=True)
        if cord.get('pattern') is not None:
            if heights is not None:
                raise DrawError(f'cord {k + 1}: give "pattern" or "heights", not both')
            patterns[k] = _letters(cord['pattern'], k)
        length = sum(math.dist(a, b) for a, b in zip(poly, poly[1:]))
        lengths += length
        tool = tool_of(cord)
        if tool:
            tools[k] = tool
        width = _number(cord.get('width', TOOL_WIDTH if tool else DEFAULT_WIDTH), f'cord {k + 1} width')
        if not WIDTH_RANGE[0] <= width <= WIDTH_RANGE[1]:
            raise DrawError(f'cord {k + 1}: width must be between {WIDTH_RANGE[0]} and {WIDTH_RANGE[1]}')
        if length < 3 * width:
            raise DrawError(f'cord {k + 1} is only {length:.0f} px long; make it at least three times its '
                            f'width ({3 * width:.0f} px) so it reads as a cord')
        color = colors.parse(str(cord.get('color', TOOL_COLOR if tool else 'teal')))
        second = colors.parse(str(cord['second_color'])) if cord.get('second_color') else None
        group = str(cord.get('label') or (tool.capitalize() if tool else f'Cord {k + 1}'))[:40]
        made.append((poly, color, group, width, closed, second, heights))
        if _flag(cord.get('tucked', False), f'cord {k + 1} "tucked"'):
            tucked.add(k)
    if progress is not None:
        import numpy as np
        from .progress import picture
        progress(None, 'draw', lambda: picture(
            [np.c_[np.asarray(poly)[:, :2], heights] if heights is not None else np.asarray(poly)[:, :2]
             for poly, _, _, _, _, _, heights in made],
            max(m[3] for m in made), [str(m[1]) for m in made], [m[4] for m in made]))
    if lengths > MAX_LENGTH:
        what = 'the cords and arrows are' if arrows else 'the cords are'
        raise DrawError(f'{what} {lengths:.0f} px long together; keep them under {MAX_LENGTH} px '
                        '(shorter or fewer cords and arrows), so drawing takes minutes, not hours')

    levels = {}                 # heights worked out from the patterns, for the cords that gave none

    def scene_for(room, unders=None):
        # A fresh name per build: the fitter caches its fits by scene name.
        scene = g.Scene(f"drawn_{next(_BUILDS)}_{spec.get('name') or 'design'}")
        for k, (poly, color, group, width, closed, second, heights) in enumerate(made):
            scene.cord(poly, color, group, width, closed=closed,
                       second_color=second, split='auto' if second else None)
            scene.cords[-1]['join_room'] = room
            scene.cords[-1]['first'] = poly[0]      # where the cord starts (a closed cord is turned later)
            if heights is not None:
                scene.cords[-1]['heights'] = list(heights)
                scene.cords[-1]['tight'] = True     # its parts lie against each other, as a knot pulled tight
            elif k in levels:
                scene.cords[-1]['heights'] = list(levels[k])
            if unders and not closed:
                scene.cords[-1]['joins'] = sorted(unders.get(k, ()))
        return scene

    scene = scene_for(1.0)
    dense = scene.dense_crossings()
    crossed = {c for h in dense for c in h['cords']}
    shallow = _shallow_crossings(scene, dense)
    flat = [c for c in shallow if c[1] < FLAT_ANGLE]
    if flat:
        (x, y), angle, a, b = flat[0]
        who = f'cord {a + 1} runs along itself' if a == b else f'cords {a + 1} and {b + 1} run along each other'
        raise DrawError(f'{who} near ({x:.0f}, {y:.0f}), meeting at {angle:.0f} degrees: one cord is lying on '
                        'top of another. Keep cords apart, or let them cross at 40 degrees or more '
                        '(a closed curve that goes round twice does this: draw it once).')
    for k, cord in enumerate(scene.cords):
        if cord['closed'] and k not in crossed:
            raise DrawError(f"cord {k + 1} ({cord['group']}) is closed but crosses nothing: its two ends "
                            'meet hidden under a crossing, so a closed cord must cross another cord or '
                            'itself. Move or resize it so it crosses, or make it open ("closed": false).')
    rule = g.woven(start_over=weave == 'alternate', tucked=tucked)
    if any(heights is not None for *_, heights in made):
        rule = by_height(rule)
    conflicts = None
    if patterns:
        # The patterns say which part is on top where they speak; the rest
        # alternates. Kept as heights along every cord, so each crossing is
        # found again on the fitted strands, wherever a closed cord is joined.
        levels, conflicts = _levels(scene, dense, rule, patterns)
        for k, cord in enumerate(scene.cords):
            if k in levels:
                cord['heights'] = list(levels[k])
        rule = by_height(g.woven(start_over=weave == 'alternate', tucked=tucked))
    # Joins stay clear of crossings, so the strands' end circles and shadows
    # never show there. A tight knot has crossings everywhere: when that
    # leaves no room to follow the design, let joins come closer.
    limit = min(FIT_LIMIT, FIT_SHARE * min(width for _, _, _, width, *_ in made))
    # Last resort, for a tight knot: joins right where a cord passes under,
    # hidden by the part on top, so every stretch between them is short.
    unders = _under_passes(scene, dense, rule)
    tries = [(room, None) for room in JOIN_ROOM] + ([(JOIN_ROOM[-1], unders)] if unders else [])
    best, error = None, None
    for n, (room, joins) in enumerate(tries):
        if n:
            scene = scene_for(room, joins)
        try:
            scene.interlace(rule)
        except AssertionError as e:
            error = e
            continue
        # Close to the design, every crossing of the design still there, and
        # each drawn with the part on top that the design puts on top.
        score = (len(scene.hits) != len(dense), len(wrong_crossings(scene)), fit_error(scene))
        if best is None or score < best[0]:
            best = (score, scene)
        if score[0] == 0 and score[1] == 0 and score[2] <= limit:
            break
    if best is None:
        raise DrawError(_explain(error)) from None
    scene = best[1]
    if conflicts is not None:
        scene.woven_conflicts = conflicts
    for k, tool in tools.items():
        _shape_tool(scene.cords[k]['chain'], tool)
    _add_arrows(scene, arrows)
    data = _serialize(scene)
    data['project_settings'] = project_settings()
    if arrows:
        data['project_settings'].update(ARROW_SETTINGS)
    data['design_crossings'] = design_crossings(scene)
    text = report(scene, time.monotonic() - started, shallow)
    if arrows:
        text += f'\n{len(arrows)} arrow{"s" if len(arrows) != 1 else ""} drawn on top (arrows are never woven)'
    if mask_check and any(cord.get('heights') is not None for cord in scene.cords):
        text += '\n' + mask_findings(data)
    return data, text


def _letters(pattern, index):
    """A cord's pattern as a list of 'O', 'U' and '-' (left to the other cord
    or to the weave), one per crossing the cord passes."""
    what = f'cord {index + 1}'
    if isinstance(pattern, (list, tuple)):
        pattern = ''.join(map(str, pattern))
    if not isinstance(pattern, str):
        raise DrawError(f'{what}: "pattern" is text such as "OUUO": O (over) or U (under) for each crossing '
                        'the cord passes, in order from its start')
    letters = []
    for ch in pattern.upper():
        if ch in 'OU':
            letters.append(ch)
        elif ch in '-?._*':
            letters.append('-')
        elif not (ch.isspace() or ch in ',;/|'):
            raise DrawError(f'{what}: the pattern "{pattern}" has "{ch}" in it; use O (over), U (under) and '
                            '- (leave that crossing to the other cord or to the weave)')
    return letters


def _visits(hits):
    """Per cord, the crossings it passes in order: (position, hit number, side)."""
    visits = {}
    for k, h in enumerate(hits):
        for side in (0, 1):
            visits.setdefault(h['cords'][side], []).append((h['positions'][side], k, side))
    for row in visits.values():
        row.sort()
    return visits


def _levels(scene, dense, rule, patterns):
    """Over and under at every crossing of the design, as the patterns say
    where they speak and as rule (the weave) gives elsewhere, turned into
    heights along each cord that has none of its own: up where it goes over,
    down where it goes under. Returns ({cord: heights}, conflicts left in the
    weave). A pattern that does not fit the design is a DrawError that lists
    the cord's crossings."""
    import numpy as np
    over = list(rule(scene, dense))             # for each crossing: its first part is on top
    conflicts = getattr(scene, 'woven_conflicts', 0)
    visits = _visits(dense)
    said = {}

    def place(k):
        x, y = dense[k]['point']
        return f'({x:.0f}, {y:.0f})'

    def listed(c):
        row = visits.get(c, [])
        names = []
        for n, (_, k, side) in enumerate(row, start=1):
            other = dense[k]['cords'][1 - side]
            names.append(f"{n} {'itself' if other == c else f'cord {other + 1}'} at {place(k)}")
        return '; '.join(names) if names else 'none'

    for c, letters in sorted(patterns.items()):
        row = visits.get(c, [])
        if len(letters) != len(row):
            twice = ' (a crossing of the cord with itself is passed twice, so it has two letters)' \
                if any(dense[k]['cords'][0] == dense[k]['cords'][1] for _, k, _ in row) else ''
            raise DrawError(f'cord {c + 1} passes {len(row)} crossing{"s" if len(row) != 1 else ""} but its '
                            f'pattern has {len(letters)} letter{"s" if len(letters) != 1 else ""}{twice}. '
                            f'Its crossings in order from its start: {listed(c)}. Give one letter for each.')
        for n, ((_, k, side), ch) in enumerate(zip(row, letters), start=1):
            if ch == '-':
                continue
            first_on_top = (ch == 'O') == (side == 0)
            if k in said and said[k][0] != first_on_top:
                c0, n0, ch0 = said[k][1:]
                a, b = dense[k]['cords']
                if a == b:
                    raise DrawError(f'cord {c + 1} crosses itself at {place(k)}: letters {n0} and {n} of its '
                                    f'pattern are both {ch}. One pass goes over (O), the other under (U).')
                raise DrawError(f'the crossing at {place(k)} is letter {n0} of cord {c0 + 1}\'s pattern ({ch0}) '
                                f'and letter {n} of cord {c + 1}\'s ({ch}): one cord goes over (O) there and '
                                'the other under (U). Change one of the two letters, or write - for one.')
            said.setdefault(k, (first_on_top, c, n, ch))
            over[k] = first_on_top
    if len(said) == len(dense):
        conflicts = 0                           # nothing was left to the weave
    for c, cord in enumerate(scene.cords):
        row = visits.get(c, [])
        if cord['closed'] and row and all(over[k] == (side == 0) for _, k, side in row):
            raise DrawError(f'cord {c + 1} is closed and goes over at every crossing it passes: the two ends of a '
                            'closed cord meet hidden under a crossing, so it has to pass under at least once. '
                            'Make one of its letters U, or draw it open ("closed": false).')
    given = [abs(v) for cord in scene.cords if cord.get('tight') for v in cord['heights']]
    level = 1.0 + 2.0 * (max(given) if given else 0.0)   # above and below any height a cord brought
    out = {}
    for c, cord in enumerate(scene.cords):
        if cord.get('tight'):
            continue
        size = len(cord['poly'])
        row = visits.get(c, [])
        if not row:
            out[c] = [0.0] * size
            continue
        at = [p for p, _, _ in row]
        up = [level if over[k] == (side == 0) else -level for _, k, side in row]
        if cord['closed']:
            out[c] = np.interp(np.arange(size), at, up, period=size - 1).tolist()
        else:
            out[c] = np.interp(np.arange(size), at, up).tolist()
    return out, conflicts


def _shape_tool(chain, tool):
    """Give a tool's two free ends their shapes: the handle at the cord's
    start, the tip at its end."""
    from end_style import normalize_style
    handle, tip = TOOLS[tool]
    first, last = chain[0], chain[-1]
    # A strand before the cord's first strand runs against the cord: its
    # free end is its own end. The last strand always runs with the cord.
    for strand, side, (shape, depth, tilt) in ((first, 1 if first.reversed else 0, handle), (last, 1, tip)):
        if not hasattr(strand, 'end_styles') or strand.end_styles is None:
            strand.end_styles = [None, None]
        strand.end_styles[side] = normalize_style({'shape': shape, 'depth': depth, 'tilt': tilt})
        strand.update_shape()
        strand.update_side_line()


def _arrows(given):
    """The design's arrows as [(centerline, color, label)]."""
    from sample_geometry import resample, spline
    if given is None:
        return []
    if not isinstance(given, list) or len(given) > MAX_ARROWS:
        raise DrawError(f'"arrows" must list at most {MAX_ARROWS} arrows')
    out = []
    for n, arrow in enumerate(given, start=1):
        what = f'arrow {n}'
        if not isinstance(arrow, dict) or not isinstance(arrow.get('points'), list) \
                or not 2 <= len(arrow['points']) <= ARROW_POINTS:
            raise DrawError(f'{what} must be {{"points": [[x, y], ...]}} with 2 to {ARROW_POINTS} points, '
                            'from its tail to its head')
        pts = [_point(p, f'{what} point {k + 1}') for k, p in enumerate(arrow['points'])]
        for a, b in zip(pts, pts[1:]):
            if math.dist(a, b) < 1:
                raise DrawError(f'{what}: two points in a row are the same ({a[0]:g}, {a[1]:g})')
        for x, y in pts:
            if not (BOUNDS[0] <= x <= BOUNDS[1] and BOUNDS[0] <= y <= BOUNDS[1]):
                raise DrawError(f'{what} goes to ({x:.0f}, {y:.0f}); keep every point between '
                                f'{BOUNDS[0]} and {BOUNDS[1]}')
        smooth = _flag(arrow.get('smooth', True), f'{what} "smooth"') and len(pts) > 2
        poly = spline(pts, closed=False, spacing=SPACING) if smooth else resample(pts, SPACING)
        length = sum(math.dist(a, b) for a, b in zip(poly, poly[1:]))
        head = ARROW_SETTINGS['arrow_head_length']
        if length < 2 * head:
            raise DrawError(f'{what} is only {length:.0f} px long; make it at least {2 * head:.0f} px')
        # The app draws the head beyond the strand's end: stop the shaft a
        # head short, so the tip lands on the arrow's last point.
        keep = max(2, len(poly) - int(round(head / SPACING)))
        color = colors.parse(str(arrow.get('color', ARROW_COLOR)))
        out.append((poly[:keep], color, str(arrow.get('label') or f'Arrow {n}')[:40]))
    return out


def _add_arrows(scene, arrows):
    """Each arrow as hidden strands showing their full arrow, above
    everything: one strand where one curve follows the arrow, else a few in a
    row with the head on the last."""
    if not arrows:
        return
    from PyQt5.QtCore import QPointF
    from PyQt5.QtGui import QColor
    from strand import Strand
    import generate_creative_samples as g
    for poly, color, label in arrows:
        spans = g.NATIVE.fit(poly, False, ARROW_TOLERANCE, free_ends=True, min_length=ARROW_WIDTH * 3,
                             max_turn=math.radians(200), max_bend_error=30.0)
        entry = scene.groups.setdefault(label, dict(layers=[], main_strands=[], strands=[], control_points={}))
        for k, (_, _, curve) in enumerate(spans):
            scene.set_count += 1
            start, c1, c2, end = (QPointF(*p) for p in curve)
            strand = Strand(start, end, ARROW_WIDTH, QColor(color), QColor(color), 2, scene.set_count)
            strand.is_first_strand = True
            strand.layer_name = f'{scene.set_count}_1'
            strand.control_point1, strand.control_point2 = c1, c2
            strand.control_point2_activated = strand.control_point2_shown = True
            strand.control_point_center_locked = False
            for key, value in g.CURVE_SETTINGS.items():
                setattr(strand, key, value)
            strand.triangle_has_moved = True
            strand.start_circle_stroke_color = QColor(0, 0, 0, 0)
            strand.end_circle_stroke_color = QColor(0, 0, 0, 0)
            strand.is_hidden = True                 # only its arrow shows
            strand.full_arrow_visible = True
            strand.arrow_color = QColor(color)
            strand.arrow_head_visible = k == len(spans) - 1
            strand.hide_shadow = True
            strand.update_shape()
            strand.update_side_line()
            scene.strands.append(strand)
            entry['main_strands'].append(strand)
            entry['strands'].append(strand)
            entry['layers'].append(strand.layer_name)
            entry['control_points'][strand.layer_name] = dict(control_point1=c1, control_point2=c2)


def mask_findings(data, limit=12):
    """For a design whose cords lie close (given heights, as a tight knot):
    where a mask or a crossing is drawn wrong, as masks.check finds it. This
    replaces the crowded-crossing warnings, which such a design has at every
    crossing."""
    from . import masks
    try:
        found = masks.check(data)['problems']
    except masks.MaskError as e:
        return f'mask check: {e}'
    if not found:
        return 'mask check: no problems (every crossing shows the strand on top all over)'
    lines = [f'mask check: {len(found)} place{"s" if len(found) != 1 else ""} drawn wrong '
             '(check_masks lists them, edit_mask fixes them):']
    lines += ['  ' + p['text'] for p in found[:limit]]
    if len(found) > limit:
        lines.append(f'  … and {len(found) - limit} more')
    return '\n'.join(lines)


def design_crossings(scene):
    """Which strand the design puts on top at each crossing, kept in the
    project (masks.check reads it to tell a crossing drawn the wrong way)."""
    out = []
    for h in getattr(scene, 'hits', []):
        a, b = h['strands']
        top, under = (a, b) if h['over'] else (b, a)
        x, y = h['point']
        out.append({'point': [round(float(x), 2), round(float(y), 2)],
                    'over': top.layer_name, 'under': under.layer_name})
    return out


JOIN_ROOM = (1.0, 0.6, 0.4)     # how far joins keep from crossings, as a share of the usual


def _under_passes(scene, dense, rule):
    """Per cord, the sample indices where it passes under another part."""
    out = {}
    for h, first_over in zip(dense, rule(scene, dense)):
        side = 1 if first_over else 0
        out.setdefault(h['cords'][side], set()).add(int(round(h['positions'][side])))
    return out
FIT_LIMIT = 8.0                 # px: a fit further than this from the design is tried again
FIT_SHARE = 0.3                 # or further than this share of the narrowest cord


def wrong_crossings(scene):
    """Crossings the strands would draw the other way round: the part on top
    is the first strand of the pair's mask (outside its erased corners), else
    the strand later in the layer order, as the app paints them."""
    from masked_strand import MaskedStrand
    order = {id(s): k for k, s in enumerate(scene.strands)}
    masks = {}
    for s in scene.strands:
        if isinstance(s, MaskedStrand):
            masks[(id(s.first_selected_strand), id(s.second_selected_strand))] = s
            masks[(id(s.second_selected_strand), id(s.first_selected_strand))] = s
    wrong = []
    for h in getattr(scene, 'hits', []):
        a, b = h['strands']
        want = a if h['over'] else b
        top = None
        mask = masks.get((id(a), id(b)))
        if mask is not None:
            x, y = h['point']
            erased = any(r['top_left'][0] <= x <= r['top_right'][0] and r['top_left'][1] <= y <= r['bottom_left'][1]
                         for r in (getattr(mask, 'deletion_rectangles', None) or []))
            if not erased:
                top = mask.first_selected_strand
        if top is None:
            top = a if order.get(id(a), -1) > order.get(id(b), -1) else b
        if top is not want:
            wrong.append(h['point'])
    return wrong


def fit_error(scene):
    """How far (px) the fitted strands stray from the designed centerlines at worst."""
    from sample_geometry import segment_distance
    worst = 0.0
    for cord in scene.cords:
        poly = cord['poly']
        for strand, (i, j) in zip(cord.get('chain') or [], cord.get('spans') or []):
            path = strand.get_path()
            piece = poly[max(i - 2, 0):min(j + 3, len(poly))]
            for k in range(1, 24):
                q = path.pointAtPercent(k / 24)
                q = (q.x(), q.y())
                worst = max(worst, min(segment_distance(q, a, b) for a, b in zip(piece, piece[1:])))
    return worst


def project_settings():
    """The curve settings the fitter fits strands for, as the app saves them in
    a project: opening the design applies them, so its curves come out as
    fitted whatever the person's own Settings are."""
    from generate_creative_samples import CURVE_SETTINGS
    return {'version': 1, **CURVE_SETTINGS}


def _shallow_crossings(scene, hits, limit=25):
    """Crossings where two centerlines meet at less than limit degrees.

    Nearly parallel cords overlap for a long way, so their over/under
    shading smears; the report asks for steeper crossings there.
    """
    from sample_geometry import tangents
    heading = [tangents(c['poly'], c['closed']) for c in scene.cords]
    found = []
    for h in hits:
        (a, b), (u, v) = h['cords'], h['positions']
        ta = heading[a][min(int(round(u)), len(heading[a]) - 1)]
        tb = heading[b][min(int(round(v)), len(heading[b]) - 1)]
        angle = math.degrees(math.acos(min(1.0, abs(ta[0] * tb[0] + ta[1] * tb[1]))))
        if angle < limit:
            found.append((h['point'], angle, a, b))
    return found


def _explain(error):
    text = ' '.join(str(a) for a in (error.args[0] if error.args and isinstance(error.args[0], tuple) else error.args))
    if 'closed cord needs a crossing' in text:
        return ('a closed cord must cross another cord or itself: its two ends meet hidden under a '
                'crossing. Make it open ("closed": false) or let it cross something.')
    if 'cannot reverse span' in text or 'mask conflict' in text:
        return ('two crossings sit too close together for the fitter. Space crossings at least two '
                f'cord widths apart, cross at steeper angles (40 degrees or more), and avoid near-misses. ({text})')
    return f'the fitter could not build this design ({text}). Simplify the cords and try again.'


PATTERN_SHOWN = 80              # a cord that passes more crossings than this shows no pattern


def passes(scene):
    """Per cord, the crossings it passes in order from its start, as built:
    (letter, the other cord, the place), letter O where it goes over and U
    where it goes under. A closed cord is fitted from a join the fitter
    chose; its crossings are still listed from the point it was drawn from."""
    hits = getattr(scene, 'hits', [])
    out = []
    for c, cord in enumerate(scene.cords):
        poly = cord['poly']
        size = len(poly) - 1
        start = 0
        if cord['closed'] and cord.get('first') is not None:
            fx, fy = cord['first']
            start = min(range(size), key=lambda i: (poly[i][0] - fx) ** 2 + (poly[i][1] - fy) ** 2)
        row = []
        for h in hits:
            for side in (0, 1):
                if h['cords'][side] != c:
                    continue
                position = h['positions'][side]
                if 'strands' in h and cord.get('spans'):
                    position = scene.poly_index(c, position)
                if cord['closed']:
                    position = (position - start) % size
                row.append((position, 'O' if bool(h.get('over')) == (side == 0) else 'U',
                            h['cords'][1 - side], h['point']))
        row.sort(key=lambda item: item[0])
        out.append([item[1:] for item in row])
    return out


def report(scene, seconds, shallow=()):
    """What was built, for a person or the agent to check against the plan."""
    from masked_strand import MaskedStrand
    lines = []
    tight = any(cord.get('tight') for cord in scene.cords)
    hits = getattr(scene, 'hits', [])
    along = passes(scene)
    for k, cord in enumerate(scene.cords):
        visits = [h for h in hits if k in h['cords']]
        strands = len(cord.get('chain') or [])
        letters = ''.join(letter for letter, _, _ in along[k])
        lines.append(f"cord {k + 1} ({cord['group']}): {strands} strands, {len(visits)} crossings, "
                     f"{'closed' if cord['closed'] else 'open'}"
                     + (f', pattern {letters}' if 0 < len(letters) <= PATTERN_SHOWN else ''))
    lines.append(f'{len(hits)} crossings in all, '
                 f'{sum(isinstance(s, MaskedStrand) for s in scene.strands)} masks; '
                 f"over/under conflicts: {getattr(scene, 'woven_conflicts', 0)}")
    for h in hits[:40]:
        a, b = h['cords']
        top = a if h.get('over') else b
        under = b if top == a else a
        x, y = h['point']
        who = f'cord {top + 1} over cord {under + 1}' if a != b else f'cord {a + 1} over itself'
        lines.append(f'  crossing at ({x:.0f}, {y:.0f}): {who}')
    if len(hits) > 40:
        lines.append(f'  … and {len(hits) - 40} more crossings')
    if 0 < len(hits) <= 40 and (len(scene.cords) > 1 or not tight):
        # Each cord's crossings in the order it passes them: what a pattern is written from.
        for k, row in enumerate(along):
            if row:
                said = ', '.join(f"{n} {'over' if letter == 'O' else 'under'} "
                                 f"{'itself' if other == k else f'cord {other + 1}'} ({x:.0f}, {y:.0f})"
                                 for n, (letter, other, (x, y)) in enumerate(row, start=1))
                lines.append(f'  cord {k + 1} passes, from its start: {said}')
        lines.append('  (a pattern is these letters in that order, O over and U under: to turn a crossing the '
                     'other way, draw again with the pattern of a cord that passes it, that letter changed)')
    for k, cord in enumerate(scene.cords):
        wanted = cord.get('second_color')
        if wanted and not any(s.color.name().lower() == wanted.lower() for s in cord.get('chain') or []):
            lines.append(f'warning: cord {k + 1} stayed one color: a second_color changes under a crossing '
                         'the cord passes under, apart from the one hiding its ends, and this cord has no '
                         'such crossing. Let it cross more, or draw the second color as its own cord.')
    for (x, y), angle, a, b in shallow:
        lines.append(f'warning: shallow crossing at ({x:.0f}, {y:.0f}), {angle:.0f} degrees between '
                     f'cord {a + 1} and cord {b + 1}: nearly parallel cords overlap and their shading '
                     'smears. Cross at 40 degrees or more, or move them apart.')
    for w in scene.warnings:
        if w and w[0] == 'crowded crossing' and tight:
            continue                    # at every crossing of a tight knot: build adds the mask check instead
        if w and w[0] == 'crowded crossing' and len(w) >= 5:
            lines.append(f'warning: crowded crossing near ({w[-2]}, {w[-1]}): another strand passes through '
                         'the spot where two cords cross, so its over/under is unclear. Spread the crossings '
                         'there further apart (two cord widths or more).')
        elif w and w[0] == 'overlap without crossing' and tight:
            continue                    # parts of a tight knot lie against each other
        elif w and w[0] == 'overlap without crossing' and len(w) >= 5:
            lines.append(f'warning: near ({w[-2]}, {w[-1]}) two parts of the design touch without crossing; '
                         'move them apart or let them cross.')
        else:
            lines.append('warning: ' + ' '.join(map(str, w)))
    for x, y in wrong_crossings(scene):
        lines.append(f'warning: the crossing at ({x:.0f}, {y:.0f}) is drawn the other way round: the two '
                     'strands there also cross nearby the other way, too close to split them. Move the '
                     'two crossings further apart.')
    lines.append(f'built in {seconds:.0f} s')
    return '\n'.join(lines)
