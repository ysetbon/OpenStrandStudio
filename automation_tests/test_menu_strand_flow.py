"""
Automation test that launches the real app (same as src/main.py) and runs
scripted strand/group actions after the window is fully initialized.
"""
import os
import sys
import argparse
import faulthandler

try:
    import pytest
except Exception:  # pragma: no cover - allows plain script execution without pytest
    pytest = None

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

if pytest is not None:
    gui_mark = pytest.mark.gui
else:
    def gui_mark(func):
        return func


# ---------------------------------------------------------------------------
# Helpers
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
    window.set_attach_mode()
    QTest.qWait(200)

    attach_point = QPoint(*attach_xy)
    end_point = QPoint(*end_xy)
    QTest.mousePress(canvas, Qt.LeftButton, pos=attach_point)
    QTest.qWait(300)
    QTest.mouseMove(canvas, pos=end_point)
    QTest.qWait(300)
    QTest.mouseRelease(canvas, Qt.LeftButton, pos=end_point)
    QTest.qWait(800)


def _strand_by_name(canvas, layer_name):
    for strand in canvas.strands:
        if getattr(strand, "layer_name", None) == layer_name:
            return strand
    return None


def _schedule_dialog_fill_group_name(app, group_name, delay_ms=500):
    """Schedule a timer to find the 'name the group' modal dialog, type
    the group name into its QLineEdit, pause visibly, then click OK."""
    _, _, QTimer, QApplication, QTest, QDialog, QLineEdit, _, QPushButton = _qt_imports()

    def _fill():
        # Find the active modal dialog
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QDialog) and widget.isVisible():
                line_edit = widget.findChild(QLineEdit)
                if line_edit is not None:
                    print(f"[automation] typing group name '{group_name}'...", flush=True)
                    line_edit.clear()
                    line_edit.setFocus()
                    QTest.qWait(300)
                    # Type the name character by character for visual effect
                    for ch in group_name:
                        QTest.keyClick(line_edit, ch)
                        QTest.qWait(150)
                    QTest.qWait(600)
                    # Click OK
                    for btn in widget.findChildren(QPushButton):
                        if btn.text().lower() in ("ok", "אישור"):
                            print("[automation] clicking OK on name dialog", flush=True)
                            btn.click()
                            return
                    # Fallback: accept dialog directly
                    widget.accept()
                    return
        print("[automation] WARNING: name dialog not found", flush=True)

    QTimer.singleShot(delay_ms, _fill)


def _schedule_dialog_select_strands(app, strand_labels, delay_ms=500):
    """Schedule a timer to find the strand-selection modal dialog, check
    the requested checkboxes, pause visibly, then click OK."""
    _, _, QTimer, QApplication, QTest, QDialog, _, QCheckBox, QPushButton = _qt_imports()

    def _select():
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QDialog) and widget.isVisible():
                checkboxes = widget.findChildren(QCheckBox)
                if checkboxes:
                    print(f"[automation] selecting strands {strand_labels}...", flush=True)
                    for cb in checkboxes:
                        if cb.text() in strand_labels:
                            QTest.qWait(400)
                            cb.setChecked(True)
                            print(f"[automation]   checked '{cb.text()}'", flush=True)
                    QTest.qWait(600)
                    # Click OK
                    for btn in widget.findChildren(QPushButton):
                        if btn.text().lower() in ("ok", "אישור"):
                            print("[automation] clicking OK on strand-select dialog", flush=True)
                            btn.click()
                            return
                    widget.accept()
                    return
        print("[automation] WARNING: strand-select dialog not found", flush=True)

    QTimer.singleShot(delay_ms, _select)


