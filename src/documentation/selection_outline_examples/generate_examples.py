r"""Generate selection-outline documentation samples and screenshots.

The input can be either an OpenStrand Studio history export or a plain project
snapshot.  By default the script uses the bug report file in Downloads; pass a
different path as the first argument when needed.

Run from the repository root with Qt in offscreen mode:

    $env:QT_QPA_PLATFORM = "offscreen"
    python src\documentation\selection_outline_examples\generate_examples.py
"""

from __future__ import annotations

import copy
import json
import math
import os
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
SRC = REPO_ROOT / "src"
sys.path.insert(0, str(SRC))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QPointF, QRectF, Qt  # noqa: E402
from PyQt5.QtGui import QColor, QImage, QPainter, QPen  # noqa: E402
from PyQt5.QtWidgets import QApplication  # noqa: E402

from save_load_manager import load_strands_from_data  # noqa: E402
from select_mode import SelectMode  # noqa: E402


SAMPLES_DIR = HERE / "samples"
SCREENSHOTS_DIR = HERE / "screenshots"
DEFAULT_SOURCE = Path.home() / "Downloads" / "masknotworkingexample.json"


VARIANTS = (
    ("00_reference", "Reference: original step 18", "Original six-layer geometry; 1_4 is hovered.", "1_4"),
    ("01_side_lines_visible", "Side-line control: all visible", "Circles are disabled so every supported side line can be seen.", "1_1"),
    ("02_start_side_lines_hidden", "Start side lines hidden", "All start_line_visible flags are false; end lines remain visible.", "2_1"),
    ("03_end_side_lines_hidden", "End side lines hidden", "All end_line_visible flags are false; start lines remain visible.", "2_2"),
    ("04_all_side_lines_hidden", "All side lines hidden", "Both side-line flags are false on every layer.", "1_3"),
    ("05_circles_visible", "Circle control: all visible", "Both endpoint circles are enabled and side lines are hidden.", "1_2"),
    ("06_start_circles_hidden", "Start circles hidden", "Start circles are disabled; end circles remain visible.", "2_1"),
    ("07_end_circles_hidden", "End circles hidden", "End circles are disabled; start circles remain visible.", "1_3"),
    ("08_all_circles_hidden", "All circles hidden", "Both circle flags are false on every layer.", "2_2"),
    ("09_transparent_circle_outlines", "Circle outlines transparent", "Circle geometry remains enabled while its outline alpha is zero.", "1_2"),
    ("10_mixed_visibility", "Mixed per-layer visibility", "A practical mixture of visible, hidden, and transparent decorations.", "1_1"),
)

SOURCE_SELECTION_TARGETS = ("1_1", "1_2", "1_3", "1_4", "2_1", "2_2")


class RenderCanvas:
    """Small canvas adapter used by the real project loader and renderers."""

    highlight_color = QColor(255, 0, 0, 255)
    default_shadow_color = QColor(0, 0, 0, 150)
    shadow_enabled = False
    show_control_points = False
    show_hover_highlights = True
    default_transparent_start_circle = False
    enable_curvature_bias_control = False
    grid_size = 28
    zoom_factor = 1.0
    pan_offset_x = 0
    pan_offset_y = 0
    current_mode = None

    def update(self):
        pass

    def setCursor(self, *_args):
        pass


def load_current_snapshot(source: Path) -> dict:
    with source.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if payload.get("type") != "OpenStrandStudioHistory":
        return copy.deepcopy(payload)

    current_step = payload.get("current_step")
    for entry in payload.get("states", []):
        if entry.get("step") == current_step:
            return copy.deepcopy(entry["data"])
    raise ValueError(f"History has no state for current step {current_step!r}")


def clean_snapshot(snapshot: dict) -> dict:
    """Normalize metadata so the derived files open as ordinary snapshots."""
    result = copy.deepcopy(snapshot)
    result["selected_strand_name"] = None
    result.setdefault("groups", {})
    result.setdefault("locked_layers", [])
    result.setdefault("lock_mode", False)
    result["shadow_enabled"] = False
    result["show_control_points"] = False
    result.setdefault("shadow_overrides", {})
    return result


