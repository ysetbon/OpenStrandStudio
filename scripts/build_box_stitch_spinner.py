"""Render the OpenStrand logo, a box stitch, tied and then continued level after level, frame
by frame with OpenStrand Studio's own canvas.

The Assistant's working line no longer plays these frames: it draws the stitch itself, live,
from the same geometry (src/claude_stitch.py), so a level can be k = 0 as well as k = 1 and the
stitch can start again from the plus. This script stays as the reference render of that
geometry by the app's canvas, and it makes the Assistant button's pressed picture
(src/images/assistant_pressed.png).

The steps, in the logo's colours (set 1 blue, set 2 orange), right-handed like the logo:

1. A plus: 1_1 across, 2_1 up.
2. It turns to an x, the way 1_1 and 2_1 lie in the 1x1 starting stitch.
3. The attached strands grow from both ends of both (1_2, 1_3, then 2_2, 2_3), over and
   under as in the logo (the sample's masks). They grow to the length they keep after the
   stretch, so the stretch only moves them closer together.
4. The stitch stretches into the stretched 1x1 starting stitch, keeping its centre.
5. k = 1, level after level: each level is a New Level holding one k = 1 round. The four
   newest strands shorten and four new ones grow from their ends, with two masks so every
   orange strand goes over one blue strand and under the other.

One k = 1 level turns the pattern 2*atan(2) = 126.87 degrees, the one angle at which each level
is an exact copy of the one under it (no growth, no drift). That never comes back exactly to
0 degrees: after 10 levels it is 8.70 degrees off with the colours in place, so the whole design
turns back 0.87 degrees per level and level 10 lands exactly on the stretched stitch. The
animation runs 20 levels; level 20 looks like level 10, so the player plays everything once and
then repeats levels 11 to 20 (loop_from in the .json).

Every frame shows for 45 ms, with no pauses, and the strand ends move at about the same speed
in every step (the orange attach a little faster). Frames where nothing visible moves (strand
tips growing under another strand) are left out.

    python scripts/build_box_stitch_spinner.py      # output/box_stitch_frames.png + .json, src/images/assistant_pressed.png

The sheet is a grid of square frames, `columns` to a row; the .json next to it gives the frame
size, the columns, how long each frame shows and the frame the loop comes back to.
Rendering takes about 25 minutes (some 1100 frames).
"""
import argparse
import copy
import json
import math
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))

SAMPLES = ROOT / 'mxn_samples' / 'rh'  # right hand: the logo's hand
BLUE = {'r': 21, 'g': 37, 'b': 255, 'a': 255}     # set 1, the logo's blue
ORANGE = {'r': 255, 'g': 85, 'b': 0, 'a': 255}    # set 2, the logo's orange
FRAME_MS = 45
ROT_FRAMES, ATTACH_FRAMES, STRETCH_FRAMES, LEVEL_FRAMES = 11, 34, 11, 52
LEVELS, PERIOD = 20, 10  # levels drawn; after PERIOD levels the pattern is back at 0 degrees


def state(path):
    d = json.loads(Path(path).read_text(encoding='utf-8'))
    return d['states'][d['current_step'] - 1]['data']


START = state(SAMPLES / 'starting/json/mxn_rh_1x1.json')
STRETCH = state(SAMPLES / 'stretched/json/mxn_rh_stretch_1x1.json')
K1 = state(SAMPLES / 'k1_continuation/json/mxn_rh_1x1_k1_continuation.json')
W = 46


def ends(d):
    return {s['layer_name']: ((s['start']['x'], s['start']['y']), (s['end']['x'], s['end']['y']))
            for s in d['strands'] if s['type'] != 'MaskedStrand'}


def mid(g):
    return tuple((g['1_1'][0][k] + g['1_1'][1][k]) / 2 for k in (0, 1))


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def moved(g, d):
    return {n: ((a[0] + d[0], a[1] + d[1]), (b[0] + d[0], b[1] + d[1])) for n, (a, b) in g.items()}


