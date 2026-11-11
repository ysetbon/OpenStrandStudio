"""Which knot does a design show? Read from its strands, the way the app draws them.

Each cord is followed along its attached strands; every strand's curve is
sampled as the app draws it (the native two-handle curve with the design's
curve settings); where two parts cross, the one on top is the first strand of
the crossing's mask when there is one and the crossing is not in one of its
erase boxes, else the strand later in the layer order. From that, invariants
gives each cord's knot type.

A knot that joins two cords, or makes a loop, is not in any one cord: each
cord of a square knot is unknotted on its own. So the design's crossing code
(code(): every cord's crossings in order, over or under at each) is also
compared with the ready-made knots (bends.py): named() says which of them the
design is, crossing for crossing, or which crossings go the other way round,
and summary() adds, for every two cords that cross, how often, which is on
top, and whether one passes through a loop of the other.

    from openstrand import identify
    for cord in identify.cords(project_data):
        print(cord['strands'], cord['crossings'], cord['knot'])
    print(identify.summary(project_data))
"""
import numpy as np

from . import invariants
from .steps import mask_parts, set_of

SAMPLES = 24          # points per strand
DEFAULT_CURVE = dict(control_point_base_fraction=1.0, distance_multiplier=2.0, curve_response_exponent=2.0)


def _curve(project):
    from sample_geometry import NativeCurve
    settings = dict(DEFAULT_CURVE)
    block = project.get('project_settings') if isinstance(project, dict) else None
    if isinstance(block, dict):
        for key in settings:
            if isinstance(block.get(key), (int, float)):
                settings[key] = float(block[key])
    return NativeCurve(settings['control_point_base_fraction'], settings['distance_multiplier'],
                       settings['curve_response_exponent'])


def _points(strand, curve, forward):
    p = lambda d: (float(d['x']), float(d['y']))
    cps = strand.get('control_points') or [strand['start'], strand['end']]
    c = (p(strand['start']), p(cps[0]), p(cps[1] if len(cps) > 1 else cps[0]), p(strand['end']))
    pts = [curve.point(c, k / SAMPLES) for k in range(SAMPLES + 1)]
    return pts if forward else pts[::-1]


def _chains(strands):
    """Each cord's strands in order along it, as [(strand, forward)]."""
    by_name = {s['layer_name']: s for s in strands}
    children = {}
    for s in strands:
        if s.get('attached_to') in by_name:
            children.setdefault(s['attached_to'], []).append(s)
    seen, out = set(), []

    def run(first):
        chain, current = [], first
        while current is not None and current['layer_name'] not in seen:
            seen.add(current['layer_name'])
            chain.append(current)
            nxt = [c for c in children.get(current['layer_name'], []) if c['layer_name'] not in seen]
            current = nxt[0] if nxt else None
        return chain

    for root in [s for s in strands if s.get('attached_to') not in by_name] + strands:
        if root['layer_name'] in seen:
            continue
        seen.add(root['layer_name'])
        kids = children.get(root['layer_name'], [])
        back = [c for c in kids if c.get('attachment_side') == 0]
        on = [c for c in kids if c.get('attachment_side') != 0]
        behind = run(back[0]) if back else []
        ahead = run(on[0]) if on else []
        out.append([(s, False) for s in reversed(behind)] + [(root, True)] + [(s, True) for s in ahead])
    return out