def set_all_circles(snapshot: dict, start: bool, end: bool,
                    force_junction_caps: bool = False) -> None:
    for strand in snapshot["strands"]:
        strand["has_circles"] = [start, end]
        # Attachment validation reconstructs circles from topology during load.
        # Explicit overrides make these documentation choices persistent.
        strand["manual_circle_visibility"] = [start, end]
        if force_junction_caps:
            strand["closed_connections"] = [start, end]


def set_all_side_lines(snapshot: dict, start: bool, end: bool) -> None:
    for strand in snapshot["strands"]:
        strand["start_line_visible"] = start
        strand["end_line_visible"] = end


def transparent_color(color: dict | None) -> dict:
    value = copy.deepcopy(color or {"r": 0, "g": 0, "b": 0, "a": 255})
    value["a"] = 0
    return value


def make_variants(reference: dict) -> dict[str, dict]:
    variants = {"00_reference": clean_snapshot(reference)}

    line_control = clean_snapshot(reference)
    set_all_circles(line_control, False, False)
    set_all_side_lines(line_control, True, True)
    variants["01_side_lines_visible"] = line_control

    start_lines_hidden = copy.deepcopy(line_control)
    set_all_side_lines(start_lines_hidden, False, True)
    variants["02_start_side_lines_hidden"] = start_lines_hidden

    end_lines_hidden = copy.deepcopy(line_control)
    set_all_side_lines(end_lines_hidden, True, False)
    variants["03_end_side_lines_hidden"] = end_lines_hidden

    all_lines_hidden = copy.deepcopy(line_control)
    set_all_side_lines(all_lines_hidden, False, False)
    variants["04_all_side_lines_hidden"] = all_lines_hidden

    circle_control = clean_snapshot(reference)
    set_all_side_lines(circle_control, False, False)
    set_all_circles(circle_control, True, True, force_junction_caps=True)
    variants["05_circles_visible"] = circle_control

    start_circles_hidden = copy.deepcopy(circle_control)
    set_all_circles(start_circles_hidden, False, True, force_junction_caps=True)
    variants["06_start_circles_hidden"] = start_circles_hidden

    end_circles_hidden = copy.deepcopy(circle_control)
    set_all_circles(end_circles_hidden, True, False, force_junction_caps=True)
    variants["07_end_circles_hidden"] = end_circles_hidden

    all_circles_hidden = copy.deepcopy(circle_control)
    set_all_circles(all_circles_hidden, False, False)
    variants["08_all_circles_hidden"] = all_circles_hidden

    transparent_outlines = copy.deepcopy(circle_control)
    for strand in transparent_outlines["strands"]:
        strand["circle_stroke_color"] = transparent_color(strand.get("circle_stroke_color"))
        strand["start_circle_stroke_color"] = transparent_color(strand.get("start_circle_stroke_color"))
        strand["end_circle_stroke_color"] = transparent_color(strand.get("end_circle_stroke_color"))
    variants["09_transparent_circle_outlines"] = transparent_outlines

    mixed = clean_snapshot(reference)
    by_name = {strand["layer_name"]: strand for strand in mixed["strands"]}
    for strand in mixed["strands"]:
        strand["manual_circle_visibility"] = [None, None]
    by_name["1_1"]["start_line_visible"] = False
    by_name["1_2"]["has_circles"][0] = False
    by_name["1_2"]["manual_circle_visibility"][0] = False
    by_name["2_1"]["has_circles"][1] = False
    by_name["2_1"]["manual_circle_visibility"][1] = False
    by_name["2_1"]["end_line_visible"] = True
    by_name["2_2"]["end_line_visible"] = False
    by_name["1_3"]["has_circles"][1] = False
    by_name["1_3"]["manual_circle_visibility"][1] = False
    by_name["1_3"]["end_line_visible"] = False
    by_name["1_4"]["start_circle_stroke_color"] = transparent_color(
        by_name["1_4"].get("start_circle_stroke_color"))
    variants["10_mixed_visibility"] = mixed

    return variants


def transform_points(value, center: tuple[float, float], angle: float,
                     scale: float, offset: tuple[float, float]):
    """Recursively transform every serialized point dictionary."""
    if isinstance(value, dict):
        if set(("x", "y")).issubset(value):
            x = (float(value["x"]) - center[0]) * scale
            y = (float(value["y"]) - center[1]) * scale
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            value["x"] = round(x * cos_a - y * sin_a + offset[0], 4)
            value["y"] = round(x * sin_a + y * cos_a + offset[1], 4)
        else:
            for child in value.values():
                transform_points(child, center, angle, scale, offset)
    elif isinstance(value, list):
        for child in value:
            transform_points(child, center, angle, scale, offset)


