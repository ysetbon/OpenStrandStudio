"""Selective copy/paste support for strand geometry and appearance.

The clipboard deliberately stores value objects only.  In particular, QPointF and
QColor instances are copied so later edits to the source strand cannot mutate an
existing clipboard snapshot.
"""

import math

from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QColor

from attached_strand import AttachedStrand
from masked_strand import MaskedStrand


COPY_PROPERTIES = (
    "start_point",
    "end_point",
    "control_points",
    "width",
    "strand_color",
    "stroke_color",
)


def _point(value):
    return QPointF(value) if value is not None else None


def _color(value):
    return QColor(value) if value is not None else None


def _point_close(first, second, tolerance=0.5):
    if first is None or second is None:
        return False
    return math.hypot(first.x() - second.x(), first.y() - second.y()) <= tolerance


def _map_point(point, source_anchor, target_anchor):
    """Re-anchor a copied point: same offset (angle + length), new origin.

    The copied deltas are part of the data — pasting never rotates them, it
    only moves the whole shape so the source anchor lands on the target anchor.
    """
    if point is None:
        return None
    return QPointF(
        target_anchor.x() + point.x() - source_anchor.x(),
        target_anchor.y() + point.y() - source_anchor.y(),
    )


def snapshot_strand_data(strand, selected_properties=None):
    """Create a detached clipboard snapshot from ``strand``.

    ``selected_properties`` is an iterable containing values from
    :data:`COPY_PROPERTIES`.  Masked strands are intentionally unsupported because
    their geometry is derived from their two source strands.
    """
    if isinstance(strand, MaskedStrand):
        raise ValueError("Masked strands cannot be copied")

    selected = set(selected_properties or COPY_PROPERTIES).intersection(COPY_PROPERTIES)
    if not selected:
        raise ValueError("At least one strand property must be selected")

    snapshot = {
        "source_layer_name": getattr(strand, "layer_name", ""),
        "selected_properties": tuple(key for key in COPY_PROPERTIES if key in selected),
        # The complete source frame is metadata needed to map even a single copied
        # point; it does not imply that both endpoint toggles were selected.
        "source_start": _point(strand.start),
        "source_end": _point(strand.end),
    }

    if "start_point" in selected:
        snapshot["start_point"] = _point(strand.start)
    if "end_point" in selected:
        snapshot["end_point"] = _point(strand.end)
    if "width" in selected:
        snapshot["width"] = float(strand.width)
        snapshot["stroke_width"] = float(strand.stroke_width)
    if "strand_color" in selected:
        snapshot["strand_color"] = _color(strand.color)
    if "stroke_color" in selected:
        snapshot["stroke_color"] = _color(strand.stroke_color)

    if "control_points" in selected:
        snapshot["control_points"] = {
            "control_point1": _point(getattr(strand, "control_point1", None)),
            "control_point_center": _point(getattr(strand, "control_point_center", None)),
            "control_point2": _point(getattr(strand, "control_point2", None)),
            "control_point_center_locked": bool(
                getattr(strand, "control_point_center_locked", False)
            ),
            "triangle_has_moved": bool(getattr(strand, "triangle_has_moved", False)),
            "control_point2_shown": bool(getattr(strand, "control_point2_shown", False)),
            "control_point2_activated": bool(
                getattr(strand, "control_point2_activated", False)
            ),
        }
        bias = getattr(strand, "bias_control", None)
        if bias is not None:
            snapshot["control_points"]["bias"] = {
                "triangle_bias": float(getattr(bias, "triangle_bias", 0.5)),
                "circle_bias": float(getattr(bias, "circle_bias", 0.5)),
                "triangle_position": _point(getattr(bias, "triangle_position", None)),
                "circle_position": _point(getattr(bias, "circle_position", None)),
            }

    return snapshot


def clipboard_property_count(snapshot):
    return len(snapshot.get("selected_properties", ())) if snapshot else 0


def _refresh_attached_geometry(strand):
    dx = strand.end.x() - strand.start.x()
    dy = strand.end.y() - strand.start.y()
    strand.length = math.hypot(dx, dy)
    if strand.length > 1e-9:
        strand.angle = math.degrees(math.atan2(dy, dx))
        strand.current_angle = strand.angle


