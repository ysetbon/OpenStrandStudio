"""Check the app's mask shadows against the observation catalogue.

For every example in docs/mask_shadow_observations/ this renders the scene
with the code in src/ (nothing selected) and compares it with the example's
committed expected.png. It also re-renders every reference layer order (the
mask-free drawings the expected images were built from) and compares them
with the committed reference PNGs, so a fix that changes how ordinary,
mask-free crossings are drawn shows up as a regression.

Run offscreen from the repo root:

    QT_QPA_PLATFORM=offscreen python automation_tests/check_mask_shadow_fix.py [out_dir]

Writes a side-by-side image per example (render | expected | differences in
red) to out_dir. Exits non-zero if a mask-free reference changed, or if a pixel
that is not drawn as in a genuine render differs from expected.png by more
than anti-aliasing (AA_TOLERANCE per channel).
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import capture_mask_shadow_observations as capture
from PIL import Image, ImageChops, ImageDraw

# Largest per-channel difference (0-255) still counted as anti-aliasing: where
# two drawings of the same edge put its partially covered pixels.
AA_TOLERANCE = 32


def describe(mask):
    pieces = sorted(capture.components(mask), key=len, reverse=True)
    return [(len(c), (min(p[0] for p in c), min(p[1] for p in c), max(p[0] for p in c), max(p[1] for p in c)))
            for c in pieces]


def side_by_side(render, expected, mask, out_path, scale=2):
    marked = render.copy()
    marked.paste((255, 0, 0), mask=mask)
    width, height = render.size
    sheet = Image.new("RGB", (width * 3 * scale + 40, height * scale + 30), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    for i, (image, title) in enumerate([(render, "render (src/)"), (expected, "expected.png"),
                                         (marked, "differences")]):
        x = i * (width * scale + 20)
        sheet.paste(image.resize((width * scale, height * scale), Image.NEAREST), (x, 30))
        draw.text((x, 8), title, fill=(30, 30, 35), font=capture.font(14, bold=True))
    sheet.save(out_path)


def check_example(renderer, example_dir, out_dir):
    with open(os.path.join(example_dir, "example.json"), encoding="utf-8") as handle:
        spec = json.load(handle)
    name = os.path.basename(example_dir)
    scene = os.path.join(example_dir, spec["scene"])
    crop = tuple(spec["crop"])
    renderer.configure(spec.get("window_size", capture.WINDOW_SIZE), spec.get("canvas_background"))
    failures = 0

    render = renderer.render(scene, spec["shadow"]).crop(crop)
    expected = Image.open(os.path.join(example_dir, "expected.png")).convert("RGB")
    mask = capture.changed(render, expected)
    pieces = describe(mask)
    print("%s: %d px differ from expected.png%s" % (
        name, capture.count_on(mask), "" if not pieces else "; largest pieces %s" % pieces[:6]), flush=True)
    side_by_side(render, expected, mask, os.path.join(out_dir, "%s.png" % name))

    entries = spec.get("masks") or [spec]
    references = []
    for entry in entries:
        reference_name = "reference.png" if len(entries) == 1 else "reference_%s.png" % entry["mask"]
        reference = renderer.render(scene, spec["shadow"], order=entry["reference_order"]).crop(crop)
        committed = Image.open(os.path.join(example_dir, reference_name)).convert("RGB")
        diff = capture.changed(reference, committed)
        print("  %s (mask-free): %d px differ from the committed render" % (reference_name, capture.count_on(diff)),
              flush=True)
        failures += bool(capture.count_on(diff))
        references.append(committed)

    # expected.png is today's render with pieces of the genuine (mask-free)
    # renders pasted in. Where the render differs from expected.png but equals
    # a genuine render, it is drawing the genuine crossing there and the
    # difference is only where the pasted piece happened to end.
    if pieces:
        as_genuine = Image.new("L", render.size, 0)
        for reference in references:
            as_genuine = ImageChops.lighter(as_genuine, ImageChops.invert(capture.changed(render, reference)))
        unexplained = ImageChops.multiply(mask, ImageChops.invert(as_genuine))
        rest = describe(unexplained)
        worst = 0
        render_px, expected_px, flags = render.load(), expected.load(), unexplained.load()
        for y in range(render.height):
            for x in range(render.width):
                if flags[x, y]:
                    worst = max(worst, max(abs(a - b) for a, b in zip(render_px[x, y], expected_px[x, y])))
        print("  of those, %d px are drawn exactly as in the genuine render; %d px are not%s" % (
            capture.count_on(mask) - capture.count_on(unexplained), capture.count_on(unexplained),
            "" if not rest else " (largest %s, at most %d/255 off: %s)" % (
                rest[:6], worst, "anti-aliasing" if worst <= AA_TOLERANCE else "FAIL")), flush=True)
        failures += worst > AA_TOLERANCE
    return failures


def main(argv):
    out_dir = argv[1] if len(argv) > 1 else tempfile.mkdtemp(prefix="mask_shadow_check_")
    os.makedirs(out_dir, exist_ok=True)
    examples = sorted(
        os.path.join(capture.DOCS_DIR, name) for name in os.listdir(capture.DOCS_DIR)
        if os.path.exists(os.path.join(capture.DOCS_DIR, name, "expected.png")))
    renderer = capture.Renderer()
    failures = sum(check_example(renderer, example, out_dir) for example in examples)
    print("side-by-side images in %s" % out_dir, flush=True)
    print("FAIL" if failures else "OK: every example matches expected.png up to anti-aliasing", flush=True)
    # Tear-down of the offscreen window hangs in QApplication shutdown.
    os._exit(1 if failures else 0)


if __name__ == "__main__":
    main(sys.argv)
