"""A mask lifts its first strand over its second strand at their crossing.
Where the user erased part of the mask, the second strand stays on top, so it
casts its shadow on the first strand there as at any crossing; near the
mask's piece the first strand lies above it and gets none
(shader_utils._pair_shadow).

tests/shadow_scenes/mask_with_erased_crossing.json: 1_2 crosses 2_2 (above
it in the layer order) twice. Mask 1_2_2_2 lifts 1_2 over 2_2 at the left
crossing; its deletion rectangle erases it at the right crossing.
"""

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QPainterPath
from PyQt5.QtWidgets import QApplication

import shader_utils
from save_load_manager import load_strands_from_data

APP = QApplication.instance() or QApplication([])
SCENE = Path(__file__).resolve().parent / "shadow_scenes" / "mask_with_erased_crossing.json"
BLUR = 30.0


class LayerState:
    def __init__(self, order):
        self.order = order

    def getOrder(self):
        return list(self.order)

    def getConnections(self):
        return {}

    def get_shadow_override(self, casting, receiving):
        return None

    def get_shadow_visibility(self, casting, receiving):
        return True

    def get_subtracted_layers(self, casting, receiving):
        return []


def scene(erased=True):
    data = json.loads(SCENE.read_text(encoding="utf-8"))["states"][0]["data"]
    if not erased:
        for item in data["strands"]:
            item.pop("deletion_rectangles", None)
    loader = SimpleNamespace(strands=[], groups={}, strand_colors={}, shadow_enabled=True,
                             _suppress_layer_panel_refresh=True, _suppress_repaint=True,
                             update=lambda: None)
    strands = load_strands_from_data(data, loader)[0]
    canvas = SimpleNamespace(strands=strands, shadow_enabled=True, shadow_selected_only=False,
                             enable_third_control_point=False, max_blur_radius=BLUR, num_steps=2,
                             layer_state_manager=LayerState([s.layer_name for s in strands]))
    for strand in strands:
        strand.canvas = canvas
        # The curve settings the scene was drawn with, which are not saved in the file.
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