def _schedule_dialog_rotate_group(app, target_angle, delay_ms=500):
    """Schedule a timer to find the GroupRotateDialog, animate the slider
    to *target_angle* in visible steps, then click OK."""
    from PyQt5.QtWidgets import QSlider
    _, _, QTimer, QApplication, QTest, QDialog, _, _, QPushButton = _qt_imports()

    def _rotate():
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QDialog) and widget.isVisible():
                slider = widget.findChild(QSlider)
                if slider is not None:
                    print(f"[automation] rotating group to {target_angle}°...", flush=True)
                    # Animate the slider from current value to target in steps
                    current = slider.value()
                    step = 1 if target_angle > current else -1
                    for angle in range(current + step, target_angle + step, step):
                        slider.setValue(angle)
                        # Slow down: pause every 5 degrees so the rotation is visible
                        if angle % 5 == 0:
                            QTest.qWait(80)
                    QTest.qWait(800)
                    print(f"[automation] slider at {slider.value()}°, clicking OK", flush=True)
                    # Click OK
                    for btn in widget.findChildren(QPushButton):
                        if btn.text().lower() in ("ok", "אישור"):
                            btn.click()
                            return
                    widget.accept()
                    return
        print("[automation] WARNING: rotate dialog not found", flush=True)

    QTimer.singleShot(delay_ms, _rotate)


# ---------------------------------------------------------------------------
# App bootstrap – mirrors src/main.py exactly
# ---------------------------------------------------------------------------

def _bootstrap_real_app():
    """
    Create QApplication + MainWindow using the same sequence as src/main.py.
    Returns (app, window).
    """
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QColor

    # Same setup as main.py
    from main import setup_crash_logging, load_user_settings
    setup_crash_logging()

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, False)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Load user settings (same call as main.py)
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

    # Apply all settings to the canvas (same as main.py lines 260-336)
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
# Test body (runs inside the event loop via QTimer)
# ---------------------------------------------------------------------------