P_START, P_STRETCH = ends(START), ends(STRETCH)
C = mid(P_START)
# The stretched sample sits 42 units up and left of the starting one: centre it on the same point.
P_STRETCH = moved(P_STRETCH, (C[0] - mid(P_STRETCH)[0], C[1] - mid(P_STRETCH)[1]))
# _2 and _3 grow to the length they keep after the stretch, so the stretch only moves them.
for n in ('1_2', '1_3', '2_2', '2_3'):
    (a, b), length = P_START[n], math.dist(*P_STRETCH[n])
    d = math.dist(a, b)
    P_START[n] = (a, (a[0] + (b[0] - a[0]) * length / d, a[1] + (b[1] - a[1]) * length / d))

TEMPL = {s['layer_name']: s for s in K1['strands']}  # every field a strand and a mask carry
NAMES = [s['layer_name'] for s in K1['strands'] if s['type'] != 'MaskedStrand']
MASKS = {s['layer_name']: (s['first_selected_strand'], s['second_selected_strand'])
         for s in K1['strands'] if s['type'] == 'MaskedStrand'}


def round_names(r):
    """k = 1 round r (level r): parent -> its new strand, for the four arms."""
    if r == 1:
        return {'2_2': '2_4', '2_3': '2_5', '1_2': '1_4', '1_3': '1_5'}
    a, b = 2 * r, 2 * r + 1
    return {f'2_{a}': f'2_{a + 2}', f'2_{b}': f'2_{b + 2}', f'1_{a}': f'1_{a + 2}', f'1_{b}': f'1_{b + 2}'}


LEVEL = {}
for _r in range(1, LEVELS + 1):
    for _parent, _child in round_names(_r).items():
        LEVEL[_child] = _r
        if _child not in TEMPL:
            t = copy.deepcopy(TEMPL['2_4' if _child.startswith('2_') else '1_4'])
            t.update(layer_name=_child, attached_to=_parent, attachment_side=1)
            TEMPL[_child] = t
            NAMES.append(_child)
    c1, c2 = 2 * _r + 2, 2 * _r + 3  # as in round one: set 2's first over set 1's second, and back
    for a, b in ((f'2_{c1}', f'1_{c2}'), (f'2_{c2}', f'1_{c1}')):
        if f'{a}_{b}' not in TEMPL:
            mk = copy.deepcopy(TEMPL['2_4_1_5'])
            mk.update(layer_name=f'{a}_{b}', first_selected_strand=a, second_selected_strand=b)
            TEMPL[mk['layer_name']] = mk
            MASKS[mk['layer_name']] = (a, b)


def strand(name, a, b, level=0):
    s = copy.deepcopy(TEMPL[name])
    s['start'], s['end'] = {'x': a[0], 'y': a[1]}, {'x': b[0], 'y': b[1]}
    s['control_points'] = [dict(s['start']), dict(s['end'])]
    s['control_point_center'] = {'x': (a[0] + b[0]) / 2, 'y': (a[1] + b[1]) / 2}
    s['color'] = dict(BLUE if name.startswith('1_') else ORANGE)
    s['width'] = W
    s['level'] = level
    s['closed_connections'] = [False, False]
    return s


def tip_beneath(tip, a, b, half):
    """Whether the point tip lies within half of the strand a -> b (its round start included)."""
    length = math.dist(a, b)
    if length < 1e-6:
        return False
    d = ((b[0] - a[0]) / length, (b[1] - a[1]) / length)
    along = (tip[0] - a[0]) * d[0] + (tip[1] - a[1]) * d[1]
    across = (tip[0] - a[0]) * d[1] - (tip[1] - a[1]) * d[0]
    return -half <= along <= length and abs(across) <= half


