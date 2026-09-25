"""Render the mask-shadow observation examples: what the app draws today
("current") next to what it should draw ("expected").

Each example lives in docs/mask_shadow_observations/<example>/ with a
scene.json (a normal history file, so Load opens it in the app) and an
example.json describing the mask and how to build the reference.

"Expected" is not hand-painted. The same strands are rendered a second time
with the masked crossing expressed as a genuine layer order (the mask's first
strand moved above its second strand and the mask removed), which is exactly
what the app already draws for a normal crossing. Pixels that differ from the
current render near the masked crossing are transplanted from that reference.
Places the reordering also changes but the mask does not govern are listed in
example.json as keep_zones (strand pairs) and stay as the app draws them.

Besides current/expected, the script records which shadow pass paints each
visible shadow pixel (attribution.png) and an experiment with the mask's
shadow blocker switched off (blocker_experiment.png).

Run offscreen from the repo root:

    QT_QPA_PLATFORM=offscreen python automation_tests/capture_mask_shadow_observations.py [example_dir ...]
"""
import io
import json
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
DOCS_DIR = os.path.join(ROOT_DIR, "docs", "mask_shadow_observations")
for _path in (SRC_DIR, os.path.dirname(os.path.abspath(__file__))):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from capture_screen_ratio_mocks import _bootstrap, _force_available_size, _wait

WINDOW_SIZE = (1264, 935)   # default window size (the first reported screenshot)
DIFF_THRESHOLD = 8          # per-channel difference (0-255) that counts as changed

CURRENT_RED = (190, 30, 45)
EXPECTED_GREEN = (25, 125, 60)
INK = (30, 30, 35)
MUTED = (95, 95, 105)
PASS_COLORS = [
    (0, 150, 255), (0, 190, 90), (255, 140, 0), (220, 0, 0),
    (170, 0, 200), (0, 170, 170), (140, 90, 40), (120, 120, 120),
    (255, 0, 255), (0, 0, 0), (255, 215, 0), (0, 80, 160),
]


# ----------------------------------------------------------------------------
# Rendering through the real app
# ----------------------------------------------------------------------------

def qimage_to_pil(qimage):
    from PyQt5.QtCore import QBuffer, QIODevice
    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    qimage.save(buffer, "PNG")
    return Image.open(io.BytesIO(bytes(buffer.data()))).convert("RGB")


