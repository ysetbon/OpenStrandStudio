"""Capture REAL app screenshots for the control-point-visibility-during-drag
issue (src/documentation/cp_drag_visibility_issue.md).

Launches the actual application (same bootstrap as src/main.py), draws 1_1,
attaches 1_2 with real mouse events, selects 1_2, switches to move mode and
drags 1_1's start point - grabbing the real window mid-drag.

Usage:
    python automation_tests\\capture_cp_drag_screens.py --mode fixed
        writes 01_before_drag_1_2_selected.png, 03_expected_during_drag.png,
               04_correct_shaped_curve_drag.png
    python automation_tests\\capture_cp_drag_screens.py --mode bug
        writes 02_bug_during_drag.png
        (run this with the fix reverted, e.g.
         git stash push -- src/strand_drawing_canvas.py ... git stash pop)

Screenshots go to src/documentation/images/cp_drag/.
Add --visible to watch it happen in a real window.
"""
import os
import sys
import argparse

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
for p in (SRC_DIR, os.path.dirname(os.path.abspath(__file__))):
    if p not in sys.path:
        sys.path.insert(0, p)

from test_menu_strand_flow import (_bootstrap_real_app, _draw_new_strand,
                                   _attach_from_point, _strand_by_name,
                                   _qt_imports)

OUT_DIR = os.path.join(SRC_DIR, "documentation", "images", "cp_drag")

MODE = "fixed"
VISIBLE = False

# canvas-coordinate layout (zoom=1, no pan -> equals widget coords).
# Keep everything within ~500x500: the offscreen canvas is small.
S1_START = (300, 120)
S1_END = (340, 300)
S2_END = (120, 340)
DRAG_TO = (230, 80)
CP1_SHAPE_TO = (390, 200)
DRAG2_TO = (300, 110)


def _wait(ms):
    from PyQt5.QtTest import QTest
    QTest.qWait(int(ms * (2.0 if VISIBLE else 1.0)))


def _shot(window, name):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name + ".png")
    window.grab().save(path)
    print("wrote", path, flush=True)


