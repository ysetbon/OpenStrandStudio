"""Make the craft library's Pan Chang knot, step by step, as Lydia Chen ties it.

Run from any directory: python scripts/build_pan_chang_steps.py [--spec-only] [--out DIR]

The Pan Chang (盘长结, the two-loop pan chang, 二回盘长结) is tied flat on pins
in five pictures (Chen, Chinese Knotting):

1. The cord laid in two upright hairpins (four uprights, A B C D), then
   four rows across them, each over A, under B, over C, under D.
2. The other end lays four more rows between those, alternately over all
   four uprights and under all four.
3. That end weaves up and down twice. Going up it goes under the second and
   fourth rows of step 1 and over the rest; coming down, over only the first
   and third rows of step 1.
4. The ears are pulled out to close the body.
5. The finished knot: a woven square body hung by a corner, three large
   ears, four small ones, the two ends below.

Every row and every upright then crosses the eight it meets under 2, over 1,
under 3, over 1, under 1 (挑二压一挑三压一挑一) or under 1, over 3, under 1,
over 3 (挑一压三挑一压三), or these read the other way, as the Chinese
tutorials say; no strand lies over or under the whole body. The cord is laid out here
from those rules with a turtle (straight runs, round turns), its over and
under at every crossing worked out from them, and drawn with `draw-steps`
into craft_library/chinese_knotting/steps/pan_chang_knot/.
"""
import argparse
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_crown_steps import Ribbon, crossings, resample, thin  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'craft_library' / 'chinese_knotting'
NAME = 'pan_chang_knot'
COLOR = '#c9a95c'
ARROW = '#c83e4d'

UPRIGHTS = ['d1', 'd2', 'A', 'B', 'd3', 'd4', 'C', 'D']     # left to right
ROWS = ['s1', 's2', 'R1', 'R2', 's3', 's4', 'R3', 'R4']       # top to bottom


def on_top(a, b):
    """True if part a lies over part b where they cross (one upright, one row)."""
    if a in ROWS and b in UPRIGHTS:
        return not on_top(b, a)
    if not (a in UPRIGHTS and b in ROWS):
        raise ValueError(f'unexpected crossing: {a} with {b}')
    if a in ('d1', 'd3'):
        return b not in ('R2', 'R4')        # step 3, going up: over all but the 2nd and 4th rows of step 1
    if a in ('d2', 'd4'):
        return b in ('R1', 'R3')            # coming down: over only the 1st and 3rd rows of step 1
    if b in ('s1', 's3'):
        return False                        # step 2: over all four uprights ...
    if b in ('s2', 's4'):
        return True                         # ... and under all four, in turn
    return a in ('B', 'D')                  # step 1: over A, under B, over C, under D


class Turtle(Ribbon):
    """A Ribbon whose straights and turns are measured to a target: x or y reached."""

    def to(self, label, x=None, y=None):
        d = (x - self.p[0]) / self.t[0] if x is not None else (y - self.p[1]) / self.t[1]
        self.straight(d, label)

    def turn(self, radius, degrees, label):
        self.arc(radius, math.radians(degrees), label)


