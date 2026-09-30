"""A mask draws a piece of its first strand over its second strand, at the
mask's place in the layer order. The piece must not cover a strand that lies
above both of its strands (it lies above their crossing), so the piece is
clipped around what such a strand paints solidly (shader_utils
._covering_strands, ._piece_keep).

The designs in tests/mask_piece/ each put one kind of strand next to (or
across) the crossing of 1_1 and 2_1, which mask 1_1_2_1 lifts. Leaving a
hole in the piece where a strand paints nothing solid would show the
unlifted strand through it: a shadow-only strand, a see-through one, and
the see-through outline of an otherwise solid one. A strand that continues
either of the two at a joint inside the crossing is left covered, as before.
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

from PyQt5.QtCore import QPointF
from PyQt5.QtWidgets import QApplication

import shader_utils
from save_load_manager import load_strands_from_data

APP = QApplication.instance() or QApplication([])
DESIGNS = Path(__file__).resolve().parent / "mask_piece"


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


def design(name):
    """The strands of tests/mask_piece/<name>.json by layer name, on one
    canvas in the file's layer order."""
    data = json.loads((DESIGNS / f"{name}.json").read_text(encoding="utf-8"))
    if data.get("type") == "OpenStrandStudioHistory":
        data = data["states"][data.get("current_step", 1) - 1]["data"]
    loader = SimpleNamespace(strands=[], groups={}, strand_colors={}, shadow_enabled=True,
                             _suppress_layer_panel_refresh=True, _suppress_repaint=True,
                             update=lambda: None)
    strands = load_strands_from_data(data, loader)[0]
    canvas = SimpleNamespace(strands=strands, shadow_enabled=True, shadow_selected_only=False,
                             enable_third_control_point=True,
                             layer_state_manager=LayerState([s.layer_name for s in strands]))
    for strand in strands:
        strand.canvas = canvas
        # The canvas's default curve settings, which are not saved in the file.
        strand.control_point_base_fraction = 1.0
        strand.distance_multiplier = 2.0
        strand.curve_response_exponent = 2.0
    for strand in strands:
        if not hasattr(strand, "get_mask_path"):
            strand.update_shape()
    return {strand.layer_name: strand for strand in strands}


def uncovered(name, mask="1_1_2_1"):
    """Layer names of the strands the mask's piece keeps clear of."""
    strands = design(name)
    return sorted(item.layer_name for item, _solid in shader_utils._covering_strands(strands[mask], {}))


@pytest.mark.parametrize("name, expected", [
    # Above both strands: a neighbour beside the crossing, one crossing it.
    ("neighbour_opaque", ["3_1"]),
    ("third_strand_over", ["3_1"]),
    ("diagonal_crossing", ["3_1", "4_1"]),
    ("first_already_above", ["3_1"]),
    # Its fill is see-through, but it paints its body in its opaque outline
    # colour under the fill, so it hides what is below.
    ("neighbour_translucent", ["3_1"]),
    # Its outline is see-through: only its fill counts (see below).
    ("neighbour_no_outline", ["3_1"]),
    # Drawn after the mask (4_1), it lies over the piece anyway.
    ("mask_mid_order", ["3_1"]),
    # Between the two strands in the layer order: covered, as before.
    ("third_strand_between", []),
    # Nothing solid to keep clear of: the unlifted strand would show.
    ("neighbour_shadow_only", []),
    ("neighbour_see_through", []),
    ("neighbour_hidden", []),
    # It continues 1_1 at a joint inside the crossing: covered, as before.
    ("joint_seamless", []),
    ("joint_circle", []),
])
def test_the_piece_keeps_clear_only_of_solid_strands_above_its_crossing(name, expected):
    assert uncovered(name) == expected


def test_the_piece_is_clipped_around_a_solid_neighbour():
    strands = design("neighbour_opaque")
    keep = shader_utils._piece_keep(strands["1_1_2_1"], {})
    assert keep is not None
    assert keep.contains(QPointF(290, 300))      # the piece, clear of the neighbour
    assert not keep.contains(QPointF(326, 300))  # the neighbour's edge over the crossing


def test_the_piece_still_covers_a_see_through_outline():
    """The neighbour's outline band (318 to 322) is see-through: the piece
    paints there, else the unlifted strand shows as a thin strip."""
    strands = design("neighbour_no_outline")
    keep = shader_utils._piece_keep(strands["1_1_2_1"], {})
    assert keep.contains(QPointF(319.5, 300))
    assert not keep.contains(QPointF(328, 300))


def test_nothing_is_clipped_when_the_piece_keeps_clear_of_nothing():
    for name in ("neighbour_shadow_only", "joint_seamless", "third_strand_between"):
        assert shader_utils._piece_keep(design(name)["1_1_2_1"], {}) is None