class Renderer:
    """One offscreen MainWindow; every render re-imports the scene from disk."""

    def __init__(self):
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QWindow

        # Never-mapped windows report isExposed() False, and the canvas then
        # skips blitting its supersampled buffer (see record_tutorial_videos.py).
        QWindow.isExposed = lambda self: True
        self.app, self.window = _bootstrap()
        self.window._initial_show_completed = True
        self.window.setAttribute(Qt.WA_DontShowOnScreen, True)
        self.window.setMinimumSize(0, 0)
        self.window.show()
        self.app.processEvents()
        self.canvas_style = self.window.canvas.styleSheet()
        self.configure(WINDOW_SIZE, None)

        import masked_strand
        import shader_utils
        self.shader_utils = shader_utils
        self.original_strand_shadow = shader_utils.draw_strand_shadow
        self.original_blocker = shader_utils.get_shadow_blocker_path
        self.original_mask_draw = masked_strand.MaskedStrand.draw
        # The mask's own shadow passes: draw_mask_strand_shadow before the
        # mask shadow fix, draw_mask_lift_shadow and draw_mask_overlying after.
        self.mask_passes = {name: getattr(shader_utils, name) for name in
                            ("draw_mask_strand_shadow", "draw_mask_lift_shadow", "draw_mask_overlying")
                            if hasattr(shader_utils, name)}

        # Every call site imports these from shader_utils at call time, so
        # wrapping the module attributes lets us name and skip single passes.
        self.skip = set()
        self.calls = []
        self.drawing_mask = None
        renderer = self

        def strand_shadow(painter, strand, *args, **kwargs):
            if kwargs.get("collect_only"):
                # A mask pass reusing the strand's shadow paths, not a pass of its own.
                return renderer.original_strand_shadow(painter, strand, *args, **kwargs)
            key = "%s: draw_strand_shadow" % strand.layer_name
            renderer.calls.append(key)
            if key not in renderer.skip:
                return renderer.original_strand_shadow(painter, strand, *args, **kwargs)

        def mask_pass(name):
            def wrapped(painter, *args, **kwargs):
                key = "%s: %s" % (renderer.drawing_mask, name)
                renderer.calls.append(key)
                if key not in renderer.skip:
                    return renderer.mask_passes[name](painter, *args, **kwargs)
            return wrapped

        def mask_draw(strand, painter, *args, **kwargs):
            renderer.drawing_mask = strand.layer_name
            try:
                return renderer.original_mask_draw(strand, painter, *args, **kwargs)
            finally:
                renderer.drawing_mask = None

        shader_utils.draw_strand_shadow = strand_shadow
        for name in self.mask_passes:
            setattr(shader_utils, name, mask_pass(name))
        masked_strand.MaskedStrand.draw = mask_draw

    def configure(self, window_size, canvas_background):
        """Match the reporter's window size and canvas background colour
        (the "default" theme paints the canvas #ECECEC instead of white)."""
        _force_available_size(self.window, *window_size)
        self.window.canvas.setStyleSheet(
            "background-color: %s;" % canvas_background if canvas_background else self.canvas_style)
        self.app.processEvents()

    def render(self, scene_path, shadow, order=None, select=None, skip=(),
               neutralise_blocker=False):
        """Load *scene_path* through the app's history import and grab the canvas.

        order: layer names to keep, in drawing order (others are removed).
        select: layer to select before grabbing (drawn with its highlight).
        skip: shadow passes (keys as recorded in self.calls) to leave out.
        neutralise_blocker: make get_shadow_blocker_path return a far-away
            speck, i.e. masks stop cutting holes into other strands' shadows.
        """
        from PyQt5.QtCore import QRectF
        from PyQt5.QtGui import QPainterPath

        window, canvas = self.window, self.window.canvas
        assert window.layer_panel.undo_redo_manager.import_history(scene_path), scene_path
        canvas.num_steps = shadow["num_steps"]
        canvas.max_blur_radius = shadow["max_blur_radius"]
        if not canvas.shadow_enabled:
            canvas.toggle_shadow()
        canvas.show_control_points = False
        canvas.deselect_all_strands()
        if order:
            by_name = {s.layer_name: s for s in canvas.strands}
            canvas.strands = [by_name[name] for name in order]
            canvas.layer_state_manager.save_current_state()
        if select:
            canvas.select_strand([s.layer_name for s in canvas.strands].index(select))
        # Selecting can switch modes; the report was taken in View mode.
        window.set_view_mode()

        if neutralise_blocker:
            speck = QPainterPath()
            speck.addRect(QRectF(-5000, -5000, 0.5, 0.5))
            self.shader_utils.get_shadow_blocker_path = lambda *_a, **_k: QPainterPath(speck)
        self.skip = set(skip)
        self.calls = []
        try:
            canvas.update()
            self.app.processEvents()
            _wait(150)
            self.calls = []
            image = qimage_to_pil(canvas.grab().toImage())
        finally:
            self.skip = set()
            self.shader_utils.get_shadow_blocker_path = self.original_blocker
        return image

    def _grown(self, paths, grow_px):
        """Binary image of *paths* filled and grown by *grow_px* on every side.
        Each path is drawn on its own: uniting mask paths is unreliable because
        they share edges with the component strands' outlines."""
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QColor, QImage, QPainter, QPen

        canvas = self.window.canvas
        image = QImage(canvas.width(), canvas.height(), QImage.Format_Grayscale8)
        image.fill(0)
        painter = QPainter(image)
        pen = QPen(QColor(255, 255, 255))
        pen.setWidthF(grow_px * 2)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(QColor(255, 255, 255))
        for path in paths:
            painter.drawPath(path)
        painter.end()
        return qimage_to_pil(image).convert("L").point(lambda v: 255 if v > 127 else 0)

    def _strand(self, layer_name):
        return next(s for s in self.window.canvas.strands if s.layer_name == layer_name)

    def mask_zone(self, mask_name, grow_px):
        """The mask's drawn footprint grown by *grow_px* (scene of the last render)."""
        mask = self._strand(mask_name)
        return self._grown([mask.get_mask_path_stroke(), mask.get_mask_path()], grow_px)

    def pair_zone(self, first, second, grow_px):
        """Everything within *grow_px* of both strands: where they overlap and
        where either one's shadow can reach the other (scene of the last render)."""
        from shader_utils import build_rendered_geometry
        zones = [self._grown([build_rendered_geometry(self._strand(name))], grow_px)
                 for name in (first, second)]
        return ImageChops.multiply(zones[0], zones[1])

    def canvas_highlight_color(self):
        color = getattr(self.window.canvas, "highlight_color", None)
        return (color.red(), color.green(), color.blue()) if color is not None else (255, 0, 0)


