"""Designs the commands can make, built with the sample generators in scripts/.

Each function returns (project dict, warnings, source): source names the
published sample a design was copied from, or is None when it was built.
Building a woven design fits its curve with the generators' pure-Python
fitter, which can take a minute; sizes that exist as samples are copied.
"""
import math
from types import SimpleNamespace

from . import ROOT, project

SAMPLE_FOLDERS = (ROOT / 'knot_samples', ROOT / 'mxn_samples')

# Inner radius and cord width of the published Turk's head samples (outer
# radius 290), so the same sizes come out exactly as in knot_samples/.
_TURKS_SAMPLES = {(2, 3): (135, 30), (3, 2): (50, 28), (2, 5): (175, 26), (2, 7): (205, 22),
                  (3, 4): (125, 26), (3, 5): (135, 22), (4, 3): (110, 26), (4, 5): (150, 20)}
_TURKS_SAMPLE_NAMES = {(2, 3): 'trefoil_3_1', (3, 2): 'figure_eight_4_1', (2, 5): 'cinquefoil_5_1',
                       (2, 7): 'septafoil_7_1', (3, 4): 'carrick_mat_3x4', (3, 5): 'turks_head_3x5',
                       (4, 3): 'turks_head_4x3', (4, 5): 'turks_head_4x5'}
TURKS_OUTER = 290


_APP = None


def application():
    """The QApplication the app's code needs; QT_QPA_PLATFORM decides where it draws.

    Kept in a module global: a QApplication nobody holds is destroyed at once.
    """
    global _APP
    from PyQt5 import sip
    from PyQt5.QtWidgets import QApplication
    # Leave Qt's objects alone when Python exits: destroying the hidden
    # render window after the QApplication crashed the process at exit.
    sip.setdestroyonexit(False)
    _APP = QApplication.instance() or _APP or QApplication([])
    return _APP


def _serialize(scene):
    from generate_creative_samples import serialize_project_state
    canvas = SimpleNamespace(selected_strand=None, shadow_enabled=True, show_control_points=False)
    return serialize_project_state(scene.strands, scene.groups, canvas)


def turks_head(leads, bights, color, width=None, inner=None):
    """A Turk's head ring knot woven over and under: leads turns, bights loops on the rim."""
    if not (2 <= leads <= 7 and 2 <= bights <= 13):
        raise ValueError("a Turk's head here needs 2 to 7 leads and 2 to 13 bights")
    common = math.gcd(leads, bights)
    if common != 1:
        nearest = next(b for b in range(bights + 1, bights + leads + 1) if math.gcd(leads, b) == 1)
        raise ValueError(f'{leads} leads and {bights} bights share a factor of {common}, which makes '
                         f'{common} separate cords; pick numbers with no common factor, '
                         f'like {leads} leads and {nearest} bights')
    sample_inner, sample_width = _TURKS_SAMPLES.get((leads, bights), (None, None))
    if inner is None and width is None and (leads, bights) in _TURKS_SAMPLE_NAMES:
        # The same design is published: copy it instead of fitting it again.
        from . import edit
        name = _TURKS_SAMPLE_NAMES[leads, bights]
        data, _, _ = sample(name)
        edit.recolor(data, {1: color})
        return data, [], name
    if inner is None:
        inner = sample_inner or max(50, min(220, round(TURKS_OUTER * (1 - 2.1 / bights))))
    if width is None:
        width = sample_width or max(14, min(30, round(36 - 2.8 * bights)))
    if not 0 < inner < TURKS_OUTER - width:
        raise ValueError(f'--inner must be between 1 and {TURKS_OUTER - width - 1}')
    application()
    import generate_creative_samples as g
    from generate_knot_samples import turks_head as ring
    scene = g.Scene(f'turks_head_{leads}x{bights}')
    scene.cord(ring(leads, bights, inner, TURKS_OUTER), color, "Turk's head", width, closed=True)
    scene.interlace(g.woven())
    return _serialize(scene), scene.warnings, None


def heart(color, width=26):
    """A ribbon heart from one cord, its two ends crossing below the tip."""
    application()
    import generate_creative_samples as g
    from sample_geometry import resample
    cx, cy, depth, reach = 600, 300, 280, 300
    # The samples' heart outline starts and ends at its rounded tip. Leave
    # the tip out; each side then runs on straight past it, so the two ends
    # cross below it, the way a ribbon is tied.
    ring = g.heart_outline((cx, cy), lobe_gap=140, lobe=145, depth=depth, dip=24)
    inside = [k for k, p in enumerate(ring) if p[1] < cy + depth]
    body = ring[inside[0]:inside[-1] + 1]

    def tail(end, inward):
        dx, dy = end[0] - inward[0], end[1] - inward[1]
        length = math.hypot(dx, dy)
        return [(end[0] + dx / length * reach * k / 40, end[1] + dy / length * reach * k / 40) for k in range(1, 41)]
    start = list(reversed(tail(body[0], body[5])))
    finish = tail(body[-1], body[-6])
    scene = g.Scene('heart')
    scene.cord(resample(start + list(body) + finish, 2.0), color, 'Heart', width)
    scene.interlace(g.woven())
    return _serialize(scene), scene.warnings, None


def mxn(m, n, hand='lh', stretch=False):
    """An MxN stitch from mxn_samples/: m vertical ribbons, n horizontal ones."""
    if not (1 <= m <= 8 and 1 <= n <= 8):
        raise ValueError('an MxN stitch needs --m and --n from 1 to 8')
    if hand not in ('lh', 'rh'):
        raise ValueError('--hand is lh (left hand) or rh (right hand)')
    kind, suffix = ('stretched', '_stretch') if stretch else ('starting', '')
    path = ROOT / 'mxn_samples' / hand / kind / 'json' / f'mxn_{hand}{suffix}_{m}x{n}.json'
    return project.read(path), [], path.stem


def samples():
    """{name: path} for every ready-made design in knot_samples/ and mxn_samples/."""
    found = {}
    for folder in SAMPLE_FOLDERS:
        for path in sorted(folder.glob('**/json/*.json')):
            found.setdefault(path.stem, path)
    return found


def sample(name):
    found = samples()
    if name not in found:
        close = [n for n in found if name.lower() in n.lower()][:8]
        hint = f"; did you mean: {', '.join(close)}" if close else '; run "openstrand samples" to list them'
        raise ValueError(f'no sample named "{name}"{hint}')
    return project.read(found[name]), [], name
