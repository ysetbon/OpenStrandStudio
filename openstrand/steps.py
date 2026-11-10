"""Tying steps: a design shown as it is drawn, one stage at a time.

Step k holds the strands drawn so far, walking each cord from its first
strand along its attachments (layer order sets over and under, not the order
along the cord, so the two differ). The strands keep their layers, so every
crossing whose two strands are both there already shows the finished over and
under, and the
last strand drawn carries an arrow on its loose end: where the cord goes next.
The last step is the whole design.

    from openstrand import steps
    for title, data in steps.make(design, count=5):
        ...

Also used by scripts/build_knot_spinner.py for the agent's working-line knot.
"""
import copy

ATTACHED_ONLY = ('attached_to', 'attachment_side', 'angle', 'length')
MAX_STEPS = 12


class StepsError(ValueError):
    pass


# ----------------------------------------------------------- curve helpers
def split(p0, p1, p2, p3, t):
    """The first part, up to t, of a cubic Bezier curve (de Casteljau)."""
    lerp = lambda a, b: (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    a, b, c = lerp(p0, p1), lerp(p1, p2), lerp(p2, p3)
    d, e = lerp(a, b), lerp(b, c)
    return p0, a, d, lerp(d, e)


def rest(p0, p1, p2, p3, t):
    """The part of a cubic Bezier curve after t."""
    q3, q2, q1, q0 = split(p3, p2, p1, p0, 1 - t)
    return q0, q1, q2, q3


def point(p):
    return (p['x'], p['y'])


def as_dict(p):
    return {'x': p[0], 'y': p[1]}


def grown(strand, t):
    """The strand drawn part of the way, its loose end without a joint."""
    s = copy.deepcopy(strand)
    if t >= 1:
        return s
    cps = s['control_points']
    _, a, b, end = split(point(s['start']), point(cps[0]), point(cps[1]), point(s['end']), t)
    s['end'], s['control_points'] = as_dict(end), [as_dict(a), as_dict(b)]
    s['control_point_center'] = as_dict(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))
    s['has_circles'] = [s['has_circles'][0], False]
    s['closed_connections'] = [s['closed_connections'][0], False]
    return s


def receded(strand, t):
    """The strand with its first part, up to t, gone: its start is now loose."""
    s = copy.deepcopy(strand)
    cps = s['control_points']
    start, a, b, _ = rest(point(s['start']), point(cps[0]), point(cps[1]), point(s['end']), t)
    s['start'], s['control_points'] = as_dict(start), [as_dict(a), as_dict(b)]
    s['control_point_center'] = as_dict(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))
    s['has_circles'] = [False, s['has_circles'][1]]
    return s


def as_first(strand):
    """An attached strand whose parent is gone becomes its cord's first strand."""
    s = copy.deepcopy(strand)
    s['type'], s['is_first_strand'] = 'Strand', True
    for key in ATTACHED_ONLY:
        s.pop(key, None)
    s['has_circles'] = [False, s['has_circles'][1]]
    return s


def mask_parts(mask_name, names):
    """'1_1_1_6' -> ('1_1', '1_6'), matched against the strand names."""
    for n in names:
        if mask_name.startswith(n + '_') and mask_name[len(n) + 1:] in names:
            return n, mask_name[len(n) + 1:]
    return (mask_name,)


def cords_and_masks(project):
    strands = [s for s in project['strands'] if s['type'] != 'MaskedStrand']
    masks = [s for s in project['strands'] if s['type'] == 'MaskedStrand']
    return strands, masks


def assemble(project, drawn, masks, names):
    """A project of the strands given, with the masks of crossings whose two
    strands are both there, numbered as the loader expects."""
    there = {s['layer_name'] for s in drawn}
    kept = [copy.deepcopy(m) for m in masks if all(n in there for n in mask_parts(m['layer_name'], names))]
    frame = dict(project, strands=drawn + kept, groups={})
    for i, s in enumerate(frame['strands']):  # the loader places each strand by its index
        s['index'] = i
    return frame