def project(geom):
    """A project of the strands in geom (name -> (start, end)), with the masks of crossings
    whose two strands are both there."""
    strands = [strand(n, *geom[n], level=LEVEL.get(n, 0)) for n in NAMES if n in geom]
    for m, (a, b) in MASKS.items():
        if a in geom and b in geom:
            mk = copy.deepcopy(TEMPL[m])
            first = next(s for s in strands if s['layer_name'] == a)
            mk.update(color=dict(first['color']), width=first['width'], start=dict(first['start']),
                      end=dict(first['end']), deletion_rectangles=[])
            mk.pop('level', None)
            strands.append(mk)
            # While the under strand's tip is beneath the over strand, the app still draws the
            # tip's end line on top of the mask: a stray line down the middle of the over strand.
            under = next(s for s in strands if s['layer_name'] == b)
            if tip_beneath(geom[b][1], *geom[a], first['width'] / 2 + first['stroke_width'] + 2):
                under['end_line_visible'] = False
    for i, s in enumerate(strands):
        s['index'] = i
    out = {k: v for k, v in K1.items() if k != 'strands'}
    out.update(strands=strands, groups={}, shadow_overrides={}, shadow_enabled=False)
    top = max((s.get('level', 0) for s in strands), default=0)
    if top:
        out['level_count'] = top
    return out


# ---- k = 1, exactly self-repeating (see the docstring)
def rot(v, t):
    return (v[0] * math.cos(t) - v[1] * math.sin(t), v[0] * math.sin(t) + v[1] * math.cos(t))


def exact_k1(parent):
    """The turn and the shortened arm length at which the k = 1 strand of `parent` starts
    exactly where the stretched stitch, turned about its centre, would put it."""
    s0, e0 = P_STRETCH[parent]
    length = math.dist(s0, e0)
    d = ((e0[0] - s0[0]) / length, (e0[1] - s0[1]) / length)
    v = (s0[0] - C[0], s0[1] - C[1])
    f = lambda t: (rot(v, t)[0] - v[0]) * d[1] - (rot(v, t)[1] - v[1]) * d[0]  # noqa: E731
    lo, hi = math.radians(100), math.radians(160)
    for _ in range(80):
        m = (lo + hi) / 2
        lo, hi = (lo, m) if f(lo) * f(m) <= 0 else (m, hi)
    w = rot(v, lo)
    return lo, (w[0] - v[0]) * d[0] + (w[1] - v[1]) * d[1], length


TURN, ARM_SHORT, ARM = exact_k1('2_2')
for _p in ('2_3', '1_2', '1_3'):
    _t, _s, _ = exact_k1(_p)
    assert abs(_t - TURN) < 1e-6 and abs(_s - ARM_SHORT) < 1e-6
RESIDUAL = ((math.degrees(TURN) * PERIOD + 90) % 180) - 90  # 8.70 degrees after 10 levels


def k1_round(arms, names, t):
    geom = {}
    for parent, child in names.items():
        a, b = arms[parent]
        th, ell = math.atan2(b[1] - a[1], b[0] - a[0]), math.dist(a, b)
        short = ell + (ARM_SHORT - ell) * t
        end = (a[0] + math.cos(th) * short, a[1] + math.sin(th) * short)
        geom[parent] = (a, end)
        geom[child] = (end, (end[0] + math.cos(th + TURN) * ARM * t, end[1] + math.sin(th + TURN) * ARM * t))
    return geom


def turned(geom, deg):
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    f = lambda p: (C[0] + (p[0] - C[0]) * c - (p[1] - C[1]) * s, C[1] + (p[0] - C[0]) * s + (p[1] - C[1]) * c)  # noqa: E731
    return {n: (f(a), f(b)) for n, (a, b) in geom.items()}


