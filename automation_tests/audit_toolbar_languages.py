"""Audit main-window toolbar fit for every language x every screen ratio.

Measures whether any toolbar button is clipped or pushed past the canvas
pane's right edge, for each supported UI language at each simulated screen
size. Prints a matrix and writes a PNG for every failing combination.

Run:
    python automation_tests/audit_toolbar_languages.py
"""
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from capture_screen_ratio_mocks import (
    SCREENS, OUT_DIR, _bootstrap, _force_available_size, _toolbar_buttons, _wait,
)

LANGUAGES = ["en", "fr", "de", "it", "es", "pt", "he"]
PROBLEM_DIR = os.path.join(OUT_DIR, "language_audit")


def _squeezed_buttons(window):
    """Toolbar buttons narrower than the width their label needs.

    The toolbar buttons use an Expanding size policy, so they never overflow
    the row geometrically — instead they shrink and Qt elides the label. The
    real symptom is therefore width() < sizeHint().width()."""
    squeezed = []
    for btn in _toolbar_buttons(window):
        label = btn.text()
        if not label:
            continue  # icon-only (settings gear)
        shortfall = btn.sizeHint().width() - btn.width()
        if shortfall > 0:
            squeezed.append((label, shortfall, btn.width(), btn.sizeHint().width()))
    return squeezed


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

    problems = []
    for lang in LANGUAGES:
        window.setMaximumSize(16777215, 16777215)
        window.set_language(lang)
        app.processEvents()
        _wait(200)
        for spec in SCREENS:
            avail_w = spec["width"]
            avail_h = spec["height"] - spec["chrome_top"] - spec["chrome_bottom"]
            window.setFixedSize(16777215, 16777215)
            window.setMaximumSize(16777215, 16777215)
            _force_available_size(window, avail_w, avail_h)
            app.processEvents()
            squeezed = _squeezed_buttons(window)
            worst = max((s for _, s, _, _ in squeezed), default=0)
            status = f"SQUEEZED(worst {worst}px)" if squeezed else "ok"
            detail = ", ".join(f"{lbl} -{sh}px" for lbl, sh, _, _ in squeezed[:8])
            print(f"{lang} | {spec['id']:32s} | {avail_w:4d}x{avail_h:4d} | "
                  f"{status}" + (f" | {detail}" if squeezed else ""), flush=True)
            if squeezed:
                problems.append((lang, spec["id"], squeezed, worst))
                pix = QPixmap(window.size())
                pix.fill(Qt.white)
                window.render(pix)
                path = os.path.join(PROBLEM_DIR, f"{lang}_{spec['id']}.png")
                pix.save(path, "PNG")
                print(f"      wrote {path}", flush=True)

    print("\n===== SUMMARY =====", flush=True)
    if not problems:
        print("no squeezed toolbar buttons in any language/ratio", flush=True)
    for lang, sid, squeezed, worst in problems:
        labels = ", ".join(f"{lbl}({w}<{hint})" for lbl, _, w, hint in squeezed)
        print(f"{lang} {sid}: worst -{worst}px | {labels}", flush=True)

    window.close()
    app.quit()
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
