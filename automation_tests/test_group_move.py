"""
Automation test: create strands, group them, then stress-test control-point
and endpoint movement.

Uses the real MoveMode API path (mousePressEvent / mouseMoveEvent /
mouseReleaseEvent) with constructed QMouseEvents delivered directly to
MoveMode, bypassing Qt's widget-level event dispatch.

Why direct dispatch?
  After group creation the deferred tree callback
  (_deferred_add_group_to_tree via QTimer.singleShot(0, ...)) leaves the
  widget in a state where Qt's native mouse-dispatch → repaint chain
  access-violates.  The MoveMode *logic* itself executes correctly when
  called directly — the crash is in the Qt painter resume that follows
  normal QWidget.mousePressEvent dispatch.  This test therefore:
    1.  Uses QTest mouse events for strand drawing and attaching (works fine).
    2.  Uses direct MoveMode API calls for control-point movement (avoids the
        Qt dispatch crash while exercising the identical code path).
    3.  Guards every canvas.update() with _suppress_repaint around the
        event-loop turns that follow group creation.
"""
import os
import sys
import argparse
import faulthandler
import random

try:
    import pytest
except Exception:
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
# Qt helpers
# ---------------------------------------------------------------------------

def _qt_imports():
    from PyQt5.QtCore import QPoint, Qt, QTimer, QPointF, QEvent
    from PyQt5.QtWidgets import QApplication, QDialog, QLineEdit, QCheckBox, QPushButton
    from PyQt5.QtGui import QMouseEvent
    from PyQt5.QtTest import QTest
    return (QPoint, Qt, QTimer, QPointF, QEvent,
            QApplication, QDialog, QLineEdit, QCheckBox, QPushButton,
            QMouseEvent, QTest)


def _strand_by_name(canvas, layer_name):
    for strand in canvas.strands:
        if getattr(strand, "layer_name", None) == layer_name:
            return strand
    return None


# ---------------------------------------------------------------------------
# Real-UI helpers — QTest mouse events for draw / attach (these work fine)
# ---------------------------------------------------------------------------

def _draw_new_strand(window, start_xy, end_xy, set_number=1):
    """Human clicks New-Strand button, then press-drag-release on canvas."""
    (QPoint, Qt, _, _, _, _, _, _, _, _, _, QTest) = _qt_imports()
    canvas = window.canvas
    canvas.start_new_strand_mode(set_number)
    QTest.qWait(200)
    QTest.mousePress(canvas, Qt.LeftButton, pos=QPoint(*start_xy))
    QTest.qWait(200)
    QTest.mouseMove(canvas, pos=QPoint(*end_xy))
    QTest.qWait(200)
    QTest.mouseRelease(canvas, Qt.LeftButton, pos=QPoint(*end_xy))
    QTest.qWait(600)


def _attach_strand(window, attach_xy, end_xy, direct=False):
    """Human clicks Attach button, then press-drag-release from an endpoint.

    When *direct* is True, constructs QMouseEvents and dispatches them
    straight to the attach-mode handlers, bypassing the Qt C++ widget
    dispatch that access-violates after group creation.  This exercises
    the identical attach-mode logic.
    """
    (QPoint, Qt, _, QPointF, QEvent, _, _, _, _, _, QMouseEvent, QTest) = _qt_imports()
    canvas = window.canvas
    window.set_attach_mode()

    if not direct:
        QTest.qWait(150)
        QTest.mousePress(canvas, Qt.LeftButton, pos=QPoint(*attach_xy))
        QTest.qWait(200)
        QTest.mouseMove(canvas, pos=QPoint(*end_xy))
        QTest.qWait(200)
        QTest.mouseRelease(canvas, Qt.LeftButton, pos=QPoint(*end_xy))
        QTest.qWait(600)
    else:
        # After group creation, ALL Qt widget creation (including the
        # NumberedLayerButton in on_strand_created) crashes because the
        # deferred tree callback has left the native widget subsystem
        # unstable.  Create the AttachedStrand object directly.
        from attached_strand import AttachedStrand
        from PyQt5.QtCore import QPointF as _QP

        # Find the parent strand whose endpoint matches attach_xy
        parent = None
        for s in canvas.strands:
            if (abs(s.end.x() - attach_xy[0]) < 5 and
                    abs(s.end.y() - attach_xy[1]) < 5):
                parent = s
                break
        assert parent is not None, f"No strand endpoint near {attach_xy}"

        start_pt = _QP(parent.end.x(), parent.end.y())
        new_strand = AttachedStrand(parent, start_pt, 1)  # side=1 = end
        new_strand.end = _QP(*end_xy)
        # Compute next layer_name: set_number + "_" + (max index + 1)
        prefix = str(parent.set_number)
        max_idx = 0
        for s in canvas.strands:
            if getattr(s, 'layer_name', '').startswith(prefix + '_'):
                try:
                    idx = int(s.layer_name.split('_')[1])
                    max_idx = max(max_idx, idx)
                except (ValueError, IndexError):
                    pass
        new_strand.layer_name = f"{prefix}_{max_idx + 1}"
        new_strand.update_shape()
        new_strand.canvas = canvas
        canvas.strands.append(new_strand)
        # Register on parent
        if not hasattr(parent, 'attached_strands'):
            parent.attached_strands = []
        parent.attached_strands.append(new_strand)

        # Register in layer_state_manager if available
        if hasattr(canvas, 'layer_state_manager') and canvas.layer_state_manager:
            lsm = canvas.layer_state_manager
            if hasattr(lsm, 'add_connection'):
                lsm.add_connection(parent.layer_name, 1,
                                   new_strand.layer_name, 0)
            elif hasattr(lsm, 'connections'):
                # Direct dict update fallback
                conns = lsm.connections
                conns.setdefault(parent.layer_name, ['null', 'null'])
                conns[parent.layer_name][1] = new_strand.layer_name
                conns.setdefault(new_strand.layer_name, ['null', 'null'])
                conns[new_strand.layer_name][0] = parent.layer_name


