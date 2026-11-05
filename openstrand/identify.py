"""Which knot does a design show? Read from its strands, the way the app draws them.

Each cord is followed along its attached strands; every strand's curve is
sampled as the app draws it (the native two-handle curve with the design's
curve settings); where two parts cross, the one on top is the first strand of
the crossing's mask when there is one, else the strand later in the layer
order. From that, invariants gives each cord's knot type.

    from openstrand import identify
    for cord in identify.cords(project_data):
        print(cord['strands'], cord['crossings'], cord['knot'])
"""
import numpy as np

from . import invariants
from .steps import mask_parts

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


def cords(project):
    """Per cord: strands, closed, crossings with itself and with other cords,
    and its knot (dict from invariants.describe, closed up when open)."""
    strands = [s for s in project.get('strands', []) if s.get('type') != 'MaskedStrand']
    masks = [s for s in project.get('strands', []) if s.get('type') == 'MaskedStrand']
    if not strands:
        return []
    names = [s['layer_name'] for s in strands]
    layer = {s['layer_name']: k for k, s in enumerate(project['strands'])}
    on_top = {}
    for m in masks:
        parts = mask_parts(m['layer_name'], names)
        if len(parts) == 2:
            on_top[(parts[0], parts[1])] = parts[0]
            on_top[(parts[1], parts[0])] = parts[0]
    curve = _curve(project)
    lines, owners, closed = [], [], []
    for chain in _chains(strands):
        pts, own = [], []
        for strand, forward in chain:
            piece = _points(strand, curve, forward)
            if pts and np.hypot(pts[-1][0] - piece[0][0], pts[-1][1] - piece[0][1]) < 1.0:
                piece = piece[1:]
            pts += piece
            own += [strand['layer_name']] * len(piece)
        first, last = chain[0][0], chain[-1][0]
        is_closed = len(chain) > 1 and np.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) < 1.0
        if is_closed:
            pts, own = pts[:-1], own[:-1]
        lines.append(np.array(pts, dtype=float))
        owners.append(own)
        closed.append(bool(is_closed))
    found = invariants.crossings(lines, closed)
    passes = [[] for _ in lines]          # (position, over) per cord, its own crossings
    between = [0] * len(lines)
    for c in found:
        a, b = c['cords']
        sa = _owner_at(lines[a], owners[a], c['positions'][0], closed[a])
        sb = _owner_at(lines[b], owners[b], c['positions'][1], closed[b])
        top = on_top.get((sa, sb)) or (sa if layer.get(sa, 0) > layer.get(sb, 0) else sb)
        if a != b:
            between[a] += 1
            between[b] += 1
            continue
        passes[a].append((c['positions'][0], top == sa))
        passes[a].append((c['positions'][1], top == sb))
    out = []
    for k, line in enumerate(lines):
        s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(line, axis=0).T))])
        visits = sorted(passes[k])
        z = _heights(s, visits)
        knot = invariants.describe(np.c_[line, z], closed[k])
        out.append(dict(strands=len(set(owners[k])), closed=closed[k], crossings=len(visits) // 2,
                        with_others=between[k], alexander=knot['alexander'], knot=knot['knot'],
                        meaning=knot['meaning']))
    return out


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


def summary(project):
    """One line per cord, for a person or Claude."""
    lines = []
    for n, c in enumerate(cords(project), start=1):
        kind = 'closed' if c['closed'] else 'open (ends joined above everything to name it)'
        name = c['meaning'] or (f"a knot with Alexander polynomial {c['alexander']}" if c['knot'] is None else c['knot'])
        other = f", {c['with_others']} crossings with other cords" if c['with_others'] else ''
        lines.append(f"cord {n}: {c['strands']} strands, {kind}, {c['crossings']} crossings with itself{other}: {name}")
    return '\n'.join(lines) if lines else 'the design has no strands'
