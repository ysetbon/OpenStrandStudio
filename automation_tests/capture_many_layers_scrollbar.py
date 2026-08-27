"""Capture the layer panel with ~30 layers so the vertical scrollbar shows.

Produces two PNGs in docs/screen_ratio_layout_feature/screenshots:
  11_compact_30_layers.png  - 1280x737 (MacBook Air M2 More Space, compact)
  12_full_30_layers.png     - 1440x805 (MacBook Air Intel, full width)

Run:
    python automation_tests/capture_many_layers_scrollbar.py
"""
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from capture_screen_ratio_mocks import (
    OUT_DIR, _bootstrap, _force_available_size, _draw_sample_strands, _wait,
)

LAYER_COUNT = 30


def main():
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QPixmap

    os.makedirs(OUT_DIR, exist_ok=True)
    app, window = _bootstrap()
    window._initial_show_completed = True
    window.setAttribute(Qt.WA_DontShowOnScreen, True)
    window.setMinimumSize(0, 0)
    window.show()
    app.processEvents()

    _force_available_size(window, 1600, 900)
    _draw_sample_strands(window)
    window.canvas.deselect_all_strands()
    app.processEvents()

    panel = window.layer_panel
    for i in range(len(panel.layer_buttons), LAYER_COUNT):
        panel.add_layer_button(1, i + 1)
    app.processEvents()
    _wait(300)

    # Wide first: capturing compact before wide would leave the compact
    # gutter lingering in the wide shot (Qt keeps the wider list column
    # within a session), which a real wide-screen launch never shows.
    for w, h, name in [
        (1440, 805, "12_full_30_layers.png"),
        (1280, 737, "11_compact_30_layers.png"),
    ]:
        window.setFixedSize(16777215, 16777215)
        window.setMaximumSize(16777215, 16777215)
        _force_available_size(window, w, h)
        _wait(300)
        app.processEvents()
        sa = panel.scroll_area
        vbar = sa.verticalScrollBar()
        print(f"[many-layers] {w}x{h}: viewport={sa.viewport().width()} "
              f"vbar visible={vbar.isVisible()} range=0..{vbar.maximum()}", flush=True)
        pix = QPixmap(window.size())
        pix.fill(Qt.white)
        window.render(pix)
        path = os.path.join(OUT_DIR, name)
        pix.save(path, "PNG")
        print(f"[many-layers] wrote {path}", flush=True)

    window.close()
    app.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