# ----------------------------------------------------------------------------
# Pixel bookkeeping
# ----------------------------------------------------------------------------

def count_on(mask):
    """Number of non-zero pixels in a binary 'L' image."""
    return mask.size[0] * mask.size[1] - mask.histogram()[0]


def changed(a, b):
    r, g, bl = ImageChops.difference(a, b).split()
    worst = ImageChops.lighter(ImageChops.lighter(r, g), bl)
    return worst.point(lambda v: 255 if v > DIFF_THRESHOLD else 0)


def components(mask):
    """8-connected components of a binary 'L' image, as lists of (x, y)."""
    bbox = mask.getbbox()
    if not bbox:
        return []
    width, height = mask.size
    px = mask.load()
    seen = set()
    found = []
    for y in range(bbox[1], bbox[3]):
        for x in range(bbox[0], bbox[2]):
            if not px[x, y] or (x, y) in seen:
                continue
            seen.add((x, y))
            stack, component = [(x, y)], []
            while stack:
                cx, cy = stack.pop()
                component.append((cx, cy))
                for nx in (cx - 1, cx, cx + 1):
                    for ny in (cy - 1, cy, cy + 1):
                        if (0 <= nx < width and 0 <= ny < height and px[nx, ny]
                                and (nx, ny) not in seen):
                            seen.add((nx, ny))
                            stack.append((nx, ny))
            found.append(component)
    return found


def transplant_region(current, reference, near_zone, keep_zone, own_zone=None):
    """Pixels to take from the reference: changed components that reach the
    masked crossing's neighbourhood and stay clear of the keep zone, plus
    every changed pixel on the mask's own piece (*own_zone*), which only this
    mask governs even where a keep zone reaches over it."""
    near, keep = near_zone.load(), keep_zone.load()
    region = Image.new("L", current.size, 0)
    out = region.load()
    picked = []
    diff = changed(current, reference)
    for component in components(diff):
        if not any(near[x, y] for x, y in component):
            continue
        if any(keep[x, y] for x, y in component):
            continue
        picked.append(component)
        for x, y in component:
            out[x, y] = 255
    if own_zone is not None:
        on_piece = ImageChops.subtract(ImageChops.multiply(diff, own_zone), region)
        for component in components(on_piece):
            picked.append(component)
            for x, y in component:
                out[x, y] = 255
    # One pixel of slack so anti-aliased fringes come from the same render.
    return region.filter(ImageFilter.MaxFilter(3)), picked


