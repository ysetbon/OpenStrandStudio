"""
Automation test that launches the real app in Hebrew, draws 1_1 and 1_2,
opens the per-layer "Change Width (This Layer Only)" dialog for 1_1, and
grabs a PNG snapshot so the RTL alignment of the labels and the
"match connected strand" checkbox/toggle can be inspected.

Run headless (default) or visible:
    python automation_tests/test_width_dialog_rtl.py
    python automation_tests/test_width_dialog_rtl.py --visible
The snapshot is written to automation_tests/output/width_dialog_he.png
"""
import os
import sys
import argparse
import faulthandler

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
SNAPSHOT_PATH = os.path.join(OUTPUT_DIR, "width_dialog_he.png")


def _qt_imports():
    from PyQt5.QtCore import QPoint, Qt, QTimer
    from PyQt5.QtWidgets import QApplication, QDialog
    from PyQt5.QtTest import QTest
    return QPoint, Qt, QTimer, QApplication, QTest, QDialog


def _draw_new_strand(window, start_xy, end_xy, set_number=1):
    QPoint, Qt, _, _, QTest, _ = _qt_imports()
    canvas = window.canvas
    canvas.start_new_strand_mode(set_number)
    QTest.qWait(300)
    start = QPoint(*start_xy)
    end = QPoint(*end_xy)
    QTest.mousePress(canvas, Qt.LeftButton, pos=start)
    QTest.qWait(200)
    QTest.mouseMove(canvas, pos=end)
    QTest.qWait(200)
    QTest.mouseRelease(canvas, Qt.LeftButton, pos=end)
    QTest.qWait(600)


def _attach_from_point(window, attach_xy, end_xy):
    QPoint, Qt, _, _, QTest, _ = _qt_imports()
    canvas = window.canvas
    window.set_attach_mode()
    QTest.qWait(200)
    attach_point = QPoint(*attach_xy)
    end_point = QPoint(*end_xy)
    QTest.mousePress(canvas, Qt.LeftButton, pos=attach_point)
    QTest.qWait(200)
    QTest.mouseMove(canvas, pos=end_point)
    QTest.qWait(200)
    QTest.mouseRelease(canvas, Qt.LeftButton, pos=end_point)
    QTest.qWait(600)


def _strand_by_name(canvas, layer_name):
    for strand in canvas.strands:
        if getattr(strand, "layer_name", None) == layer_name:
            return strand
    return None


def _bootstrap_real_app(language_code="he"):
    """Create QApplication + MainWindow mirroring src/main.py, forcing language."""
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication

    from main import setup_crash_logging, load_user_settings
    setup_crash_logging()

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, False)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Load user settings then override the language with the requested one.
    settings = load_user_settings()
    theme = settings[0]

    from main_window import MainWindow
    window = MainWindow()

    if hasattr(window, 'layer_panel') and window.layer_panel:
        window.layer_panel.update_default_colors()

    window.set_language(language_code)
    window.apply_theme(theme)
    return app, window


def _grab_width_dialog(app, snapshot_path, delay_ms=700):
    """Find the open width dialog, snapshot it, log alignment, then close it."""
    _, Qt, QTimer, QApplication, QTest, QDialog = _qt_imports()

    def _grab():
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QDialog) and widget.isVisible() and \
                    widget.__class__.__name__ == "WidthConfigDialog":
                QTest.qWait(150)
                os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
                pixmap = widget.grab()
                pixmap.save(snapshot_path)
                direction = ("RTL" if widget.layoutDirection() == Qt.RightToLeft
                             else "LTR")
                print(f"[automation] dialog layoutDirection={direction}", flush=True)
                cb = getattr(widget, 'elliptical_checkbox', None)
                if cb is not None:
                    cb_dir = ("RTL" if cb.layoutDirection() == Qt.RightToLeft
                              else "LTR")
                    # Distance from the checkbox's right edge to the dialog's right edge.
                    cb_right = cb.mapTo(widget, cb.rect().topRight()).x()
                    gap_right = widget.width() - cb_right
                    print(f"[automation] checkbox layoutDirection={cb_dir} "
                          f"right_gap={gap_right}px dialog_w={widget.width()}", flush=True)
                print(f"[automation] snapshot saved -> {snapshot_path}", flush=True)
                QTest.qWait(200)
                widget.reject()
                return
        print("[automation] WARNING: WidthConfigDialog not found", flush=True)

    QTimer.singleShot(delay_ms, _grab)


def _run_automation(window, app):
    _, _, QTimer, _, QTest, _ = _qt_imports()
    try:
        print("[automation] starting width-dialog RTL flow...", flush=True)
        _draw_new_strand(window, start_xy=(140, 140), end_xy=(360, 140), set_number=1)
        canvas = window.canvas
        strand_11 = _strand_by_name(canvas, "1_1")
        assert strand_11 is not None, "1_1 missing"
        print("[automation] strand 1_1 created", flush=True)

        attach_xy_11 = (int(strand_11.end.x()), int(strand_11.end.y()))
        _attach_from_point(window, attach_xy=attach_xy_11, end_xy=(360, 320))
        assert _strand_by_name(canvas, "1_2") is not None, "1_2 missing"
        print("[automation] strand 1_2 attached", flush=True)

        layer_panel = window.layer_panel
        index = canvas.strands.index(strand_11)
        button = layer_panel.layer_buttons[index]
        print(f"[automation] opening per-layer Change Width for 1_1 "
              f"(button text='{button.text()}')...", flush=True)

        # Snapshot + close the modal dialog from a timer (change_layer_width blocks).
        _grab_width_dialog(app, SNAPSHOT_PATH, delay_ms=700)
        button.change_layer_width(strand_11, layer_panel)
        QTest.qWait(400)

        assert os.path.exists(SNAPSHOT_PATH), "snapshot was not written"
        print("[automation] ALL CHECKS PASSED", flush=True)
    except Exception as exc:
        print(f"[automation] FAILED: {exc}", flush=True)
        import traceback
        traceback.print_exc()
    finally:
        faulthandler.cancel_dump_traceback_later()
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, app.quit)


def test_width_dialog_rtl_alignment(visible=False):
    if not visible:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    else:
        os.environ.pop("QT_QPA_PLATFORM", None)

    app, window = _bootstrap_real_app(language_code="he")
    _, _, QTimer, _, _, _ = _qt_imports()

    window.show()
    window.showMaximized()
    window.raise_()
    window.activateWindow()
    if hasattr(window, 'set_initial_splitter_sizes'):
        window.set_initial_splitter_sizes()

    QTimer.singleShot(600, lambda: _run_automation(window, app))
    app.exec_()
    os._exit(0)


if __name__ == "__main__":
    faulthandler.enable(all_threads=True)
    parser = argparse.ArgumentParser()
    parser.add_argument("--visible", action="store_true",
                        help="Show real app window while running the flow")
    args = parser.parse_args()
    test_width_dialog_rtl_alignment(visible=args.visible)
