"""
Stress test: create a group, then attach strands and hammer control-point
moves (200 moves) to expose any stale-state crashes after group creation.
No rotation — isolates the group-creation cleanup path.
"""
import os
import sys
import argparse
import faulthandler
import random

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


# ---------------------------------------------------------------------------
# Helpers (shared with test_menu_strand_flow.py)
# ---------------------------------------------------------------------------

def _qt_imports():
    from PyQt5.QtCore import QPoint, Qt, QTimer
    from PyQt5.QtWidgets import QApplication, QDialog, QLineEdit, QCheckBox, QPushButton
    from PyQt5.QtTest import QTest
    return QPoint, Qt, QTimer, QApplication, QTest, QDialog, QLineEdit, QCheckBox, QPushButton


def _draw_new_strand(window, start_xy, end_xy, set_number=1):
    QPoint, Qt, _, _, QTest, *_ = _qt_imports()
    canvas = window.canvas
    canvas.start_new_strand_mode(set_number)
    QTest.qWait(300)
    start = QPoint(*start_xy)
    end = QPoint(*end_xy)
    QTest.mousePress(canvas, Qt.LeftButton, pos=start)
    QTest.qWait(300)
    QTest.mouseMove(canvas, pos=end)
    QTest.qWait(300)
    QTest.mouseRelease(canvas, Qt.LeftButton, pos=end)
    QTest.qWait(800)


def _attach_from_point(window, attach_xy, end_xy):
    QPoint, Qt, _, _, QTest, *_ = _qt_imports()
    canvas = window.canvas
    print(f"[attach] set_attach_mode at {attach_xy} -> {end_xy}", flush=True)
    window.set_attach_mode()
    QTest.qWait(200)
    attach_point = QPoint(*attach_xy)
    end_point = QPoint(*end_xy)
    print(f"[attach] mousePress...", flush=True)
    QTest.mousePress(canvas, Qt.LeftButton, pos=attach_point)
    print(f"[attach] mousePress done, waiting...", flush=True)
    QTest.qWait(300)
    print(f"[attach] mouseMove...", flush=True)
    QTest.mouseMove(canvas, pos=end_point)
    print(f"[attach] mouseMove done, waiting...", flush=True)
    QTest.qWait(300)
    print(f"[attach] mouseRelease...", flush=True)
    QTest.mouseRelease(canvas, Qt.LeftButton, pos=end_point)
    print(f"[attach] mouseRelease done, waiting...", flush=True)
    QTest.qWait(800)
    print(f"[attach] complete", flush=True)


def _strand_by_name(canvas, layer_name):
    for strand in canvas.strands:
        if getattr(strand, "layer_name", None) == layer_name:
            return strand
    return None


def _schedule_dialog_fill_group_name(app, group_name, delay_ms=500):
    _, _, QTimer, QApplication, QTest, QDialog, QLineEdit, _, QPushButton = _qt_imports()

    def _fill():
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QDialog) and widget.isVisible():
                line_edit = widget.findChild(QLineEdit)
                if line_edit is not None:
                    print(f"[stress] setting group name '{group_name}'...", flush=True)
                    # Use setText instead of QTest.keyClick to avoid
                    # corrupting Qt's input state
                    line_edit.setText(group_name)
                    QTest.qWait(400)
                    for btn in widget.findChildren(QPushButton):
                        if btn.text().lower() in ("ok", "\u05d0\u05d9\u05e9\u05d5\u05e8"):
                            btn.click()
                            return
                    widget.accept()
                    return
        print("[stress] WARNING: name dialog not found", flush=True)

    QTimer.singleShot(delay_ms, _fill)


def _schedule_dialog_select_strands(app, strand_labels, delay_ms=500):
    _, _, QTimer, QApplication, QTest, QDialog, _, QCheckBox, QPushButton = _qt_imports()

    def _select():
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QDialog) and widget.isVisible():
                checkboxes = widget.findChildren(QCheckBox)
                if checkboxes:
                    for cb in checkboxes:
                        if cb.text() in strand_labels:
                            cb.setChecked(True)
                    QTest.qWait(400)
                    for btn in widget.findChildren(QPushButton):
                        if btn.text().lower() in ("ok", "\u05d0\u05d9\u05e9\u05d5\u05e8"):
                            btn.click()
                            return
                    widget.accept()
                    return
        print("[stress] WARNING: strand-select dialog not found", flush=True)

    QTimer.singleShot(delay_ms, _select)


