"""Draw a design from cords: any geometry, made into real woven strands.

A design is a list of cords. Each cord is a centerline, given as points the
cord passes through, as a parametric curve x(t), y(t), or as a ready shape.
The sample generators' fitter turns each centerline into a chain of attached
strands, and every crossing gets over and under: alternating along each cord
by default. This is what lets a person, or Claude, design something no
template covers.

    {"cords": [
        {"points": [[300, 400], [600, 250], [900, 400]], "color": "teal"},
        {"x": "600 + 200*cos(t)", "y": "400 + 200*sin(t)", "t1": "2*pi", "closed": true},
        {"shape": "circle", "center": [600, 400], "radius": 150, "color": "gold"}
    ]}
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
DEFAULT_WIDTH = 24
SPACING = 4.0               # px between centerline samples (the samples use 2; 4 fits about 4x faster)

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
def centerline(cord, index):
    """The cord's centerline as a polyline sampled every SPACING px, and whether it is closed."""
    from sample_geometry import parametric, resample, spline
    what = f'cord {index + 1}'
    closed = _flag(cord.get('closed', False), f'{what} "closed"')
    kinds = [k for k in ('points', 'x', 'shape') if k in cord]
    if len(kinds) != 1:
        raise DrawError(f'{what} needs exactly one of "points", "x" and "y", or "shape"')
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
    elif kind == 'x':
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
    else:
        poly = _shape(cord, what)
        closed = True
    for x, y in poly:
        if not (BOUNDS[0] <= x <= BOUNDS[1] and BOUNDS[0] <= y <= BOUNDS[1]):
            raise DrawError(f'{what} goes to ({x:.0f}, {y:.0f}); keep every point between '
                            f'{BOUNDS[0]} and {BOUNDS[1]} (the samples use about 0-1200 by 0-800)')
    return poly, closed


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


def build(spec):
    """Fit and weave a design. Returns (project dict, report text)."""
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
    # A fresh name per build: the fitter caches its fits by scene name.
    scene = g.Scene(f"drawn_{next(_BUILDS)}_{spec.get('name') or 'design'}")
    tucked, lengths = set(), 0.0
    for k, cord in enumerate(cords):
        if not isinstance(cord, dict):
            raise DrawError(f'cord {k + 1} must be an object')
        poly, closed = centerline(cord, k)
        lengths += sum(math.dist(a, b) for a, b in zip(poly, poly[1:]))
        width = _number(cord.get('width', DEFAULT_WIDTH), f'cord {k + 1} width')
        if not WIDTH_RANGE[0] <= width <= WIDTH_RANGE[1]:
            raise DrawError(f'cord {k + 1}: width must be between {WIDTH_RANGE[0]} and {WIDTH_RANGE[1]}')
        color = colors.parse(str(cord.get('color', 'teal')))
        second = colors.parse(str(cord['second_color'])) if cord.get('second_color') else None
        group = str(cord.get('label') or f'Cord {k + 1}')[:40]
        scene.cord(poly, color, group, width, closed=closed,
                   second_color=second, split='auto' if second else None)
        if _flag(cord.get('tucked', False), f'cord {k + 1} "tucked"'):
            tucked.add(k)
    if lengths > MAX_LENGTH:
        raise DrawError(f'the cords are {lengths:.0f} px long together; keep them under {MAX_LENGTH} px '
                        '(shorter or fewer cords), so drawing takes minutes, not hours')
    dense = scene.dense_crossings()
    crossed = {c for h in dense for c in h['cords']}
    shallow = _shallow_crossings(scene, dense)
    for k, cord in enumerate(scene.cords):
        if cord['closed'] and k not in crossed:
            raise DrawError(f"cord {k + 1} ({cord['group']}) is closed but crosses nothing: its two ends "
                            'meet hidden under a crossing, so a closed cord must cross another cord or '
                            'itself. Move or resize it so it crosses, or make it open ("closed": false).')
    try:
        scene.interlace(g.woven(start_over=weave == 'alternate', tucked=tucked))
    except AssertionError as e:
        raise DrawError(_explain(e)) from None
    data = _serialize(scene)
    return data, report(scene, time.monotonic() - started, shallow)


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


def report(scene, seconds, shallow=()):
    """What was built, for a person or Claude to check against the plan."""
    from masked_strand import MaskedStrand
    lines = []
    hits = getattr(scene, 'hits', [])
    for k, cord in enumerate(scene.cords):
        visits = [h for h in hits if k in h['cords']]
        strands = len(cord.get('chain') or [])
        lines.append(f"cord {k + 1} ({cord['group']}): {strands} strands, {len(visits)} crossings, "
                     f"{'closed' if cord['closed'] else 'open'}")
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
        if w and w[0] == 'crowded crossing' and len(w) >= 5:
            lines.append(f'warning: crowded crossing near ({w[-2]}, {w[-1]}): another strand passes through '
                         'the spot where two cords cross, so its over/under is unclear. Spread the crossings '
                         'there further apart (two cord widths or more).')
        elif w and w[0] == 'overlap without crossing' and len(w) >= 5:
            lines.append(f'warning: near ({w[-2]}, {w[-1]}) two parts of the design touch without crossing; '
                         'move them apart or let them cross.')
        else:
            lines.append('warning: ' + ' '.join(map(str, w)))
    lines.append(f'built in {seconds:.0f} s')
    return '\n'.join(lines)
