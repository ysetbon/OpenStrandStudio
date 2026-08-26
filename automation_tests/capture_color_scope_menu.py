"""
Capture proof screenshots of the new set-wide vs layer-only color/stroke
entries in the layer context menu (branch worktree-color-stroke-scope),
in English (LTR) and Hebrew (RTL).

Launches the real app, draws two strands of set 1, right-clicks layer 1_1,
grabs the open context menu while exec_() is running, and writes PNGs to
docs/color_stroke_scope_feature/.

Also asserts:
  - all four color/stroke entries are present in the menu, in order
    (Color, Color (This Layer Only), Stroke Color, Stroke Color (This
    Layer Only)), plus both Width entries;
  - in Hebrew each entry's HoverLabel is RightToLeft;
  - in English each entry's HoverLabel is LeftToRight.

Run:  python automation_tests/capture_color_scope_menu.py
"""
import os
import sys
import faulthandler

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

OUT_DIR = os.path.join(ROOT_DIR, "docs", "color_stroke_scope_feature", "screenshots")

FAILURES = []


def check(condition, message):
    status = "PASS" if condition else "FAIL"
    print(f"[capture] {status}: {message}", flush=True)
    if not condition:
        FAILURES.append(message)


def _bootstrap_real_app(language_code):
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication

    from main import setup_crash_logging, load_user_settings
    setup_crash_logging()

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, False)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    settings = load_user_settings()
    theme = settings[0]

    from main_window import MainWindow
    window = MainWindow()

    if hasattr(window, 'layer_panel') and window.layer_panel:
        window.layer_panel.update_default_colors()

    window.set_language(language_code)
    window.apply_theme(theme)
    return app, window


def _draw_new_strand(window, start_xy, end_xy, set_number=1):
    from PyQt5.QtCore import QPoint, Qt
    from PyQt5.QtTest import QTest
    canvas = window.canvas
    canvas.start_new_strand_mode(set_number)
    QTest.qWait(250)
    QTest.mousePress(canvas, Qt.LeftButton, pos=QPoint(*start_xy))
    QTest.qWait(150)
    QTest.mouseMove(canvas, pos=QPoint(*end_xy))
    QTest.qWait(150)
    QTest.mouseRelease(canvas, Qt.LeftButton, pos=QPoint(*end_xy))
    QTest.qWait(500)


def _button_by_name(layer_panel, layer_name):
    for button in layer_panel.layer_buttons:
        if button.text() == layer_name:
            return button
    return None


def _expected_labels(lang):
    from translations import translations
    _ = translations[lang]
    return [
        _['change_color'],
        _['change_layer_color'],
        _['change_stroke_color'],
        _['change_layer_stroke_color'],
        _['change_width'],
        _['change_layer_width'],
    ]


def _capture_menu(window, button, lang, png_path):
    """Open the layer context menu and grab it while exec_() blocks."""
    from PyQt5.QtCore import QPoint, Qt, QTimer
    from PyQt5.QtWidgets import QApplication, QMenu, QLabel

    state = {"menu": None, "shot": False}

    def grab_when_open():
        popup = QApplication.activePopupWidget()
        if popup is None or not isinstance(popup, QMenu):
            QTimer.singleShot(120, grab_when_open)
            return
        state["menu"] = popup
        QTimer.singleShot(600, do_grab)

    def do_grab():
        from PyQt5.QtGui import QPixmap, QPainter
        menu = state["menu"]
        try:
            menu.repaint()
            if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
                pixmap = QPixmap(menu.size())
                pixmap.fill()
                painter = QPainter(pixmap)
                menu.render(painter)
                painter.end()
            else:
                # Real screen pixels — widget-action labels only paint
                # reliably on an actual screen backing store.
                screen = QApplication.primaryScreen()
                pixmap = screen.grabWindow(0, menu.x(), menu.y(),
                                           menu.width(), menu.height())
            os.makedirs(os.path.dirname(png_path), exist_ok=True)
            pixmap.save(png_path)
            state["shot"] = True

            # Verify entries + direction on the live widgets
            labels = [w for w in menu.findChildren(QLabel) if w.text()]
            texts = [w.text() for w in labels]
            expected = _expected_labels(lang)
            for exp in expected:
                check(exp in texts, f"[{lang}] menu shows entry: {exp!r}")
            # order: set-wide immediately before its layer-only sibling
            idx = {t: i for i, t in enumerate(texts)}
            for a, b in [(expected[0], expected[1]),
                         (expected[2], expected[3]),
                         (expected[4], expected[5])]:
                if a in idx and b in idx:
                    check(idx[a] < idx[b],
                          f"[{lang}] {a!r} listed before {b!r}")
            want_rtl = (lang == 'he')
            for w in labels:
                if w.text() in expected:
                    is_rtl = w.layoutDirection() == Qt.RightToLeft
                    check(is_rtl == want_rtl,
                          f"[{lang}] {w.text()!r} direction "
                          f"{'RTL' if is_rtl else 'LTR'} as expected")
        finally:
            menu.close()

    QTimer.singleShot(200, grab_when_open)
    # Right-click the button for real so the menu opens exactly as in the app
    button.show_context_menu(QPoint(button.width() // 2, button.height() // 2))
    return state["shot"]


def run_language(lang, tag):
    from PyQt5.QtTest import QTest

    app, window = _bootstrap_real_app(lang)
    window.resize(1400, 900)
    window.show()
    QTest.qWait(800)

    _draw_new_strand(window, (300, 300), (600, 300), set_number=1)
    _draw_new_strand(window, (300, 450), (600, 450), set_number=2)

    layer_panel = window.layer_panel
    button = _button_by_name(layer_panel, "1_1")
    check(button is not None, f"[{lang}] layer button 1_1 exists")
    if button is None:
        window.close()
        return

    png = os.path.join(OUT_DIR, f"layer_menu_{tag}.png")
    shot = _capture_menu(window, button, lang, png)
    check(shot and os.path.exists(png), f"[{lang}] screenshot written: {png}")

    QTest.qWait(300)


def main():
    faulthandler.enable()
    if "--visible" not in sys.argv:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    print("[capture] starting", flush=True)
    lang = sys.argv[1] if len(sys.argv) > 1 else "en"
    tag = {"en": "english", "he": "hebrew"}.get(lang, lang)
    run_language(lang, tag)
    print(f"[capture] done: {len(FAILURES)} failure(s)", flush=True)
    # Hard-exit: skips the window close prompt and Qt teardown, which
    # segfault under the offscreen platform after the app has run.
    os._exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
