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
from generate_knot_samples import OUT, CENTRE, circle, rounded_polygon, turks_head
from sample_geometry import parametric, resample

# Old-metal and enamel tones of insular and Viking-age metalwork.
ANTIQUE_GOLD, BRONZE, IRON, OXBLOOD, FOREST, SLATE = (
    '#c9a227', '#a8692f', '#3f4a56', '#8e2b2b', '#2f6b4f', '#2d4b6e')
# Indian bridal tones: sindoor red, zari gold and emerald.
BRIDAL_RED, ZARI_GOLD, EMERALD = '#a3162c', '#d4a72c', '#1d6b50'
# Metallic thread tones for the ornaments, one per cord.
CLASSIC_GOLD, SILVER, ROSE_SILVER, AMETHYST, CHAMPAGNE_GOLD = (
    '#d4af37', '#b4b9c2', '#d3a6b3', '#8d6aa8', '#e3c27a')


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


def hermite(points, tangents, steps=80):
    """Cubic Hermite curve through points with the given tangent vectors."""
    out = []
    for (p0, p1), (t0, t1) in zip(zip(points, points[1:]), zip(tangents, tangents[1:])):
        for k in range(steps):
            s = k / steps
            h00, h10, h01, h11 = 2*s**3 - 3*s**2 + 1, s**3 - 2*s**2 + s, -2*s**3 + 3*s**2, s**3 - s**2
            out.append((h00*p0[0] + h10*t0[0] + h01*p1[0] + h11*t1[0],
                        h00*p0[1] + h10*t0[1] + h01*p1[1] + h11*t1[1]))
    out.append(points[-1])
    return out


def paisley(centre, curl_centre=(-140, -205), curl_radius=62, curl_angle=150):
    """A paisley (buta) whose tip curls into an exactly round loop and crosses itself once.

    The curl is a 270 degree circular arc. Two short lines tangent to it meet at
    X, sqrt(2) radii from the curl centre in direction curl_angle, where they
    cross at right angles. The body leaves X along the outgoing line and
    returns along the incoming one, so it joins the curl without a kink.
    """
    cx, cy = centre[0] + curl_centre[0], centre[1] + curl_centre[1]
    psi = math.radians(curl_angle)
    X = (cx + curl_radius * math.sqrt(2) * math.cos(psi), cy + curl_radius * math.sqrt(2) * math.sin(psi))
    phi_in, phi_out = psi - math.pi / 4, psi + math.pi / 4 - math.tau
    arc = [(cx + curl_radius * math.cos(phi_in + (phi_out - phi_in) * k / 540),
            cy + curl_radius * math.sin(phi_in + (phi_out - phi_in) * k / 540)) for k in range(541)]
    line_in = [(X[0] + (arc[0][0] - X[0]) * k / 30, X[1] + (arc[0][1] - X[1]) * k / 30) for k in range(30)]
    line_out = [(arc[-1][0] + (X[0] - arc[-1][0]) * k / 30, arc[-1][1] + (X[1] - arc[-1][1]) * k / 30)
                for k in range(1, 30)]
    head_in, head_out = (math.sin(phi_in), -math.cos(phi_in)), (math.sin(phi_out), -math.cos(phi_out))

    body = [(X[0] - 10, X[1] + 120)] + [(centre[0] + x, centre[1] + y) for x, y in [
        (-215, 110), (-130, 220), (20, 262), (180, 180), (250, 0), (195, -170), (70, -280),
        (-70, -322), (-215, -320)]] + [(X[0] - 50, X[1] - 80)]
    pts = [X] + body + [X]
    tangents = []
    for i, p in enumerate(pts):
        if i in (0, len(pts) - 1):
            direction = head_out if i == 0 else head_in
            length = math.dist(p, pts[1] if i == 0 else pts[-2])
        else:
            v = (pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1])
            direction = (v[0] / math.hypot(*v), v[1] / math.hypot(*v))
            length = (math.dist(p, pts[i - 1]) + math.dist(p, pts[i + 1])) / 2
        tangents.append((direction[0] * length, direction[1] * length))
    outline = line_in + arc + line_out + hermite(pts, tangents)
    return resample(outline, 2.0)


def lemniscate(centre, reach, height=1.0, offset=0.0):
    """A lemniscate of Bernoulli (an infinity sign), optionally offset sideways by a constant distance.

    Offsetting to the left of travel puts a cord outside one lobe and inside
    the other, so two cords at +offset and -offset cross at the centre.
    """
    def track(u):
        s = 1 + math.sin(u) ** 2
        return reach * math.cos(u) / s, height * reach * math.sin(u) * math.cos(u) / s

    def point(u):
        x, y = track(u)
        x2, y2 = track(u + 1e-4)
        length = math.hypot(x2 - x, y2 - y)
        return centre[0] + x - offset * (y2 - y) / length, centre[1] + y + offset * (x2 - x) / length
    return parametric(point, 0, math.tau, closed=True, steps=6000)


def infinity_tails(centre, reach, height, steep=1.6):
    """A long, slim infinity whose middle is steepened so it crosses itself at a wide angle.

    The lobes stay flat (height times the lemniscate), but near the centre the
    curve is scaled up to (1 + steep) times as tall, so the self-crossing is
    not a shallow X.
    """
    def point(u):
        s = 1 + math.sin(u) ** 2
        x = reach * math.cos(u) / s
        y = height * reach * math.sin(u) * math.cos(u) / s
        return centre[0] + x, centre[1] + y * (1 + steep * math.exp(-(x / (0.3 * reach)) ** 2))
    return parametric(point, 0, math.tau, closed=True, steps=6000)