def layout(g):
    """The whole cord in steps of the tying, from the end left at the right of step 1.
    g holds the sizes: the eight uprights' x, the eight rows' y, turns and ears.
    Returns (points as (xy, label), [index where step 1 ends, where step 2 ends])."""
    X = dict(zip(UPRIGHTS, g['x']))
    Y = dict(zip(ROWS, g['y']))
    top, bottom = g['top'], g['bottom']
    left, right = g['left'], g['right']
    # The end of step 1's rows, R4, R3, R2, R1, laid back to front: the loose end first,
    # drawn out from where it leaves row R4 and turned round.
    prefix = []
    if 'tail' in g:
        radius, degrees, lead = g['tail']
        out = Turtle([g['tail_x'], Y['R4']], [1.0, 0.0])
        out.straight(1.0, 'R4')
        out.turn(radius, degrees, 'R4')
        out.straight(lead, 'R4')
        prefix = [(p, lab) for p, _, lab in reversed(out.samples)][:-1]
    t = Turtle([g['tail_x'], Y['R4']], [-1.0, 0.0])
    t.to('R4', x=left)
    t.turn((Y['R4'] - Y['R3']) / 2, 180, 'uR43')
    t.to('R3', x=right)
    t.turn((Y['R3'] - Y['R2']) / 2, -180, 'uR32')
    t.to('R2', x=left)
    t.turn((Y['R2'] - Y['R1']) / 2, 180, 'uR21')
    corner = g['corner']
    rc, lc = g.get('right_corner', corner), g.get('left_corner', corner)   # the two side ears' turns
    t.to('R1', x=g['up_x'] - rc)
    t.turn(rc, -90, 'cR1')
    t.to('xR', y=top)
    t.turn((g['up_x'] - X['D']) / 2, -180, 'aD')
    # The uprights of step 1: D, C, B, A, back to front.
    t.to('D', y=bottom)
    t.turn((X['D'] - X['C']) / 2, 180, 'uDC')
    t.to('C', y=top)
    t.turn((X['C'] - X['B']) / 2, -180, 'aCB')
    t.to('B', y=bottom)
    t.turn((X['B'] - X['A']) / 2, 180, 'uBA')
    t.to('A', y=top)
    t.turn((X['A'] - g['down_x']) / 2, -180, 'aA')
    t.to('xL', y=Y['s1'] - corner)
    step1 = len(t.samples)
    # Step 2: the other end's rows, s1 to s4.
    t.turn(corner, -90, 'cS1')
    t.to('s1', x=right)
    t.turn((Y['s2'] - Y['s1']) / 2, 180, 'u12')
    t.to('s2', x=left)
    t.turn((Y['s3'] - Y['s2']) / 2, -180, 'u23')
    t.to('s3', x=right)
    t.turn((Y['s4'] - Y['s3']) / 2, 180, 'u34')
    t.to('s4', x=g['out_x'] + lc)
    t.turn(lc, -90, 'cS4')
    step2 = len(t.samples)
    # Step 3: up and down twice, d1 to d4.
    t.to('xB', y=g['low_y'] - lc)
    t.turn(lc, -90, 'cB1')
    t.to('xB', x=X['d1'] - lc)
    t.turn(lc, -90, 'cB2')
    t.to('d1', y=top)
    t.turn((X['d2'] - X['d1']) / 2, 180, 'a12')
    t.to('d2', y=bottom)
    t.turn((X['d3'] - X['d2']) / 2, -180, 'u23d')
    t.to('d3', y=top)
    t.turn((X['d4'] - X['d3']) / 2, 180, 'a34')
    t.to('d4', y=g['end_y'])
    if 'end_turn' in g:
        t.turn(g['end_turn'][0], g['end_turn'][1], 'd4')
        t.straight(g['end_lead'], 'd4')
    points = prefix + [(p, lab) for p, _, lab in t.samples]
    return points, [len(prefix) + step1, len(prefix) + step2]


def place(points, g):
    """Points in the picture: turned by g['turn'] degrees about the body's centre, moved to (600, 420)."""
    c = np.array([np.mean(g['x']), np.mean(g['y'])])
    a = math.radians(g.get('turn', 0))
    rot = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    return [((rot @ (p - c)) * g.get('scale', 1) + np.array([600.0, 420.0]), lab) for p, lab in points]


def pattern(points):
    """O or U at every crossing in order along the cord, and where the passes are."""
    arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff([q for q, _ in points], axis=0), axis=1))])
    passes = []
    for i, j, _ in crossings(points):
        over = on_top(points[i][1], points[j][1])
        passes += [(arc[i], 'O' if over else 'U'), (arc[j], 'U' if over else 'O')]
    passes.sort()
    return ''.join(c for _, c in passes), len(passes) // 2, arc, [s for s, _ in passes]