def _mouse_move_held(canvas, x, y):
    """Mouse move with the left button held (a real drag step)."""
    from PyQt5.QtCore import QPointF, QEvent, Qt
    from PyQt5.QtGui import QMouseEvent
    from PyQt5.QtWidgets import QApplication
    ev = QMouseEvent(QEvent.MouseMove, QPointF(x, y),
                     Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    QApplication.sendEvent(canvas, ev)
    canvas.repaint()


def _drag_with_midshot(window, canvas, start_xy, end_xy, shot_name):
    """Press at start_xy, drag toward end_xy in steps, screenshot while the
    button is still held, then release."""
    from PyQt5.QtCore import QPoint, Qt
    from PyQt5.QtTest import QTest
    QTest.mousePress(canvas, Qt.LeftButton,
                     pos=QPoint(int(start_xy[0]), int(start_xy[1])))
    _wait(300)
    mm = canvas.move_mode
    print("  press at", start_xy, "-> is_moving:", mm.is_moving,
          "| moving_side:", mm.moving_side,
          "| moving_cp:", mm.is_moving_control_point,
          "| affected:", getattr(mm.affected_strand, "layer_name", None),
          flush=True)
    steps = 8
    for i in range(1, steps + 1):
        x = start_xy[0] + (end_xy[0] - start_xy[0]) * i / steps
        y = start_xy[1] + (end_xy[1] - start_xy[1]) * i / steps
        _mouse_move_held(canvas, x, y)
        _wait(60)
    _wait(400)
    if shot_name:
        _shot(window, shot_name)          # mid-drag, button still held
    QTest.mouseRelease(canvas, Qt.LeftButton,
                       pos=QPoint(int(end_xy[0]), int(end_xy[1])))
    _wait(500)


def _select_strand_by_name(canvas, layer_name):
    for i, s in enumerate(canvas.strands):
        if getattr(s, "layer_name", None) == layer_name:
            canvas.select_strand(i)
            return True
    return False


def _run(window, app):
    canvas = window.canvas
    from PyQt5.QtCore import QTimer

    try:
        # --- build the scene with real mouse events ---
        _draw_new_strand(window, S1_START, S1_END)          # 1_1
        print("after draw:", [getattr(s, "layer_name", "?") for s in canvas.strands],
              flush=True)
        s1 = _strand_by_name(canvas, "1_1")
        assert s1 is not None, "1_1 was not created"
        # attach exactly at 1_1's real end (snap-to-grid may have moved it)
        _attach_from_point(window, (int(s1.end.x()), int(s1.end.y())), S2_END)  # 1_2
        print("after attach:", [getattr(s, "layer_name", "?") for s in canvas.strands],
              flush=True)
        s1 = _strand_by_name(canvas, "1_1")
        s2 = _strand_by_name(canvas, "1_2")
        assert s1 is not None and s2 is not None, "strands were not created"
        print("sanity: 1_1 cp1==start:", s1.control_point1 == s1.start,
              "| triangle_has_moved:", getattr(s1, "triangle_has_moved", None),
              flush=True)

        # --- the user's settings ("case #5"), applied once the scene exists ---
        canvas.show_control_points = True
        canvas.show_cp_selected_only = True
        canvas.move_selected_only = False
        canvas.enable_third_control_point = True
        canvas.move_mode.draw_only_affected_strand = False

        # --- select 1_2, enter move mode ---
        _select_strand_by_name(canvas, "1_2")
        _wait(300)
        window.set_move_mode()
        _wait(500)
        canvas.repaint()

        if MODE == "fixed":
            _shot(window, "01_before_drag_1_2_selected")

            # drag 1_1's never-moved start: with the fix, no triangle appears
            _drag_with_midshot(window, canvas,
                               (s1.start.x(), s1.start.y()), DRAG_TO,
                               "03_expected_during_drag")

            # --- scenario 04: shape 1_1's curve, then drag its start again ---
            _select_strand_by_name(canvas, "1_1")
            _wait(300)
            window.set_move_mode()      # selecting a layer can switch modes
            _wait(400)
            # grab the triangle (cp1 sits on the start) and drag it out
            _drag_with_midshot(window, canvas,
                               (s1.start.x(), s1.start.y()), CP1_SHAPE_TO, None)
            print("sanity: triangle_has_moved after shaping:",
                  getattr(s1, "triangle_has_moved", None), flush=True)
            _select_strand_by_name(canvas, "1_2")
            _wait(300)
            window.set_move_mode()
            _wait(400)
            # now drag the start point: handles must stay visible
            _drag_with_midshot(window, canvas,
                               (s1.start.x(), s1.start.y()), DRAG2_TO,
                               "04_correct_shaped_curve_drag")
        else:  # MODE == "bug"  (run with the fix reverted)
            _drag_with_midshot(window, canvas,
                               (s1.start.x(), s1.start.y()), DRAG_TO,
                               "02_bug_during_drag")

        print("done", flush=True)
    except Exception:
        import traceback
        traceback.print_exc()
        QTimer.singleShot(0, lambda: os._exit(1))
        return
    QTimer.singleShot(2000 if VISIBLE else 0, app.quit)


def main():
    global MODE, VISIBLE
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("fixed", "bug"), default="fixed")
    parser.add_argument("--visible", action="store_true")
    args = parser.parse_args()
    MODE = args.mode
    VISIBLE = args.visible
    if not VISIBLE:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    app, window = _bootstrap_real_app()
    _, _, QTimer, _, _, *_ = _qt_imports()

    window.show()
    window.showMaximized()
    window.raise_()
    window.activateWindow()
    if hasattr(window, "set_initial_splitter_sizes"):
        window.set_initial_splitter_sizes()

    QTimer.singleShot(800, lambda: _run(window, app))
    app.exec_()


if __name__ == "__main__":
    main()
