"""Capture the full review matrix: every language at every screen ratio.

Writes docs/screen_ratio_layout_feature/review/:
    contact_sheets/<language>.png      one sheet per language (all 10 ratios)
    by_language/<language>/NN_*.png    the 70 individual screens
    scrollbar/                         the 30-layer scrollbar cases

Every screen carries a footer with its measurements and an OK / LABELS CUT /
BUTTONS CLIPPED status, so each image verifies itself.

Run:
    python automation_tests/capture_review_matrix.py
"""
import os
import shutil
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from capture_screen_ratio_mocks import (
    SCREENS, OUT_DIR, _bootstrap, _force_available_size, _draw_sample_strands,
    _measure, _grab_window, _compose_screen, _contact_sheet, _wait,
)

REVIEW_DIR = os.path.join(ROOT_DIR, "docs", "screen_ratio_layout_feature", "review")
LANGUAGES = [
    ("en", "english"), ("fr", "french"), ("de", "german"), ("it", "italian"),
    ("es", "spanish"), ("pt", "portuguese"), ("he", "hebrew"),
]


def main():
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication

    sheets_dir = os.path.join(REVIEW_DIR, "contact_sheets")
    langs_dir = os.path.join(REVIEW_DIR, "by_language")
    scroll_dir = os.path.join(REVIEW_DIR, "scrollbar")
    for d in (sheets_dir, langs_dir, scroll_dir):
        os.makedirs(d, exist_ok=True)

    app, window = _bootstrap()
    window._initial_show_completed = True
    window.setAttribute(Qt.WA_DontShowOnScreen, True)
    window.setMinimumSize(0, 0)
    window.show()
    app.processEvents()

    # Draw sample content once, at a comfortable size.
    _force_available_size(window, 1600, 900)
    _draw_sample_strands(window)
    window.canvas.deselect_all_strands()
    app.processEvents()

    problems = []
    for code, name in LANGUAGES:
        window.setMaximumSize(16777215, 16777215)
        window.set_language(code)
        app.processEvents()
        _wait(250)

        out_dir = os.path.join(langs_dir, name)
        os.makedirs(out_dir, exist_ok=True)
        written = []
        for spec in SCREENS:
            avail_w = spec["width"]
            avail_h = spec["height"] - spec["chrome_top"] - spec["chrome_bottom"]
            window.setFixedSize(16777215, 16777215)
            window.setMaximumSize(16777215, 16777215)
            _force_available_size(window, avail_w, avail_h)
            app.processEvents()
            metrics = _measure(window)
            app_pix = _grab_window(window)
            composed, warning = _compose_screen(spec, app_pix, metrics)
            path = os.path.join(out_dir, spec["id"] + ".png")
            composed.save(path, "PNG")
            written.append(path)
            if warning:
                problems.append(f"{name}/{spec['id']}: "
                                f"clipped={metrics['clipped']} squeezed={metrics['squeezed']}")
        sheet = _contact_sheet(written)
        if sheet is not None:
            sheet.save(os.path.join(sheets_dir, f"{name}.png"), "PNG")
        print(f"[review] {name}: {len(written)} screens", flush=True)

    # Bring the 30-layer scrollbar cases along, if they have been generated.
    for src_name, dst_name in (
        ("11_compact_30_layers.png", "compact_1280_30_layers.png"),
        ("12_full_30_layers.png", "wide_1440_30_layers.png"),
    ):
        src = os.path.join(OUT_DIR, src_name)
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(scroll_dir, dst_name))

    print("\n[review] problems:", flush=True)
    if problems:
        for p in problems:
            print("   " + p, flush=True)
    else:
        print("   none — every language at every ratio is clean", flush=True)

    window.close()
    app.quit()
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
