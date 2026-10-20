"""A mask lifts its first strand over its second strand at their crossing.
Where the user erased part of the mask, the second strand stays on top, so it
casts its shadow on the first strand there as at any crossing; near the
mask's piece the first strand lies above it and gets none
(shader_utils._pair_shadow).

tests/shadow_scenes/mask_with_erased_crossing.json: 1_2 crosses 2_2 (above
it in the layer order) twice. Mask 1_2_2_2 lifts 1_2 over 2_2 at the left
crossing; its deletion rectangle erases it at the right crossing.

tests/shadow_scenes/erased_mask/: 1_1 (a U) dips through the straight 2_1,
above it in the layer order, crossing it near x=220 and x=580, or (the
half_ scenes) a straight 1_1 crosses 2_1 once near x=360. Mask 1_1_2_1 is
erased at the right crossing unless the scene's name says otherwise. Each
erased crossing is measured against the same crossing in a scene without
the mask: an erased crossing is an ordinary crossing.
"""

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QColor, QImage, QPainter, QPainterPath
from PyQt5.QtWidgets import QApplication

import shader_utils
from save_load_manager import load_strands_from_data

APP = QApplication.instance() or QApplication([])
SCENES = Path(__file__).resolve().parent / "shadow_scenes"
BLUR = 30.0


class LayerState:
    def __init__(self, order, overrides):
        self.order = order
        self.overrides = overrides

    def getOrder(self):
        return list(self.order)

    def getConnections(self):
        return {}

    def get_shadow_override(self, casting, receiving):
        return self.overrides.get(casting, {}).get(receiving)

    def get_shadow_visibility(self, casting, receiving):
        override = self.get_shadow_override(casting, receiving)
        return True if override is None else override.get("visibility", True)

    def get_subtracted_layers(self, casting, receiving):
        return list((self.get_shadow_override(casting, receiving) or {}).get("subtracted_layers", []))


def scene(name="mask_with_erased_crossing", erased=True):
    data = json.loads((SCENES / f"{name}.json").read_text(encoding="utf-8"))["states"][0]["data"]
    if not erased:
        for item in data["strands"]:
            item.pop("deletion_rectangles", None)
    loader = SimpleNamespace(strands=[], groups={}, strand_colors={}, shadow_enabled=True,
                             _suppress_layer_panel_refresh=True, _suppress_repaint=True,
                             update=lambda: None)
    strands = load_strands_from_data(data, loader)[0]
    canvas = SimpleNamespace(strands=strands, shadow_enabled=True, shadow_selected_only=False,
                             enable_third_control_point=False, max_blur_radius=BLUR, num_steps=2,
                             layer_state_manager=LayerState([s.layer_name for s in strands],
                                                            data.get("shadow_overrides") or {}))
    for strand in strands:
        strand.canvas = canvas
        # The curve settings the scenes were drawn with, which are not saved in the file.
        strand.control_point_base_fraction = 3.25
        strand.distance_multiplier = 3.6
        strand.curve_response_exponent = 2.6
    for strand in strands:
        if not hasattr(strand, "get_mask_path"):
            strand.update_shape()
    return canvas, {strand.layer_name: strand for strand in strands}


def shadow(canvas, strands, caster, receiver):
    return shader_utils.shadow_preview(canvas, strands[caster], strands[receiver], caster, receiver,
                                       cache={})


def erased_rect(mask):
    rect = mask.deletion_rectangles[0]
    path = QPainterPath()
    path.addRect(QRectF(*rect["top_left"], rect["top_right"][0] - rect["top_left"][0],
                        rect["bottom_left"][1] - rect["top_left"][1]))
    return path


def shaded_pixels(name, caster="2_1", receiver="1_1", box=(0, 0, 800, 700)):
    """Pixels inside *box* the caster's shadow on the receiver covers, painted
    as the Shadow Editor's preview paints it (clipped by the painter, which
    gets Qt's boolean operations out of the measurement)."""
    canvas, strands = scene(f"erased_mask/{name}")
    preview = shadow(canvas, strands, caster, receiver)
    if preview is None:
        return 0
    area, clips = preview
    x0, y0, x1, y1 = box
    image = QImage(x1 - x0, y1 - y0, QImage.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    painter.translate(-x0, -y0)
    for clip in clips:
        painter.setClipPath(clip, Qt.IntersectClip)
    painter.fillPath(area, QColor(0, 0, 0))
    painter.end()
    alpha = image.constBits().asstring(image.byteCount())[3::4]
    return sum(1 for value in alpha if value)


LEFT, RIGHT = (150, 200, 300, 400), (500, 200, 650, 400)
# Either side of where the half_erased_crossing mask's deletion rectangle starts (x=360).
LIFTED_HALF, ERASED_HALF = (250, 200, 360, 400), (360, 200, 480, 400)


def test_the_second_strand_casts_on_the_first_where_the_mask_is_erased():
    canvas, strands = scene()
    preview = shadow(canvas, strands, "2_2", "1_2")
    assert preview is not None
    area, _clips = preview
    assert area.intersects(erased_rect(strands["1_2_2_2"]))


def test_it_casts_nothing_near_the_lifted_crossing():
    canvas, strands = scene()
    area, clips = shadow(canvas, strands, "2_2", "1_2")
    piece = shader_utils._piece_of(strands["1_2_2_2"], {})
    for path in [area] + clips:
        assert shader_utils._approx_path_area(path.intersected(piece)) < 1.0


def test_the_first_strand_still_casts_on_the_second_at_the_lifted_crossing():
    canvas, strands = scene()
    assert shadow(canvas, strands, "1_2_2_2", "2_2") is not None


def test_with_nothing_erased_the_second_strand_casts_nothing_on_the_first():
    canvas, strands = scene(erased=False)
    assert shadow(canvas, strands, "2_2", "1_2") is None


@pytest.mark.parametrize("name, box, plain", [
    ("one_crossing_erased", RIGHT, "no_mask"),
    # 3_1 lies between the two strands, over 1_1 just below the crossing.
    ("strand_between", RIGHT, "strand_between_no_mask"),
    ("half_erased_crossing", ERASED_HALF, "half_no_mask"),
    # Nothing left to lift: the mask changes nothing.
    ("everything_erased", (0, 0, 800, 700), "no_mask"),
])
def test_an_erased_crossing_is_shaded_like_a_crossing_without_the_mask(name, box, plain):
    expected = shaded_pixels(plain, box=box)
    assert expected > 1000
    assert abs(shaded_pixels(name, box=box) - expected) <= 0.01 * expected


@pytest.mark.parametrize("name, box", [
    ("one_crossing_erased", LEFT),
    ("half_erased_crossing", LIFTED_HALF),
])
def test_the_lifted_crossing_stays_unshaded(name, box):
    assert shaded_pixels(name, box=box) == 0


@pytest.mark.parametrize("name", [
    # The mask covers both crossings: 1_1 lies above 2_1 everywhere.
    "nothing_erased",
    # The Shadow Editor hides 2_1's shadow on 1_1.
    "shadow_hidden_in_editor",
    # 2_1 lies below 1_1 in the layer order.
    "first_already_above",
])
def test_no_shadow_where_none_belongs(name):
    assert shaded_pixels(name) == 0


def test_a_hidden_mask_lifts_nothing():
    assert shaded_pixels("mask_hidden") == shaded_pixels("no_mask") > 1000