def drawing(project):
    """The design as its cords run and cross, read the way the app draws it:
    dict(lines, owners, closed, strands, found). lines: each cord's centre
    line; owners: the strand drawing each of its points; found: every
    crossing, as invariants.crossings lists them, with over (0 or 1: which of
    its two parts is on top) taken from the masks, their erase boxes and the
    layer order."""
    # A hidden strand is not drawn (an arrow of draw's "arrows" is one): it is no part of a knot.
    strands = [s for s in project.get('strands', []) if s.get('type') != 'MaskedStrand' and not s.get('is_hidden')]
    masks = [s for s in project.get('strands', []) if s.get('type') == 'MaskedStrand']
    if not strands:
        return dict(lines=[], owners=[], closed=[], strands=[], found=[])
    names = [s['layer_name'] for s in strands]
    layer = {s['layer_name']: k for k, s in enumerate(project['strands'])}
    on_top, erased = {}, {}
    for m in masks:
        parts = mask_parts(m['layer_name'], names)
        if len(parts) == 2:
            on_top[(parts[0], parts[1])] = parts[0]
            on_top[(parts[1], parts[0])] = parts[0]
            boxes = [b for b in (_corners(r) for r in m.get('deletion_rectangles') or []) if b]
            erased[(parts[0], parts[1])] = erased[(parts[1], parts[0])] = boxes
    curve = _curve(project)
    lines, owners, closed = [], [], []
    # Cords are numbered as their sets are (the first cord of a drawn design is
    # set 1), whichever strand lies lowest in the layers: the numbers the
    # drawing's report, make_steps and the layer panel go by.
    for chain in sorted(_chains(strands), key=lambda chain: min(set_of(strand) for strand, _ in chain)):
        pts, own = [], []
        for strand, forward in chain:
            piece = _points(strand, curve, forward)
            if pts and np.hypot(pts[-1][0] - piece[0][0], pts[-1][1] - piece[0][1]) < 1.0:
                piece = piece[1:]
            pts += piece
            own += [strand['layer_name']] * len(piece)
        is_closed = len(chain) > 1 and np.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) < 1.0
        if is_closed:
            pts, own = pts[:-1], own[:-1]
        lines.append(np.array(pts, dtype=float))
        owners.append(own)
        closed.append(bool(is_closed))
    found = invariants.crossings(lines, closed)
    for c in found:
        a, b = c['cords']
        sa = _owner_at(lines[a], owners[a], c['positions'][0], closed[a])
        sb = _owner_at(lines[b], owners[b], c['positions'][1], closed[b])
        top = on_top.get((sa, sb))
        if top is not None and any(_inside(c['point'], box) for box in erased.get((sa, sb), ())):
            top = None                  # erased there: the layer order shows
        if top is None:
            top = sa if layer.get(sa, 0) > layer.get(sb, 0) else sb
        c['over'] = 0 if top == sa else 1
    return dict(lines=lines, owners=owners, closed=closed, found=found,
                strands=[len(set(own)) for own in owners])


def code(project, read=None):
    """The design's crossing code (see invariants.code): every cord's
    crossings in order, over and under as the app draws them."""
    read = read or drawing(project)
    return invariants.code(read['found'], len(read['lines']), read['closed'])


def cords(project, read=None):
    """Per cord: strands, closed, crossings with itself and with other cords,
    its pattern (O over, U under at each crossing it passes) and its knot
    (dict from invariants.describe, closed up when open)."""
    read = read or drawing(project)
    lines, closed, found = read['lines'], read['closed'], read['found']
    passes = [[] for _ in lines]          # (position, over) per cord, its own crossings
    between = [0] * len(lines)
    for c in found:
        a, b = c['cords']
        if a != b:
            between[a] += 1
            between[b] += 1
            continue
        passes[a].append((c['positions'][0], c['over'] == 0))
        passes[a].append((c['positions'][1], c['over'] == 1))
    letters = code(project, read) if found else None
    out = []
    for k, line in enumerate(lines):
        s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(line, axis=0).T))])
        visits = sorted(passes[k])
        z = _heights(s, visits)
        knot = invariants.describe(np.c_[line, z], closed[k])
        out.append(dict(strands=read['strands'][k], closed=closed[k], crossings=len(visits) // 2,
                        with_others=between[k], alexander=knot['alexander'], knot=knot['knot'],
                        meaning=knot['meaning'], cord=np.c_[line, z],
                        pattern=invariants.pattern(letters, k) if letters else ''))
    return out


