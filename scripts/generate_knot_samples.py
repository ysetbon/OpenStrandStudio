"""Build the knot and link samples in knot_samples/ with the application's own serializer.

Run from any directory: python scripts/generate_knot_samples.py [--only NAME ...] [--no-preview]

Every design is a closed centerline (or several) fitted into attached strands by
the same code as the creative samples, then woven so each cord alternates over
and under along its whole length. Alternating diagrams of these curves are the
classical knots and links named after them.

Outputs, per category folder (knots, turks_heads, links):
    knot_samples/<category>/json/<name>.json     OpenStrandStudio project
    knot_samples/<category>/images/<name>.png    capture of the real canvas, with shadows
"""
import argparse
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_creative_samples as g
from generate_creative_samples import (ROOT, Scene, QApplication, serialize_project_state,
                                       validate, AppPreview, woven, MaskedStrand)
from sample_geometry import parametric, resample

OUT = ROOT / 'knot_samples'
CENTRE = (600, 400)

TEAL, GOLD, ROSE, VIOLET, JADE, COPPER = '#257d98', '#e5a13b', '#d56272', '#6554a4', '#399780', '#b76c40'
INK, CRIMSON, SKY = '#2b3a67', '#c83e4d', '#4aa3df'


def turks_head(leads, bights, r_in, r_out, centre=CENTRE):
    """A rosette ring: r = mean + swing * cos(bights * theta / leads), leads turns around.

    leads and bights must be coprime. The curve is a single closed cord with
    bights * (leads - 1) crossings; woven alternately it is the Turk's head
    with that many leads and bights (2 x 3 is the trefoil, 3 x 2 the
    figure-eight, 3 x 4 the Carrick mat).
    """
    assert math.gcd(leads, bights) == 1
    mean, swing = (r_out + r_in) / 2, (r_out - r_in) / 2

    def point(t):
        r = mean + swing * math.cos(bights * t / leads)
        return centre[0] + r * math.sin(t), centre[1] - r * math.cos(t)
    return parametric(point, 0, math.tau * leads, closed=True, steps=9000)


def circle(centre, radius):
    return parametric(lambda t: (centre[0] + radius * math.cos(t), centre[1] + radius * math.sin(t)),
                      0, math.tau, closed=True, steps=2400)


def superellipse(centre, a, b, power=2.6, tilt=0.0):
    def point(t):
        c, s = math.cos(t), math.sin(t)
        x = a * math.copysign(abs(c) ** (2 / power), c)
        y = b * math.copysign(abs(s) ** (2 / power), s)
        return (centre[0] + x * math.cos(tilt) - y * math.sin(tilt),
                centre[1] + x * math.sin(tilt) + y * math.cos(tilt))
    return parametric(point, 0, math.tau, closed=True, steps=3600)


def rounded_polygon(centre, sides, reach, rounding, turn=0.0):
    """A regular polygon with rounded corners; reach is the distance to the farthest point."""
    inner = reach - rounding
    pts = []
    for k in range(sides):
        vertex = turn + math.tau * k / sides
        cx, cy = centre[0] + inner * math.cos(vertex), centre[1] + inner * math.sin(vertex)
        a0, a1 = vertex - math.pi / sides, vertex + math.pi / sides
        for j in range(61):
            a = a0 + (a1 - a0) * j / 60
            pts.append((cx + rounding * math.cos(a), cy + rounding * math.sin(a)))
    pts.append(pts[0])
    return resample(pts, 2.0)


CATEGORIES = {'knots': 'Single knots', 'turks_heads': "Turk's heads", 'links': 'Links and chains'}


