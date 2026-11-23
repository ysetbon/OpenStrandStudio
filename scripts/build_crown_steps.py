"""Make the craft library's crowned knots, step by step: the good luck knot family.

Run from any directory: python scripts/build_crown_steps.py [--only NAME ...] [--spec-only] [--out DIR]

A knot tied by crowning (the good luck knot, the chrysanthemum knot, ...) is
taught in pictures that differ from step to step: the cord laid out as a
star of bights round a centre, then each bight folded over the next one
(a crown), pulled tight, crowned again on top. Its pictures are not the cord
drawn further and further, so these knots are not recipes: each is a
`draw-steps` design, written here from the geometry of a crown, kept under
craft_library/chinese_knotting/spec/<name>.json and drawn into
craft_library/chinese_knotting/steps/<name>/ with the app's own code.

The geometry: N arms (bights, and the two ends as one arm) leave the centre
at equal angles, each a ribbon of two legs. Crowning folds every arm, in
turn, round over the base of the next one: its fold lies along one edge of a
regular N-gon facing that arm, crosses the folds before and after it at the
polygon's corners, then leaves the knot. The last arm is tucked through the
bend of the first, so the crown has no first or last: every fold goes over
the fold made before it and the base of the next arm, under the fold made
after it. A second crown is tied the same way on the arms as they leave the
first, on top of it. Over and under at every crossing come from that rule
and are given to `draw-steps` as the cord's pattern.
"""
import argparse
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'craft_library' / 'chinese_knotting'
CENTRE = np.array([600.0, 420.0])


# ------------------------------------------------------------------ geometry
def unit(angle):
    return np.array([math.cos(angle), math.sin(angle)])


def left(t):
    return np.array([-t[1], t[0]])


def line_cross(p, t, q, s):
    """Where p + a*t meets q + b*s: (a, b)."""
    m = np.array([[t[0], -s[0]], [t[1], -s[1]]])
    a, b = np.linalg.solve(m, q - p)
    return a, b


class Ribbon:
    """A ribbon's centreline as pieces (straight or arc), each with a label, sampled
    with its left normal so the two legs can be offset from it."""

    def __init__(self, start, heading):
        self.p = np.array(start, float)
        self.t = np.array(heading, float) / np.linalg.norm(heading)
        self.samples = []  # (point, normal, label)

    def _add(self, p, n, label):
        self.samples.append((np.array(p), np.array(n), label))

    def straight(self, length, label):
        if abs(length) < 1e-6:
            if not self.samples:
                self._add(self.p, left(self.t), label)
            return
        count = max(2, int(abs(length) / 3))
        for i in range(count + (0 if self.samples else 1)):
            k = i + (1 if self.samples else 0)
            self._add(self.p + self.t * length * k / count, left(self.t), label)
        self.p = self.p + self.t * length

    def arc(self, radius, turn, label):
        """Turn by `turn` radians (positive: to the left) on a circle of radius."""
        side = 1.0 if turn > 0 else -1.0
        centre = self.p + side * radius * left(self.t)
        start = math.atan2(*(self.p - centre)[::-1])
        count = max(4, int(abs(turn) * radius / 3))
        for i in range(1, count + 1):
            a = start + turn * i / count
            p = centre + radius * unit(a)
            t = side * left(p - centre) / radius
            self._add(p, left(t), label)
        self.p = self.samples[-1][0]
        heading = start + turn
        self.t = side * left(unit(heading))

    def to_line(self, q, s, side, lead, label_straight, label_arc, radius=None):
        """Go straight, then turn (side +1 left, -1 right) onto the line q + b*s, heading
        along s, arriving at b = -lead (lead px before q). Lines that are parallel take a
        half turn of the radius their distance gives; others a radius found to arrive there."""
        cross = float(self.t[0] * s[1] - self.t[1] * s[0])
        if abs(cross) < 1e-9:  # parallel: a half turn
            gap = float(np.dot(q - self.p, side * left(self.t)))
            radius = gap / 2
            # arriving at b = -lead: the turn starts where its end is lead before q
            a = float(np.dot(q - lead * s - self.p, self.t))
            if a < 0:
                raise ValueError(f'the half turn would start {a:.0f} px behind the straight')
            self.straight(a, label_straight)
            self.arc(radius, side * math.pi, label_arc)
            return radius
        turn = math.atan2(cross, float(np.dot(self.t, s)))
        if side * turn < 0:
            turn += side * 2 * math.pi

        def arrive(r):
            off_a = self.p + side * r * left(self.t)
            off_b = q + side * r * left(s)
            a, b = line_cross(off_a, self.t, off_b, s)
            return a, b

        lo, hi = 5.0, 600.0
        for _ in range(80):
            mid = (lo + hi) / 2
            a, b = arrive(mid)
            # a larger radius arrives later along s when the turn is under a half turn, earlier past it
            if (b > -lead) == (abs(turn) < math.pi):
                hi = mid
            else:
                lo = mid
        radius = (lo + hi) / 2
        a, b = arrive(radius)
        if a < 0 or abs(b + lead) > 1:
            raise ValueError(f'no turn arrives {lead} px before the corner (a {a:.0f}, b {b:.0f})')
        self.straight(a, label_straight)
        self.arc(radius, turn, label_arc)
        return radius