def set_of(strand):
    """The number of the strand's set (its cord): 2 for '2_5'."""
    try:
        return int(strand.get('set_number') or str(strand['layer_name']).split('_')[0])
    except ValueError:
        return 0


def cord_path(strands):
    """[(strand, forward)] in the order each cord runs, tail to tail.

    A cord's first strand can sit in the middle of it: strands attached at
    its start (attachment side 0) run back from it, those at its end run on.
    The walk starts at the far end of the part that runs back, so those
    strands are traversed end to start (forward False), then the first
    strand and the rest start to end. Cords come in set order (cord 1, then
    cord 2), whichever lies lower in the layers."""
    by_name = {s['layer_name']: s for s in strands}
    children = {}
    for s in strands:
        if s.get('attached_to') in by_name:
            children.setdefault(s['attached_to'], []).append(s)
    seen = set()

    def chain(first):
        out, current = [], first
        while current is not None and current['layer_name'] not in seen:
            seen.add(current['layer_name'])
            out.append(current)
            nxt = [c for c in children.get(current['layer_name'], []) if c['layer_name'] not in seen]
            current = nxt[0] if nxt else None
        return out

    path = []
    roots = sorted((s for s in strands if s.get('attached_to') not in by_name), key=set_of)
    for root in roots + strands:  # then anything left over, in layer order
        if root['layer_name'] in seen:
            continue
        seen.add(root['layer_name'])
        kids = children.get(root['layer_name'], [])
        back = [c for c in kids if c.get('attachment_side') == 0]
        on = [c for c in kids if c.get('attachment_side') != 0]
        behind = chain(back[0]) if back else []
        ahead = chain(on[0]) if on else []
        path += [(s, False) for s in reversed(behind)] + [(root, True)] + [(s, True) for s in ahead]
        for extra in back[1:] + on[1:]:  # a branch: shown after the main run
            path += [(s, True) for s in chain(extra)]
    return path


def cord_order(strands):
    """The strands in the order each cord runs."""
    return [s for s, _ in cord_path(strands)]


# ------------------------------------------------------------------- steps
def make(project, count=None, arrows=True):
    """[(title, project)] for count steps (default: one per strand, at most
    six); the last is the whole design, with its groups."""
    strands, masks = cords_and_masks(project)
    if not strands:
        raise StepsError('the design has no strands to show in steps')
    n = len(strands)
    count = min(n, 6) if count is None else int(count)
    if not 2 <= count <= min(MAX_STEPS, n):
        raise StepsError(f'steps must be between 2 and {min(MAX_STEPS, n)} for this design ({n} strands)')
    names = [s['layer_name'] for s in strands]
    path = cord_path(strands)
    along = [s for s, _ in path]
    cuts = sorted({max(1, round(i * n / count)) for i in range(1, count + 1)})
    out = []
    for number, cut in enumerate(cuts, start=1):
        title = f'Step {number} of {len(cuts)}'
        if cut >= n:
            out.append((title, copy.deepcopy(project)))
            continue
        so_far = {s['layer_name'] for s in along[:cut]}
        drawn = [copy.deepcopy(s) for s in strands if s['layer_name'] in so_far]  # in layer order
        for k, s in enumerate(drawn):
            s['closed_connections'] = [False, False]  # a closed cord is not closed yet
            if s.get('attached_to') and s['attached_to'] not in so_far:
                drawn[k] = as_first(s)  # its parent comes later: it starts the cord for now
        front, forward = path[cut - 1]
        last = next(s for s in drawn if s['layer_name'] == front['layer_name'])
        side = 1 if forward else 0  # the working end: where the cord goes next
        circles = list(last['has_circles'])
        circles[side] = False
        last['has_circles'] = circles
        if arrows:
            last['end_arrow_visible' if forward else 'start_arrow_visible'] = True
        out.append((title, assemble(project, drawn, masks, names)))
    return out
