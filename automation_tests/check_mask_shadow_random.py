"""Check mask shadows against genuine crossings in random scenes.

Builds scenes of 3-5 straight strands in a random layer order and masks one
crossing (first strand below second strand in the layer order). When moving
the first strand right above the second strand (or the second right below the
first) flips no other overlapping pair, that layer order without the mask is
the genuine crossing the mask stands for, and the two must look the same.

The mask's lifted piece itself is drawn by filling the mask paths, whose
anti-aliased corners and the end lines of strands ending inside the crossing
differ from a genuine crossing; that is not a shadow. So each scene is also
compared with shadows switched off, and only differences that appear with
shadows on count ("shadow-only").

Run offscreen from the repo root:

    QT_QPA_PLATFORM=offscreen python automation_tests/check_mask_shadow_random.py [first_seed] [last_seed]

Exits non-zero if any scene has a shadow-only difference larger than
MAX_SPECK pixels.
"""
import copy
import json
import os
import random
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import capture_mask_shadow_observations as capture
from PIL import ImageChops, ImageFilter

MAX_SPECK = 2  # isolated anti-aliased pixels
SHADOW = {"num_steps": 2, "max_blur_radius": 30.0}
COLORS = [(200, 170, 230, 255), (170, 220, 190, 255), (240, 200, 150, 255),
          (160, 200, 240, 255), (240, 170, 170, 255), (220, 220, 140, 255)]


def templates():
    """A plain strand record and a mask record from example 1's scene."""
    path = os.path.join(capture.DOCS_DIR, "example_01_mask_2_1_over_2_3", "scene.json")
    with open(path, encoding="utf-8") as handle:
        history = json.load(handle)
    strands = history["states"][0]["data"]["strands"]
    return history, strands[1], strands[4]


def write_scene(path, history, strand_t, mask_t, strands, masks):
    def point(x, y):
        return {"x": float(x), "y": float(y)}
    records = []
    for index, (name, (x0, y0, x1, y1), rgba) in enumerate(strands):
        record = copy.deepcopy(strand_t)
        red, green, blue, alpha = rgba
        record.update(index=index, start=point(x0, y0), end=point(x1, y1), has_circles=[False, False],
                      layer_name=name, set_number=int(name.split("_")[0]),
                      color={"r": red, "g": green, "b": blue, "a": alpha},
                      control_points=[point(x0, y0), point(x0, y0)], control_point_center=point(x0, y0))
        records.append(record)
    by_name = {record["layer_name"]: record for record in records}
    for first, second in masks:
        record = copy.deepcopy(mask_t)
        first_record = by_name[first]
        record.update(index=len(records), start=first_record["start"], end=first_record["end"],
                      layer_name="%s_%s" % (first, second),
                      set_number=int("%s%s" % (first_record["set_number"], by_name[second]["set_number"])),
                      color=first_record["color"], control_point_center=first_record["start"])
        records.append(record)
    scene = copy.deepcopy(history)
    scene["states"][0]["data"]["strands"] = records
    scene["states"][0]["data"]["shadow_overrides"] = {}
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(scene, handle)


def area(path):
    total = 0.0
    for polygon in path.toFillPolygons():
        points = [polygon.at(i) for i in range(polygon.count())]
        total += abs(sum(a.x() * b.y() - b.x() * a.y() for a, b in zip(points, points[1:] + points[:1]))) / 2.0
    return total


def main(argv):
    first_seed = int(argv[1]) if len(argv) > 1 else 0
    last_seed = int(argv[2]) if len(argv) > 2 else 59
    work = tempfile.mkdtemp(prefix="mask_shadow_random_")
    history, strand_t, mask_t = templates()
    renderer = capture.Renderer()
    renderer.configure((1264, 935), "#ECECEC")
    canvas = renderer.window.canvas
    from PyQt5.QtGui import QPainterPath
    from shader_utils import build_rendered_geometry

    def render(scene, order=None, shadows=True):
        image = renderer.render(scene, SHADOW, order=order)
        if shadows:
            return image
        canvas.toggle_shadow()
        canvas.update()
        renderer.app.processEvents()
        capture._wait(80)
        return capture.qimage_to_pil(canvas.grab().toImage())

    compared, failed = 0, []
    for seed in range(first_seed, last_seed + 1):
        rnd = random.Random(seed)
        strands = []
        for index in range(rnd.randint(3, 5)):
            while True:
                x0, y0, x1, y1 = [rnd.randint(200, 800) for _ in range(4)]
                if (x1 - x0) ** 2 + (y1 - y0) ** 2 > 250 ** 2:
                    break
            strands.append(("%d_1" % (index + 1), (x0, y0, x1, y1), COLORS[index % len(COLORS)]))
        rnd.shuffle(strands)
        order = [name for name, _, _ in strands]
        base = os.path.join(work, "seed%d_base.json" % seed)
        write_scene(base, history, strand_t, mask_t, strands, [])
        renderer.render(base, SHADOW)
        geometry = {s.layer_name: build_rendered_geometry(s) for s in canvas.strands}
        footprint = {s.layer_name: s.get_selection_path() for s in canvas.strands}

        def overlap(a, b):
            return area(QPainterPath(geometry[a]).intersected(geometry[b])) > 200

        def touch(a, b):
            return area(QPainterPath(footprint[a]).intersected(footprint[b])) > 0.5

        pairs = [(a, b) for i, a in enumerate(order) for b in order[i + 1:] if overlap(a, b)]
        if not pairs:
            continue
        first, second = rnd.choice(pairs)
        between = order[order.index(first) + 1:order.index(second)]
        if not any(touch(first, name) for name in between):
            genuine = [name for name in order if name != first]
            genuine.insert(genuine.index(second) + 1, first)
        elif not any(touch(second, name) for name in between):
            genuine = [name for name in order if name != second]
            genuine.insert(genuine.index(first), second)
        else:
            continue  # the mask closes a loop: no layer order draws it
        scene = os.path.join(work, "seed%d.json" % seed)
        write_scene(scene, history, strand_t, mask_t, strands, [(first, second)])
        with_shadows = capture.changed(render(scene), render(scene, genuine))
        without = capture.changed(render(scene, shadows=False), render(scene, genuine, shadows=False))
        shadow_only = ImageChops.subtract(with_shadows, without.filter(ImageFilter.MaxFilter(5)))
        largest = max((len(c) for c in capture.components(shadow_only)), default=0)
        compared += 1
        verdict = "ok" if largest <= MAX_SPECK else "FAIL"
        print("seed %d: mask %s over %s, order %s: %d px differ, %d with shadows off, largest shadow-only piece %d px: %s"
              % (seed, first, second, order, capture.count_on(with_shadows), capture.count_on(without), largest, verdict),
              flush=True)
        if verdict != "ok":
            failed.append(seed)
    print("%d scenes compared, %d failed%s" % (compared, len(failed), (": seeds %s" % failed) if failed else ""),
          flush=True)
    # Tear-down of the offscreen window hangs in QApplication shutdown.
    os._exit(1 if failed else 0)


if __name__ == "__main__":
    main(sys.argv)
