"""Build the knot Claude's working line shows: a closed overhand knot drawn
step by step, strand after strand, by OpenStrand Studio's own canvas, then
untied from the other end, so the loop comes back to where it began.

The knot is a real project made with `openstrand draw` (8 attached strands,
3 crossings, 2 masks). Each frame is that project cut short: the strands
drawn so far, the one being drawn grown part of the way along its curve, and
the masks of crossings whose two strands are both there, as when the knot is
drawn by hand in the app. Once finished it unties: the cord leaves from its
first end, strand after strand along the same path, until nothing is left. The frames are rendered by the app's canvas onto a
transparent ground.

    python scripts/build_knot_spinner.py            # writes src/claude_knot.png (+ .json)
    python scripts/build_knot_spinner.py --gif x.gif --size 256

src/claude_knot.png is a strip of square frames; src/claude_knot.json gives
the frame size and how long each frame shows.
"""
import argparse
import copy
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SPEC = {"name": "closed overhand", "cords": [{
    "label": "Overhand", "color": "#D97757", "width": 30, "closed": True,
    "points": [[420, 640], [500, 420], [640, 300], [760, 360], [740, 480], [600, 520],
               [460, 480], [440, 360], [560, 300], [700, 420], [780, 640], [600, 700]]}]}
GROWTH = (1 / 3, 2 / 3, 1.0)   # each strand appears in three steps along its curve
STEP_MS, HOLD_MS, EMPTY_MS = 110, 1400, 220
ATTACHED_ONLY = ('attached_to', 'attachment_side', 'angle', 'length')


def split(p0, p1, p2, p3, t):
    """The first part, up to t, of a cubic Bezier curve (de Casteljau)."""
    lerp = lambda a, b: (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    a, b, c = lerp(p0, p1), lerp(p1, p2), lerp(p2, p3)
    d, e = lerp(a, b), lerp(b, c)
    return p0, a, d, lerp(d, e)


def point(p):
    return (p['x'], p['y'])


def as_dict(p):
    return {'x': p[0], 'y': p[1]}


def rest(p0, p1, p2, p3, t):
    """The part of a cubic Bezier curve after t (de Casteljau)."""
    q3, q2, q1, q0 = split(p3, p2, p1, p0, 1 - t)
    return q0, q1, q2, q3


def receded(strand, t):
    """The strand with its first part, up to t, gone: its start is now loose."""
    s = copy.deepcopy(strand)
    cps = s['control_points']
    p0, a, b, p3 = rest(point(s['start']), point(cps[0]), point(cps[1]), point(s['end']), t)
    s['start'], s['control_points'] = as_dict(p0), [as_dict(a), as_dict(b)]
    s['control_point_center'] = as_dict(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))
    s['has_circles'] = [False, s['has_circles'][1]]
    return s


def as_first(strand):
    """An attached strand whose parent is gone becomes the cord's first strand."""
    s = copy.deepcopy(strand)
    s['type'], s['is_first_strand'] = 'Strand', True
    for key in ATTACHED_ONLY:
        s.pop(key, None)
    s['has_circles'] = [False, s['has_circles'][1]]
    return s


def untie_frames(project):
    """The finished knot untied from its first end: each strand leaves in three
    steps, in the order it was drawn, until nothing is left."""
    strands = [s for s in project['strands'] if s['type'] != 'MaskedStrand']
    masks = [s for s in project['strands'] if s['type'] == 'MaskedStrand']
    names = [s['layer_name'] for s in strands]
    out = []
    for k in range(len(strands)):
        for t in GROWTH:
            if t >= 1:
                left = [copy.deepcopy(s) for s in strands[k + 1:]]
            else:
                left = [receded(strands[k], t)] + [copy.deepcopy(s) for s in strands[k + 1:]]
            if left:
                left[0] = as_first(left[0])
            for s in left:
                s['closed_connections'] = [False, False]
            there = {s['layer_name'] for s in left}
            kept = [m for m in masks if all(n in there for n in mask_parts(m['layer_name'], names))]
            frame = dict(project, strands=left + copy.deepcopy(kept), groups={})
            for i, s in enumerate(frame['strands']):
                s['index'] = i
            out.append(frame)
    return out


def grown(strand, t):
    """The strand drawn part of the way, its loose end without a joint."""
    s = copy.deepcopy(strand)
    if t >= 1:
        return s
    cps = s['control_points']
    p0, a, b, p3 = split(point(s['start']), point(cps[0]), point(cps[1]), point(s['end']), t)
    s['end'], s['control_points'] = as_dict(p3), [as_dict(a), as_dict(b)]
    s['control_point_center'] = as_dict(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))
    s['has_circles'] = [s['has_circles'][0], False]
    s['closed_connections'] = [s['closed_connections'][0], False]
    return s