# ---------------------------------------------------------------------------
# App bootstrap (same as test_menu_strand_flow.py)
# ---------------------------------------------------------------------------

def _bootstrap_real_app():
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QColor
    from main import setup_crash_logging, load_user_settings
    setup_crash_logging()

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, False)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    (theme, language_code, shadow_color, draw_only_affected_strand,
     enable_third_control_point, enable_curvature_bias_control,
     arrow_head_length, arrow_head_width, arrow_gap_length,
     arrow_line_length, arrow_line_width, use_default_arrow_color,
     default_arrow_fill_color, default_strand_color, default_stroke_color,
     control_point_base_fraction, distance_multiplier,
     curve_response_exponent) = load_user_settings()

    from main_window import MainWindow
    from undo_redo_manager import (connect_to_move_mode,
                                   connect_to_attach_mode,
                                   connect_to_mask_mode)

    window = MainWindow()

    if hasattr(window, 'canvas') and window.canvas:
        should_set_shadow = True
        if hasattr(window.canvas, 'default_shadow_color') and window.canvas.default_shadow_color:
            c = window.canvas.default_shadow_color
            if (c.red() == shadow_color.red() and c.green() == shadow_color.green()
                    and c.blue() == shadow_color.blue() and c.alpha() == shadow_color.alpha()):
                should_set_shadow = False
        if should_set_shadow:
            rgb_color = QColor(shadow_color.red(), shadow_color.green(),
                               shadow_color.blue(), shadow_color.alpha())
            window.canvas.set_shadow_color(rgb_color)

        if hasattr(window.canvas, 'move_mode'):
            window.canvas.move_mode.draw_only_affected_strand = draw_only_affected_strand
        if hasattr(window.canvas, 'rotate_mode'):
            window.canvas.rotate_mode.draw_only_affected_strand = draw_only_affected_strand
        if hasattr(window.canvas, 'angle_adjust_mode'):
            window.canvas.angle_adjust_mode.draw_only_affected_strand = draw_only_affected_strand

        if hasattr(window, 'layer_panel') and window.layer_panel and \
                hasattr(window.layer_panel, 'undo_redo_manager'):
            connect_to_move_mode(window.canvas, window.layer_panel.undo_redo_manager)
            if hasattr(window.canvas, 'attach_mode') and window.canvas.attach_mode:
                connect_to_attach_mode(window.canvas, window.layer_panel.undo_redo_manager)
            if hasattr(window.canvas, 'mask_mode') and window.canvas.mask_mode:
                connect_to_mask_mode(window.canvas, window.layer_panel.undo_redo_manager)

        window.canvas.enable_third_control_point = enable_third_control_point
        window.canvas.enable_curvature_bias_control = enable_curvature_bias_control
        window.canvas.arrow_head_length = arrow_head_length
        window.canvas.arrow_head_width = arrow_head_width
        window.canvas.arrow_gap_length = arrow_gap_length
        window.canvas.arrow_line_length = arrow_line_length
        window.canvas.arrow_line_width = arrow_line_width
        window.canvas.use_default_arrow_color = use_default_arrow_color
        window.canvas.default_arrow_fill_color = default_arrow_fill_color
        window.canvas.default_strand_color = default_strand_color
        window.canvas.default_stroke_color = default_stroke_color
        window.canvas.control_point_base_fraction = control_point_base_fraction
        window.canvas.distance_multiplier = distance_multiplier
        window.canvas.curve_response_exponent = curve_response_exponent

        if hasattr(window, 'layer_panel') and window.layer_panel:
            window.layer_panel.update_default_colors()

    window.set_language(language_code)
    window.apply_theme(theme)
    return app, window


# ---------------------------------------------------------------------------
# Stress test body
# ---------------------------------------------------------------------------

