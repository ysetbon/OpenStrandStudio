"""Draw a project to PNG with the app's real canvas, shadows included."""
from pathlib import Path

from .generators import application


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
        preview.capture(data, out_path)
    finally:
        preview.close()
    return out_path


def shot(preview, data, path):
    """A picture of a design cut to the design with a margin, drawn by a
    preview window that is already open (AppPreview). Returns path."""
    from PyQt5.QtCore import QRect
    from PyQt5.QtGui import QImage
    preview.capture(data, path)
    canvas = preview.window.canvas
    bounds, zoom = canvas.get_bounding_rect(), canvas.zoom_factor
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