def loop_oval(centre, loops=5, step=18, size=120, gap=35):
    """Two rows of round loops, loops pointing out, whose inner arcs interlace in the middle.

    Each row is a prolate cycloid (the path of a point on a rolling wheel's
    spoke, beyond the rim) with the given step per radian and loop size; the
    bottom row is the top row mirrored, shifted half a loop and run backwards.
    The rows are joined at both ends by smooth turns.
    """
    cx, cy = centre
    t0, t1 = -math.pi, math.tau * loops - math.pi

    def row(sign, dx):
        def at(t):
            return (cx + dx + step * (t - (math.pi * loops - math.pi)) - size * math.sin(t),
                    cy + sign * (gap + size * math.cos(t)))
        return [at(t0 + (t1 - t0) * k / 3000) for k in range(3001)]

    top = row(-1, -math.pi * step / 2)
    bottom = list(reversed(row(1, math.pi * step / 2)))

    def turn(a, before, b, after):
        def unit(p, q):
            v = (q[0] - p[0], q[1] - p[1])
            n = math.hypot(*v)
            return v[0] / n, v[1] / n
        reach = 1.6 * max(abs(b[1] - a[1]), 60)
        ta, tb = unit(before, a), unit(b, after)
        return hermite([a, b], [(ta[0] * reach, ta[1] * reach), (tb[0] * reach, tb[1] * reach)])

    right = turn(top[-1], top[-2], bottom[0], bottom[1])
    left = turn(bottom[-1], bottom[-2], top[0], top[1])
    return resample(top + right[1:] + bottom[1:] + left[1:] + [top[0]], 2.0)


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

    if wanted('bridal_lotus_mandala'):
        # Celtic interlace on an Indian lotus: eight gold petals, an emerald ring, a red carrick mat.
        s = Scene('bridal_lotus_mandala')
        s.category = 'celtic'
        s.cord(turks_head(3, 8, 195, 335), ZARI_GOLD, 'Lotus petals', 22, closed=True)
        s.cord(circle(CENTRE, 260), EMERALD, 'Ring', 18, closed=True)
        s.cord(turks_head(3, 4, 55, 145), BRIDAL_RED, 'Heart knot', 22, closed=True)
        s.interlace(woven())
        yield s

    if wanted('bridal_paisley'):
        # A paisley whose curled tip crosses itself, holding a triquetra.
        s = Scene('bridal_paisley')
        s.category = 'celtic'
        cx, cy = CENTRE
        s.cord(paisley((cx, cy + 10)), BRIDAL_RED, 'Paisley', 24, closed=True)
        knot_centre = (cx + 5, cy + 45)
        s.cord(turks_head(2, 3, 60, 165, centre=knot_centre), ZARI_GOLD, 'Triquetra', 18, closed=True)
        s.cord(circle(knot_centre, 139), EMERALD, 'Ring', 14, closed=True)
        s.interlace(woven())
        yield s

    if wanted('infinity_knot'):
        # Two infinity signs side by side: each is outside in one lobe and inside in the other.
        s = Scene('infinity_knot')
        s.category = 'celtic'
        s.cord(lemniscate(CENTRE, 400, 1.5, 50), CLASSIC_GOLD, 'Infinity A', 24, closed=True)
        s.cord(lemniscate(CENTRE, 400, 1.5, -50), SILVER, 'Infinity B', 24, closed=True)
        s.interlace(woven())
        yield s

    if wanted('loop_oval'):
        s = Scene('loop_oval')
        s.category = 'celtic'
        s.cord(loop_oval(CENTRE, step=29, size=192, gap=56), ROSE_SILVER, 'Loops', 18, closed=True)
        s.interlace(woven())
        yield s

    if wanted('tailed_knot'):
        # A 3 x 2 Lissajous knot threaded by a long infinity whose lobes are its tails.
        # Phase pi/8 and the steepened middle keep every crossing at least
        # 57 px (x 1.2 here) from the next, so none of them crowd at the centre.
        s = Scene('tailed_knot')
        s.category = 'celtic'
        s.cord(parametric(lambda t: (CENTRE[0] + 240 * math.sin(3 * t + math.pi / 8), CENTRE[1] + 336 * math.sin(2 * t)),
                          0, math.tau, closed=True, steps=8000), AMETHYST, 'Knot', 20, closed=True)
        s.cord(infinity_tails(CENTRE, 720, .2), CHAMPAGNE_GOLD, 'Tails', 18, closed=True)
        s.interlace(woven())
        yield s

    if wanted('plait_border'):
        # A three-strand Celtic plait: three sine waves a third of a period
        # apart, every crossing at least 72 degrees and 90 px from the next.
        s = Scene('plait_border')
        s.category = 'celtic'
        period, swing = 300, 75
        for k, (color, label) in enumerate([(CLASSIC_GOLD, 'Gold'), (SILVER, 'Silver'), (ROSE_SILVER, 'Rose silver')]):
            s.cord(parametric(lambda x, k=k: (150 + x, CENTRE[1] + swing * math.sin(math.tau * x / period + math.tau * k / 3)),
                              0, period * 5, steps=6000), color, label, 22)
        s.interlace(woven())
        yield s

    if wanted('plait_ring'):
        # The same plait closed into a ring: radius r = 900 + 75 sin(20 theta + k 2pi/3).
        s = Scene('plait_ring')
        s.category = 'celtic'
        for k, (color, label) in enumerate([(CLASSIC_GOLD, 'Gold'), (SILVER, 'Silver'), (ROSE_SILVER, 'Rose silver')]):
            def point(t, k=k):
                r = 900 + 75 * math.sin(20 * t + math.tau * k / 3)
                return CENTRE[0] + r * math.cos(t), CENTRE[1] + r * math.sin(t)
            s.cord(parametric(point, 0, math.tau, closed=True, steps=12000), color, label, 22, closed=True)
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