def scenes(only=None):
    def wanted(name):
        return only is None or name in only

    def ring_scene(name, category, leads, bights, r_in, r_out, color, width):
        s = Scene(name)
        s.category = category
        s.cord(turks_head(leads, bights, r_in, r_out), color, 'Knot', width, closed=True)
        s.interlace(woven())
        return s

    # --- single knots: the first rows of the knot table -------------------
    for name, leads, bights, r_in, r_out, color, width in [
            ('trefoil_3_1', 2, 3, 135, 290, TEAL, 30),
            ('figure_eight_4_1', 3, 2, 50, 290, ROSE, 28),
            ('cinquefoil_5_1', 2, 5, 175, 290, VIOLET, 26),
            ('septafoil_7_1', 2, 7, 205, 290, JADE, 22)]:
        if wanted(name):
            yield ring_scene(name, 'knots', leads, bights, r_in, r_out, color, width)

    # --- Turk's heads: the ring knots sailors weave -----------------------
    for name, leads, bights, r_in, r_out, color, width in [
            ('carrick_mat_3x4', 3, 4, 125, 290, COPPER, 26),
            ('turks_head_3x5', 3, 5, 135, 290, TEAL, 22),
            ('turks_head_4x3', 4, 3, 110, 290, GOLD, 26),
            ('turks_head_4x5', 4, 5, 150, 300, INK, 20)]:
        if wanted(name):
            yield ring_scene(name, 'turks_heads', leads, bights, r_in, r_out, color, width)

    # --- links: several closed cords, each alternating ---------------------
    if wanted('hopf_link'):
        s = Scene('hopf_link')
        s.category = 'links'
        cx, cy = CENTRE
        s.cord(circle((cx - 115, cy), 205), TEAL, 'Ring A', 30, closed=True)
        s.cord(circle((cx + 115, cy), 205), GOLD, 'Ring B', 30, closed=True)
        s.interlace(woven())
        yield s

    if wanted('solomons_knot'):
        s = Scene('solomons_knot')
        s.category = 'links'
        s.cord(superellipse(CENTRE, 300, 175), VIOLET, 'Loop A', 30, closed=True)
        s.cord(superellipse(CENTRE, 175, 300), GOLD, 'Loop B', 30, closed=True)
        s.interlace(woven())
        yield s

    if wanted('borromean_rings'):
        s = Scene('borromean_rings')
        s.category = 'links'
        for k, color in enumerate([CRIMSON, SKY, GOLD]):
            a = math.radians(-90 + 120 * k)
            s.cord(circle((CENTRE[0] + 120 * math.cos(a), CENTRE[1] + 120 * math.sin(a) + 20), 205),
                   color, f'Ring {k + 1}', 28, closed=True)
        s.interlace(woven())
        yield s

    if wanted('interlaced_triangles'):
        s = Scene('interlaced_triangles')
        s.category = 'links'
        s.cord(rounded_polygon(CENTRE, 3, 300, 55, turn=-math.pi / 2), INK, 'Triangle up', 28, closed=True)
        s.cord(rounded_polygon(CENTRE, 3, 300, 55, turn=math.pi / 2), GOLD, 'Triangle down', 28, closed=True)
        s.interlace(woven())
        yield s

    if wanted('five_ring_chain'):
        s = Scene('five_ring_chain')
        s.category = 'links'
        for k, color in enumerate([SKY, GOLD, CRIMSON, JADE, VIOLET]):
            s.cord(circle((CENTRE[0] + (k - 2) * 155, CENTRE[1] + (35 if k % 2 else -35)), 108),
                   color, f'Ring {k + 1}', 24, closed=True)
        s.interlace(woven())
        yield s

    if wanted('six_link_necklace'):
        s = Scene('six_link_necklace')
        s.category = 'links'
        colors = [TEAL, GOLD, ROSE, VIOLET, JADE, COPPER]
        for k in range(6):
            a = math.radians(-90 + 60 * k)
            s.cord(circle((CENTRE[0] + 215 * math.cos(a), CENTRE[1] + 215 * math.sin(a)), 135),
                   colors[k], f'Link {k + 1}', 24, closed=True)
        s.interlace(woven())
        yield s

    if wanted('triquetra'):
        s = Scene('triquetra')
        s.category = 'knots'
        s.cord(turks_head(2, 3, 110, 300), JADE, 'Trefoil', 28, closed=True)
        s.cord(circle(CENTRE, 252), GOLD, 'Ring', 24, closed=True)
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
        print(f'{scene.name}: {len(loaded)} layers, {sum(isinstance(s, MaskedStrand) for s in loaded)} masks, '
              f'{len(scene.groups)} groups, weave conflicts {getattr(scene, "woven_conflicts", "?")}', flush=True)
    if preview:
        preview.close()


if __name__ == '__main__':
    main()