def arm_ribbon(k, n, laid, p):
    """The centreline of arm k (of n) as it is in this picture.

    laid: 'cross' (straight out), 'one' (crowned once), 'two' (crowned twice).
    p: the sizes (see KNOTS)."""
    alpha = 2 * math.pi / n
    theta = -math.pi / 2 + k * alpha          # arm 0, the ends, points down
    s1 = p['first']                           # +1 anticlockwise, -1 clockwise
    u = unit(theta)
    r = Ribbon(p['ear'] * u, u)
    if laid == 'cross':
        r.straight(p['reach'] - p['ear'], 'O1')
        return r, None
    one = p['one']
    # The fold lies along the edge of the polygon facing the next arm (in the crown's turn).
    psi = theta + s1 * alpha
    normal = unit(psi)
    travel = s1 * left(normal)
    half = one['h'] * math.tan(alpha / 2)
    edge_from = one['h'] * normal - half * travel    # the corner with the fold before
    r.to_line(edge_from, travel, s1, one['lead'], 'O1', 'A1')
    past = one['lead'] + 2 * half + one['past']   # on, past the corner with the fold after
    if laid == 'one':
        r.straight(past + one['tail'], 'R1')
        return r, (r.p, r.t)
    r.straight(past, 'R1')
    two = p['two']
    s2 = p['second']
    # The second crown: the arms now leave along these lines; each folds over its
    # neighbour in the second crown's turn, along the edge of a larger polygon.
    heading = math.atan2(r.t[1], r.t[0])
    psi2 = heading + s2 * alpha
    normal2 = unit(psi2)
    travel2 = s2 * left(normal2)
    half2 = two['h'] * math.tan(alpha / 2)
    edge2 = two['h'] * normal2 - half2 * travel2
    r.straight(two['out'], 'O2')
    r.to_line(edge2, travel2, s2, two['lead'], 'O2', 'A2')
    r.straight(two['lead'] + 2 * half2 + two['past'] + two['tail'], 'R2')
    return r, (r.p, r.t)


def legs(ribbon, gap):
    """The two legs of a ribbon: (right, left) as lists of (point, label)."""
    right = [(p - n * gap / 2, lab) for p, n, lab in ribbon.samples]
    left_ = [(p + n * gap / 2, lab) for p, n, lab in ribbon.samples]
    return right, left_


def bend(a, b, heading, label):
    """A round bend from the end of one leg (a) to the end of the other (b), bulging along heading."""
    centre = (a + b) / 2
    radius = np.linalg.norm(b - a) / 2
    side = (a - centre) / radius
    pts = []
    for i in range(1, 16):
        ang = math.pi * i / 16
        pts.append((centre + radius * (math.cos(ang) * side + math.sin(ang) * heading * 1.6), label))
    return pts


def bezier(p0, t0, p1, t1, label, count=14):
    """From p0 heading t0 to p1 arriving heading t1."""
    d = np.linalg.norm(p1 - p0) * 0.45
    c0, c1 = p0 + t0 * d, p1 - t1 * d
    out = []
    for i in range(1, count):
        s = i / count
        q = (1 - s) ** 3 * p0 + 3 * (1 - s) ** 2 * s * c0 + 3 * (1 - s) * s * s * c1 + s ** 3 * p1
        out.append((q, label))
    return out


