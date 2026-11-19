"""Build the Celtic x Indian bridal embroidery presentation board from the Celtic sample projects.

Run from the repository root: python scripts/build_celtic_board.py

Each project in knot_samples/celtic/json is recoloured into thread tones that
read on a deep maroon ground, captured with shadows off at high resolution,
and given true transparency by rendering it on white and on black. The motifs
are then laid out on a silk-textured board: the bridal medallion (plait ring,
lotus mandala, paisleys and shield knots), the plait border, a motif library
and a thread palette.

Outputs: knot_samples/celtic/presentation/bridal_embroidery_board.jpg and .pdf
"""
import json
import math
import os
import random
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_creative_samples import ROOT, QApplication, AppPreview
from PyQt5.QtGui import QImage

CELTIC = ROOT / 'knot_samples' / 'celtic'


def _font_file(*names):
    for folder in ('/usr/share/fonts/truetype/freefont', '/usr/share/fonts/truetype/dejavu',
                   '/Library/Fonts', 'C:/Windows/Fonts'):
        for name in names:
            if Path(folder, name).exists():
                return str(Path(folder, name))
    return names[-1]

W, H = 2480, 4080
FONT = _font_file('FreeSerif.ttf', 'DejaVuSerif.ttf')
FONT_I = _font_file('FreeSerifItalic.ttf', 'DejaVuSerif-Italic.ttf')
GOLD = (222, 184, 92)
GOLD_DIM = (176, 138, 62)
IVORY = (243, 230, 204)
IVORY_DIM = (214, 190, 168)


def font(path, size):
    return ImageFont.truetype(path, size)


def trimmed(img):
    return img.crop(img.getbbox())


def load(S, name):
    # captured with true alpha (rendered on white and on black)
    return trimmed(Image.open(S / name).convert('RGBA'))


def fit(img, w=None, h=None):
    sw = w / img.width if w else 1e9
    sh = h / img.height if h else 1e9
    k = min(sw, sh)
    return img.resize((max(1, round(img.width * k)), max(1, round(img.height * k))), Image.LANCZOS)


def lift(base, motif, xy, glow=True):
    """Paste a motif with a soft dark halo so it sits on the fabric like raised thread work."""
    x, y = xy
    if glow:
        halo = Image.new('RGBA', motif.size, (0, 0, 0, 0))
        halo.putalpha(motif.getchannel('A').point(lambda v: int(v * 0.55)))
        pad = 30
        big = Image.new('RGBA', (motif.width + 2 * pad, motif.height + 2 * pad), (0, 0, 0, 0))
        big.alpha_composite(halo, (pad, pad))
        big = big.filter(ImageFilter.GaussianBlur(9))
        base.alpha_composite(big, (x - pad + 4, y - pad + 7))
    base.alpha_composite(motif, (x, y))


def spaced(draw, text, centre_x, y, f, fill, tracking=0.18):
    """Draw letter-spaced text centred on centre_x."""
    widths = [draw.textlength(ch, font=f) for ch in text]
    extra = f.size * tracking
    total = sum(widths) + extra * (len(text) - 1)
    x = centre_x - total / 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=f, fill=fill)
        x += w + extra


def centred(draw, text, cx, y, f, fill):
    draw.text((cx - draw.textlength(text, font=f) / 2, y), text, font=f, fill=fill)


def rule(draw, cx, y, half, fill=GOLD_DIM):
    draw.line([(cx - half, y), (cx - 26, y)], fill=fill, width=3)
    draw.line([(cx + 26, y), (cx + half, y)], fill=fill, width=3)
    draw.polygon([(cx, y - 13), (cx + 13, y), (cx, y + 13), (cx - 13, y)], outline=fill, width=3)


