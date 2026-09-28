"""A transparent circle at a strand's end asks for no shadow halo around it,
so draw_strand_shadow keeps the strand's shadow off a disc around that end
(shader_utils._caster_shadow_path). At a joint, where an attached strand
continues it, the disc only applies to the strands that end there.

It used to be cut out of every shadow the strand casts. The disc reaches a
sixth of the strand's full width past its edge, so a strand crossing next to
a joint lost most of the soft edge there, which ended short with a round end
(in the Chinese double coin sample at three grid squares wide: 1_8 on 1_4,
1_9 on 1_6, and 1_3 on 1_9 through its mask).

Without the disc, a shadow can end right on the neighbour's flat end, the
same segment, and Qt's boolean operations fail on shared edges; the woven
heart test covers the safeguards (_seam_slab, _subtracted).
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

from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QColor, QPainterPath
from PyQt5.QtWidgets import QApplication

import shader_utils
from attached_strand import AttachedStrand
from save_load_manager import load_strands_from_data
from strand import Strand

APP = QApplication.instance() or QApplication([])

TRANSPARENT = QColor(0, 0, 0, 0)
WIDTH, STROKE = 40, 2  # full width 44: the disc's radius is 29.3


class LayerState:
    """What draw_strand_shadow asks the layer state manager: every shadow shown."""

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


def make_strand(start, end, layer_name):
    strand = Strand(QPointF(*start), QPointF(*end), WIDTH, stroke_width=STROKE,
                    set_number=int(layer_name.split("_")[0]), layer_name=layer_name)
    strand.update_shape()
    return strand


def attach(parent, end, layer_name):
    """A strand attached to *parent*'s end, joined seamlessly (transparent
    circles on both sides of the joint)."""
    child = AttachedStrand(parent, QPointF(parent.end), 1)
    child.layer_name = layer_name
    child.update(QPointF(*end))
    parent.attached_strands.append(child)
    parent.has_circles = [parent.has_circles[0], True]
    parent.end_circle_stroke_color = QColor(TRANSPARENT)
    child.start_circle_stroke_color = QColor(TRANSPARENT)
    return child


def scene(*strands):
    """Put *strands* on one canvas, in layer order (bottom first)."""
    canvas = SimpleNamespace(strands=list(strands), shadow_enabled=True, shadow_selected_only=False,
                             enable_third_control_point=False,
                             layer_state_manager=LayerState([s.layer_name for s in strands]))
    for strand in strands:
        strand.canvas = canvas
    return canvas


def sample(name, width, stroke_width):
    """A bundled sample's strands, by layer name, every one set to *width*."""
    path = SRC_DIR / "samples" / name
    data = json.loads(path.read_text(encoding="utf-8"))
    for strand in data["strands"]:
        strand["width"], strand["stroke_width"] = width, stroke_width
    loader = SimpleNamespace(strands=[], groups={}, strand_colors={}, shadow_enabled=True,
                             _suppress_layer_panel_refresh=True, _suppress_repaint=True,
                             update=lambda: None)
    strands = load_strands_from_data(data, loader)[0]
    scene(*strands)
    return {strand.layer_name: strand for strand in strands}


def halo_area(outline, point):
    """How much of *outline* lies in the disc around a transparent end at
    *point*, where no halo may show."""
    if outline is None:
        return 0.0
    radius = (WIDTH + STROKE * 2) / 1.5
    disc = QPainterPath()
    disc.addEllipse(QPointF(*point), radius, radius)
    return shader_utils._approx_path_area(outline.intersected(disc))


def outline_on(caster, receiver):
    """The area whose outline the caster's soft edge on *receiver* is stroked
    along, or None when it casts no shadow there."""
    collected = shader_utils.draw_strand_shadow(None, caster, num_steps=3, max_blur_radius=29.99,
                                                collect_only=True)
    for name, outline in (collected or {}).get('outlines', ()):
        if name == receiver.layer_name:
            return outline
    return None


def test_strand_crossing_next_to_a_joint_keeps_its_shadow():
    # 1_1 ends at (200, 200) and 1_2 continues it to the right, over 2_1,
    # whose outline starts 3 px past the joint (x 203 to 247).
    parent = make_strand((60, 200), (200, 200), "1_1")
    child = attach(parent, (340, 200), "1_2")
    crossing = make_strand((225, 80), (225, 320), "2_1")
    scene(parent, crossing, child)

    outline = outline_on(child, crossing)
    assert outline is not None
    # Inside the disc around the joint, where 1_2 lies over 2_1: the shadow
    # starts there as it does away from the joint.
    for point in ((206, 200), (206, 181), (215, 219)):
        assert outline.contains(QPointF(*point)), point


def test_strand_that_continues_the_caster_gets_no_halo():
    # 1_2 turns up at the joint, so its start overlaps 1_1's end on the
    # inside of the bend: that overlap stays free of 1_2's shadow.
    parent = make_strand((60, 200), (200, 200), "1_1")
    child = attach(parent, (300, 90), "1_2")
    scene(parent, child)

    assert halo_area(outline_on(child, parent), (200, 200)) < 1.0


def test_free_end_with_a_transparent_circle_casts_no_halo():
    # Nothing is attached at 1_1's end; its circle is switched on and
    # transparent, and 2_1 passes under that end.
    lone = make_strand((60, 200), (200, 200), "1_1")
    lone.has_circles = [False, True]
    lone.end_circle_stroke_color = QColor(TRANSPARENT)
    under = make_strand((190, 80), (190, 320), "2_1")
    scene(under, lone)

    assert halo_area(outline_on(lone, under), (200, 200)) < 1.0


def test_joint_shadows_stay_on_their_casters_in_the_woven_heart():
    # At three grid squares wide, the heart's seamless joints sit right next
    # to the strands they cross. Subtracting a strand between caster and
    # receiver whose flat end is the caster's or the receiver's own, the same
    # segment, Qt returned nothing, or a path far past the caster: the canvas
    # then lost the shadow, or filled a large black patch.
    strands = sample("woven_heart.json", 80, 2)
    for caster, receiver in (("2_2", "1_2"), ("3_3", "2_4"), ("2_7", "1_6"), ("2_7", "3_5")):
        outline = outline_on(strands[caster], strands[receiver])
        assert outline is not None and not outline.isEmpty(), (caster, receiver)
        footprint = shader_utils.build_shadow_geometry(strands[caster], 1.0).boundingRect()
        assert footprint.contains(outline.boundingRect()), (caster, receiver)
