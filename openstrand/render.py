"""Draw a project to PNG with the app's real canvas, shadows included."""
from pathlib import Path

from .generators import application


def arrow_heads(canvas):
    """Where the canvas paints the heads of full arrows: past each strand's end, so outside
    canvas.get_bounding_rect(). A QRectF around them (null when there are none)."""
    import math
    from PyQt5.QtCore import QPointF, QRectF
    rect = QRectF()
    length = float(getattr(canvas, 'arrow_head_length', 20))
    width = float(getattr(canvas, 'arrow_head_width', 10))
    for strand in getattr(canvas, 'strands', []):
        if not (getattr(strand, 'full_arrow_visible', False) and getattr(strand, 'arrow_head_visible', True)):
            continue
        tangent = strand.calculate_cubic_tangent(0.999)  # as the strand draws its head
        size = math.hypot(tangent.x(), tangent.y())
        if not size:
            continue
        tip = strand.end + QPointF(tangent.x() / size, tangent.y() / size) * length
        reach = width / 2 + 4                           # half the head's base, and its outline
        for point in (strand.end, tip):
            box = QRectF(point.x() - reach, point.y() - reach, 2 * reach, 2 * reach)
            rect = box if rect.isNull() else rect.united(box)
    return rect


def capture(preview, data, path):
    """preview.capture as the app shows the design: with the drawing settings saved in it (its
    arrow sizes, curves), as the app's Load applies them, and with every arrow head inside the
    picture (the preview fits the view to the canvas's bounds, which leave the heads of full
    arrows out). The preview's own settings come back afterwards, for the next design.
    Returns the bounds the picture was fitted to."""
    from project_settings import apply_project_settings, capture_project_settings, read_project_settings
    canvas = preview.window.canvas
    plain = type(canvas).get_bounding_rect

    def with_heads():
        """The canvas's bounds and its arrow heads together."""
        bounds, heads = plain(canvas), arrow_heads(canvas)
        return bounds if heads.isNull() else (heads if bounds.isNull() else bounds.united(heads))
    saved = read_project_settings(data)
    before = capture_project_settings(canvas) if saved is not None else None
    if saved is not None:
        apply_project_settings(canvas, saved)
    canvas.get_bounding_rect = with_heads
    try:
        preview.capture(data, path)
        return with_heads()
    finally:
        del canvas.get_bounding_rect
        if before is not None:
            apply_project_settings(canvas, before)


def render(data, out_path):
    """Load the project into a hidden MainWindow and save its canvas as a PNG.

    The window gets fresh settings, so the user's own configuration is never
    read or written.
    """
    application()
    from generate_creative_samples import AppPreview
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    preview = AppPreview()
    try:
        capture(preview, data, out_path)
    finally:
        preview.close()
    return out_path


def shot(preview, data, path):
    """A picture of a design cut to the design with a margin, drawn by a
    preview window that is already open (AppPreview). Returns path."""
    from PyQt5.QtCore import QRect
    from PyQt5.QtGui import QImage
    bounds = capture(preview, data, path)
    canvas = preview.window.canvas
    zoom = canvas.zoom_factor
    w, h = canvas.width(), canvas.height()
    # Where the design's box lands on the canvas (the canvas's own transform).
    x0 = (bounds.left() - w / 2) * zoom + w / 2 + canvas.pan_offset_x
    y0 = (bounds.top() - h / 2) * zoom + h / 2 + canvas.pan_offset_y
    widest = max([getattr(s, 'width', 0) + 2 * getattr(s, 'stroke_width', 0) for s in canvas.strands] or [0])
    pad = widest * zoom / 2 + 12
    box = QRect(int(x0 - pad), int(y0 - pad), int(bounds.width() * zoom + 2 * pad),
                int(bounds.height() * zoom + 2 * pad)).intersected(QRect(0, 0, w, h))
    if box.width() > 8 and box.height() > 8:
        QImage(str(path)).copy(box).save(str(path))
    return path


def step_sheet(datas, titles, path, folder=None):
    """One picture of several designs side by side, numbered and titled (the
    steps of a tutorial). The single pictures go in folder (default: beside
    path) as step_1.png, step_2.png, ... Returns path."""
    from . import storyboard
    application()
    from generate_creative_samples import AppPreview
    path = Path(path)
    folder = Path(folder) if folder else path.parent
    folder.mkdir(parents=True, exist_ok=True)
    preview = AppPreview()
    try:
        pictures = [shot(preview, data, folder / f'step_{n}.png') for n, data in enumerate(datas, start=1)]
    finally:
        preview.close()
    return storyboard.sheet(pictures, titles, path)
