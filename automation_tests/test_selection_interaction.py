"""
Automation test: launches the real app (same as src/main.py) and drives the
new exact-geometry selection with real mouse events, sweeping the strand
option matrix:

  - plain strand: body, stroke edge, side lines (shown AND hidden)
  - attached strand (drawn with real attach-mode mouse drags): start junction
    circle, end side line (shown AND hidden)
  - end circle on the parent at the junction
  - closed-connection start circle (shown, then transparent stroke -> gone)
  - hidden layer -> not hoverable/selectable
  - overlap: topmost strand wins hover and click
  - mask mode: overlap click picks topmost (old code cancelled), two clicks
    create the mask, then the mask itself is hoverable/selectable

Run visibly (watch the app interact, cursor moves along):
    python automation_tests\\test_selection_interaction.py --visible
Run headless (CI):
    python automation_tests\\test_selection_interaction.py

Screenshots of every state are saved to automation_tests/screenshots/selection/.
"""
import os
import sys
import argparse
import faulthandler

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
for p in (SRC_DIR, os.path.dirname(os.path.abspath(__file__))):
    if p not in sys.path:
        sys.path.insert(0, p)

from test_menu_strand_flow import (_bootstrap_real_app, _draw_new_strand,
                                   _attach_from_point, _strand_by_name,
                                   _qt_imports)

try:
    import pytest
    gui_mark = pytest.mark.gui
except Exception:  # pragma: no cover
    def gui_mark(func):
        return func

SHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "screenshots", "selection")

VISIBLE = False          # set from CLI; slows waits + moves the real cursor
_PASS = 0
_FAIL = 0


def _wait(ms):
    from PyQt5.QtTest import QTest
    QTest.qWait(int(ms * (2.2 if VISIBLE else 1.0)))


def _check(name, cond, detail=""):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print("[PASS] %s" % name, flush=True)
    else:
        _FAIL += 1
        print("[FAIL] %s  ::  %s" % (name, detail), flush=True)


def _shot(canvas, name):
    try:
        os.makedirs(SHOT_DIR, exist_ok=True)
        canvas.grab().save(os.path.join(SHOT_DIR, name + ".png"))
    except Exception as exc:  # screenshots are best-effort
        print("[automation] screenshot %s failed: %s" % (name, exc), flush=True)


