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
