"""Make the craft library's pipa knot (琵琶结), step by step.

Run from any directory: python scripts/build_pipa_knot_steps.py [--spec-only] [--out DIR]

The pipa knot, named for the pear-shaped Chinese lute, is the knot of the
traditional frog button: a small ear at the top and a body of loops, each
inside the last. Its six pictures:

1. The cord makes the ear and one big pear-shaped loop round the standing
   part.
2. The end goes up and round the neck below the ear: up in front, behind
   the ear's two legs, and down over everything (从顶部线圈的下方穿出，再向
   左下方压过所有的线), then down the middle, inside the first loop.
3. Round the bottom, over the standing part, up the right side inside the
   first loop, and up over the neck to the upper left.
4. Round the neck again, behind the ear's legs and down over everything,
   and down the middle inside the last loop.
5. Round the bottom and up the right side inside it, as in 3.
6. Round the neck once more and down through the middle, out at the back
   under the loops' bottoms (调整后，反面烧粘: shaped, then melted and glued
   at the back).

Every round lies over the rounds before it (每圈都压住前面的圈), except where
it passes behind the neck, and the last end goes out behind. The cord is
laid through waypoints as a smooth curve; over and under at every crossing
come from those rules, and `draw-steps` draws it.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_crown_steps import crossings, resample, thin  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'craft_library' / 'chinese_knotting'
NAME = 'pipa_knot'
COLOR = '#e58fd0'
ARROW = '#d7261e'
UNDER = ('behind', 'tuck')       # the parts that pass under whatever they cross


def catmull_rom(points, per=24):
    """A smooth curve through the points (centripetal Catmull-Rom), sampled densely."""
    p = [np.array(q, float) for q in points]
    p = [2 * p[0] - p[1]] + p + [2 * p[-1] - p[-2]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        t0 = 0.0
        t1 = t0 + max(np.linalg.norm(p1 - p0), 1e-6) ** 0.5
        t2 = t1 + max(np.linalg.norm(p2 - p1), 1e-6) ** 0.5
        t3 = t2 + max(np.linalg.norm(p3 - p2), 1e-6) ** 0.5
        for t in np.linspace(t1, t2, per, endpoint=False):
            a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
            a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
            a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
            b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
            b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
            out.append(((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2, i - 1))
    out.append((p[-2], len(points) - 1))
    return out


# The cord laid out from a few sizes (y grows down; x = 0 between the two strands of the neck,
# the standing part on the right and the ear's left leg on the left). Along the neck every part
# crosses at its own height: a round comes up in front APPR above its ring, goes behind at the ring,
# and comes down in front FRONT below it; the rounds are GAP apart, so no two crossings crowd.
SIZES = {'stem_x': 16, 'ring0': -280, 'gap': 150, 'wrap': 55, 'appr': 40, 'fr': 40, 'ear_w': 60, 'ear_h': 120,
         'left': [215, 170, 125], 'right': [215, 170, 130], 'bottom': [470, 425, 380]}


def layout(P):
    sx = P['stem_x']; lx = -sx
    r0, gap, w = P['ring0'], P['gap'], P['wrap']
    r = [r0 + gap * k for k in range(3)]
    a, b, bot = P['left'], P['right'], P['bottom']
    ear = r0 - 70
    out = []
    add = lambda pts, lab: out.extend((p, lab) for p in pts)
    ap, fr = P.get('appr', 40), P.get('fr', 40)
    add([(sx, y) for y in range(560, ear, -60)] + [(sx, ear)], 'stem')
    ew, eh = P.get('ear_w', 40), P.get('ear_h', 80)
    add([(sx + ew * 0.5, ear - eh * 0.45), (sx + ew * 0.55, ear - eh * 0.8), (0, ear - eh),
         (lx - ew * 0.55, ear - eh * 0.8), (lx - ew * 0.5, ear - eh * 0.45), (lx, ear)], 'ear')
    low = r[2] + 60
    add([(lx, y) for y in range(ear + 60, low, 60)] + [(lx, low), (lx - 50, low + 70), (-a[0], 250), (-a[0], 360),
         (-a[0] * 0.6, bot[0] - 25), (0, bot[0]), (b[0] * 0.6, bot[0] - 25), (b[0], 360), (b[0], 200),
         (b[0] * 0.75, r[0] + 30), (b[0] * 0.45, r[0] - ap)], 'loop1')
    for k in range(3):
        y = r[k]
        add([(0, y - ap), (-w - 10, y - ap / 2)], 'front')            # up in front, across the bundle above the ring
        add([(-w, y), (0, y - 4), (w, y)], 'behind')              # behind the bundle
        add([(w + 16, y + 16), (0, y + fr), (-w, y + fr + 20)], 'front')   # down over it in front
        if k < 2:
            add([(-a[k + 1], y + 150), (-a[k + 1], 330), (-a[k + 1] * 0.6, bot[k + 1] - 25)], 'front')
            add([(0, bot[k + 1]), (b[k + 1] * 0.6, bot[k + 1] - 25), (b[k + 1], 330), (b[k + 1], r[k + 1] + 110),
                 (b[k + 1] * 0.85, r[k + 1] + 20), (b[k + 1] * 0.5, r[k + 1] - ap)], 'loop%d' % (k + 2))
        else:
            add([(-22, y + 120)], 'front')
            add([(-22, 330), (-24, bot[0] + 40), (-26, bot[0] + 140)], 'tuck')
    return out


PATH = layout(SIZES)


def step_ends(path):
    """The last waypoint of each step: the first loop; then each round's front, its loop; the end."""
    labels = [lab for _, lab in path]
    last = lambda lab: max(i for i, l in enumerate(labels) if l == lab)
    before = lambda lab: min(i for i, l in enumerate(labels) if l == lab) - 1
    return [last('loop1'), before('loop2'), last('loop2'), before('loop3'), last('loop3'), len(path) - 1]