def cord(n, laid, p):
    """The whole cord, as (points, labels): from one end round every arm to the other end.
    A label is (arm, part)."""
    gap = p['gap']
    ribbons = [arm_ribbon(k, n, laid, p) for k in range(n)]
    pts = []

    def put(seq, arm):
        for q, lab in seq:
            pts.append((q, (arm, lab)))

    # Arm 0 is the ends: start at the end of its left leg and come in to the centre,
    # then round every other arm (out along its right leg, round its bend, back along
    # its left leg), each joined to the last by an ear, and out along arm 0's right leg.
    _, left0 = legs(ribbons[0][0], gap)
    put(list(reversed(left0)), 0)
    for k in list(range(1, n)) + [0]:
        before = ribbons[(k - 1) % n][0]
        ribbon = ribbons[k][0]
        right_k, left_k = legs(ribbon, gap)
        put(bezier(pts[-1][0], -unit_of(before), right_k[0][0], unit_of(ribbon), 'ear'), k)
        put(right_k, k)
        if k == 0:
            break
        put(bend(right_k[-1][0], left_k[-1][0], ribbon.t, right_k[-1][1]), k)
        put(list(reversed(left_k)), k)
    return pts


def unit_of(ribbon):
    t = ribbon.samples[1][0] - ribbon.samples[0][0]
    return t / np.linalg.norm(t)


# ------------------------------------------------------------ over and under
def on_top(a, b, n, p):
    """True if the part labelled a lies over the part labelled b where they cross.
    A label is (arm, part). Raises for a crossing the knot should not have."""
    (ka, pa), (kb, pb) = a, b
    s1, s2 = p.get('first', 1), p.get('second', -1)
    # In a crown turning s, arm k folds over arm k + s ("next"), after arm k - s.
    layer = {'O1': 1, 'A1': 1, 'R1': 1, 'ear': 1, 'O2': 1, 'A2': 2, 'R2': 2}
    if layer[pa] != layer[pb]:
        return layer[pa] > layer[pb]          # the second crown lies on the first
    if layer[pa] == 2:
        s, fold, base = s2, 'R2', 'O2'
    else:
        s, fold, base = s1, 'R1', 'O1'
    nxt = lambda k: (k + s) % n
    if pa == fold and pb == fold:
        if kb == (ka - s) % n:
            return True
        if kb == nxt(ka):
            return False
    if pa == fold and pb == base and kb == nxt(ka):
        return True
    if pb == fold and pa == base and ka == nxt(kb):
        return False
    raise ValueError(f'unexpected crossing: arm {ka} {pa} with arm {kb} {pb}')


def crossings(points):
    """Every crossing of the polyline with itself: (i, j, where) for segments i < j."""
    xy = np.array([q for q, _ in points])
    found = []
    seg_a, seg_b = xy[:-1], xy[1:]
    for i in range(len(seg_a)):
        p, r = seg_a[i], seg_b[i] - seg_a[i]
        j = np.arange(i + 2, len(seg_a))
        if not len(j):
            continue
        q, s = seg_a[j], seg_b[j] - seg_a[j]
        denom = r[0] * s[:, 1] - r[1] * s[:, 0]
        ok = np.abs(denom) > 1e-12
        qp = q - p
        t = np.where(ok, (qp[:, 0] * s[:, 1] - qp[:, 1] * s[:, 0]) / np.where(ok, denom, 1), -1)
        w = np.where(ok, (qp[:, 0] * r[1] - qp[:, 1] * r[0]) / np.where(ok, denom, 1), -1)
        hit = ok & (t >= 0) & (t < 1) & (w >= 0) & (w < 1)
        for jj, tt in zip(j[hit], t[hit]):
            found.append((i, int(jj), p + tt * r))
    return found


def pattern(points, n, p):
    """Over and under along the cord: (letters, crossings, arc length of every point,
    arc length of every pass through a crossing). A crossing is passed twice, once
    over (O) and once under (U), and the letters follow the cord from its first point."""
    arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff([q for q, _ in points], axis=0), axis=1))])
    passes = []
    for i, j, _ in crossings(points):
        over = on_top(points[i][1], points[j][1], n, p)
        passes += [(arc[i], 'O' if over else 'U'), (arc[j], 'U' if over else 'O')]
    passes.sort()
    return ''.join(letter for _, letter in passes), len(passes) // 2, arc, [s for s, _ in passes]


def resample(points, spacing):
    """Points about spacing apart along the cord, keeping their labels."""
    out = [points[0]]
    run = 0.0
    for a, b in zip(points, points[1:]):
        run += float(np.linalg.norm(b[0] - a[0]))
        if run >= spacing:
            out.append(b)
            run = 0.0
    if out[-1] is not points[-1]:
        out.append(points[-1])
    return out