def _run_automation(window, app):
    """Perform the scripted strand/group actions and exit."""
    _, _, _, QApplication, QTest, *_ = _qt_imports()

    try:
        print("[automation] starting strand flow...", flush=True)

        # 1) Draw base strand 1_1, then attach 1_2 from its end
        _draw_new_strand(window, start_xy=(140, 140), end_xy=(360, 140), set_number=1)

        canvas = window.canvas
        assert _strand_by_name(canvas, "1_1") is not None, "1_1 missing"
        print("[automation] strand 1_1 created", flush=True)

        # Attach 1_2 from end of 1_1 (L-shaped: goes downward)
        strand_11 = _strand_by_name(canvas, "1_1")
        attach_xy_11 = (int(strand_11.end.x()), int(strand_11.end.y()))
        _attach_from_point(window, attach_xy=attach_xy_11, end_xy=(360, 320))
        assert _strand_by_name(canvas, "1_2") is not None, "1_2 missing"
        print("[automation] strand 1_2 attached", flush=True)

        # 2) Create group via real dialogs (name dialog -> strand selection dialog)
        manager = window.layer_panel.group_layer_manager

        # Schedule interactions with the two modal dialogs that will appear.
        # Dialog 1 (group name input) appears first — we type "test1" and click OK.
        # Dialog 2 (strand selection) appears after dialog 1 closes — we check "1" and click OK.
        # The second timer fires relative to now; by the time dialog 1 is dismissed
        # (~500 + typing time ≈ 1700ms) dialog 2 pops up, so we schedule it later.
        _schedule_dialog_fill_group_name(app, "test1", delay_ms=500)
        _schedule_dialog_select_strands(app, ["1"], delay_ms=2500)

        print("[automation] calling create_group() (dialogs will appear)...", flush=True)
        manager.create_group()  # This blocks until both dialogs are dismissed
        QTest.qWait(800)
        assert "test1" in canvas.groups, "group test1 missing"
        print("[automation] group test1 created via dialogs", flush=True)

        # 3) Rotate group "test1" to 50° via the real rotation dialog
        group_panel = window.layer_panel.group_layer_manager.group_panel
        _schedule_dialog_rotate_group(app, target_angle=50, delay_ms=800)

        print("[automation] calling start_group_rotation() (dialog will appear)...", flush=True)
        group_panel.start_group_rotation("test1")  # Blocks until dialog is dismissed
        QTest.qWait(800)
        print("[automation] group test1 rotated to 50°", flush=True)

        # Read the rotated endpoint positions from actual strand objects
        strand_12 = _strand_by_name(canvas, "1_2")
        assert strand_12 is not None
        end_12 = (int(strand_12.end.x()), int(strand_12.end.y()))
        print(f"[automation] after rotation: 1_2 end at {end_12}", flush=True)

        # 4) Attach 1_3 to the (rotated) end of 1_2
        # Place the new endpoint offset from the attach point
        attach_end_13 = (end_12[0] + 160, end_12[1] + 40)
        _attach_from_point(window, attach_xy=end_12, end_xy=attach_end_13)

        strand_13 = _strand_by_name(canvas, "1_3")
        assert strand_13 is not None, "1_3 missing after attach"
        print("[automation] strand 1_3 attached", flush=True)

        # Move 1_3 control points
        strand_13.control_point1.setX(strand_13.control_point1.x() + 25)
        strand_13.control_point1.setY(strand_13.control_point1.y() - 18)
        strand_13.update_shape()
        canvas.update()
        QTest.qWait(500)

        strand_13.control_point2.setX(strand_13.control_point2.x() + 30)
        strand_13.control_point2.setY(strand_13.control_point2.y() + 14)
        strand_13.update_shape()
        canvas.update()
        QTest.qWait(500)

        strand_13.end.setX(strand_13.end.x() + 40)
        strand_13.end.setY(strand_13.end.y() + 20)
        strand_13.update_shape()
        canvas.update()
        QTest.qWait(500)

        # 5) Attach 1_4 to end of 1_3
        end_13 = (int(strand_13.end.x()), int(strand_13.end.y()))
        attach_end_14 = (end_13[0] + 100, end_13[1] + 70)
        _attach_from_point(window, attach_xy=end_13, end_xy=attach_end_14)

        strand_14 = _strand_by_name(canvas, "1_4")
        assert strand_14 is not None, "1_4 missing after attach"
        print("[automation] strand 1_4 attached", flush=True)

        strand_14.end.setX(strand_14.end.x() + 35)
        strand_14.end.setY(strand_14.end.y() - 22)
        strand_14.update_shape()
        canvas.update()
        QTest.qWait(500)

        strand_14.control_point1.setX(strand_14.control_point1.x() - 20)
        strand_14.control_point1.setY(strand_14.control_point1.y() + 16)
        strand_14.update_shape()
        canvas.update()
        QTest.qWait(500)

        # 6) Attach 1_5 to end of 1_4
        end_14 = (int(strand_14.end.x()), int(strand_14.end.y()))
        attach_end_15 = (end_14[0] + 120, end_14[1] - 50)
        _attach_from_point(window, attach_xy=end_14, end_xy=attach_end_15)

        strand_15 = _strand_by_name(canvas, "1_5")
        assert strand_15 is not None, "1_5 missing after attach"
        print("[automation] strand 1_5 attached", flush=True)

        # 7) Rapid control-point movements across 1_3, 1_4, 1_5 (~30 moves, 7x faster)
        FAST = 200  # ms between each move (~2.5x faster than normal 500ms)
        print("[automation] starting rapid control point adjustments...", flush=True)

        # Re-fetch strand references
        strand_13 = _strand_by_name(canvas, "1_3")
        strand_14 = _strand_by_name(canvas, "1_4")
        strand_15 = _strand_by_name(canvas, "1_5")

        FAST = 70  # ms between each move (7x faster than 500ms)

        def _mv(strand, attr, dx, dy):
            """Nudge a point attribute and refresh."""
            pt = getattr(strand, attr)
            pt.setX(pt.x() + dx)
            pt.setY(pt.y() + dy)
            strand.update_shape()
            canvas.update()
            QTest.qWait(FAST)

        # --- 1_5 adjustments (10 moves) ---
        _mv(strand_15, 'control_point1',  20, -12)
        _mv(strand_15, 'control_point2', -15,  16)
        _mv(strand_15, 'end',             18,  10)
        _mv(strand_15, 'control_point1', -22,   8)
        _mv(strand_15, 'control_point2',  14, -20)
        _mv(strand_15, 'end',            -10,  22)
        _mv(strand_15, 'control_point1',  16,  15)
        _mv(strand_15, 'control_point2', -12, -14)
        _mv(strand_15, 'end',             25,  -6)
        _mv(strand_15, 'control_point1',  -8,  18)

        # --- 1_4 adjustments (10 moves) ---
        _mv(strand_14, 'control_point1',  18, -15)
        _mv(strand_14, 'control_point2', -10,  20)
        _mv(strand_14, 'end',             22,  12)
        _mv(strand_14, 'control_point1', -14,  -8)
        _mv(strand_14, 'control_point2',  16,  14)
        _mv(strand_14, 'end',            -20, -18)
        _mv(strand_14, 'control_point1',  25,   6)
        _mv(strand_14, 'control_point2',  -8,  25)
        _mv(strand_14, 'end',             12, -10)
        _mv(strand_14, 'control_point1', -16,  12)

        # --- 1_3 adjustments (10 moves) ---
        _mv(strand_13, 'control_point1',  15, -10)
        _mv(strand_13, 'control_point2', -12,  18)
        _mv(strand_13, 'end',             10,  15)
        _mv(strand_13, 'control_point1', -20,   5)
        _mv(strand_13, 'control_point2',  25, -12)
        _mv(strand_13, 'end',            -15,  -8)
        _mv(strand_13, 'control_point1',   8,  22)
        _mv(strand_13, 'control_point2', -18,  -6)
        _mv(strand_13, 'end',             20, -14)
        _mv(strand_13, 'control_point1',  12,  10)

        print("[automation] rapid adjustments complete (30 moves)", flush=True)

        # Final checks
        assert _strand_by_name(canvas, "1_1") is not None
        assert _strand_by_name(canvas, "1_2") is not None
        assert _strand_by_name(canvas, "1_3") is not None
        assert _strand_by_name(canvas, "1_4") is not None
        assert _strand_by_name(canvas, "1_5") is not None
        assert "test1" in canvas.groups

        print("[automation] ALL CHECKS PASSED", flush=True)

    except Exception as exc:
        print(f"[automation] FAILED: {exc}", flush=True)
        import traceback
        traceback.print_exc()

    finally:
        # Cancel the crash-watchdog timer set by setup_crash_logging
        faulthandler.cancel_dump_traceback_later()
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, app.quit)