def frames_of(project):
    """Partial projects, in drawing order, ending with the whole knot."""
    strands = [s for s in project['strands'] if s['type'] != 'MaskedStrand']
    masks = [s for s in project['strands'] if s['type'] == 'MaskedStrand']
    names = [s['layer_name'] for s in strands]
    out = []
    for k, strand in enumerate(strands):
        for t in GROWTH:
            done = set(names[:k] + ([names[k]] if t >= 1 else []))
            drawn = [copy.deepcopy(s) for s in strands[:k]] + [grown(strand, t)]
            if len(done) < len(names):  # the loop is not closed yet
                for s in drawn:
                    s['closed_connections'] = [False, False]
            kept = [m for m in masks if all(n in done for n in mask_parts(m['layer_name'], names))]
            frame = dict(project, strands=drawn + copy.deepcopy(kept), groups={})
            for i, s in enumerate(frame['strands']):  # the loader places each strand by its index
                s['index'] = i
            out.append(frame)
    return out


def mask_parts(mask_name, names):
    """'1_1_1_6' -> ('1_1', '1_6'), matched against the strand names."""
    for n in names:
        if mask_name.startswith(n + '_') and mask_name[len(n) + 1:] in names:
            return n, mask_name[len(n) + 1:]
    return (mask_name,)


def render_frames(frames, full, size):
    from openstrand.generators import application
    application()
    from PyQt5.QtCore import QPoint, QRectF, Qt
    from PyQt5.QtGui import QImage, QPainter, QRegion
    from PyQt5.QtWidgets import QApplication, QWidget
    os.environ['APPDATA'] = tempfile.mkdtemp(prefix='oss_knot_')
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
    # Frame every step on the finished knot, so nothing jumps.
    apply_project_state(canvas, full)
    canvas.set_mode('view')
    canvas.show_grid = canvas.show_control_points = canvas.should_draw_names = False
    bounds = canvas.get_bounding_rect()
    side = max(bounds.width(), bounds.height()) * 1.12
    zoom = min(canvas.width(), canvas.height()) / side
    images = []
    for data in frames:
        apply_project_state(canvas, data)
        canvas.set_mode('view')
        canvas.show_grid = canvas.show_control_points = canvas.should_draw_names = False
        canvas.selected_strand = None
        canvas.zoom_factor = zoom
        canvas.pan_offset_x = (canvas.width() / 2 - bounds.center().x()) * zoom
        canvas.pan_offset_y = (canvas.height() / 2 - bounds.center().y()) * zoom
        for _ in range(3):
            QApplication.processEvents()
        image = QImage(canvas.size(), QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.transparent)
        painter = QPainter(image)
        canvas.render(painter, QPoint(), QRegion(), QWidget.RenderFlags(0))  # no background
        painter.end()
        edge = min(canvas.width(), canvas.height())
        square = image.copy((canvas.width() - edge) // 2, (canvas.height() - edge) // 2, edge, edge)
        images.append(square.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    window._confirm_close_with_dirty_tabs = lambda *a, **k: True
    window.close()
    return images


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--size', type=int, default=64, help='frame size in px (default 64)')
    parser.add_argument('--out', default=str(ROOT / 'src' / 'claude_knot.png'))
    parser.add_argument('--gif', help='also write an animated GIF here')
    parser.add_argument('--frames', help='also write each frame as a PNG into this folder')
    args = parser.parse_args()
    from openstrand import draw
    full, report = draw.build(SPEC)
    assert 'conflicts: 0' in report, report
    build, untie = frames_of(full), untie_frames(full)
    # The last untie frame is empty: it stays a blank cell, the pause before it starts again.
    images = render_frames(build + untie[:-1], full, args.size)
    durations = [STEP_MS] * len(images)
    durations[len(build) - 1] = HOLD_MS  # the finished knot
    from PyQt5.QtGui import QImage, QPainter
    from PyQt5.QtCore import Qt
    strip = QImage(args.size * (len(images) + 1), args.size, QImage.Format_ARGB32_Premultiplied)
    strip.fill(Qt.transparent)
    painter = QPainter(strip)
    for i, im in enumerate(images):
        painter.drawImage(i * args.size, 0, im)
    painter.end()  # the last cell stays empty: the cord has gone, and it starts again
    durations.append(EMPTY_MS)
    strip.save(args.out)
    Path(args.out).with_suffix('.json').write_text(json.dumps(
        {'frame': args.size, 'durations_ms': durations,
         'about': 'A closed overhand knot drawn strand by strand by OpenStrand Studio, then '
                  'untied from its first end (scripts/build_knot_spinner.py).'}, indent=1) + '\n', encoding='utf-8')
    if args.frames:
        Path(args.frames).mkdir(parents=True, exist_ok=True)
        for i, im in enumerate(images):
            im.save(str(Path(args.frames) / f'frame_{i:02d}.png'))
    if args.gif:
        from PIL import Image
        cells = []
        for i in range(len(durations)):
            cell = strip.copy(i * args.size, 0, args.size, args.size)
            tmp = Path(tempfile.mkdtemp()) / 'f.png'
            cell.save(str(tmp))
            cells.append(Image.open(tmp).convert('RGBA'))
        cells[0].save(args.gif, save_all=True, append_images=cells[1:], duration=durations, loop=0,
                      disposal=2, optimize=False)
    print(f'{len(durations)} frames of {args.size}px -> {args.out}')
    os._exit(0)


if __name__ == '__main__':
    main()
