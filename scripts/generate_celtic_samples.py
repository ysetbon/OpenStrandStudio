"""Build the Celtic and Norse knotwork samples in knot_samples/celtic/.

Run from any directory: python scripts/generate_celtic_samples.py [--only NAME ...] [--no-preview]

Each design is a closed centerline (or several) fitted into attached strands
and woven so every cord alternates over and under, the rule all Celtic and
Norse interlace follows. Geometry and weaving reuse the knot sample tools.

Outputs:
    knot_samples/celtic/json/<name>.json     OpenStrandStudio project
    knot_samples/celtic/images/<name>.png    capture of the real canvas, with shadows
"""
import argparse
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_creative_samples import (Scene, QApplication, serialize_project_state,
                                       validate, AppPreview, woven, MaskedStrand)
from generate_knot_samples import OUT, CENTRE, circle, rounded_polygon
from sample_geometry import parametric

# Old-metal and enamel tones of insular and Viking-age metalwork.
ANTIQUE_GOLD, BRONZE, IRON, OXBLOOD, FOREST, SLATE = (
    '#c9a227', '#a8692f', '#3f4a56', '#8e2b2b', '#2f6b4f', '#2d4b6e')


def squared(r_of_theta, squareness, turn=0.0):
    """Push a round, star-shaped curve towards a square (squareness 0 = unchanged)."""
    def fn(theta):
        a = theta - turn
        p = 2 + 6 * squareness
        k = (abs(math.cos(a)) ** p + abs(math.sin(a)) ** p) ** (-1 / p)
        return r_of_theta(theta) * k
    return fn


def shield_knot(centre, r_in, r_out, squareness=.45):
    """A Carrick mat (3 leads x 4 bights) squared off with its bights in the corners."""
    mean, swing = (r_out + r_in) / 2, (r_out - r_in) / 2
    radius = squared(lambda t: mean + swing * math.cos(4 * t / 3), squareness, turn=math.pi / 4)

    def point(t):
        r = radius(t) / (1 + .3 * squareness)
        return centre[0] + r * math.sin(t), centre[1] - r * math.cos(t)
    return parametric(point, 0, math.tau * 3, closed=True, steps=9000)


def lissajous_panel(centre, half_w, half_h, a, b, phase, squareness=.35):
    """A Lissajous figure (a and b coprime): woven alternately it is a Celtic knot panel.

    The squareness pushes the loops out into the panel corners like the
    rectangular panels of insular manuscripts.
    """
    k = 4 * squareness

    def bend(u):
        return math.tanh(k * u) / math.tanh(k) if k else u

    def point(t):
        return (centre[0] + half_w * bend(math.sin(a * t + phase)),
                centre[1] + half_h * bend(math.sin(b * t)))
    return parametric(point, 0, math.tau, closed=True, steps=12000)


def scenes(only=None):
    def wanted(name):
        return only is None or name in only

    if wanted('valknut'):
        # Three interlaced triangles, each pointing up: the Borromean valknut.
        s = Scene('valknut')
        s.category = 'celtic'
        for k, (color, label) in enumerate([(ANTIQUE_GOLD, 'Triangle 1'), (OXBLOOD, 'Triangle 2'),
                                            (IRON, 'Triangle 3')]):
            # Offsets must not run along the triangles' sides, or sides coincide.
            a = math.radians(120 * k)
            centre = (CENTRE[0] - 30 + 120 * math.cos(a), CENTRE[1] + 120 * math.sin(a))
            s.cord(rounded_polygon(centre, 3, 250, 52, turn=-math.pi / 2), color, label, 26, closed=True)
        s.interlace(woven())
        yield s

    if wanted('celtic_knot_panel'):
        s = Scene('celtic_knot_panel')
        s.category = 'celtic'
        s.cord(lissajous_panel(CENTRE, 330, 270, 3, 4, 0, squareness=.1), FOREST, 'Panel', 26, closed=True)
        s.interlace(woven())
        yield s

    if wanted('shield_knot'):
        # Squared Carrick mat threaded by a ring: the Celtic shield knot.
        s = Scene('shield_knot')
        s.category = 'celtic'
        s.cord(shield_knot(CENTRE, 70, 330, .2), SLATE, 'Shield', 28, closed=True)
        s.cord(circle(CENTRE, 205), ANTIQUE_GOLD, 'Ring', 22, closed=True)
        s.interlace(woven())
        yield s


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', nargs='*')
    parser.add_argument('--no-preview', action='store_true')
    parser.add_argument('--out', type=Path, default=OUT)
    args = parser.parse_args()
    app = QApplication.instance() or QApplication([])
    canvas = SimpleNamespace(selected_strand=None, shadow_enabled=True, show_control_points=False)
    preview = None
    for scene in scenes(args.only):
        data = serialize_project_state(scene.strands, scene.groups, canvas)
        assert len(data['strands']) == len(scene.strands)
        folder = args.out / scene.category
        (folder / 'json').mkdir(parents=True, exist_ok=True)
        path = folder / 'json' / (scene.name + '.json')
        path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
        loaded = validate(json.loads(path.read_text(encoding='utf-8')))
        if not args.no_preview:
            (folder / 'images').mkdir(exist_ok=True)
            preview = preview or AppPreview()
            preview.capture(json.loads(path.read_text(encoding='utf-8')), folder / 'images' / (scene.name + '.png'))
        for warning in scene.warnings:
            print('  WARNING', *warning)
        print(f'{scene.name}: {len(loaded)} layers, '
              f'{sum(isinstance(s, MaskedStrand) for s in loaded)} masks')
    if preview:
        preview.close()
    del app


if __name__ == '__main__':
    main()