def reapply_highlight(selected, current, reference, region, color):
    """*selected* is *current* under the translucent selection highlight.
    Recover the highlight's coverage per pixel and lay it over *reference*."""
    result = selected.copy()
    out, sel, cur, ref, inside = result.load(), selected.load(), current.load(), reference.load(), region.load()
    bbox = region.getbbox()
    if not bbox:
        return result
    for y in range(bbox[1], bbox[3]):
        for x in range(bbox[0], bbox[2]):
            if not inside[x, y]:
                continue
            alphas = [(sel[x, y][i] - cur[x, y][i]) / float(color[i] - cur[x, y][i])
                      for i in range(3) if abs(color[i] - cur[x, y][i]) > 24]
            alpha = min(1.0, max(0.0, sum(alphas) / len(alphas))) if alphas else 0.0
            out[x, y] = tuple(int(round(ref[x, y][i] * (1 - alpha) + color[i] * alpha)) for i in range(3))
    return result


def shift_box(box, offset):
    return (box[0] + offset[0], box[1] + offset[1], box[2] + offset[0], box[3] + offset[1])


# ----------------------------------------------------------------------------
# Figures
# ----------------------------------------------------------------------------

def font(size, bold=False):
    names = (["DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf", "segoeuib.ttf"] if bold
             else ["DejaVuSans.ttf", "arial.ttf", "Arial.ttf", "segoeui.ttf"])
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def badge(draw, center, label, fill):
    x, y = center
    draw.ellipse((x - 11, y - 11, x + 11, y + 11), fill=fill, outline=(255, 255, 255), width=2)
    f = font(13, bold=True)
    w = draw.textbbox((0, 0), label, font=f)[2]
    draw.text((x - w / 2, y - 8), label, fill=(255, 255, 255), font=f)


def wrap(draw, text, f, width):
    lines, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if draw.textbbox((0, 0), trial, font=f)[2] > width and line:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    return lines


def mark_insets(draw, insets, crop, origin, color, scale=1):
    """Outline each inset box on a crop pasted at *origin*, numbered on its left."""
    for inset in insets:
        box = [(v - crop[i % 2]) * scale + origin[i % 2] for i, v in enumerate(inset["box"])]
        draw.rectangle(box, outline=color, width=2)
        badge(draw, (box[0] - 14, (box[1] + box[3]) / 2), inset["label"], color)