def make_complex_sample(reference: dict) -> dict:
    """Create a 24-layer radial weave from four transformed source motifs."""
    result = clean_snapshot(reference)
    result["strands"] = []
    result["groups"] = {}
    result["locked_layers"] = []

    source_center = (1204.0, 448.0)
    target_center = (700.0, 560.0)
    palette = (
        ((202, 147, 232), (139, 205, 244)),
        ((244, 168, 139), (250, 214, 118)),
        ((132, 214, 176), (115, 190, 206)),
        ((204, 160, 235), (238, 139, 174)),
    )

    next_index = 0
    for motif_index in range(4):
        angle = math.radians(motif_index * 90)
        layer_map = {}
        set_map = {1: motif_index * 2 + 1, 2: motif_index * 2 + 2}
        for source in reference["strands"]:
            old_name = source["layer_name"]
            old_set = int(source["set_number"])
            suffix = old_name.split("_", 1)[1]
            layer_map[old_name] = f"{set_map[old_set]}_{suffix}"

        for source in reference["strands"]:
            strand = copy.deepcopy(source)
            old_set = int(strand["set_number"])
            strand["index"] = next_index
            next_index += 1
            strand["set_number"] = set_map[old_set]
            strand["layer_name"] = layer_map[strand["layer_name"]]
            if strand.get("attached_to"):
                strand["attached_to"] = layer_map[strand["attached_to"]]
            strand["color"] = {
                "r": palette[motif_index][old_set - 1][0],
                "g": palette[motif_index][old_set - 1][1],
                "b": palette[motif_index][old_set - 1][2],
                "a": 255,
            }
            transform_points(strand, source_center, angle, 0.82, target_center)
            result["strands"].append(strand)

    return result