def thin(points, arc, passes, most=395, clear=16.0):
    """The points to keep (draw takes at most 400 a cord): close together on bends, far
    apart on straights, and none within clear px of a crossing."""
    xy = np.array([q for q, _ in points])
    near = np.zeros(len(xy), bool)
    for s in passes:
        near |= np.abs(arc - s) < clear
    tries = [(straight, turned) for turned in (0.12, 0.16, 0.2, 0.26, 0.32, 0.4)
             for straight in (40.0, 60.0, 80.0, 110.0)]
    for straight, turned in tries:          # the closest spacing that fits
        keep, last, turn = [0], 0, 0.0
        for i in range(1, len(xy) - 1):
            run = float(np.linalg.norm(xy[i] - xy[last]))
            a, b = xy[i] - xy[i - 1], xy[i + 1] - xy[i]
            turn += abs(math.atan2(a[0] * b[1] - a[1] * b[0], float(np.dot(a, b))))
            if near[i]:
                continue
            if run >= straight or (turn >= turned and run >= 6):
                keep.append(i)
                last, turn = i, 0.0
        keep.append(len(xy) - 1)
        if len(keep) <= most:
            return keep
    raise ValueError(f'the cord needs more than {most} points')


def screen(q):
    return [round(float(CENTRE[0] + q[0]), 1), round(float(CENTRE[1] - q[1]), 1)]


# ------------------------------------------------------------------ arrows
def arc_arrow(radius, a0, a1, count=5):
    return {'points': [screen(radius * unit(a0 + (a1 - a0) * i / (count - 1))) for i in range(count)]}


def fold_arrows(n, radius, turn, start=-math.pi / 2):
    """One arrow per arm, from beside it round to the next arm, in the crown's turn."""
    alpha = 2 * math.pi / n
    out = []
    for k in range(n):
        a = start + k * alpha
        out.append(arc_arrow(radius, a + turn * alpha * 0.18, a + turn * alpha * 0.82))
    return out[:8]


def pull_arrows(n, p, laid):
    """An arrow out beyond the end of every arm: pull to tighten."""
    out = []
    for k in range(n):
        ribbon, end = arm_ribbon(k, n, laid, p)
        tip, t = end
        start = tip + t * (40 if k else 30)
        out.append({'points': [screen(start), screen(start + t * 70)]})
    return out[:8]


# ------------------------------------------------------------------ the steps
def step_cord(n, laid, p, color):
    fine = resample(cord(n, laid, p), 4.0)
    letters, count, arc, passes = pattern(fine, n, p)    # from the fine cord, then fewer points
    pts = [fine[i] for i in thin(fine, arc, passes)]
    item = {'label': 'Cord', 'color': color, 'width': p['width'],
            'points': [screen(q) for q, _ in pts]}
    if count:
        item['pattern'] = letters   # O or U at every crossing, in order from the first point
    return item, count


def design(knot):
    n, p = knot['arms'], knot['sizes']
    steps = []
    for number, step in enumerate(knot['steps']):
        sizes = dict(p, **step.get('sizes', {}))
        for key in ('one', 'two'):
            if key in p or key in step.get('sizes', {}):
                sizes[key] = dict(p.get(key, {}), **step.get('sizes', {}).get(key, {}))
        item, count = step_cord(n, step['laid'], sizes, knot['color'])
        arrows = []
        if step.get('arrows') == 'first':
            arrows = fold_arrows(n, sizes['reach'] * 0.82, sizes['first'])
        elif step.get('arrows') == 'second':
            arrows = fold_arrows(n, step['arrow_radius'], sizes['second'],
                                 start=-math.pi / 2 + sizes['first'] * (math.pi / 2 + 2 * math.pi / n))
        elif step.get('arrows') == 'pull':
            arrows = pull_arrows(n, sizes, step['laid'])
        entry = {'title': step['title'], 'cords': [item]}
        if knot.get('arrow_color'):
            arrows = [dict(a, color=knot['arrow_color']) for a in arrows]
        if arrows:
            entry['arrows'] = arrows
        steps.append(entry)
        print(f"  step {number + 1}: {step['laid']}, {count} crossings")
    return {'name': knot['title'], 'steps': steps}


GOOD_LUCK = {'gap': 48, 'width': 16, 'ear': 70, 'reach': 300, 'first': 1, 'second': -1}

