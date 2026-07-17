import os
import sys

import pytest


SRC = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src")
)
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QColor

from attached_strand import AttachedStrand
from masked_strand import MaskedStrand
from strand import Strand
from strand_data_clipboard import apply_strand_data, snapshot_strand_data


def make_strand(start=(0, 0), end=(100, 0), name="1_1"):
    return Strand(
        QPointF(*start),
        QPointF(*end),
        20,
        QColor("red"),
        QColor("black"),
        4,
        1,
        name,
    )


def xy(point):
    return point.x(), point.y()


def test_snapshot_is_detached_and_selective():
    source = make_strand()
    clipboard = snapshot_strand_data(source, ("strand_color", "width"))

    source.color.setNamedColor("blue")
    source.start.setX(500)
    source.width = 99

    assert clipboard["strand_color"].name() == "#ff0000"
    assert xy(clipboard["source_start"]) == (0.0, 0.0)
    assert clipboard["width"] == 20
    assert "end_point" not in clipboard


def test_start_anchor_rotates_full_shape_without_scaling():
    source = make_strand()
    source.control_point1 = QPointF(20, 30)
    source.control_point2 = QPointF(80, 30)
    source.control_point_center = QPointF(50, 50)
    source.control_point_center_locked = True
    target = make_strand((10, 20), (10, 120), "2_1")

    apply_strand_data(snapshot_strand_data(source), target, "start")

    assert xy(target.start) == pytest.approx((10, 20))
    assert xy(target.end) == pytest.approx((10, 120))
    assert xy(target.control_point1) == pytest.approx((-20, 40))
    assert xy(target.control_point_center) == pytest.approx((-40, 70))


def test_end_anchor_keeps_target_end_fixed():
    source = make_strand()
    target = make_strand((200, 100), (200, 250), "2_1")

    apply_strand_data(
        snapshot_strand_data(source, ("start_point", "end_point")),
        target,
        "end",
    )

    assert xy(target.end) == pytest.approx((200, 250))
    assert xy(target.start) == pytest.approx((200, 150))


def test_style_only_paste_does_not_change_geometry():
    source = make_strand()
    source.width = 36.5
    source.stroke_width = 7.25
    target = make_strand((20, 30), (80, 90), "2_1")
    before = xy(target.start), xy(target.end)

    apply_strand_data(
        snapshot_strand_data(source, ("width", "strand_color")), target, "start"
    )

    assert (xy(target.start), xy(target.end)) == before
    assert target.width == 36.5
    assert target.stroke_width == 7.25
    assert target.color.name() == "#ff0000"


def test_attached_target_ignores_copied_start_and_refreshes_polar_geometry():
    parent = make_strand((0, 0), (50, 0))
    attached = AttachedStrand(parent, QPointF(parent.end), 1)
    attached.end = QPointF(50, 80)
    attached.update_control_points_from_geometry()
    source = make_strand((10, 10), (110, 10), "2_1")

    apply_strand_data(snapshot_strand_data(source), attached, "start")

    assert xy(attached.start) == pytest.approx((50, 0))
    assert xy(attached.end) == pytest.approx((50, 100))
    assert attached.length == pytest.approx(100)
    assert attached.angle == pytest.approx(90)


def test_masked_strands_are_rejected():
    first = make_strand()
    second = make_strand((50, -50), (50, 50), "2_1")
    masked = MaskedStrand(first, second)

    with pytest.raises(ValueError):
        snapshot_strand_data(masked)
    assert not apply_strand_data(snapshot_strand_data(first), masked)