def _hover(canvas, x, y, pause=350):
    """Send a real mouse-move to the canvas (hover), move the visible cursor
    along with it, and let the canvas repaint."""
    from PyQt5.QtCore import QPointF, QPoint, QEvent, Qt
    from PyQt5.QtGui import QMouseEvent, QCursor
    from PyQt5.QtWidgets import QApplication
    if VISIBLE:
        QCursor.setPos(canvas.mapToGlobal(QPoint(int(x), int(y))))
    ev = QMouseEvent(QEvent.MouseMove, QPointF(x, y),
                     Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    QApplication.sendEvent(canvas, ev)
    canvas.repaint()
    _wait(pause)


def _click(canvas, x, y, pause=450):
    from PyQt5.QtCore import QPoint, Qt
    from PyQt5.QtGui import QCursor
    from PyQt5.QtTest import QTest
    if VISIBLE:
        QCursor.setPos(canvas.mapToGlobal(QPoint(int(x), int(y))))
    QTest.mouseClick(canvas, Qt.LeftButton, pos=QPoint(int(x), int(y)))
    _wait(pause)


def _screen(canvas, x, y):
    """Canvas coords -> widget coords (handles any zoom/pan)."""
    from PyQt5.QtCore import QPointF
    p = canvas.canvas_to_screen(QPointF(x, y))
    return p.x(), p.y()


def _hovered(canvas):
    return canvas.select_mode.hovered_strand


def _hover_at_canvas(canvas, cx, cy, pause=350):
    _hover(canvas, *_screen(canvas, cx, cy), pause=pause)
    return _hovered(canvas)


def _name(strand):
    return getattr(strand, 'layer_name', None) if strand is not None else None


def _run_automation(window, app):
    from PyQt5.QtGui import QColor
    from masked_strand import MaskedStrand

    try:
        canvas = window.canvas

        # ============================================================ setup
        print("[automation] drawing strand 1_1 (horizontal)...", flush=True)
        _draw_new_strand(window, start_xy=(160, 220), end_xy=(460, 220), set_number=1)
        s1 = _strand_by_name(canvas, "1_1")
        _check("strand 1_1 drawn", s1 is not None)
        if s1 is None:
            return

        y0 = s1.start.y()
        half1 = (s1.width + 2 * s1.stroke_width) / 2
        x_mid = (s1.start.x() + s1.end.x()) / 2

        print("[automation] switching to select mode...", flush=True)
        window.set_select_mode()
        _wait(300)

        # ============================================ 1) plain strand basics
        got = _hover_at_canvas(canvas, x_mid, y0)
        _check("plain: hover body highlights 1_1", got is s1, "hovered: %r" % _name(got))
        _shot(canvas, "01_plain_body")

        got = _hover_at_canvas(canvas, x_mid, y0 + half1 - 2)
        _check("plain: hover stroke edge highlights 1_1", got is s1, "hovered: %r" % _name(got))
        _shot(canvas, "02_plain_stroke_edge")

        got = _hover_at_canvas(canvas, x_mid, y0 + half1 + 4)
        _check("plain: just outside the stroke is empty", got is None, "hovered: %r" % _name(got))

        # ------------------------------------------- side line shown/hidden
        sideline_x = s1.start.x() - s1.stroke_width / 2
        got = _hover_at_canvas(canvas, sideline_x, y0)
        _check("side line shown: hover past the cap highlights 1_1",
               got is s1, "hovered: %r" % _name(got))
        _shot(canvas, "03_side_line_shown")

        got = _hover_at_canvas(canvas, s1.start.x() - s1.stroke_width - 3, y0)
        _check("side line shown: past the band is empty", got is None, "hovered: %r" % _name(got))

        print("[automation] hiding 1_1 side lines...", flush=True)
        s1.start_line_visible = False
        s1.end_line_visible = False
        canvas.update()
        _wait(400)
        got = _hover_at_canvas(canvas, sideline_x, y0)
        _check("side line hidden: past the cap is empty", got is None, "hovered: %r" % _name(got))
        got = _hover_at_canvas(canvas, x_mid, y0)
        _check("side line hidden: body still hoverable", got is s1, "hovered: %r" % _name(got))
        _shot(canvas, "04_side_line_hidden")
        s1.start_line_visible = True
        s1.end_line_visible = True
        canvas.update()

        # ========================================= 2) attached strand cases
        print("[automation] attaching 1_2 at the end of 1_1 (real drag)...", flush=True)
        jx, jy = s1.end.x(), s1.end.y()
        _attach_from_point(window, attach_xy=(int(jx), int(jy)),
                           end_xy=(int(jx), int(jy) + 180))
        s12 = _strand_by_name(canvas, "1_2")
        _check("attached strand 1_2 created", s12 is not None)

        window.set_select_mode()
        _wait(300)

        if s12 is not None:
            # junction circle: diagonally beyond both flat caps (15,15 -> ~21px
            # from the junction, inside the 27px circle radius)
            got = _hover_at_canvas(canvas, jx + 15, jy - 15)
            _check("junction circle: hover beyond the flat caps highlights a strand",
                   got in (s1, s12), "hovered: %r" % _name(got))
            _shot(canvas, "05_junction_circle")

            # attached strand's end side line
            s12_end_y = s12.end.y()
            got = _hover_at_canvas(canvas, s12.end.x(), s12_end_y + s12.stroke_width / 2)
            _check("attached end side line: hover past the cap highlights 1_2",
                   got is s12, "hovered: %r" % _name(got))
            _shot(canvas, "06_attached_end_side_line")

            print("[automation] hiding 1_2 end side line...", flush=True)
            s12.end_line_visible = False
            canvas.update()
            _wait(400)
            got = _hover_at_canvas(canvas, s12.end.x(), s12_end_y + s12.stroke_width / 2)
            _check("attached end side line hidden: past the cap is empty",
                   got is None, "hovered: %r" % _name(got))
            _shot(canvas, "07_attached_side_line_hidden")
            s12.end_line_visible = True
            canvas.update()

            # ---------------- fold / unfold start edge ----------------
            # Folded (default): 1_2's start circle is stroked, radius 27.
            # 25px behind the junction is inside it -> topmost 1_2 wins hover.
            half12_in = s12.width / 2          # inner fill radius (23)
            got = _hover_at_canvas(canvas, jx, jy - (half12_in + 2))
            _check("folded start edge: hover 25px behind the junction highlights 1_2",
                   got is s12, "hovered: %r" % _name(got))

            # Unfold (same as the layer menu's 'Unfold Start Edge'): stroke
            # becomes transparent but the inner fill circle is still drawn.
            print("[automation] unfolding 1_2 start edge...", flush=True)
            s12.start_circle_stroke_color = QColor(0, 0, 0, 0)
            canvas.update()
            _wait(400)
            got = _hover_at_canvas(canvas, jx, jy - (half12_in - 3))
            _check("unfolded start edge: fill circle (no stroke) still hovers as 1_2",
                   got is s12, "hovered: %r" % _name(got))
            _shot(canvas, "08a_unfolded_fill_circle")
            got = _hover_at_canvas(canvas, jx, jy - (half12_in + 2))
            _check("unfolded start edge: hidden stroke ring falls through to 1_1",
                   got is s1, "hovered: %r" % _name(got))

            # Fold back: the stroke ring is hoverable again.
            print("[automation] folding 1_2 start edge back...", flush=True)
            s12.start_circle_stroke_color = QColor(0, 0, 0, 255)
            canvas.update()
            _wait(400)
            got = _hover_at_canvas(canvas, jx, jy - (half12_in + 2))
            _check("refolded start edge: stroke ring hovers as 1_2 again",
                   got is s12, "hovered: %r" % _name(got))
            _shot(canvas, "08b_refolded_circle")

            # hidden layer: not hoverable, hover falls through to nothing
            print("[automation] hiding layer 1_2...", flush=True)
            s12.is_hidden = True
            canvas.update()
            _wait(400)
            mid12_y = (s12.start.y() + s12.end.y()) / 2
            got = _hover_at_canvas(canvas, s12.start.x(), mid12_y)
            _check("hidden layer: hover over hidden 1_2 is empty",
                   got is None, "hovered: %r" % _name(got))
            _shot(canvas, "08_hidden_layer")
            s12.is_hidden = False
            canvas.update()

        # =========================== 3) circle options on an isolated strand
        print("[automation] drawing strand 2_1 (vertical, crossing 1_1)...", flush=True)
        x0 = int(x_mid)
        _draw_new_strand(window, start_xy=(x0, 100), end_xy=(x0, 360), set_number=2)
        s2 = _strand_by_name(canvas, "2_1")
        _check("strand 2_1 drawn", s2 is not None)

        window.set_select_mode()
        _wait(300)

        if s2 is not None:
            x0 = s2.start.x()
            top_y = min(s2.start.y(), s2.end.y())

            # no circle, no junction: nothing renders past the cap except side line
            got = _hover_at_canvas(canvas, x0, top_y - s2.stroke_width - 3)
            _check("no circle: past the side line band is empty",
                   got is None, "hovered: %r" % _name(got))

            # closed-connection circle appears -> hoverable past the cap
            print("[automation] enabling closed-connection start circle on 2_1...", flush=True)
            s2.has_circles[0] = True
            s2.closed_connections = [True, False]
            canvas.update()
            _wait(400)
            got = _hover_at_canvas(canvas, x0, top_y - 20)
            _check("closed-connection circle: hover 20px past the cap highlights 2_1",
                   got is s2, "hovered: %r" % _name(got))
            _shot(canvas, "09_closed_connection_circle")

            # transparent circle stroke -> circle gone, nothing past the cap
            print("[automation] making 2_1 start circle transparent...", flush=True)
            s2.start_circle_stroke_color = QColor(0, 0, 0, 0)
            canvas.update()
            _wait(400)
            got = _hover_at_canvas(canvas, x0, top_y - 20)
            _check("transparent circle: hover past the cap is empty",
                   got is None, "hovered: %r" % _name(got))
            _shot(canvas, "10_transparent_circle")

            # restore plain end
            s2.start_circle_stroke_color = QColor(0, 0, 0, 255)
            s2.has_circles[0] = False
            s2.closed_connections = [False, False]
            canvas.update()

            # ============================== 4) overlap: topmost wins hover+click
            got = _hover_at_canvas(canvas, x0, y0)
            _check("overlap: hover on the crossing highlights topmost 2_1",
                   got is s2, "hovered: %r" % _name(got))
            _shot(canvas, "11_overlap_hover_topmost")

            _click(canvas, *_screen(canvas, x0, y0))
            _check("overlap: click on the crossing selects topmost 2_1",
                   s2.is_selected and not s1.is_selected,
                   "selected flags: 1_1=%s 2_1=%s" % (s1.is_selected, s2.is_selected))
            _shot(canvas, "12_overlap_click_selected")

            # ====================================================== 5) mask mode
            print("[automation] switching to mask mode...", flush=True)
            window.set_mask_mode()
            _wait(300)

            # overlap click: old code cancelled here; now picks topmost 2_1
            _click(canvas, *_screen(canvas, x0, y0))
            _check("mask mode: overlap click picks topmost strand (2_1)",
                   canvas.mask_mode.selected_strands == [s2],
                   "selected: %s" % [st.layer_name for st in canvas.mask_mode.selected_strands])
            _shot(canvas, "13_mask_first_pick")

            x_on_1_only = max(s1.start.x() + 20, x0 - 120)
            _click(canvas, *_screen(canvas, x_on_1_only, y0))
            _wait(800)
            mask = next((st for st in canvas.strands if isinstance(st, MaskedStrand)), None)
            _check("mask 2_1_1_1 created via two clicks",
                   mask is not None and mask.layer_name == "2_1_1_1",
                   "mask: %r" % _name(mask))
            _shot(canvas, "14_mask_created")

            # ================================ 6) the mask itself is selectable
            if mask is not None:
                window.set_select_mode()
                _wait(300)

                got = _hover_at_canvas(canvas, x0, y0)
                _check("hover on mask center highlights the mask",
                       got is mask, "hovered: %r" % _name(got))
                _shot(canvas, "15_hover_mask")

                _click(canvas, *_screen(canvas, x0, y0))
                _check("click on mask center selects the mask",
                       mask.is_selected, "mask.is_selected=%s" % mask.is_selected)
                _shot(canvas, "16_click_mask_selected")

        print("\n[automation] RESULT: %d passed, %d failed" % (_PASS, _FAIL), flush=True)

    except Exception as exc:
        print("[automation] FAILED with exception: %s" % exc, flush=True)
        import traceback
        traceback.print_exc()
        globals()['_FAIL'] += 1

    finally:
        faulthandler.cancel_dump_traceback_later()
        from PyQt5.QtCore import QTimer
        # In visible mode leave the final state on screen for a moment
        QTimer.singleShot(2500 if VISIBLE else 0, app.quit)


@gui_mark
def test_selection_interaction(visible=False):
    """Launch the real app and drive selection with real mouse events."""
    global VISIBLE
    VISIBLE = visible
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

    QTimer.singleShot(600, lambda: _run_automation(window, app))
    app.exec_()
    os._exit(1 if _FAIL else 0)


if __name__ == "__main__":
    faulthandler.enable(all_threads=True)
    parser = argparse.ArgumentParser()
    parser.add_argument("--visible", action="store_true",
                        help="Show the real app window while the test interacts")
    args = parser.parse_args()
    test_selection_interaction(visible=args.visible)
