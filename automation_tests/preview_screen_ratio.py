"""Open the real app at a simulated Mac screen's available geometry.

Shows a live, interactive MainWindow locked to the size the app would get
on that screen (menu bar + dock already subtracted), so you can judge the
layout exactly as an installed user would see it.

Run:
    python automation_tests/preview_screen_ratio.py <preset>
    python automation_tests/preview_screen_ratio.py --list
"""
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Same specs as capture_screen_ratio_mocks.py: full screen minus
# chrome_top/chrome_bottom gives the window's available geometry.
PRESETS = {
    "macbook13": ('MacBook 13" (smallest scaled)  1280x800', 1280, 800 - 25 - 70),
    "air13_more_space": ('MacBook Air 13" M2 (More Space)  1280x832', 1280, 832 - 25 - 70),
    "air13_intel": ('MacBook Air 13" Intel  1440x900', 1440, 900 - 25 - 70),
    "air13_default": ('MacBook Air 13" M2 (default)  1470x956', 1470, 956 - 25 - 70),
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("--list", "-l"):
        for key, (title, w, h) in PRESETS.items():
            print(f"{key:18s} {title}  ->  window {w}x{h}")
        return 0
    preset = sys.argv[1]
    if preset not in PRESETS:
        print(f"unknown preset '{preset}', use --list")
        return 1
    title, width, height = PRESETS[preset]

    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication

    from main import setup_crash_logging, load_user_settings
    setup_crash_logging()

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, False)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)

    settings = load_user_settings()
    theme = settings[0]

    from main_window import MainWindow
    window = MainWindow()
    if hasattr(window, "layer_panel") and window.layer_panel:
        window.layer_panel.update_default_colors()
    window.set_language("en")
    window.apply_theme(theme)

    # Skip the showEvent maximize and pin the window to the simulated
    # available geometry.
    window._initial_show_completed = True
    window.setWindowState(Qt.WindowNoState)
    window.setMinimumSize(0, 0)
    window.resize(width, height)
    window.setFixedSize(width, height)
    window.setWindowTitle(f"{title}  ·  window {width}x{height}")
    window.show()
    window.set_initial_splitter_sizes()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
