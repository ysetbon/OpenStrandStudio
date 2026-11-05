"""Draw a design from cords: any geometry, made into real woven strands.

A design is a list of cords. Each cord is a centerline, given as points the
cord passes through, as a parametric curve x(t), y(t), or as a ready shape.
The sample generators' fitter turns each centerline into a chain of attached
strands, and every crossing gets over and under: alternating along each cord
by default, or, for cords given "heights" (one number per point, how high
the cord lies there), the higher part on top, the way a real cord lies. This
is what lets a person, or Claude, design something no template covers.

Every design carries the curve settings it was fitted for (project_settings),
so it opens the same whatever the person's own Settings are.

    {"cords": [
        {"points": [[300, 400], [600, 250], [900, 400]], "color": "teal"},
        {"points": [[300, 250], [600, 400], [900, 250]], "heights": [0, 30, 0]},
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
FLAT_ANGLE = 8              # crossings flatter than this are cords lying on each other
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
def centerline(cord, index, with_heights=False):
    """The cord's centerline as a polyline sampled every SPACING px and whether
    it is closed; with_heights adds its heights along the polyline (None when
    the cord gives none)."""
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
    else:
        heights = None
        poly = _shape(cord, what)
        closed = True
    if heights is None and 'heights' in cord:
        raise DrawError(f'{what}: "heights" go with "points" (one height per point)')
    for x, y in poly:
        if not (BOUNDS[0] <= x <= BOUNDS[1] and BOUNDS[0] <= y <= BOUNDS[1]):
            raise DrawError(f'{what} goes to ({x:.0f}, {y:.0f}); keep every point between '
                            f'{BOUNDS[0]} and {BOUNDS[1]} (the samples use about 0-1200 by 0-800)')
    return (poly, closed, heights) if with_heights else (poly, closed)


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


def build(spec, mask_check=True):
    """Fit and weave a design. Returns (project dict, report text). A design
    with heights gets the mask check at the end of its report (mask_check)."""
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
    tucked, lengths, made = set(), 0.0, []
    for k, cord in enumerate(cords):
        if not isinstance(cord, dict):
            raise DrawError(f'cord {k + 1} must be an object')
        poly, closed, heights = centerline(cord, k, with_heights=True)
        length = sum(math.dist(a, b) for a, b in zip(poly, poly[1:]))
        lengths += length
        width = _number(cord.get('width', DEFAULT_WIDTH), f'cord {k + 1} width')
        if not WIDTH_RANGE[0] <= width <= WIDTH_RANGE[1]:
            raise DrawError(f'cord {k + 1}: width must be between {WIDTH_RANGE[0]} and {WIDTH_RANGE[1]}')
        if length < 3 * width:
            raise DrawError(f'cord {k + 1} is only {length:.0f} px long; make it at least three times its '
                            f'width ({3 * width:.0f} px) so it reads as a cord')
        color = colors.parse(str(cord.get('color', 'teal')))
        second = colors.parse(str(cord['second_color'])) if cord.get('second_color') else None
        group = str(cord.get('label') or f'Cord {k + 1}')[:40]
        made.append((poly, color, group, width, closed, second, heights))
        if _flag(cord.get('tucked', False), f'cord {k + 1} "tucked"'):
            tucked.add(k)
    if lengths > MAX_LENGTH:
        raise DrawError(f'the cords are {lengths:.0f} px long together; keep them under {MAX_LENGTH} px '
                        '(shorter or fewer cords), so drawing takes minutes, not hours')

    def scene_for(room, unders=None):
        # A fresh name per build: the fitter caches its fits by scene name.
        scene = g.Scene(f"drawn_{next(_BUILDS)}_{spec.get('name') or 'design'}")
        for k, (poly, color, group, width, closed, second, heights) in enumerate(made):
            scene.cord(poly, color, group, width, closed=closed,
                       second_color=second, split='auto' if second else None)
            scene.cords[-1]['join_room'] = room
            if heights is not None:
                scene.cords[-1]['heights'] = list(heights)
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
    data = _serialize(scene)
    data['project_settings'] = project_settings()
    data['design_crossings'] = design_crossings(scene)
    text = report(scene, time.monotonic() - started, shallow)
    if mask_check and any(cord.get('heights') is not None for cord in scene.cords):
        text += '\n' + mask_findings(data)
    return data, text


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


def report(scene, seconds, shallow=()):
    """What was built, for a person or Claude to check against the plan."""
    from masked_strand import MaskedStrand
    lines = []
    tight = any(cord.get('heights') is not None for cord in scene.cords)
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