def _run_stress(window, app):
    _, _, _, QApplication, QTest, *_ = _qt_imports()
    random.seed(42)  # reproducible

    try:
        print("[stress] starting group stress test...", flush=True)
        canvas = window.canvas

        # 1) Draw 1_1
        _draw_new_strand(window, start_xy=(200, 200), end_xy=(400, 200), set_number=1)
        assert _strand_by_name(canvas, "1_1") is not None, "1_1 missing"
        print("[stress] 1_1 created", flush=True)

        # 2) Attach 1_2
        s11 = _strand_by_name(canvas, "1_1")
        _attach_from_point(window,
                           attach_xy=(int(s11.end.x()), int(s11.end.y())),
                           end_xy=(400, 400))
        assert _strand_by_name(canvas, "1_2") is not None, "1_2 missing"
        print("[stress] 1_2 attached", flush=True)

        # 3) Create group — use skip_dialog to avoid modal dialog + QTest
        #    incompatibility on Windows (dialog.open() or exec_() both corrupt
        #    native input state, causing QTest.mousePress to crash after)
        manager = window.layer_panel.group_layer_manager
        manager.create_group_with_params("stress1", ["1"], skip_dialog=True)
        QTest.qWait(500)
        assert "stress1" in canvas.groups, "group stress1 missing"
        print("[stress] group stress1 created", flush=True)

        # 4) Attach 1_3, 1_4, 1_5, 1_6
        for i, name in enumerate(["1_3", "1_4", "1_5", "1_6"]):
            prev = _strand_by_name(canvas, f"1_{i + 2}")
            assert prev is not None, f"1_{i + 2} missing before attaching {name}"
            end_prev = (int(prev.end.x()), int(prev.end.y()))
            offset_x = 120 + (i % 2) * 40
            offset_y = 60 - (i % 3) * 30
            _attach_from_point(window,
                               attach_xy=end_prev,
                               end_xy=(end_prev[0] + offset_x, end_prev[1] + offset_y))
            assert _strand_by_name(canvas, name) is not None, f"{name} missing"
            print(f"[stress] {name} attached", flush=True)

        # 5) Hammer 200 random control-point / endpoint moves
        strands = [_strand_by_name(canvas, n) for n in
                   ["1_3", "1_4", "1_5", "1_6"]]
        attrs = ["control_point1", "control_point2", "end"]
        FAST = 50  # ms

        print("[stress] starting 200 random moves...", flush=True)
        for i in range(200):
            strand = random.choice(strands)
            attr = random.choice(attrs)
            dx = random.randint(-25, 25)
            dy = random.randint(-25, 25)
            pt = getattr(strand, attr)
            pt.setX(pt.x() + dx)
            pt.setY(pt.y() + dy)
            strand.update_shape()
            canvas.update()
            QTest.qWait(FAST)
            if (i + 1) % 50 == 0:
                print(f"[stress]   {i + 1}/200 moves done", flush=True)

        print("[stress] 200 moves complete", flush=True)

        # Final checks
        for name in ["1_1", "1_2", "1_3", "1_4", "1_5", "1_6"]:
            assert _strand_by_name(canvas, name) is not None, f"{name} missing at end"
        assert "stress1" in canvas.groups

        print("[stress] ALL CHECKS PASSED", flush=True)

    except Exception as exc:
        print(f"[stress] FAILED: {exc}", flush=True)
        import traceback
        traceback.print_exc()

    finally:
        faulthandler.cancel_dump_traceback_later()
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, app.quit)


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

def main(visible=False):
    if not visible:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    else:
        os.environ.pop("QT_QPA_PLATFORM", None)

    app, window = _bootstrap_real_app()
    _, _, QTimer, _, _, *_ = _qt_imports()

    window.show()
    window.showMaximized()
    window.raise_()
    window.activateWindow()
    if hasattr(window, 'set_initial_splitter_sizes'):
        window.set_initial_splitter_sizes()

    QTimer.singleShot(600, lambda: _run_stress(window, app))
    app.exec_()
    os._exit(0)


if __name__ == "__main__":
    faulthandler.enable(all_threads=True)
    parser = argparse.ArgumentParser()
    parser.add_argument("--visible", action="store_true")
    args = parser.parse_args()
    main(visible=args.visible)
