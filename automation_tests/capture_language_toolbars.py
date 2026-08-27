"""Capture the toolbar at 1280x705 for every language and verify the fit.

Checks the whole trade-off in one pass: toolbar labels fit, the layer list
keeps room for its buttons plus a scrollbar gutter, and the group panel still
shows its Create Group button.

Run:
    python automation_tests/capture_language_toolbars.py
"""
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from capture_screen_ratio_mocks import (
    OUT_DIR, _bootstrap, _force_available_size, _toolbar_buttons, _wait,
)

LANGUAGES = ["en", "fr", "de", "it", "es", "pt", "he"]
LIST_MIN = 158
PROBLEM_DIR = os.path.join(OUT_DIR, "language_audit")


def main():
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QPixmap

    os.makedirs(PROBLEM_DIR, exist_ok=True)
    app, window = _bootstrap()
    window._initial_show_completed = True
    window.setAttribute(Qt.WA_DontShowOnScreen, True)
    window.setMinimumSize(0, 0)
    window.show()
    app.processEvents()

    panel = window.layer_panel
    failures = []
    for lang in LANGUAGES:
        window.setMaximumSize(16777215, 16777215)
        window.set_language(lang)
        app.processEvents()
        _wait(200)
        window.setFixedSize(16777215, 16777215)
        window.setMaximumSize(16777215, 16777215)
        _force_available_size(window, 1280, 705)
        _wait(200)
        app.processEvents()

        worst, label = 0, ""
        for btn in _toolbar_buttons(window):
            if not btn.text():
                continue
            short = btn.sizeHint().width() - btn.width()
            if short > worst:
                worst, label = short, btn.text()
        cg = panel.group_layer_manager.create_group_button
        list_w = panel.scroll_area.width()
        cg_ok = cg.width() >= cg.sizeHint().width()
        list_ok = list_w >= LIST_MIN
        ok = worst == 0 and cg_ok and list_ok
        print(f"{lang} | panel={panel.width():3d} | toolbar "
              f"{'OK' if worst == 0 else f'-{worst}px({label})':16s} | "
              f"list {list_w:3d} {'ok' if list_ok else 'TOO NARROW'} | "
              f"CreateGroup {cg.width():3d}/{cg.sizeHint().width():3d} "
              f"{'ok' if cg_ok else 'CLIPPED'} | {'PASS' if ok else 'FAIL'}", flush=True)
        if not ok:
            failures.append(lang)

        pix = QPixmap(window.size())
        pix.fill(Qt.white)
        window.render(pix)
        pix.save(os.path.join(PROBLEM_DIR, f"{lang}_1280x705.png"), "PNG")

    print(f"\nfailures: {failures if failures else 'none'}", flush=True)
    window.close()
    app.quit()
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