def _move_attached_children(parent, old_start, old_end):
    """Keep children glued to a parent endpoint moved by a paste operation."""
    for child in list(getattr(parent, "attached_strands", ())):
        old_child_start = _point(child.start)
        old_child_end = _point(child.end)
        if _point_close(old_child_start, old_start):
            new_child_start = _point(parent.start)
        elif _point_close(old_child_start, old_end):
            new_child_start = _point(parent.end)
        else:
            continue

        delta = new_child_start - old_child_start
        child.start = new_child_start
        # Match the app's angle-adjust behavior: the child's free end stays put,
        # while its curve controls retain their offsets from the attached start.
        child.end = old_child_end
        for name in ("control_point1", "control_point2", "control_point_center"):
            value = getattr(child, name, None)
            if value is not None:
                setattr(child, name, QPointF(value.x() + delta.x(), value.y() + delta.y()))
        bias = getattr(child, "bias_control", None)
        if bias is not None:
            for name in ("triangle_position", "circle_position"):
                value = getattr(bias, name, None)
                if value is not None:
                    setattr(bias, name, QPointF(value.x() + delta.x(), value.y() + delta.y()))
        _refresh_attached_geometry(child)
        child.update_shape()
        child.update_side_line()
        _move_attached_children(child, old_child_start, old_child_end)


def apply_strand_data(snapshot, strand, anchor="start"):
    """Apply a clipboard snapshot to one strand.

    The copied geometry keeps its own angles and lengths — the deltas relative
    to the copied strand's anchor are part of the data. Pasting re-anchors the
    whole shape so the source's start (or end) lands on the target's start (or
    end); nothing is rotated or scaled.  Returns ``True`` when data was applied
    and ``False`` for an unsupported masked target or when nothing applies
    (e.g. only the Start Point was copied onto an attached strand, whose start
    is pinned to its parent).
    """
    if not snapshot or isinstance(strand, MaskedStrand):
        return False
    if anchor not in ("start", "end"):
        raise ValueError("anchor must be 'start' or 'end'")

    selected = set(snapshot.get("selected_properties", ()))
    source_start = snapshot["source_start"]
    source_end = snapshot["source_end"]
    old_start = _point(strand.start)
    old_end = _point(strand.end)
    source_anchor = source_end if anchor == "end" else source_start
    target_anchor = old_end if anchor == "end" else old_start

    def mapped(value):
        return _map_point(value, source_anchor, target_anchor)

    applied = False
    geometry_changed = False
    endpoint_changed = False
    if "start_point" in selected and not isinstance(strand, AttachedStrand):
        strand.start = mapped(snapshot["start_point"])
        applied = geometry_changed = endpoint_changed = True
    if "end_point" in selected:
        strand.end = mapped(snapshot["end_point"])
        applied = geometry_changed = endpoint_changed = True

    controls = snapshot.get("control_points") if "control_points" in selected else None
    if controls is not None:
        for name in ("control_point1", "control_point_center", "control_point2"):
            if name in controls:
                setattr(strand, name, mapped(controls[name]))
        for name in (
            "control_point_center_locked",
            "triangle_has_moved",
            "control_point2_shown",
            "control_point2_activated",
        ):
            if name in controls:
                setattr(strand, name, controls[name])

        bias_data = controls.get("bias")
        bias = getattr(strand, "bias_control", None)
        if bias_data is not None and bias is not None:
            bias.triangle_bias = bias_data["triangle_bias"]
            bias.circle_bias = bias_data["circle_bias"]
            bias.triangle_position = mapped(bias_data.get("triangle_position"))
            bias.circle_position = mapped(bias_data.get("circle_position"))
        applied = geometry_changed = True
    elif endpoint_changed and hasattr(strand, "update_control_points_from_geometry"):
        strand.update_control_points_from_geometry()

    if "width" in selected:
        strand.width = snapshot["width"]
        strand.stroke_width = snapshot["stroke_width"]
        applied = True
    if "strand_color" in selected:
        strand.color = _color(snapshot["strand_color"])
        applied = True
    if "stroke_color" in selected:
        strand.stroke_color = _color(snapshot["stroke_color"])
        applied = True

    if not applied:
        return False

    if isinstance(strand, AttachedStrand):
        # Its start remains attached to its parent even when Start Point was copied.
        strand.start = old_start
        _refresh_attached_geometry(strand)

    if geometry_changed or "width" in selected:
        strand.update_shape()
        strand.update_side_line()
        _move_attached_children(strand, old_start, old_end)
    return True