def write_json(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def strand_bounds(strands) -> QRectF:
    bounds = QRectF()
    for strand in strands:
        current = strand.get_selection_path().boundingRect()
        bounds = current if bounds.isNull() else bounds.united(current)
    return bounds.adjusted(-20, -20, 20, 20)


def draw_grid(painter: QPainter, world: QRectF, spacing: float = 28.0) -> None:
    painter.save()
    painter.setPen(QPen(QColor(218, 221, 225), 1))
    left = math.floor(world.left() / spacing) * spacing
    top = math.floor(world.top() / spacing) * spacing
    x = left
    while x <= world.right():
        painter.drawLine(QPointF(x, world.top()), QPointF(x, world.bottom()))
        x += spacing
    y = top
    while y <= world.bottom():
        painter.drawLine(QPointF(world.left(), y), QPointF(world.right(), y))
        y += spacing
    painter.restore()


def render_snapshot(snapshot: dict, output: Path, title: str, note: str,
                    hover_name: str = "1_4", legacy_outline: bool = False) -> None:
    canvas = RenderCanvas()
    strands = load_strands_from_data(copy.deepcopy(snapshot), canvas)[0]
    canvas.strands = strands

    # Mirror StrandDrawingCanvas.update_attachment_statuses(): manual circle
    # choices win after topology has been recomputed by the loader.
    serialized = {item["layer_name"]: item for item in snapshot["strands"]}
    for strand in strands:
        override = serialized[strand.layer_name].get("manual_circle_visibility", [None, None])
        for index, value in enumerate(override[:2]):
            if value is not None:
                strand.has_circles[index] = value

    width, height = 1200, 820
    margin = 36
    image = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
    image.fill(QColor(247, 248, 250))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

    bounds = strand_bounds(strands)
    available_w = width - margin * 2
    available_h = height - margin * 2
    scale = min(available_w / bounds.width(), available_h / bounds.height())
    tx = margin + (available_w - bounds.width() * scale) / 2 - bounds.left() * scale
    ty = margin + (available_h - bounds.height() * scale) / 2 - bounds.top() * scale

    painter.save()
    painter.translate(tx, ty)
    painter.scale(scale, scale)
    visible_world = QRectF(
        -tx / scale, -ty / scale, width / scale, height / scale)
    draw_grid(painter, visible_world)
    for strand in strands:
        strand.draw(painter)

    hovered = next((strand for strand in strands if strand.layer_name == hover_name), None)
    if hovered is not None:
        if legacy_outline:
            # Reproduce the old bug for the documentation comparison: the pen
            # outlines every overlapping subpath, including the cap seam.
            painter.setBrush(QColor(255, 230, 160, 170))
            legacy_pen = QPen(Qt.black, 2, Qt.SolidLine)
            legacy_pen.setJoinStyle(Qt.MiterJoin)
            legacy_pen.setCapStyle(Qt.FlatCap)
            painter.setPen(legacy_pen)
            painter.drawPath(hovered.get_selection_path())
        else:
            mode = SelectMode(canvas)
            mode.hovered_strand = hovered
            mode.draw(painter)
    painter.restore()
    painter.end()

    if not image.save(str(output), "PNG"):
        raise RuntimeError(f"Could not save {output}")


def make_contact_sheet(image_paths: list[Path], output: Path) -> None:
    thumb_w, thumb_h = 480, 328
    gap = 18
    columns = 2
    rows = math.ceil(len(image_paths) / columns)
    sheet = QImage(columns * thumb_w + (columns + 1) * gap,
                   rows * thumb_h + (rows + 1) * gap,
                   QImage.Format_ARGB32_Premultiplied)
    sheet.fill(QColor(231, 234, 238))
    painter = QPainter(sheet)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    for index, path in enumerate(image_paths):
        image = QImage(str(path))
        thumb = image.scaled(thumb_w, thumb_h, Qt.KeepAspectRatio,
                             Qt.SmoothTransformation)
        x = gap + (index % columns) * (thumb_w + gap)
        y = gap + (index // columns) * (thumb_h + gap)
        painter.drawImage(x, y, thumb)
    painter.end()
    if not sheet.save(str(output), "PNG"):
        raise RuntimeError(f"Could not save {output}")


def main() -> int:
    app = QApplication.instance() or QApplication([])
    source = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else DEFAULT_SOURCE
    if not source.exists():
        raise FileNotFoundError(
            f"Source JSON not found: {source}. Pass the history/snapshot path explicitly.")

    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    reference = load_current_snapshot(source)
    variants = make_variants(reference)
    generated_images = []

    for name, title, note, hover_name in VARIANTS:
        sample_path = SAMPLES_DIR / f"{name}.json"
        image_path = SCREENSHOTS_DIR / f"{name}.png"
        write_json(sample_path, variants[name])
        render_snapshot(variants[name], image_path, title, note, hover_name=hover_name)
        generated_images.append(image_path)

    complex_name = "11_complex_24_layers"
    complex_sample = make_complex_sample(reference)
    write_json(SAMPLES_DIR / f"{complex_name}.json", complex_sample)
    complex_image = SCREENSHOTS_DIR / f"{complex_name}.png"
    render_snapshot(
        complex_sample, complex_image,
        "Complex sample: 24-layer radial weave",
        "Four rotated six-layer motifs; the top 7_4 layer uses the corrected selection silhouette.",
        hover_name="7_4")
    generated_images.append(complex_image)

    legacy_image = SCREENSHOTS_DIR / "before_internal_component_strokes.png"
    render_snapshot(
        variants["00_reference"], legacy_image,
        "Before: component outlines leak inside",
        "Legacy direct-pen rendering exposes the start-cap seam.",
        legacy_outline=True)

    target_images = []
    for layer_name in SOURCE_SELECTION_TARGETS:
        target_image = SCREENSHOTS_DIR / f"selection_target_{layer_name}.png"
        render_snapshot(
            variants["00_reference"], target_image,
            f"Selection target: {layer_name}",
            "The same reference snapshot with a different hovered strand.",
            hover_name=layer_name)
        target_images.append(target_image)

    make_contact_sheet(
        [legacy_image, SCREENSHOTS_DIR / "00_reference.png"],
        SCREENSHOTS_DIR / "before_after_comparison.png")
    make_contact_sheet(
        target_images,
        SCREENSHOTS_DIR / "selection_targets_contact_sheet.png")
    make_contact_sheet(
        [legacy_image] + generated_images,
        SCREENSHOTS_DIR / "contact_sheet.png")
    print(f"Generated {len(variants) + 1} JSON samples and {len(generated_images) + 10} images in {HERE}")
    app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