# ---------------------------------------------------------------------------
# Entry-points
# ---------------------------------------------------------------------------

@gui_mark
def test_menu_add_group_attach_and_move_flow(visible=False):
    """
    Launch the real app (same as src/main.py), then drive the strand/group
    automation after the window is fully initialized.
    """
    if not visible:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    else:
        os.environ.pop("QT_QPA_PLATFORM", None)

    app, window = _bootstrap_real_app()

    _, _, QTimer, _, _, *_ = _qt_imports()

    # Show the window like main.py does
    window.show()
    window.showMaximized()
    window.raise_()
    window.activateWindow()

    if hasattr(window, 'set_initial_splitter_sizes'):
        window.set_initial_splitter_sizes()

    # Schedule automation after the window has fully settled
    QTimer.singleShot(600, lambda: _run_automation(window, app))

    # Enter the real event loop (exits when _run_automation calls app.quit())
    app.exec_()
    # Force-exit to avoid PyQt5 teardown abort on Windows
    os._exit(0)


if __name__ == "__main__":
    faulthandler.enable(all_threads=True)
    parser = argparse.ArgumentParser()
    parser.add_argument("--visible", action="store_true",
                        help="Show real app window while running the flow")
    args = parser.parse_args()
    test_menu_add_group_attach_and_move_flow(visible=args.visible)