def build():
    """The frames as projects, their step names and the index the loop comes back to."""
    frames, labels = [], []

    def add(geom, label):
        frames.append(project(geom))
        labels.append(label)

    (s11, e11), (s21, e21) = P_START['1_1'], P_START['2_1']
    l1, l2 = math.dist(s11, e11), math.dist(s21, e21)
    a1, a2 = math.atan2(e11[1] - s11[1], e11[0] - s11[0]), math.atan2(e21[1] - s21[1], e21[0] - s21[0])

    def cross(t1, t2):
        u = (math.cos(t1) * l1 / 2, math.sin(t1) * l1 / 2)
        v = (math.cos(t2) * l2 / 2, math.sin(t2) * l2 / 2)
        return {'1_1': ((C[0] - u[0], C[1] - u[1]), (C[0] + u[0], C[1] + u[1])),
                '2_1': ((C[0] - v[0], C[1] - v[1]), (C[0] + v[0], C[1] + v[1]))}

    add(cross(0.0, -math.pi / 2), 'plus')
    for i in range(1, ROT_FRAMES + 1):
        t = i / ROT_FRAMES
        add(cross(a1 * t, -math.pi / 2 + (a2 + math.pi / 2) * t), 'rotate')
    base = {'1_1': P_START['1_1'], '2_1': P_START['2_1']}
    for i in range(1, ATTACH_FRAMES + 1):  # set 2 starts before set 1 ends: one motion
        t, geom = i / ATTACH_FRAMES, dict(base)
        for group, (a, b) in ((('1_2', '1_3'), (0.0, 0.62)), (('2_2', '2_3'), (0.38, 1.0))):
            u = min(max((t - a) / (b - a), 0.0), 1.0)
            if u > 0:
                for n in group:
                    geom[n] = (P_START[n][0], lerp(*P_START[n], u))
        add(geom, 'attach')
    labels[-1] = 'logo'
    for i in range(1, STRETCH_FRAMES + 1):
        t = i / STRETCH_FRAMES
        add({n: (lerp(P_START[n][0], P_STRETCH[n][0], t), lerp(P_START[n][1], P_STRETCH[n][1], t))
             for n in P_START}, 'stretch')
    labels[-1] = 'stretched'
    geom, loop_from = dict(P_STRETCH), None
    for r in range(1, LEVELS + 1):
        before = dict(geom)
        for i in range(1, LEVEL_FRAMES + 1):
            g = dict(before)
            g.update(k1_round(before, round_names(r), i / LEVEL_FRAMES))
            step = (r - 1) * LEVEL_FRAMES + i
            add(turned(g, -RESIDUAL * step / (PERIOD * LEVEL_FRAMES)), f'k{r}')
        geom = g
        if r == PERIOD:
            loop_from = len(frames) - 1  # level 10, at 0 degrees: the loop comes back here
    return frames, labels, loop_from


def extent(p):
    """Half the side of the square, about the centre, that holds every strand with its width."""
    r = 0
    for s in p['strands']:
        if s['type'] != 'MaskedStrand':
            pad = s['width'] / 2 + s['stroke_width']
            for q in (s['start'], s['end']):
                r = max(r, abs(q['x'] - C[0]) + pad, abs(q['y'] - C[1]) + pad)
    return r