def _corners(rect):
    """An erase box's corners in order round it, as MaskedStrand reads them."""
    try:
        if 'top_left' in rect and 'bottom_right' in rect:
            keys = ('top_left', 'top_right', 'bottom_right', 'bottom_left')
            fallback = {'top_right': 'bottom_right', 'bottom_left': 'top_left'}
            return [tuple(float(v) for v in rect.get(k, rect.get(fallback.get(k, k)))) for k in keys]
        x, y, w, h = (float(rect[k]) for k in ('x', 'y', 'width', 'height'))
        return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    except (KeyError, TypeError, ValueError):
        return None


def _inside(point, polygon):
    """Whether a point lies inside a polygon (ray casting)."""
    x, y = point[0], point[1]
    inside = False
    for (x0, y0), (x1, y1) in zip(polygon, polygon[1:] + polygon[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside


def cord_of(project):
    """The one open cord of a design, as (x, y, height) points along it with its
    over and under as heights, ready for tying.tie(cord=...)."""
    found = cords(project)
    if len(found) != 1:
        raise ValueError(f'the design has {len(found)} cords; tying works on a design of one cord')
    if found[0]['closed']:
        raise ValueError('the cord is closed (its ends are joined): tying needs two ends to pull')
    if found[0]['crossings'] == 0:
        raise ValueError('the cord never crosses itself: there is no knot in it')
    return found[0]['cord']


def _owner_at(line, owner, position, closed):
    """The strand drawing the cord at this arc position: a segment belongs to
    the strand of its far end (a joint point is its earlier strand's end)."""
    s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(line, axis=0).T))])
    k = int(np.searchsorted(s, position, side='right')) - 1
    return owner[max(0, min(k + 1, len(owner) - 1))] if not closed else owner[(k + 1) % len(owner)]


def _heights(s, visits, level=1.0, reach=None):
    """Heights along a cord: up at its over-passes, down at its under-passes."""
    z = np.zeros(len(s))
    if not visits:
        return z
    at = [v[0] for v in visits]
    levels = [level if v[1] else -level for v in visits]
    gaps = np.diff(at) if len(at) > 1 else np.array([s[-1]])
    reach = reach if reach is not None else max(1.0, float(np.min(gaps[gaps > 0]) if np.any(gaps > 0) else 1.0) / 2)
    xs = [at[0] - reach] + at + [at[-1] + reach]
    zs = [0.0] + levels + [0.0]
    return np.interp(s, xs, zs)


COMPARED = 4          # designs of up to this many cords are compared with the ready-made knots


def named(project, read=None, found=None):
    """Which ready-made knot (bends.LIBRARY: square knot, sheet bend, bowline,
    fisherman's knot...) the design is, from its crossing code; None when it
    is laid like none of them. See bends.recognise for what comes back."""
    read = read or drawing(project)
    if not 1 <= len(read['lines']) <= COMPARED or not read['found']:
        return None
    from . import bends
    found = found or cords(project, read)
    try:
        return bends.recognise(code(project, read), alone=[c['alexander'] for c in found],
                               closed=[c['closed'] for c in found])
    except bends.BendError:
        return None             # a library drawing that fails its own check names nothing