def capture(jobs, size=2400):
    """Render each project on white and on black and save it with true transparency."""
    app = QApplication.instance() or QApplication([])
    p = AppPreview()
    p.window.resize(3400, 3000)
    p.window.canvas.setFixedSize(size, size)
    for _ in range(5):
        QApplication.processEvents()

    def hexrgb(h):
        h = h.lstrip('#'); return [int(h[i:i+2], 16) for i in (0, 2, 4)]

    for job in jobs:
        data = json.loads(Path(job['src']).read_text())
        rec = {tuple(hexrgb(k)): hexrgb(v) for k, v in job.get('recolor', {}).items()}
        for s in data['strands']:
            c = s.get('color')
            if c and (c['r'], c['g'], c['b']) in rec:
                r, g, b = rec[(c['r'], c['g'], c['b'])]
                s['color'] = dict(r=r, g=g, b=b, a=c.get('a', 255))
        data['shadow_enabled'] = job.get('shadows', False)
        from save_load_manager import apply_project_state
        apply_project_state(p.window.canvas, data)
        canvas = p.window.canvas
        canvas.set_mode('view')
        canvas.show_grid = canvas.show_control_points = canvas.should_draw_names = False
        canvas.shadow_enabled = job.get('shadows', False)
        bounds = canvas.get_bounding_rect()
        canvas.zoom_factor = min((canvas.width() - 40) / bounds.width(), (canvas.height() - 40) / bounds.height())
        canvas.pan_offset_x = (canvas.width() / 2 - bounds.center().x()) * canvas.zoom_factor
        canvas.pan_offset_y = (canvas.height() / 2 - bounds.center().y()) * canvas.zoom_factor
        for _ in range(3):
            QApplication.processEvents()
        canvas.update(); QApplication.processEvents()
        shots = []
        for bg in ('#FFFFFF', '#000000'):
            canvas.setStyleSheet('background-color: %s;' % bg)
            canvas.update()
            for _ in range(3):
                QApplication.processEvents()
            img = canvas.grab().toImage().convertToFormat(QImage.Format_RGB888)
            ptr = img.constBits(); ptr.setsize(img.byteCount())
            arr = np.frombuffer(ptr, np.uint8).reshape(img.height(), img.bytesPerLine())[:, :img.width() * 3]
            shots.append(arr.reshape(img.height(), img.width(), 3).astype(np.float32))
        canvas.setStyleSheet('background-color: #FFFFFF;')
        white, black = shots
        # composite = alpha * colour + (1 - alpha) * background, on both backgrounds
        alpha = np.clip(1.0 - (white - black).mean(axis=2) / 255.0, 0, 1)
        colour = np.where(alpha[..., None] > 1e-3, black / np.maximum(alpha[..., None], 1e-3), 0)
        rgba = np.dstack([np.clip(colour, 0, 255), alpha * 255]).astype(np.uint8)
        Image.fromarray(rgba, 'RGBA').save(job['dst'])
        print('wrote', job['dst'], canvas.width(), canvas.height(), round(canvas.zoom_factor, 2))
    p.close()


def jobs(folder):
    """Which projects to capture, and the thread colours that read on maroon."""
    def job(name, out, recolor=None):
        return dict(src=str(CELTIC / 'json' / (name + '.json')), dst=str(folder / out), recolor=recolor or {})
    lighter_emerald, rose_silver, zari = '#2f9a74', '#e3b8c2', '#d4a72c'
    return [job('bridal_lotus_mandala', 'hr_mandala.png', {'#1d6b50': lighter_emerald, '#a3162c': rose_silver}),
            job('bridal_paisley', 'hr_paisley.png', {'#a3162c': zari, '#d4a72c': rose_silver, '#1d6b50': lighter_emerald}),
            job('plait_border', 'hr_plait.png'),
            job('plait_ring', 'hr_ring.png'),
            job('infinity_knot', 'hr_infinity.png'),
            job('loop_oval', 'hr_oval.png'),
            job('tailed_knot', 'hr_tailed.png', {'#8d6aa8': '#b393d3'}),
            job('shield_knot', 'hr_shield.png', {'#2d4b6e': '#c9ced6', '#c9a227': zari})]


