"""Check the Shadow Editor's shadow preview against what the canvas draws.

For every shadow row the Shadow Editor offers in a scene (each strand onto
each layer below it, and each mask onto its second strand), this finds where
the canvas draws that shadow: the pixels the caster's shadow pass paints (for
a mask, the pass that paints its first strand's shadow on its second strand),
where the receiver shows (the pixels that change when the receiver is drawn
in another colour). Both are measured with every other shadow pass left out:
where the shadows below it have made the canvas nearly black, the faint end
of a soft edge changes a pixel by less than CHANGED. Switching off a single
row would not do: the soft edge is stroked along all the caster's outlines
at once and lands on every receiver it reaches, so where receivers overlap a
row's shadow also reaches the receiver through the other one. The preview
(shader_utils.shadow_preview) is measured against those pixels:

- missed: how much of the drawn shadow the preview does not cover;
- spill: how much of the preview, where the receiver shows, gets no shadow.

The measure the preview used before the mask shadow fix
(auto_shadow._surviving_shadow) is reported next to it for comparison.

Run offscreen from the repo root:

    QT_QPA_PLATFORM=offscreen python automation_tests/check_shadow_preview.py [scene.json ...]

Without arguments it checks the examples in docs/mask_shadow_observations/.
Exits non-zero if the preview misses more than MAX_MISSED of a drawn shadow,
or spills more than MAX_SPILL, on any row.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import capture_mask_shadow_observations as capture
from PIL import ImageChops, ImageFilter

SHADOW = {"num_steps": 2, "max_blur_radius": 30.0}
CHANGED = 8        # per-channel difference (0-255) that counts as drawn
SLACK_PX = 2       # anti-aliased pixels along the edges of either area
MAX_MISSED = 0.02  # share of a drawn shadow the preview may miss
MAX_SPILL = 0.05   # share of the shown preview the canvas may leave undrawn
MIN_DRAWN = 30     # fewer pixels than this, drawn or shown, are anti-aliasing noise


def binary(image):
    return image.point(lambda v: 255 if v > 127 else 0)


def count(mask):
    return mask.histogram()[255]


def both(a, b):
    return ImageChops.multiply(a, b)


def grown(mask, px):
    return mask.filter(ImageFilter.MaxFilter(2 * px + 1)) if px else mask


def solid(mask):
    """*mask* without the parts thinner than 3 px: anti-aliased rims, which
    show the layers below through their half-covered pixels."""
    return mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))


def changed_pixels(before, after):
    difference = ImageChops.difference(before, after)
    r, g, b = difference.split()
    return ImageChops.lighter(ImageChops.lighter(r, g), b).point(lambda v: 255 if v > CHANGED else 0)


class PreviewCheck:
    def __init__(self):
        self.renderer = capture.Renderer()
        import shader_utils
        import auto_shadow
        self.shader_utils = shader_utils
        self.auto_shadow = auto_shadow

    @property
    def canvas(self):
        return self.renderer.window.canvas

    def grab(self):
        self.canvas.update()
        self.renderer.app.processEvents()
        return capture.qimage_to_pil(self.canvas.grab().toImage())

    def raster(self, paths):
        """Binary image of *paths*, filled without anti-aliasing. An entry may
        be (path, clips), as shadow_preview returns it, or None."""
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QColor, QImage, QPainter
        image = QImage(self.canvas.width(), self.canvas.height(), QImage.Format_Grayscale8)
        image.fill(0)
        painter = QPainter(image)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255))
        for entry in paths:
            path, clips = entry if isinstance(entry, tuple) else (entry, [])
            if path is None or path.isEmpty():
                continue
            painter.save()
            for clip in clips:
                painter.setClipPath(clip, Qt.IntersectClip if painter.hasClipping() else Qt.ReplaceClip)
            painter.drawPath(path)
            painter.restore()
        painter.end()
        return binary(capture.qimage_to_pil(image).convert("L"))

    def shows(self, strand):
        """Where *strand* shows: the pixels that change when it is drawn in
        another colour (the drawing order, joint circles and translucency
        decide that, not the strands' outlines), without shadows."""
        from PyQt5.QtGui import QColor
        color = QColor(strand.color)
        probe = QColor(255 - color.red(), 255 - color.green(), 128 if color.blue() < 128 else 0, color.alpha())
        strand.color = probe
        try:
            return changed_pixels(self.bare, self.render_skipping(self.passes))
        finally:
            strand.color = color

    def painted_by(self, shadow_pass):
        """The pixels *shadow_pass* paints, on the scene without shadows."""
        return changed_pixels(self.bare, self.render_skipping(self.passes - {shadow_pass}))

    def rows(self):
        """(caster, receiver) layer names of every row the Shadow Editor shows."""
        order = self.canvas.layer_state_manager.getOrder()
        by_name = {s.layer_name: s for s in self.canvas.strands}
        rows = []
        for index, caster in enumerate(order):
            strand = by_name.get(caster)
            if strand is None or getattr(strand, "is_hidden", False):
                continue
            if hasattr(strand, "get_mask_path"):
                second = getattr(strand.second_selected_strand, "layer_name", None)
                if second in order[:index]:
                    rows.append((caster, second))
                continue
            for receiver in order[:index]:
                other = by_name.get(receiver)
                if other is not None and not getattr(other, "is_hidden", False):
                    rows.append((caster, receiver))
        return rows

    def check_scene(self, scene_path, window_size, background):
        self.renderer.configure(window_size, background)
        self.renderer.render(scene_path, SHADOW)
        self.passes = set(self.renderer.calls)
        self.bare = self.render_skipping(self.passes)
        canvas = self.canvas
        by_name = {s.layer_name: s for s in canvas.strands}
        shows, painted = {}, {}
        results = []
        for caster, receiver in self.rows():
            cs, rs = by_name[caster], by_name[receiver]
            new = self.raster([self.shader_utils.shadow_preview(canvas, cs, rs, caster, receiver)])
            old = self.raster([self.auto_shadow._surviving_shadow(canvas, cs, rs, caster, receiver)])
            if count(new) == 0 and count(old) == 0 and not self.may_touch(cs, rs):
                continue
            if caster not in painted:
                painted[caster] = self.painted_by("%s: %s" % (
                    caster, "draw_mask_lift_shadow" if hasattr(cs, "get_mask_path") else "draw_strand_shadow"))
            if receiver not in shows:
                shows[receiver] = self.shows(rs)
            drawn = both(painted[caster], shows[receiver])
            results.append((caster, receiver, self.measure(drawn, new, shows[receiver]),
                            self.measure(drawn, old, shows[receiver])))
        return results

    def render_skipping(self, shadow_passes):
        """The scene drawn with *shadow_passes* left out (the scene stays loaded)."""
        self.renderer.skip = set(shadow_passes)
        try:
            return self.grab()
        finally:
            self.renderer.skip = set()

    def may_touch(self, caster, receiver):
        from PyQt5.QtCore import QRectF
        reach = SHADOW["max_blur_radius"]
        a = QRectF(caster.boundingRect()).adjusted(-reach, -reach, reach, reach)
        return a.intersects(receiver.boundingRect())

    @staticmethod
    def measure(drawn, preview, shows):
        drawn_px = count(drawn)
        missed = count(solid(ImageChops.subtract(drawn, grown(preview, SLACK_PX))))
        shown = both(preview, shows)
        shown_px = count(shown)
        spill = count(solid(ImageChops.subtract(shown, grown(drawn, SLACK_PX))))
        return {"drawn": drawn_px, "missed": missed, "shown": shown_px, "spill": spill}


def example_scenes():
    scenes = []
    for name in sorted(os.listdir(capture.DOCS_DIR)):
        spec_path = os.path.join(capture.DOCS_DIR, name, "example.json")
        if not os.path.exists(spec_path):
            continue
        with open(spec_path, encoding="utf-8") as handle:
            spec = json.load(handle)
        scenes.append((os.path.join(capture.DOCS_DIR, name, spec["scene"]),
                       tuple(spec.get("window_size", capture.WINDOW_SIZE)), spec.get("canvas_background")))
    return scenes


def share(part, whole):
    return part / whole if whole else 0.0


def main(argv):
    scenes = [(path, (1600, 1200), "#ECECEC") for path in argv[1:]] or example_scenes()
    check = PreviewCheck()
    failed = []
    for scene_path, window_size, background in scenes:
        results = check.check_scene(scene_path, window_size, background)
        name = os.path.basename(os.path.dirname(scene_path)) if scene_path.endswith("scene.json") \
            else os.path.basename(scene_path)
        totals = {"new": [0, 0, 0, 0], "old": [0, 0, 0, 0]}
        worst = []
        for caster, receiver, new, old in results:
            for key, m in (("new", new), ("old", old)):
                totals[key][0] += m["drawn"]
                totals[key][1] += m["missed"]
                totals[key][2] += m["shown"]
                totals[key][3] += m["spill"]
            missed_share, spill_share = share(new["missed"], new["drawn"]), share(new["spill"], new["shown"])
            if ((new["drawn"] >= MIN_DRAWN and missed_share > MAX_MISSED)
                    or (new["shown"] >= MIN_DRAWN and spill_share > MAX_SPILL)):
                worst.append((caster, receiver, new, missed_share, spill_share))
        print("%s: %d rows" % (name, len(results)))
        for key, label in (("old", "preview before the fix"), ("new", "preview now")):
            drawn, missed, shown, spill = totals[key]
            print("  %-24s misses %5.1f%% of %6d drawn px, spills %5.1f%% of %6d shown px"
                  % (label, 100 * share(missed, drawn), drawn, 100 * share(spill, shown), shown))
        for caster, receiver, m, missed_share, spill_share in worst:
            print("  FAIL %s -> %s: misses %.1f%% of %d drawn px, spills %.1f%% of %d shown px"
                  % (caster, receiver, 100 * missed_share, m["drawn"], 100 * spill_share, m["shown"]))
            failed.append((name, caster, receiver))
        sys.stdout.flush()
    print("OK: the preview matches the canvas on every row" if not failed
          else "%d rows differ from the canvas" % len(failed))
    # Tear-down of the offscreen window hangs in QApplication shutdown.
    os._exit(1 if failed else 0)


if __name__ == "__main__":
    main(sys.argv)