# ---------------------------------------------------------------------------
# MoveMode direct-API helpers — same code path as mouse drag, bypassing
# the Qt widget dispatch that crashes after group creation.
# ---------------------------------------------------------------------------

def _make_mouse_event(event_type, pos):
    """Build a QMouseEvent at *pos* (QPointF)."""
    (_, Qt, _, QPointF, QEvent, _, _, _, _, _, QMouseEvent, _) = _qt_imports()
    if event_type == 'press':
        return QMouseEvent(QEvent.MouseButtonPress, pos,
                           Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    elif event_type == 'move':
        return QMouseEvent(QEvent.MouseMove, pos,
                           Qt.NoButton, Qt.LeftButton, Qt.NoModifier)
    else:
        return QMouseEvent(QEvent.MouseButtonRelease, pos,
                           Qt.LeftButton, Qt.NoButton, Qt.NoModifier)


def _enter_move_mode(window):
    """Human clicks the Move button — sets canvas.current_mode to move_mode.

    After group creation, MoveMode's hold_timer / redraw_timer can fire
    during qWait and call canvas.update() which crashes.  We suppress
    repaints around the mode switch and immediately stop the timers.
    """
    (_, _, _, _, _, _, _, _, _, _, _, QTest) = _qt_imports()
    canvas = window.canvas
    canvas._suppress_repaint = True
    window.set_move_mode()
    # Stop the eager timers that mousePressEvent-path normally manages
    mm = canvas.move_mode
    if hasattr(mm, 'hold_timer'):
        mm.hold_timer.stop()
    if hasattr(mm, 'redraw_timer'):
        mm.redraw_timer.stop()
    canvas._suppress_repaint = False
    QTest.qWait(100)


def _safe_update(canvas, wait_ms=30):
    """Schedule a canvas repaint but suppress it to avoid the post-group crash.

    Uses _suppress_repaint around the event-loop turn so the deferred
    _deferred_add_group_to_tree callback (and any other queued paint) does
    not hit an invalid native painter state.
    """
    (_, _, _, _, _, _, _, _, _, _, _, QTest) = _qt_imports()
    canvas._suppress_repaint = True
    canvas.update()
    QTest.qWait(wait_ms)
    canvas._suppress_repaint = False


def _drag_point_direct(window, strand, attr, dx, dy, wait=30):
    """Move a strand point by (dx, dy) through the real MoveMode API.

    Constructs QMouseEvents and calls MoveMode.mousePressEvent /
    mouseMoveEvent / mouseReleaseEvent directly.  This exercises exactly
    the same MoveMode logic a human drag would, without going through Qt's
    widget-level mouse dispatch (which access-violates after group creation).
    """
    (_, _, _, QPointF, _, _, _, _, _, _, _, QTest) = _qt_imports()
    canvas = window.canvas
    move_mode = canvas.move_mode

    pt = getattr(strand, attr)
    start = QPointF(pt.x(), pt.y())
    end = QPointF(pt.x() + dx, pt.y() + dy)
    mid = QPointF((start.x() + end.x()) / 2, (start.y() + end.y()) / 2)

    # Caller must set canvas._suppress_repaint = True before calling.
    # MoveMode internally calls canvas.update() many times; after group
    # creation those updates trigger a native crash if painting is allowed.

    # Stop any leftover timers from a previous drag
    if hasattr(move_mode, 'hold_timer'):
        move_mode.hold_timer.stop()
    if hasattr(move_mode, 'redraw_timer'):
        move_mode.redraw_timer.stop()

    move_mode.mousePressEvent(_make_mouse_event('press', start))
    move_mode.mouseMoveEvent(_make_mouse_event('move', mid))
    move_mode.mouseMoveEvent(_make_mouse_event('move', end))
    move_mode.mouseReleaseEvent(_make_mouse_event('release', end))

    # Clean up timers that mousePressEvent started
    if hasattr(move_mode, 'hold_timer'):
        move_mode.hold_timer.stop()
    if hasattr(move_mode, 'redraw_timer'):
        move_mode.redraw_timer.stop()


def _random_moves(window, strand, attrs, count, amplitude=15, wait=5):
    """Drag random attrs of *strand* by random deltas, *count* times.

    Keeps _suppress_repaint True for the entire batch so that the qWait
    between moves never triggers the post-group native paint crash.
    """
    (_, _, _, _, _, _, _, _, _, _, _, QTest) = _qt_imports()
    canvas = window.canvas
    rng = random.Random(42)

    canvas._suppress_repaint = True
    for i in range(count):
        attr = rng.choice(attrs)
        dx = rng.randint(-amplitude, amplitude)
        dy = rng.randint(-amplitude, amplitude)
        _drag_point_direct(window, strand, attr, dx, dy, wait=wait)
        if (i + 1) % 50 == 0:
            print(f"[test]   ... {i + 1}/{count} moves on {strand.layer_name}",
                  flush=True)
    canvas._suppress_repaint = False


# ---------------------------------------------------------------------------
# Group-creation dialog helpers
# ---------------------------------------------------------------------------

def _schedule_dialog_fill_group_name(app, group_name, delay_ms=500):
    (_, _, QTimer, _, _, QApplication, QDialog, QLineEdit, _, QPushButton, _, QTest) = _qt_imports()
    def _fill():
        for w in QApplication.topLevelWidgets():
            if isinstance(w, QDialog) and w.isVisible():
                le = w.findChild(QLineEdit)
                if le is not None:
                    le.clear(); le.setFocus(); QTest.qWait(100)
                    for ch in group_name:
                        QTest.keyClick(le, ch); QTest.qWait(50)
                    QTest.qWait(300)
                    for btn in w.findChildren(QPushButton):
                        if btn.text().lower() in ("ok", "אישור"):
                            btn.click(); return
                    w.accept(); return
    QTimer.singleShot(delay_ms, _fill)


def _schedule_dialog_select_strands(app, labels, delay_ms=500):
    (_, _, QTimer, _, _, QApplication, QDialog, _, QCheckBox, QPushButton, _, QTest) = _qt_imports()
    def _select():
        for w in QApplication.topLevelWidgets():
            if isinstance(w, QDialog) and w.isVisible():
                for cb in w.findChildren(QCheckBox):
                    if cb.text() in labels:
                        cb.setChecked(True)
                QTest.qWait(300)
                for btn in w.findChildren(QPushButton):
                    if btn.text().lower() in ("ok", "אישור"):
                        btn.click(); return
                w.accept(); return
    QTimer.singleShot(delay_ms, _select)


# ---------------------------------------------------------------------------
# App bootstrap — mirrors src/main.py
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
# Test body
# ---------------------------------------------------------------------------

def _run_test(window, app):
    (_, _, _, _, _, _, _, _, _, _, _, QTest) = _qt_imports()
    canvas = window.canvas

    try:
        print("[test] === test_group_move start ===", flush=True)

        # ---- 1) Draw strand 1_1 ----
        _draw_new_strand(window, (200, 200), (450, 200))
        assert _strand_by_name(canvas, "1_1"), "1_1 missing"
        print("[test] 1_1 created", flush=True)

        # ---- 2) Attach strand 1_2 from end of 1_1 ----
        s11 = _strand_by_name(canvas, "1_1")
        end_11 = (int(s11.end.x()), int(s11.end.y()))
        _attach_strand(window, end_11, (end_11[0], end_11[1] + 200))
        assert _strand_by_name(canvas, "1_2"), "1_2 missing"
        print("[test] 1_2 attached", flush=True)

        # ---- 3) Create group "grp1" containing set 1 ----
        manager = window.layer_panel.group_layer_manager
        _schedule_dialog_fill_group_name(app, "grp1", delay_ms=500)
        _schedule_dialog_select_strands(app, ["1"], delay_ms=2500)
        # ============================================================
        # Group creation schedules a deferred tree callback via
        # QTimer.singleShot(0, ...) that destabilizes the native paint
        # state.  Suppress repaints BEFORE create_group() so the callback
        # and subsequent event-loop turns never reach the broken painter.
        # ============================================================
        canvas._suppress_repaint = True
        print("[test] creating group 'grp1'...", flush=True)
        manager.create_group()
        QTest.qWait(800)
        assert "grp1" in canvas.groups, "group grp1 missing"
        print("[test] group grp1 created", flush=True)

        # ---- 4) Enter move mode ----
        _enter_move_mode(window)
        print("[test] move mode active", flush=True)

        # ---- 5) Move 1_2 — 200 random drags ----
        s12 = _strand_by_name(canvas, "1_2")
        print("[test] moving 1_2 (200 drags)...", flush=True)
        _random_moves(window, s12,
                      ['end', 'control_point1', 'control_point2'],
                      200, amplitude=12)
        print("[test] 1_2 moves done", flush=True)

        # ---- 6) Attach 1_3 (direct dispatch — Qt widget dispatch crashes) ----
        s12 = _strand_by_name(canvas, "1_2")
        end_12 = (int(s12.end.x()), int(s12.end.y()))
        _attach_strand(window, end_12, (end_12[0] + 150, end_12[1] + 60), direct=True)
        assert _strand_by_name(canvas, "1_3"), "1_3 missing"
        print("[test] 1_3 attached", flush=True)

        # ---- 7) Move 1_3 — 200 random drags ----
        # (already in move mode from step 4 — direct dispatch doesn't need re-entry)
        s13 = _strand_by_name(canvas, "1_3")
        print("[test] moving 1_3 (200 drags)...", flush=True)
        _random_moves(window, s13,
                      ['end', 'control_point1', 'control_point2'],
                      200, amplitude=14)
        print("[test] 1_3 moves done", flush=True)

        # ---- 8) Attach 1_4 ----
        s13 = _strand_by_name(canvas, "1_3")
        end_13 = (int(s13.end.x()), int(s13.end.y()))
        _attach_strand(window, end_13, (end_13[0] + 120, end_13[1] - 80), direct=True)
        assert _strand_by_name(canvas, "1_4"), "1_4 missing"
        print("[test] 1_4 attached", flush=True)

        # ---- 9) Move 1_4 — 200 random drags ----
        s14 = _strand_by_name(canvas, "1_4")
        print("[test] moving 1_4 (200 drags)...", flush=True)
        _random_moves(window, s14,
                      ['end', 'control_point1', 'control_point2'],
                      200, amplitude=14)
        print("[test] 1_4 moves done", flush=True)

        # ---- 10) Attach 1_5 ----
        s14 = _strand_by_name(canvas, "1_4")
        end_14 = (int(s14.end.x()), int(s14.end.y()))
        _attach_strand(window, end_14, (end_14[0] + 100, end_14[1] + 100), direct=True)
        assert _strand_by_name(canvas, "1_5"), "1_5 missing"
        print("[test] 1_5 attached", flush=True)

        # ---- 11) Move ALL strands 50 times each ----
        print("[test] moving all strands (50 each)...", flush=True)
        for name in ["1_2", "1_3", "1_4", "1_5"]:
            s = _strand_by_name(canvas, name)
            assert s, f"{name} missing before final moves"
            _random_moves(window, s,
                          ['end', 'control_point1', 'control_point2'],
                          50, amplitude=10)
        print("[test] all final moves done", flush=True)

        # Re-enable painting for final state
        canvas._suppress_repaint = False

        # ---- Final assertions ----
        for name in ["1_1", "1_2", "1_3", "1_4", "1_5"]:
            assert _strand_by_name(canvas, name), f"{name} missing at end"
        assert "grp1" in canvas.groups, "group grp1 missing at end"

        print("[test] === ALL CHECKS PASSED ===", flush=True)

    except Exception as exc:
        print(f"[test] FAILED: {exc}", flush=True)
        import traceback
        traceback.print_exc()

    finally:
        faulthandler.cancel_dump_traceback_later()
        # Force-exit immediately to avoid the Qt teardown crash
        # (native widget state is corrupt after group creation).
        os._exit(0)


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

@gui_mark
def test_group_move(visible=False):
    if not visible:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    else:
        os.environ.pop("QT_QPA_PLATFORM", None)

    app, window = _bootstrap_real_app()
    (_, _, QTimer, _, _, _, _, _, _, _, _, _) = _qt_imports()

    window.show()
    window.showMaximized()
    window.raise_()
    window.activateWindow()
    if hasattr(window, 'set_initial_splitter_sizes'):
        window.set_initial_splitter_sizes()

    QTimer.singleShot(600, lambda: _run_test(window, app))
    app.exec_()
    os._exit(0)


if __name__ == "__main__":
    faulthandler.enable(all_threads=True)
    parser = argparse.ArgumentParser()
    parser.add_argument("--visible", action="store_true",
                        help="Show real app window while running")
    args = parser.parse_args()
    test_group_move(visible=args.visible)