def compose(S, OUT):
    """Lay the captured motifs out on the board and save it as OUT (a .jpg, plus a .pdf beside it)."""
    # ---------------------------------------------------------------- background
    random.seed(7)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.hypot((xx - W / 2) / W, (yy - H * 0.42) / H)
    inner, outer = np.array([96, 18, 38]), np.array([38, 6, 16])
    t = np.clip(r / 0.75, 0, 1)[..., None]
    bg = inner * (1 - t) + outer * t
    # silk sheen: a soft diagonal highlight band and fine woven grain
    sheen = np.exp(-((xx * 0.55 + yy * 0.35 - 1500) / 900) ** 2)[..., None] * np.array([28, 8, 10])
    grain = (np.sin(xx * 1.9) * np.sin(yy * 1.7) * 3.0 + np.random.default_rng(1).normal(0, 2.2, (H, W)))[..., None]
    bg = np.clip(bg + sheen + grain, 0, 255).astype(np.uint8)
    board = Image.fromarray(bg, 'RGB').convert('RGBA')
    draw = ImageDraw.Draw(board)

    # double gold frame with corner knots
    for inset, width in ((60, 5), (84, 2)):
        draw.rectangle([inset, inset, W - inset, H - inset], outline=GOLD_DIM, width=width)

    # ---------------------------------------------------------------- header
    spaced(draw, 'CELTIC  ×  INDIAN', W / 2, 170, font(FONT, 96), GOLD, tracking=0.22)
    spaced(draw, 'BRIDAL EMBROIDERY', W / 2, 288, font(FONT, 64), IVORY, tracking=0.32)
    rule(draw, W / 2, 400, 520)
    centred(draw, 'Interlace knotwork for a hand-embroidered wedding ensemble', W / 2, 432, font(FONT_I, 50), IVORY_DIM)

    # ---------------------------------------------------------------- medallion
    ring = load(S, 'hr_ring.png')
    mandala = load(S, 'hr_mandala.png')
    paisley = load(S, 'hr_paisley.png')
    D = 1360
    ring = fit(ring, D, D)
    med = Image.new('RGBA', (D + 120, D + 120), (0, 0, 0, 0))
    cx = cy = med.width // 2
    inner_r = 0.825 * D / 2
    m = fit(mandala, int(inner_r * 0.86), int(inner_r * 0.86))
    lift(med, m, (cx - m.width // 2, cy - m.height // 2))
    # four paisleys on the diagonals, tips pointing outward and turning clockwise
    p_size = int(inner_r * 0.46)
    p = fit(paisley, p_size, p_size)
    # paisley's own axis runs from its bulb up to its curled tip (up and to the left)
    axis = math.degrees(math.atan2(-285, -140))
    for k in range(4):
        theta = 45 + 90 * k
        q = p.rotate(axis - theta, resample=Image.BICUBIC, expand=True)
        rr = inner_r * 0.73
        px = cx + rr * math.cos(math.radians(theta)) - q.width / 2
        py = cy + rr * math.sin(math.radians(theta)) - q.height / 2
        lift(med, q, (int(px), int(py)))
    # small shield knots at the four cardinal points
    shield = fit(load(S, 'hr_shield.png'), int(inner_r * 0.25), int(inner_r * 0.25))
    for k in range(4):
        theta = 90 * k
        sx = cx + inner_r * 0.79 * math.cos(math.radians(theta)) - shield.width / 2
        sy = cy + inner_r * 0.79 * math.sin(math.radians(theta)) - shield.height / 2
        lift(med, shield, (int(sx), int(sy)))
    lift(med, ring, (cx - ring.width // 2, cy - ring.height // 2))
    MED_Y = 540
    board.alpha_composite(med, (W // 2 - med.width // 2, MED_Y))
    draw = ImageDraw.Draw(board)
    cap_y = MED_Y + med.height + 6
    spaced(draw, 'THE BRIDAL MEDALLION', W / 2, cap_y, font(FONT, 54), GOLD, tracking=0.25)
    centred(draw, 'A lotus of eight gold petals, four curled paisleys, four shield knots and an unbroken plait,',
            W / 2, cap_y + 78, font(FONT_I, 42), IVORY_DIM)
    centred(draw, 'for the back of the blouse or the four corners of the dupatta.', W / 2, cap_y + 132, font(FONT_I, 42), IVORY_DIM)

    # ---------------------------------------------------------------- border
    plait = load(S, 'hr_plait.png')
    band_w = W - 2 * 150
    plait = fit(plait, band_w * 1.12)
    plait = plait.crop(((plait.width - band_w) // 2, 0, (plait.width + band_w) // 2, plait.height))
    # fade the cut ends into the fabric
    fade = Image.new('L', plait.size, 255)
    fd = ImageDraw.Draw(fade)
    for i in range(90):
        v = int(255 * i / 90)
        fd.line([(i, 0), (i, plait.height)], fill=v)
        fd.line([(plait.width - 1 - i, 0), (plait.width - 1 - i, plait.height)], fill=v)
    plait.putalpha(ImageChops.multiply(plait.getchannel('A'), fade))
    BAND_Y = cap_y + 250
    lift(board, plait, (150, BAND_Y))
    draw = ImageDraw.Draw(board)
    centred(draw, 'Plait border  ·  lehenga hem, dupatta edge, sleeve cuffs', W / 2, BAND_Y + plait.height + 22,
            font(FONT_I, 42), IVORY_DIM)

    # ---------------------------------------------------------------- motif library
    LIB_Y = BAND_Y + plait.height + 150
    rule(draw, W / 2, LIB_Y, 520)
    spaced(draw, 'MOTIF LIBRARY', W / 2, LIB_Y + 34, font(FONT, 54), GOLD, tracking=0.25)
    motifs = [('hr_shield.png', 'Shield knot', 'buti for the skirt'),
              ('hr_infinity.png', 'Double infinity', 'the couple, entwined'),
              ('hr_tailed.png', 'Knot with tails', 'neckline centre'),
              ('hr_oval.png', 'Loop oval', 'waistband panel')]
    cell = (W - 2 * 150) / len(motifs)
    row_y = LIB_Y + 140
    for i, (name, title, use) in enumerate(motifs):
        img = load(S, name)
        img = fit(img, int(cell * 0.80), 330)
        x = int(150 + cell * i + (cell - img.width) / 2)
        y = int(row_y + (330 - img.height) / 2)
        lift(board, img, (x, y))
        draw = ImageDraw.Draw(board)
        centred(draw, title, 150 + cell * i + cell / 2, row_y + 360, font(FONT, 44), IVORY)
        centred(draw, use, 150 + cell * i + cell / 2, row_y + 414, font(FONT_I, 36), IVORY_DIM)

    # ---------------------------------------------------------------- palette
    PAL_Y = row_y + 520
    rule(draw, W / 2, PAL_Y, 520)
    spaced(draw, 'THREAD PALETTE', W / 2, PAL_Y + 34, font(FONT, 54), GOLD, tracking=0.25)
    palette = [((212, 175, 55), 'Zari gold', 'couched metal thread'),
               ((227, 194, 122), 'Champagne gold', 'zardozi dabka'),
               ((201, 206, 214), 'Silver', 'couched kasab'),
               ((227, 184, 194), 'Rose silver', 'silk satin stitch'),
               ((47, 154, 116), 'Emerald', 'silk stem stitch'),
               ((179, 147, 211), 'Amethyst', 'silk satin stitch')]
    cell = (W - 2 * 150) / len(palette)
    sw_y = PAL_Y + 150
    for i, (rgb, name, stitch) in enumerate(palette):
        ccx = 150 + cell * i + cell / 2
        # a swatch drawn as a small skein: a filled disc with a lighter sheen arc
        draw.ellipse([ccx - 62, sw_y, ccx + 62, sw_y + 124], fill=rgb, outline=(38, 52, 70), width=4)
        hi = tuple(min(255, int(c * 1.18 + 20)) for c in rgb)
        draw.arc([ccx - 46, sw_y + 16, ccx + 46, sw_y + 108], 200, 290, fill=hi, width=8)
        centred(draw, name, ccx, sw_y + 146, font(FONT, 40), IVORY)
        centred(draw, stitch, ccx, sw_y + 196, font(FONT_I, 33), IVORY_DIM)

    # ---------------------------------------------------------------- footer
    foot_y = sw_y + 300
    assert foot_y + 140 < H - 90, foot_y
    rule(draw, W / 2, foot_y, 360)
    centred(draw, 'Every cord passes alternately over and under, as in traditional Celtic interlace,',
            W / 2, foot_y + 34, font(FONT_I, 38), IVORY_DIM)
    centred(draw, 'and every cord is one continuous line for the needle to follow.', W / 2, foot_y + 82, font(FONT_I, 38), IVORY_DIM)

    board.convert('RGB').save(OUT, quality=92, subsampling=0)
    board.convert('RGB').save(OUT.with_suffix('.pdf'), resolution=300)
    print('board', OUT, 'sections y:', MED_Y, cap_y, BAND_Y, LIB_Y, PAL_Y, sw_y + 240, 'footer', foot_y)


def main():
    out = CELTIC / 'presentation'
    out.mkdir(exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix='celtic_board_'))
    capture(jobs(folder))
    compose(folder, out / 'bridal_embroidery_board.jpg')
    print('wrote', out / 'bridal_embroidery_board.jpg', 'and .pdf')


if __name__ == '__main__':
    main()