STEP_ENDS = step_ends(PATH)


def cord_points(upto):
    """The cord from its start to waypoint `upto`, sampled finely, each point with (part, order)."""
    pts = [p for p, _ in PATH[:upto + 1]]
    labels = [lab for _, lab in PATH[:upto + 1]]
    out = []
    for q, seg in catmull_rom(pts):
        out.append((np.array(q) + np.array([600.0, 360.0]), (labels[seg], seg)))
    return out


def on_top(a, b):
    """a, b: (part, waypoint) of the two parts at a crossing, a laid after b."""
    if a[0] in UNDER:
        return False
    if b[0] in UNDER:
        return True
    return True                      # every round lies over what was laid before it


def pattern(points):
    arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff([q for q, _ in points], axis=0), axis=1))])
    passes = []
    for i, j, _ in crossings(points):
        later, earlier = (points[j], points[i]) if j > i else (points[i], points[j])
        over = on_top(later[1], earlier[1])
        li, ei = (j, i) if j > i else (i, j)
        passes += [(arc[li], 'O' if over else 'U'), (arc[ei], 'U' if over else 'O')]
    passes.sort()
    return ''.join(c for _, c in passes), len(passes) // 2, arc, [s for s, _ in passes]


def cord(points, width=14):
    fine = resample(points, 3.0)
    letters, count, arc, passes = pattern(fine)
    pts = [fine[i] for i in thin(fine, arc, passes)]
    item = {'label': 'Cord', 'color': COLOR, 'width': width,
            'points': [[round(float(q[0]), 1), round(float(q[1]), 1)] for q, _ in pts]}
    if count:
        item['pattern'] = letters
    return item, count


def end_arrow(points, length=70, gap=20):
    p, q = points[-1][0], points[-8][0]
    t = (p - q) / np.linalg.norm(p - q)
    a, b = p + t * gap, p + t * (gap + length)
    return {'points': [[round(float(a[0]), 1), round(float(a[1]), 1)], [round(float(b[0]), 1), round(float(b[1]), 1)]],
            'color': ARROW}


TITLES = ['The ear, and one big loop round the standing part',
          'Across the neck, behind the ear, down the middle',
          'Round the bottom and up the right side',
          'Round the neck again, down inside the last loop',
          'Round the bottom and up the right side again',
          'Round the neck once more, out at the back']


def design():
    steps = []
    for k, upto in enumerate(STEP_ENDS):
        points = cord_points(upto)
        item, count = cord(points)
        steps.append({'title': TITLES[k], 'cords': [item], 'arrows': [end_arrow(points)]})
        print(f'  step {k + 1}: {count} crossings')
    return {'name': 'Pipa knot', 'steps': steps}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--spec-only', action='store_true', help='write the design, do not draw it')
    parser.add_argument('--out', help='folder for the drawn steps instead of the library (to try them)')
    args = parser.parse_args(argv)
    spec = design()
    spec_path = FOLDER / 'spec' / f'{NAME}.json'
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(json.dumps(spec, indent=1) + '\n', encoding='utf-8')
    if args.spec_only:
        return
    out = Path(args.out) / NAME if args.out else FOLDER / 'steps' / NAME
    subprocess.run([sys.executable, '-m', 'openstrand', 'draw-steps', str(spec_path), '--out-dir', str(out)],
                   cwd=ROOT, check=True)
    if not args.out:
        for picture in out.glob('step_*.png'):
            picture.unlink()
        (FOLDER / 'images').mkdir(exist_ok=True)
        (out / 'steps.png').replace(FOLDER / 'images' / f'{NAME}_steps.png')


if __name__ == '__main__':
    main()