KNOTS = {
    # Steps 3 and 4 of the good luck knot drawn by hand in the app (steps 1 and 2,
    # steps/good_luck_knot_crowned/): the snug first crown, then the second, clockwise.
    'good_luck_knot_crowned': {
        'title': 'Good luck knot, tied by crowning',
        'after': 2,
        'arms': 4,
        'color': '#7a8c30',
        'arrow_color': '#c83e4d',
        'sizes': dict(GOOD_LUCK, ear=70, reach=340,
                      one={'h': 140, 'lead': 55, 'past': 60, 'tail': 260},
                      two={'h': 380, 'lead': 70, 'out': 0, 'past': 80, 'tail': 110}),
        'steps': [
            {'laid': 'one', 'arrows': 'second', 'arrow_radius': 380,
             'title': 'Pull it snug, then crown clockwise'},
            {'laid': 'two', 'arrows': 'pull',
             'title': 'The second crown, on top of the first'},
        ],
    },
    'chrysanthemum_knot': {
        'title': 'Chrysanthemum knot',
        'arms': 4,
        'color': 'gold',
        'sizes': dict(GOOD_LUCK, second=1, ear=80, reach=340,
                      one={'h': 150, 'lead': 65, 'past': 65, 'tail': 130},
                      two={'h': 320, 'lead': 60, 'out': 0, 'past': 70, 'tail': 110}),
        'steps': [
            {'laid': 'cross', 'arrows': 'first',
             'title': 'Lay the cord in a cross: three bights and the two ends'},
            {'laid': 'one', 'arrows': 'pull',
             'title': 'Crown anticlockwise: each bight over the next'},
            {'laid': 'one', 'arrows': 'second', 'arrow_radius': 340,
             'sizes': {'one': {'h': 124, 'lead': 50, 'past': 55, 'tail': 250}, 'ear': 66},
             'title': 'Pull it snug, then crown anticlockwise again'},
            {'laid': 'two', 'arrows': 'pull',
             'sizes': {'one': {'h': 124, 'lead': 50, 'past': 55, 'tail': 250}, 'ear': 66},
             'title': 'The second crown, the same way round'},
        ],
    },
    'five_sided_good_luck_knot': {
        'title': 'Five-sided good luck knot',
        'arms': 5,
        'color': 'teal',
        'sizes': dict(GOOD_LUCK, ear=90, reach=380,
                      one={'h': 180, 'lead': 70, 'past': 70, 'tail': 130},
                      two={'h': 420, 'lead': 60, 'out': 0, 'past': 70, 'tail': 110}),
        'steps': [
            {'laid': 'cross', 'arrows': 'first',
             'title': 'Lay the cord in a star: four bights and the two ends'},
            {'laid': 'one', 'arrows': 'pull',
             'title': 'Crown anticlockwise: each bight over the next'},
            {'laid': 'one', 'arrows': 'second', 'arrow_radius': 420,
             'sizes': {'one': {'h': 140, 'lead': 50, 'past': 55, 'tail': 300}, 'ear': 72},
             'title': 'Pull it snug, then crown clockwise'},
            {'laid': 'two', 'arrows': 'pull',
             'sizes': {'one': {'h': 140, 'lead': 50, 'past': 55, 'tail': 300}, 'ear': 72},
             'title': 'The second crown, on top of the first'},
        ],
    },
}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--only', nargs='*', help='knots to make (default: all)')
    parser.add_argument('--spec-only', action='store_true', help='write the designs, do not draw them')
    parser.add_argument('--out', help='folder for the drawn steps instead of the library (to try them)')
    args = parser.parse_args(argv)
    for name, knot in KNOTS.items():
        if args.only and name not in args.only:
            continue
        print(name)
        spec = design(knot)
        spec_path = FOLDER / 'spec' / f'{name}.json'
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(json.dumps(spec, indent=1) + '\n', encoding='utf-8')
        if args.spec_only:
            continue
        out = Path(args.out) / name if args.out else FOLDER / 'steps' / name
        after = knot.get('after', 0)    # steps drawn by hand before these, kept as they are
        drawn = out / 'drawn' if after else out
        subprocess.run([sys.executable, '-m', 'openstrand', 'draw-steps', str(spec_path), '--out-dir', str(drawn)],
                       cwd=ROOT, check=True)
        if after:
            for number in range(1, len(knot['steps']) + 1):
                for kind in ('json', 'png'):
                    made = drawn / f'step_{number}.{kind}'
                    if made.exists():
                        made.replace(out / f'step_{number + after}.{kind}')
        if not args.out:  # the library keeps the projects, and one picture of all the steps under images/
            for picture in out.glob('step_*.png'):
                picture.unlink()
            if after:
                (drawn / 'steps.png').unlink()
                drawn.rmdir()
            else:
                images = FOLDER / 'images'
                images.mkdir(exist_ok=True)
                (out / 'steps.png').replace(images / f'{name}_steps.png')


if __name__ == '__main__':
    main()