def comparison_figure(title, left, right, crop, insets, footer, out_path):
    """Two labelled columns (current | expected), each a crop with numbered
    boxes plus a row of zoomed insets underneath."""
    pad, gap = 28, 36
    cw, ch = crop[2] - crop[0], crop[3] - crop[1]
    inset_px = (cw - (len(insets) - 1) * 16) // max(1, len(insets))
    width = pad * 2 + cw * 2 + gap
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    footer_lines = wrap(probe, footer, font(14), width - pad * 2)
    captions = []
    for inset in insets:
        text = "%s  (%dx zoom)" % (inset["title"], inset_px // (inset["box"][2] - inset["box"][0]))
        fits = probe.textbbox((0, 0), text, font=font(13))[2] <= inset_px
        captions.append([text] if fits else wrap(probe, text, font(13), inset_px))
    extra = 16 * (max(len(c) for c in captions) - 1) if captions else 0
    height = 64 + 34 + ch + 22 + inset_px + 30 + extra + 16 + 20 * len(footer_lines) + pad
    fig = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(fig)
    draw.text((pad, 20), title, fill=INK, font=font(20, bold=True))
    for column, (image, heading, color) in enumerate([
            (left, "CURRENT \u2014 what the app draws today", CURRENT_RED),
            (right, "EXPECTED \u2014 what it should look like", EXPECTED_GREEN)]):
        x0 = pad + column * (cw + gap)
        y0 = 64
        draw.text((x0, y0), heading, fill=color, font=font(16, bold=True))
        y0 += 34
        fig.paste(image.crop(crop), (x0, y0))
        draw.rectangle((x0 - 1, y0 - 1, x0 + cw, y0 + ch), outline=(200, 200, 205))
        mark_insets(draw, insets, crop, (x0, y0), color)
        iy = y0 + ch + 22
        for i, inset in enumerate(insets):
            ix = x0 + i * (inset_px + 16)
            zoomed = image.crop(inset["box"]).resize((inset_px, inset_px), Image.NEAREST)
            fig.paste(zoomed, (ix, iy))
            draw.rectangle((ix - 1, iy - 1, ix + inset_px, iy + inset_px), outline=color, width=2)
            badge(draw, (ix + 14, iy + 14), inset["label"], color)
            for n, line in enumerate(captions[i]):
                draw.text((ix, iy + inset_px + 6 + 16 * n), line, fill=MUTED, font=font(13))
    y = height - pad - 20 * len(footer_lines)
    for line in footer_lines:
        draw.text((pad, y), line, fill=MUTED, font=font(14))
        y += 20
    fig.save(out_path)


def attribution_figure(title, no_shadow, passes, crop, insets, out_path, scale=2):
    """Faded shadow-free render with each pass's visible pixels in its own colour."""
    base = Image.blend(no_shadow, Image.new("RGB", no_shadow.size, (255, 255, 255)), 0.55)
    for (_, mask), color in zip(passes, PASS_COLORS):
        base.paste(color, mask=mask)
    view = base.crop(crop)
    view = view.resize((view.width * scale, view.height * scale), Image.NEAREST)
    pad = 24
    legend_h = 26 + 22 * len(passes)
    fig = Image.new("RGB", (view.width + pad * 2, view.height + pad * 2 + 40 + legend_h), (255, 255, 255))
    draw = ImageDraw.Draw(fig)
    draw.text((pad, 16), title, fill=INK, font=font(18, bold=True))
    fig.paste(view, (pad, 52))
    mark_insets(draw, insets, crop, (pad, 52), INK, scale=scale)
    y = 52 + view.height + 14
    draw.text((pad, y), "Colour = pixels that change when only that shadow pass is switched off:",
              fill=MUTED, font=font(14))
    y += 24
    for (name, mask), color in zip(passes, PASS_COLORS):
        count = count_on(mask)
        draw.rectangle((pad, y + 2, pad + 16, y + 16), fill=color)
        draw.text((pad + 26, y), "%s   (%d px)" % (name, count), fill=INK, font=font(14))
        y += 22
    fig.save(out_path)


def strip_figure(title, panels, box, caption, out_path, size=300):
    """Panels of the same zoomed *box* side by side; a panel may carry a
    canvas-space rectangle to circle."""
    pad, gap = 24, 20
    width = pad * 2 + len(panels) * size + (len(panels) - 1) * gap
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    lines = wrap(probe, caption, font(14), width - pad * 2)
    fig = Image.new("RGB", (width, 52 + 28 + size + 20 + 20 * len(lines) + pad), (255, 255, 255))
    draw = ImageDraw.Draw(fig)
    draw.text((pad, 16), title, fill=INK, font=font(18, bold=True))
    scale = size / float(box[2] - box[0])
    for i, (image, heading, color, circle) in enumerate(panels):
        x = pad + i * (size + gap)
        draw.text((x, 52), heading, fill=color, font=font(14, bold=True))
        fig.paste(image.crop(box).resize((size, size), Image.NEAREST), (x, 80))
        draw.rectangle((x - 1, 79, x + size, 80 + size), outline=color, width=2)
        if circle:
            cx0, cy0 = x + (circle[0] - box[0]) * scale, 80 + (circle[1] - box[1]) * scale
            cx1, cy1 = x + (circle[2] - box[0]) * scale, 80 + (circle[3] - box[1]) * scale
            draw.ellipse((cx0 - 12, cy0 - 12, cx1 + 12, cy1 + 12), outline=CURRENT_RED, width=3)
    y = 80 + size + 16
    for line in lines:
        draw.text((pad, y), line, fill=MUTED, font=font(14))
        y += 20
    fig.save(out_path)


# ----------------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------------

def run_example(renderer, example_dir):
    with open(os.path.join(example_dir, "example.json"), encoding="utf-8") as handle:
        spec = json.load(handle)
    scene = os.path.join(example_dir, spec["scene"])
    shadow = spec["shadow"]
    crop = tuple(spec["crop"])
    out = lambda name: os.path.join(example_dir, name)
    label = spec["label"]
    renderer.configure(spec.get("window_size", WINDOW_SIZE), spec.get("canvas_background"))

    # One entry per mask. A single mask can be described at the top level; a
    # scene with several masks whose crossings form a loop (no layer order
    # draws them all) lists each mask with its own reference order in "masks".
    entries = spec.get("masks") or [spec]

    current = renderer.render(scene, shadow)
    passes_seen = list(dict.fromkeys(renderer.calls))
    zones = []  # computed while the masks are still loaded
    for entry in entries:
        keep = Image.new("L", current.size, 0)
        for zone in entry.get("keep_zones", []):
            keep = ImageChops.lighter(keep, renderer.pair_zone(*zone["strands"], grow_px=zone["grow_px"]))
        own = renderer.mask_zone(entry["mask"], entry["own_piece_px"]) if "own_piece_px" in entry else None
        zones.append((renderer.mask_zone(entry["mask"], entry["near_mask_px"]), keep, own))
    highlight = renderer.canvas_highlight_color()
    selected = renderer.render(scene, shadow, select=spec.get("screenshot_select", entries[0]["mask"]))

    expected, expected_selected = current, selected
    region = Image.new("L", current.size, 0)
    picked, per_mask = [], {}
    references = [renderer.render(scene, shadow, order=entry["reference_order"]) for entry in entries]
    for index, (entry, (near, keep, own), reference) in enumerate(zip(entries, zones, references)):
        mine, mine_picked = transplant_region(current, reference, near, keep, own)
        # Each mask's own piece belongs to that mask's reference alone.
        for other_index, (_near, _keep, other_own) in enumerate(zones):
            if other_index != index and other_own is not None:
                mine = ImageChops.subtract(mine, other_own)
        mine = ImageChops.subtract(mine, region)  # the first mask to claim a pixel keeps it
        expected = Image.composite(reference, expected, mine)
        expected_selected = reapply_highlight(expected_selected, current, reference, mine, highlight)
        region = ImageChops.lighter(region, mine)
        picked += mine_picked
        per_mask[entry["mask"]] = sum(len(c) for c in mine_picked)
        name = "reference.png" if len(entries) == 1 else "reference_%s.png" % entry["mask"]
        reference.crop(crop).save(out(name))

    for name, image in [("current.png", current), ("expected.png", expected)]:
        image.crop(crop).save(out(name))

    if len(entries) == 1:
        footer = ("Expected = %s, used only where it differs from today's drawing next to the masked "
                  "crossing. Everything else is today's render, untouched." % spec["reference_note"])
    else:
        footer = ("Expected = %s; each used only where it differs from today's drawing next to its own "
                  "mask. Everything else is today's render, untouched."
                  % "; ".join("around %s, %s" % (e["mask"], e["reference_note"]) for e in entries))
    comparison_figure("%s \u2014 clean render (nothing selected)" % label, current, expected, crop,
                      spec["insets"], footer, out("compare_clean.png"))

    report = {"transplanted_pixels": sum(len(c) for c in picked),
              "transplanted_components": [
                  {"bbox": [min(p[0] for p in c), min(p[1] for p in c),
                            max(p[0] for p in c), max(p[1] for p in c)], "pixels": len(c)}
                  for c in picked]}
    if len(entries) > 1:
        report["transplanted_pixels_per_mask"] = per_mask

    shot_name = spec.get("screenshot")
    if shot_name and os.path.exists(out(shot_name)):
        offset = tuple(spec["screenshot_canvas_offset"])
        shot = Image.open(out(shot_name)).convert("RGB")
        same = shot.crop(shift_box(crop, offset))
        mismatch = changed(same, selected.crop(crop))
        report["screenshot_pixels_off_by_more_than_%d" % DIFF_THRESHOLD] = count_on(mismatch)
        report["screenshot_pixels_compared"] = same.width * same.height
        # Places where the screenshot shows something the rebuilt scene does
        # not draw: the expected screenshot takes the expected render there.
        paste = region.copy()
        unexplained = ImageDraw.Draw(paste)
        for item in spec.get("screenshot_unreproduced", []):
            x0, y0, x1, y1 = item["box"]
            unexplained.rectangle([x0, y0, x1 - 1, y1 - 1], fill=255)
            box = shift_box(tuple(item["box"]), (-crop[0], -crop[1]))
            report.setdefault("screenshot_unreproduced_pixels", []).append(count_on(mismatch.crop(box)))
        shot_expected = shot.copy()
        shot_expected.paste(expected_selected, offset, paste)
        shot_expected.save(out("user_screenshot_expected.png"))
        comparison_figure("%s \u2014 the reported screenshot (mask selected)" % label, shot, shot_expected,
                          shift_box(crop, offset),
                          [dict(i, box=list(shift_box(i["box"], offset))) for i in spec["insets"]],
                          footer, out("compare_screenshot.png"))

    # Which pass paints what: switch each pass off on its own and diff.
    no_shadow = renderer.render(scene, shadow, skip=passes_seen)
    attributed = []
    for key in passes_seen:
        visible = changed(current, renderer.render(scene, shadow, skip=[key]))
        attributed.append((key, visible))
    attribution_figure("%s \u2014 which shadow pass paints each shadow" % label,
                       no_shadow, attributed, crop, spec["insets"], out("attribution.png"))
    report["passes"] = {key: count_on(mask) for key, mask in attributed}

    # A layer order, mask included, that a user could set by hand to get
    # (close to) the expected look with today's code.
    if "workaround_order" in spec:
        workaround = renderer.render(scene, shadow, order=spec["workaround_order"])
        workaround.crop(crop).save(out("workaround.png"))
        report["workaround_pixels_off_expected"] = count_on(changed(workaround, expected))

    if "blocker_inset" in spec:
        blocker_experiment(renderer, spec, scene, shadow, current, reference, report, out)

    with open(out("capture_report.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print("[mask-shadow] %s: %s" % (os.path.basename(example_dir), json.dumps(report)), flush=True)


def blocker_experiment(renderer, spec, scene, shadow, current, reference, report, out):
    """Switch the mask shadow blocker off to see what it currently hides."""
    label = spec["label"]
    unblocked = renderer.render(scene, shadow, neutralise_blocker=True)
    inset = next(i for i in spec["insets"] if i["label"] == spec["blocker_inset"])
    box = tuple(inset["box"])
    leftover = changed(unblocked.crop(box), reference.crop(box))
    pieces = components(leftover)
    circle = None
    if pieces:
        biggest = max(pieces, key=len)
        circle = (box[0] + min(p[0] for p in biggest), box[1] + min(p[1] for p in biggest),
                  box[0] + max(p[0] for p in biggest) + 1, box[1] + max(p[1] for p in biggest) + 1)
    report["blocker_off_vs_reference_pixels_in_inset"] = count_on(leftover)
    strip_figure("%s \u2014 mask shadow blocker switched off (inset %s)" % (label, inset["label"]),
                 [(current, "current", CURRENT_RED, None),
                  (unblocked, "blocker switched off", MUTED, circle),
                  (reference, "reference (genuine crossing)", EXPECTED_GREEN, None)],
                 box,
                 "Middle: get_shadow_blocker_path() replaced by an empty path, so masks stop cutting "
                 "holes into other strands' shadows. Circled: what then still differs from the "
                 "reference.",
                 out("blocker_experiment.png"))


def main(argv):
    targets = argv[1:] or sorted(
        os.path.join(DOCS_DIR, name) for name in os.listdir(DOCS_DIR)
        if os.path.exists(os.path.join(DOCS_DIR, name, "example.json")))
    renderer = Renderer()
    for example_dir in targets:
        run_example(renderer, os.path.abspath(example_dir))
    # Tear-down of the offscreen window hangs in QApplication shutdown, and
    # nothing needs flushing once the PNGs are on disk.
    os._exit(0)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