def summary(project, unknown=False):
    """What the design shows, for a person or the agent: the knot it is when
    it is one of the ready-made ones (or how it differs from the nearest),
    then one line per cord, and for a design of a few cords one line per pair
    of cords that cross. unknown: also say so, first, when a design of a few
    cords is laid like none of the ready-made knots (for a check of what was
    meant to be a knot; after a mask edit on a weave it would only be noise)."""
    read = drawing(project)
    found = cords(project, read)
    if not found:
        return 'the design has no strands'
    known = named(project, read, found)
    letters = code(project, read) if read['found'] else None
    lines = []
    if len(found) == 1:
        c = found[0]
        kind = 'closed' if c['closed'] else 'open (ends joined above everything to name it)'
        name = c['meaning'] or (f"a knot with Alexander polynomial {c['alexander']}" if c['knot'] is None else c['knot'])
        if known and known['how'] != 'near':
            name = known['title'][0].lower() + known['title'][1:]   # a loop knot: its ends joined name another
        lines.append(f"cord 1: {c['strands']} strands, {kind}, {c['crossings']} crossings with itself: {name}")
    else:
        for n, c in enumerate(found, start=1):
            if c['knot'] == 'unknot':
                own = 'not knotted on its own'
            else:
                own = (c['meaning'] or f"a knot with Alexander polynomial {c['alexander']}") + ' on its own'
            shown = f", pattern {c['pattern']}" if 0 < len(c['pattern']) <= 60 else ''
            lines.append(f"cord {n}: {c['strands']} strand{'s' if c['strands'] != 1 else ''}, "
                         f"{'closed' if c['closed'] else 'open'}, "
                         f"{c['crossings']} crossing{'s' if c['crossings'] != 1 else ''} with itself, "
                         f"{c['with_others']} with other cords{shown}: {own}")
        if len(found) <= COMPARED and letters:
            lines += _pairs(letters)
    verdict = _verdict(known, letters, len(found), unknown)
    return '\n'.join(([verdict] if verdict else []) + lines)


def _verdict(known, letters, count, unknown=False):
    """The first line: the ready-made knot this is, or is nearly."""
    if known is None:
        if unknown and 2 <= count <= COMPARED and letters and letters['hand']:
            total = len(letters['hand'])
            return (f"{count} cords, {total} crossing{'s' if total != 1 else ''}: laid like none of the "
                    'ready-made knots (knot_library lists them).')
        return ''
    total = len(letters['hand'])
    title = known['title']
    if known['how'] == 'exact':
        text = (f"{title}: {'all ' if total > 1 else ''}{total} crossing{'s' if total != 1 else ''} go as in "
                f"the checked drawing of this knot{' (its mirror image)' if known['mirror'] else ''}.")
        return text + (' ' + known['note'] if known.get('note') else '')
    if known['how'] == 'structure':
        return f"{title}: {known['why']} (laid differently from the library's drawing)."
    where = '; '.join(_wrong(letters, k) for k in known['flipped'][:8])
    more = f"; and {len(known['flipped']) - 8} more" if len(known['flipped']) > 8 else ''
    plain = title[0].lower() + title[1:]
    count = len(known['flipped'])
    return (f"Laid like a {plain}, but {count} of its {total} crossings {'goes' if count == 1 else 'go'} the "
            f"other way round: {where}{more}. As drawn it is not a {plain}.")


def _wrong(letters, k):
    """One crossing that goes the other way round from the ready-made knot: where, and what it should be."""
    x, y = letters['points'][k]
    top, under = letters['between'][k]
    if top == under:
        return f'at ({x:.0f}, {y:.0f}) cord {top + 1} crosses itself the other way round'
    return f'at ({x:.0f}, {y:.0f}) cord {under + 1} should go over cord {top + 1}'


def _pairs(letters):
    """One line for each two cords that cross: how often, which is on top
    how often, and whether one passes through a loop of the other."""
    count = len(letters['passes'])
    lines = []
    for a in range(count):
        for b in range(a + 1, count):
            over_a = sum(1 for top, under in letters['between'] if (top, under) == (a, b))
            over_b = sum(1 for top, under in letters['between'] if (top, under) == (b, a))
            if not over_a + over_b:
                continue
            line = (f'cords {a + 1} and {b + 1} cross {over_a + over_b} time{"s" if over_a + over_b != 1 else ""}: '
                    f'cord {a + 1} over at {over_a}, cord {b + 1} over at {over_b}')
            if not over_a or not over_b:
                top, low = (a, b) if over_a else (b, a)
                line += (f'; cord {top + 1} lies over cord {low + 1} everywhere (these two alone are not '
                         'joined: one lifts off the other)')
            for loop, other in ((a, b), (b, a)):
                if any(abs(v) >= 1 for v in invariants.through(letters, loop, other).values()):
                    line += f'; cord {other + 1} passes through a loop of cord {loop + 1}'
            lines.append(line)
    return lines