def render(frames, framing, size):
    """Each project drawn by the app's canvas on a transparent ground, size x size, all framed on
    `framing` (with room for a new level's joint caps). The zoom is worked out for every frame:
    a new level can resize the layers panel, and the canvas with it."""
    from openstrand.generators import application
    application()
    from PyQt5.QtCore import QPoint, Qt
    from PyQt5.QtGui import QImage, QPainter, QRegion
    from PyQt5.QtWidgets import QApplication, QWidget
    os.environ['APPDATA'] = tempfile.mkdtemp(prefix='oss_spinner_')
    cwd = os.getcwd()
    os.chdir(ROOT / 'src')
    try:
        from main_window import MainWindow
        from save_load_manager import apply_project_state
        window = MainWindow()
    finally:
        os.chdir(cwd)
    window.resize(1500, 1100)
    window.show()
    canvas = window.canvas

    def show(data):
        apply_project_state(canvas, data)
        canvas.set_mode('view')
        canvas.show_grid = canvas.show_control_points = canvas.should_draw_names = False
        canvas.selected_strand = None
        for _ in range(3):
            QApplication.processEvents()

    show(framing)
    bounds = canvas.get_bounding_rect()
    side = max(bounds.width(), bounds.height()) * 1.12 * 1.15
    images = []
    for data in frames:
        show(data)
        zoom = min(canvas.width(), canvas.height()) / side
        canvas.zoom_factor = zoom
        canvas.pan_offset_x = (canvas.width() / 2 - bounds.center().x()) * zoom
        canvas.pan_offset_y = (canvas.height() / 2 - bounds.center().y()) * zoom
        for _ in range(3):
            QApplication.processEvents()
        image = QImage(canvas.size(), QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.transparent)
        painter = QPainter(image)
        canvas.render(painter, QPoint(), QRegion(), QWidget.RenderFlags(0))
        painter.end()
        edge = min(canvas.width(), canvas.height())
        square = image.copy((canvas.width() - edge) // 2, (canvas.height() - edge) // 2, edge, edge)
        images.append(square.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    window._confirm_close_with_dirty_tabs = lambda *a, **k: True
    window.close()
    return images


def to_pil(qimage):
    from PIL import Image
    from PyQt5.QtCore import QBuffer, QIODevice
    buf = QBuffer()
    buf.open(QIODevice.WriteOnly)
    qimage.save(buf, 'PNG')
    import io
    return Image.open(io.BytesIO(bytes(buf.data()))).convert('RGBA')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--frame', type=int, default=112, help='frame size in the sheet, px (default 112)')
    parser.add_argument('--out', default=str(ROOT / 'output' / 'box_stitch_frames.png'))
    parser.add_argument('--pressed', default=str(ROOT / 'src' / 'images' / 'assistant_pressed.png'),
                        help='the Assistant button pressed: the stretched 1x1 starting stitch')
    args = parser.parse_args()
    from PIL import Image

    frames, labels, loop_from = build()
    framing = max(frames, key=extent)
    rendered = render(frames + [project(P_STRETCH)], framing, 256)
    images = [to_pil(im) for im in rendered[:-1]]
    # Leave out frames where nothing visible moves (strand tips growing under another strand),
    # never the two the loop joins.
    keep = [0] + [i for i in range(1, len(images))
                  if images[i].tobytes() != images[i - 1].tobytes() or i in (loop_from, loop_from + 1, len(images) - 1)]
    images = [images[i] for i in keep]
    loop_from = keep.index(loop_from)

    size, columns = args.frame, 32
    rows = math.ceil(len(images) / columns)
    sheet = Image.new('RGBA', (columns * size, rows * size), (0, 0, 0, 0))
    for i, im in enumerate(images):
        sheet.paste(im.resize((size, size), Image.LANCZOS), ((i % columns) * size, (i // columns) * size))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    sheet.quantize(colors=128, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE).save(args.out, optimize=True)
    durations = [FRAME_MS] * len(images)
    Path(args.out).with_suffix('.json').write_text(json.dumps(
        {'frame': size, 'columns': columns, 'durations_ms': durations, 'loop_from': loop_from,
         'about': 'The OpenStrand logo, a box stitch, tied and continued with k = 1 level after level, '
                  'drawn by OpenStrand Studio (scripts/build_box_stitch_spinner.py). Plays once, then '
                  'repeats from the frame after loop_from.'}, indent=1) + '\n', encoding='utf-8')

    # The button while pressed: the stretched 1x1 starting stitch, framed on itself.
    stretched = project(P_STRETCH)
    to_pil(render([stretched], stretched, 512)[0]).resize((128, 128), Image.LANCZOS).save(args.pressed, optimize=True)
    first_pass = sum(durations[:loop_from + 1]) / 1000
    print(f'{len(images)} frames of {size}px ({len(keep)} kept), first pass {first_pass:.1f} s, '
          f'then a {sum(durations[loop_from + 1:]) / 1000:.1f} s loop -> {args.out}, {args.pressed}')
    os._exit(0)


if __name__ == '__main__':
    main()