def cord(points, width):
    fine = resample(points, 4.0)
    letters, count, arc, passes = pattern(fine)
    pts = [fine[i] for i in thin(fine, arc, passes)]
    item = {'label': 'Cord', 'color': COLOR, 'width': width,
            'points': [[round(float(q[0]), 1), round(float(q[1]), 1)] for q, _ in pts]}
    if count:
        item['pattern'] = letters
    return item, count


def arrow(a, b):
    return {'points': [[round(float(a[0]), 1), round(float(a[1]), 1)], [round(float(b[0]), 1), round(float(b[1]), 1)]],
            'color': ARROW}


def end_arrow(points, length=70, gap=26, first=False):
    """An arrow beyond the last point of a cord (or its first), along its heading."""
    p, q = (points[0][0], points[5][0]) if first else (points[-1][0], points[-6][0])
    t = (p - q) / np.linalg.norm(p - q)
    return arrow(p + t * gap, p + t * (gap + length))


def ear_arrows(points, labels, length=75, gap=30):
    """An arrow out from the middle of each of these turns: pull the ears."""
    out = []
    centre = np.mean([q for q, _ in points], axis=0)
    for lab in labels:
        part = [q for q, l in points if l == lab]
        tip = max(part, key=lambda q: np.linalg.norm(q - centre))
        t = (tip - centre) / np.linalg.norm(tip - centre)
        out.append(arrow(tip + t * gap, tip + t * (gap + length)))
    return out


# A loose layout to tie on (steps 1-4) and the finished knot (step 5), turned to hang by a corner.
LOOSE = {'x': [0, 44, 120, 164, 240, 284, 360, 404], 'y': [0, 44, 120, 164, 240, 284, 360, 404],
         'top': -60, 'bottom': 464, 'left': -56, 'right': 460, 'corner': 30,
         'up_x': 520, 'down_x': -76, 'out_x': -120, 'low_y': 500, 'end_y': 600,
         'tail_x': 600, 'width': 14}
TIGHT = {'x': [0, 34, 68, 102, 136, 170, 204, 238], 'y': [0, 34, 68, 102, 136, 170, 204, 238],
         'top': -40, 'bottom': 278, 'left': -40, 'right': 278, 'corner': 34,
         'right_corner': 80, 'left_corner': 150,
         'up_x': 470, 'down_x': -232, 'out_x': -300, 'low_y': 520, 'end_y': 340,
         'tail_x': 330, 'tail': (40, 45, 130), 'end_turn': (40, -45), 'end_lead': 130,
         'turn': 45, 'width': 20}


def design():
    steps = []
    loose, (end1, end2) = layout(LOOSE)
    loose = place(loose, LOOSE)
    w = LOOSE['width']
    c1, n1 = cord(loose[:end1], w)
    c2, n2 = cord(loose[:end2], w)
    c3, n3 = cord(loose, w)
    steps.append({'title': 'Two upright hairpins, then four rows: over, under, over, under',
                  'cords': [c1], 'arrows': [end_arrow(loose[:end1], first=True)]})
    steps.append({'title': 'The other end: four rows between them', 'cords': [c2],
                  'arrows': [end_arrow(loose[:end2])]})
    steps.append({'title': 'Weave up and down twice', 'cords': [c3], 'arrows': [end_arrow(loose)]})
    steps.append({'title': 'Pull the ears out', 'keep': ['Cord'],
                  'arrows': ear_arrows(loose, ['aA', 'aCB', 'aD', 'uR32', 'u23', 'u23d', 'cB1', 'uR43'])})
    tight, _ = layout(TIGHT)
    tight = place(tight, TIGHT)
    c5, n5 = cord(tight, TIGHT['width'])
    steps.append({'title': 'The finished knot', 'cords': [c5]})
    for k, n in enumerate((n1, n2, n3, n3, n5), start=1):
        print(f'  step {k}: {n} crossings')
    return {'name': 'Pan Chang knot', 'steps': steps}


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
