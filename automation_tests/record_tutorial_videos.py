r"""Record beginner tutorial videos by driving the REAL app with mouse events.

Builds on test_menu_strand_flow.py: launches the actual application offscreen,
performs scripted interactions (drawing strands, attaching, masking, closing a
knot), and records every frame with a visible animated mouse cursor + numbered
step captions, then encodes the frames to mp4/mov with ffmpeg.

Usage:
    python automation_tests\record_tutorial_videos.py --scenario settings
    python automation_tests\record_tutorial_videos.py --scenario buttons
    python automation_tests\record_tutorial_videos.py --scenario mask
    python automation_tests\record_tutorial_videos.py --scenario knot
    python automation_tests\record_tutorial_videos.py --scenario mask --test
        (--test stops after the first two steps: quick clip to check the look)

Scenario -> tutorial mapping: settings=1, buttons=2, mask=3, knot=4.
Output goes to automation_tests\recordings\<scenario>\ (frames + .mp4).
"""
import os
import sys
import time
import math
import shutil
import argparse
import subprocess
import faulthandler

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
for p in (SRC_DIR, os.path.dirname(os.path.abspath(__file__))):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# The offscreen platform ships no fonts; use the Windows font directory so
# UI labels and captions render.
os.environ.setdefault("QT_QPA_FONTDIR", r"C:\Windows\Fonts")

# Sandbox APPDATA: recordings start from clean default settings (English,
# default theme), and the settings tutorial's OK button cannot overwrite the
# user's real OpenStrandStudio settings.
_APPDATA_SANDBOX = os.path.join(os.environ.get("TEMP", "."),
                                "oss_tutorial_recording_appdata")
shutil.rmtree(_APPDATA_SANDBOX, ignore_errors=True)
os.makedirs(_APPDATA_SANDBOX, exist_ok=True)
os.environ["APPDATA"] = _APPDATA_SANDBOX

from test_menu_strand_flow import _bootstrap_real_app, _strand_by_name

OUT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recordings")

FPS = 30
WINDOW_W, WINDOW_H = 1920, 1080


# ---------------------------------------------------------------------------
# Recorder: timer-driven frame capture with cursor + caption overlay
# ---------------------------------------------------------------------------

class Recorder:
    def __init__(self, window, out_dir, fps=FPS):
        from PyQt5.QtCore import QTimer, QPoint
        self.window = window
        self.fps = fps
        self.frames_dir = os.path.join(out_dir, "frames")
        if os.path.isdir(self.frames_dir):
            shutil.rmtree(self.frames_dir)
        os.makedirs(self.frames_dir, exist_ok=True)
        self.n = 0
        self.cursor = QPoint(window.width() // 2, window.height() // 2)
        self.click_frames_left = 0
        self.caption_text = ""
        self.t0 = None
        self.elapsed = 0.0
        self.timer = QTimer()
        self.timer.setInterval(int(1000 / fps))
        self.timer.timeout.connect(self._capture)
        from concurrent.futures import ThreadPoolExecutor
        self._save_pool = ThreadPoolExecutor(max_workers=2)

    # -- lifecycle ---------------------------------------------------------
    def start(self):
        self.t0 = time.time()
        self.timer.start()

    def stop(self):
        self.timer.stop()
        self.elapsed = time.time() - self.t0
        self._save_pool.shutdown(wait=True)

    # -- state used by the overlay ------------------------------------------
    def set_cursor(self, x, y):
        from PyQt5.QtCore import QPoint
        self.cursor = QPoint(int(x), int(y))

    def click_effect(self):
        """Show a click ripple around the cursor for ~0.4s."""
        self.click_frames_left = int(self.fps * 0.4)

    def caption(self, text):
        self.caption_text = text

    # -- frame capture -------------------------------------------------------
    def _capture(self):
        from PyQt5.QtCore import QPoint, Qt
        from PyQt5.QtGui import QPainter
        from PyQt5.QtWidgets import QApplication, QMenu, QDialog

        pm = self.window.grab()
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.Antialiasing)

        # Composite popups (menus, dialogs): they are separate top-level
        # windows so window.grab() does not include them.
        win_origin = self.window.mapToGlobal(QPoint(0, 0))
        for w in QApplication.topLevelWidgets():
            if w is self.window or not w.isVisible():
                continue
            if isinstance(w, (QMenu, QDialog)) or \
                    w.windowType() in (Qt.Popup, Qt.ToolTip, Qt.Tool, Qt.Sheet):
                try:
                    off = w.mapToGlobal(QPoint(0, 0)) - win_origin
                    painter.drawPixmap(off, w.grab())
                except Exception:
                    pass

        self._draw_caption(painter, pm.width(), pm.height())
        self._draw_cursor(painter)
        painter.end()

        self._save_jpeg(pm, os.path.join(self.frames_dir, f"{self.n:05d}.jpg"))
        self.n += 1
        if self.click_frames_left > 0:
            self.click_frames_left -= 1

    def _save_jpeg(self, pm, path):
        # This PyQt5 build has no JPEG image plugin; encode via PIL instead
        # (PNG saving is too slow for continuous capture). The encode runs on
        # a worker thread so the capture tick only pays for grab + convert.
        from PyQt5.QtGui import QImage
        img = pm.toImage().convertToFormat(QImage.Format_RGB888)
        ptr = img.constBits()
        ptr.setsize(img.byteCount())
        data = bytes(ptr)
        w, h, stride = img.width(), img.height(), img.bytesPerLine()

        def _encode():
            from PIL import Image
            Image.frombytes("RGB", (w, h), data, "raw", "RGB", stride, 1) \
                .save(path, quality=90)

        self._save_pool.submit(_encode)

    def _draw_cursor(self, painter):
        from PyQt5.QtCore import QPointF
        from PyQt5.QtGui import QPolygonF, QPen, QColor, QBrush

        x, y = self.cursor.x(), self.cursor.y()

        # Click ripple (behind the arrow)
        if self.click_frames_left > 0:
            total = int(self.fps * 0.4)
            progress = 1.0 - self.click_frames_left / total
            radius = 10 + 22 * progress
            alpha = int(230 * (1.0 - progress))
            pen = QPen(QColor(255, 140, 0, alpha), 4)
            painter.setPen(pen)
            painter.setBrush(QBrush())
            painter.drawEllipse(QPointF(x, y), radius, radius)

        # Arrow pointer, ~1.8x normal size: white fill, black outline
        s = 1.8
        pts = [(0, 0), (0, 16.5), (4.2, 12.8), (7.2, 19.5),
               (10.2, 18.2), (7.2, 11.5), (12.5, 11.5)]
        poly = QPolygonF([QPointF(x + px * s, y + py * s) for px, py in pts])
        painter.setPen(QPen(QColor(0, 0, 0), 2.4))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawPolygon(poly)

    def _draw_caption(self, painter, w, h):
        from PyQt5.QtCore import Qt, QRectF
        from PyQt5.QtGui import QFont, QColor, QPen, QBrush, QFontMetrics

        if not self.caption_text:
            return
        font = QFont("Segoe UI", 22, QFont.DemiBold)
        painter.setFont(font)
        fm = QFontMetrics(font)
        text_w = fm.horizontalAdvance(self.caption_text)
        pad_x, pad_y = 34, 16
        box_w = min(text_w + 2 * pad_x, w - 80)
        box_h = fm.height() + 2 * pad_y
        rect = QRectF((w - box_w) / 2, h - box_h - 36, box_w, box_h)

        painter.setPen(QPen(QColor(255, 255, 255, 50), 1))
        painter.setBrush(QBrush(QColor(20, 20, 25, 215)))
        painter.drawRoundedRect(rect, 14, 14)
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.drawText(rect, Qt.AlignCenter, self.caption_text)


# ---------------------------------------------------------------------------
# Virtual mouse: animates the drawn cursor and sends real Qt mouse events
# ---------------------------------------------------------------------------

class Mouse:
    def __init__(self, recorder, window):
        self.rec = recorder
        self.window = window

    def _wait(self, ms):
        from PyQt5.QtTest import QTest
        QTest.qWait(int(ms))

    def _widget_to_window(self, widget, pos):
        # Map via global coordinates: works for widgets in other top-level
        # windows (dialogs, popups), which mapTo() cannot handle.
        from PyQt5.QtCore import QPoint
        gp = widget.mapToGlobal(QPoint(int(pos[0]), int(pos[1])))
        return gp - self.window.mapToGlobal(QPoint(0, 0))

    def glide_to_window_pos(self, wx, wy, dur_ms=650):
        """Animate the drawn cursor to a window-coordinate position."""
        from PyQt5.QtCore import QPoint
        start = QPoint(self.rec.cursor)
        steps = max(2, int(dur_ms / (1000 / self.rec.fps)))
        for i in range(1, steps + 1):
            t = i / steps
            e = t * t * (3 - 2 * t)  # smoothstep for a natural glide
            x = start.x() + (wx - start.x()) * e
            y = start.y() + (wy - start.y()) * e
            self.rec.set_cursor(x, y)
            self._wait(1000 / self.rec.fps)

    def glide_to_widget(self, widget, pos=None, dur_ms=650):
        if pos is None:
            c = widget.rect().center()
            pos = (c.x(), c.y())
        wp = self._widget_to_window(widget, pos)
        self.glide_to_window_pos(wp.x(), wp.y(), dur_ms)
        return pos

    def click_widget(self, widget, pos=None, dur_ms=650):
        """Glide to a widget and left-click it (real QTest event)."""
        from PyQt5.QtCore import QPoint, Qt
        from PyQt5.QtTest import QTest
        pos = self.glide_to_widget(widget, pos, dur_ms)
        self._wait(150)
        self.rec.click_effect()
        QTest.mouseClick(widget, Qt.LeftButton,
                         pos=QPoint(int(pos[0]), int(pos[1])))
        self._wait(450)

    def canvas_press(self, canvas, x, y):
        from PyQt5.QtCore import QPoint, Qt
        from PyQt5.QtTest import QTest
        wp = self._widget_to_window(canvas, (x, y))
        self.glide_to_window_pos(wp.x(), wp.y())
        self._wait(150)
        self.rec.click_effect()
        QTest.mousePress(canvas, Qt.LeftButton, pos=QPoint(int(x), int(y)))
        self._wait(300)

    def _move_held(self, canvas, x, y):
        from PyQt5.QtCore import QPointF, QEvent, Qt
        from PyQt5.QtGui import QMouseEvent
        from PyQt5.QtWidgets import QApplication
        ev = QMouseEvent(QEvent.MouseMove, QPointF(x, y),
                         Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        QApplication.sendEvent(canvas, ev)

    def canvas_drag(self, canvas, start_xy, end_xy, dur_ms=1400):
        """Press at start, drag to end in steps, release (real events)."""
        from PyQt5.QtCore import QPoint, Qt
        from PyQt5.QtTest import QTest
        self.canvas_press(canvas, *start_xy)
        steps = max(2, int(dur_ms / (1000 / self.rec.fps)))
        for i in range(1, steps + 1):
            t = i / steps
            e = t * t * (3 - 2 * t)
            x = start_xy[0] + (end_xy[0] - start_xy[0]) * e
            y = start_xy[1] + (end_xy[1] - start_xy[1]) * e
            self._move_held(canvas, x, y)
            wp = self._widget_to_window(canvas, (x, y))
            self.rec.set_cursor(wp.x(), wp.y())
            self._wait(1000 / self.rec.fps)
        self._wait(250)
        QTest.mouseRelease(canvas, Qt.LeftButton,
                           pos=QPoint(int(end_xy[0]), int(end_xy[1])))
        self._wait(500)

    def canvas_click(self, canvas, x, y):
        from PyQt5.QtCore import QPoint, Qt
        from PyQt5.QtTest import QTest
        wp = self._widget_to_window(canvas, (x, y))
        self.glide_to_window_pos(wp.x(), wp.y())
        self._wait(150)
        self.rec.click_effect()
        QTest.mouseClick(canvas, Qt.LeftButton, pos=QPoint(int(x), int(y)))
        self._wait(450)


# ---------------------------------------------------------------------------
# Shared scenario helpers
# ---------------------------------------------------------------------------

def _layer_button(window, name):
    for btn in window.layer_panel.layer_buttons:
        if btn and btn.text() == name:
            return btn
    return None


def _point_along(strand, t):
    """A point at fraction t along a (straight) strand segment."""
    x = strand.start.x() + (strand.end.x() - strand.start.x()) * t
    y = strand.start.y() + (strand.end.y() - strand.start.y()) * t
    return (int(x), int(y))


def _hold(ms):
    from PyQt5.QtTest import QTest
    QTest.qWait(int(ms))


def _draw_first_strand(window, mouse, rec, start, end, step_label):
    """Click the real 'New Strand' button, then drag on the canvas."""
    rec.caption(step_label)
    mouse.click_widget(window.layer_panel.add_new_strand_button)
    _hold(400)
    mouse.canvas_drag(window.canvas, start, end)
    _hold(600)


def _attach_strand(window, mouse, rec, from_xy, to_xy, step_label,
                   click_attach=True):
    rec.caption(step_label)
    if click_attach:
        mouse.click_widget(window.attach_button)
        _hold(400)
    mouse.canvas_drag(window.canvas, from_xy, to_xy)
    _hold(600)


def _combo_select(window, mouse, rec, combo, match_data):
    """Glide to a QComboBox and switch it to the matching item.

    The selection itself is programmatic: on the offscreen platform the
    popup list is clamped to a tiny virtual screen and closes when moved,
    so clicking it is unreliable. The viewer sees the cursor click the
    dropdown and the value change."""
    idx = None
    for i in range(combo.count()):
        if str(combo.itemData(i)).lower() == match_data.lower():
            idx = i
            break
    if idx is None:
        for i in range(combo.count()):
            if match_data.lower() in combo.itemText(i).lower():
                idx = i
                break
    assert idx is not None, f"combo item matching {match_data!r} not found"
    mouse.glide_to_widget(combo)
    _hold(250)
    rec.click_effect()
    _hold(350)
    combo.hidePopup()
    combo.setCurrentIndex(idx)
    _hold(800)


def _click_list_row(window, mouse, rec, list_widget, row):
    """Glide to and click a QListWidget row (real viewport click)."""
    item = list_widget.item(row)
    r = list_widget.visualItemRect(item)
    mouse.click_widget(list_widget.viewport(), pos=(r.center().x(),
                                                    r.center().y()))


def _right_click_hold(mouse, rec, widget, hold_ms=2000):
    """Press-and-hold right-click on a widget (tooltips show while held)."""
    from PyQt5.QtCore import QPoint, Qt
    from PyQt5.QtTest import QTest
    c = widget.rect().center()
    mouse.glide_to_widget(widget)
    _hold(200)
    rec.click_effect()
    QTest.mousePress(widget, Qt.RightButton, pos=QPoint(c.x(), c.y()))
    _hold(hold_ms)
    QTest.mouseRelease(widget, Qt.RightButton, pos=QPoint(c.x(), c.y()))
    _hold(400)


# ---------------------------------------------------------------------------
# Scenario: tutorial_1 — settings: themes and language
# ---------------------------------------------------------------------------

def _open_settings(window, mouse, rec):
    """Click the gear button and center the (non-modal) settings dialog."""
    from PyQt5.QtCore import QPoint
    mouse.click_widget(window.settings_button)
    _hold(700)
    dlg = window._settings_dialog
    assert dlg is not None and dlg.isVisible(), "settings dialog not shown"
    # Center the dialog over the main window (offscreen placement puts it at
    # the tiny virtual screen's origin otherwise).
    wc = window.mapToGlobal(QPoint(window.width() // 2, window.height() // 2))
    dlg.move(wc.x() - dlg.width() // 2, wc.y() - dlg.height() // 2)
    _hold(700)
    return dlg


def scenario_settings(window, app, rec, mouse, test_only=False):
    rec.caption("Tutorial: themes and language")
    _hold(2200)

    # Step 1: open the settings dialog with the gear button
    rec.caption("1. Click the Settings (gear) button")
    dlg = _open_settings(window, mouse, rec)
    _hold(400)

    # Step 2: pick the dark theme
    rec.caption("2. Open the theme dropdown and pick 'Dark'")
    _combo_select(window, mouse, rec, dlg.theme_combobox, "dark")
    _hold(400)

    if test_only:
        rec.caption("Test clip: cursor + captions check")
        _hold(1500)
        return

    # Step 3: apply — OK closes the dialog and the whole app switches theme
    rec.caption("3. Click OK - the whole app switches theme")
    mouse.click_widget(dlg.apply_button)
    _hold(2000)

    # Step 4: reopen settings, go to the language category (row 3)
    rec.caption("4. Open Settings again and pick 'Change Language'")
    dlg = _open_settings(window, mouse, rec)
    _click_list_row(window, mouse, rec, dlg.categories_list, 3)
    _hold(800)

    # Step 5: switch to French and apply
    rec.caption("5. Pick a language, then OK - the interface updates")
    _combo_select(window, mouse, rec, dlg.language_combobox, "fr")
    mouse.click_widget(dlg.language_ok_button)
    _hold(2400)

    # Step 6: switch back to English the same way
    rec.caption("6. Switch back anytime - settings are saved automatically")
    dlg = _open_settings(window, mouse, rec)
    _combo_select(window, mouse, rec, dlg.language_combobox, "en")
    mouse.click_widget(dlg.language_ok_button)
    _hold(1600)

    rec.caption("That's it - make OpenStrand Studio yours!")
    _hold(2200)


# ---------------------------------------------------------------------------
# Scenario: tutorial_2 — right-click layer panel buttons for descriptions
# ---------------------------------------------------------------------------

def scenario_buttons(window, app, rec, mouse, test_only=False):
    panel = window.layer_panel

    rec.caption("Tutorial: what do the layer panel buttons do?")
    _hold(2200)

    rec.caption("1. Hold right-click on any button to see its description")
    _right_click_hold(mouse, rec, panel.reset_states_button, hold_ms=2400)

    rec.caption("2. Release to hide it - try the zoom buttons too")
    _right_click_hold(mouse, rec, panel.zoom_in_button, hold_ms=2200)

    if test_only:
        rec.caption("Test clip: cursor + captions check")
        _hold(1500)
        return

    _right_click_hold(mouse, rec, panel.zoom_out_button, hold_ms=2000)

    rec.caption("3. The hand button pans the canvas view")
    _right_click_hold(mouse, rec, panel.pan_button, hold_ms=2200)

    rec.caption("4. Refresh redraws all the layers")
    _right_click_hold(mouse, rec, panel.refresh_button, hold_ms=2200)

    rec.caption("5. The target button centers your strands")
    _right_click_hold(mouse, rec, panel.center_strands_button, hold_ms=2200)

    rec.caption("Right-click any button you are unsure about - done!")
    _hold(2400)


# ---------------------------------------------------------------------------
# Scenario: tutorial_3 — first strands + mask (2_2 goes under 1_1)
# ---------------------------------------------------------------------------

def scenario_mask(window, app, rec, mouse, test_only=False):
    canvas = window.canvas

    rec.caption("Tutorial: crossing strands with a mask")
    _hold(2200)

    # Step 1: strand 1_1
    _draw_first_strand(window, mouse, rec, (520, 300), (980, 300),
                       "1. Click 'New Strand', then drag on the canvas to draw strand 1_1")
    s11 = _strand_by_name(canvas, "1_1")
    assert s11 is not None, "1_1 missing"

    # Step 2: attach 1_2 to the end of 1_1
    end11 = (int(s11.end.x()), int(s11.end.y()))
    _attach_strand(window, mouse, rec, end11, (end11[0], end11[1] + 300),
                   "2. Click 'Attach', then drag from the end of 1_1 to add strand 1_2")
    assert _strand_by_name(canvas, "1_2") is not None, "1_2 missing"

    if test_only:
        rec.caption("Test clip: cursor + captions check")
        _hold(1500)
        return

    # Step 3: new set — strand 2_1 (below 1_1, pointing up toward it)
    _draw_first_strand(window, mouse, rec, (620, 640), (700, 480),
                       "3. Click 'New Strand' again to start set 2 - draw strand 2_1")
    s21 = _strand_by_name(canvas, "2_1")
    assert s21 is not None, "2_1 missing"

    # Step 4: attach 2_2 so it crosses over 1_1
    end21 = (int(s21.end.x()), int(s21.end.y()))
    _attach_strand(window, mouse, rec, end21, (end21[0] + 60, 140),
                   "4. Click 'Attach' and add strand 2_2 - it crosses over strand 1_1")
    s22 = _strand_by_name(canvas, "2_2")
    assert s22 is not None, "2_2 missing"
    _hold(800)

    # Step 5+6: mask mode — click 1_1 (over) then 2_2 (under)
    rec.caption("5. Click 'Mask', then click strand 1_1 - it will stay on top")
    mouse.click_widget(window.mask_button)
    _hold(500)
    mouse.canvas_click(canvas, *_point_along(_strand_by_name(canvas, "1_1"), 0.25))
    _hold(700)

    rec.caption("6. Now click strand 2_2 - it goes under strand 1_1")
    mouse.canvas_click(canvas, *_point_along(_strand_by_name(canvas, "2_2"), 0.75))
    _hold(1000)

    masked = _strand_by_name(canvas, "1_1_2_2")
    assert masked is not None, "mask 1_1_2_2 missing"

    # Step 7: show the new mask layer in the panel
    rec.caption("7. A mask layer '1_1_2_2' appears in the layer panel - done!")
    btn = _layer_button(window, "1_1_2_2")
    if btn is not None:
        mouse.glide_to_widget(btn, dur_ms=900)
    _hold(2600)


# ---------------------------------------------------------------------------
# Scenario: tutorial_4 — closed knot
# ---------------------------------------------------------------------------

def scenario_knot(window, app, rec, mouse, test_only=False):
    from PyQt5.QtCore import QTimer, QPoint, Qt
    from PyQt5.QtTest import QTest
    canvas = window.canvas

    rec.caption("Tutorial: closing a knot")
    _hold(2200)

    # Step 1: strand 1_1
    _draw_first_strand(window, mouse, rec, (620, 300), (980, 300),
                       "1. Click 'New Strand' and drag to draw strand 1_1")
    s11 = _strand_by_name(canvas, "1_1")
    assert s11 is not None, "1_1 missing"

    # Step 2: attach 1_2 from the end, angling down-left
    end11 = (int(s11.end.x()), int(s11.end.y()))
    _attach_strand(window, mouse, rec, end11, (end11[0] - 80, end11[1] + 320),
                   "2. Click 'Attach' and add strand 1_2 from one end of 1_1")
    s12 = _strand_by_name(canvas, "1_2")
    assert s12 is not None, "1_2 missing"

    if test_only:
        rec.caption("Test clip: cursor + captions check")
        _hold(1500)
        return

    # Step 3: attach 1_3 from the start, angling down-right, so the two
    # free ends point toward each other
    start11 = (int(s11.start.x()), int(s11.start.y()))
    _attach_strand(window, mouse, rec, start11,
                   (start11[0] + 80, start11[1] + 320),
                   "3. Attach strand 1_3 from the other end of 1_1",
                   click_attach=False)
    s13 = _strand_by_name(canvas, "1_3")
    assert s13 is not None, "1_3 missing"
    _hold(800)

    # Step 4: right-click layer 1_2 -> "Close the Knot"
    rec.caption("4. Right-click layer '1_2' and choose 'Close the Knot'")
    btn = _layer_button(window, "1_2")
    assert btn is not None, "layer button 1_2 missing"
    mouse.glide_to_widget(btn, dur_ms=900)
    _hold(300)
    rec.click_effect()

    def _click_menu_item():
        from PyQt5.QtWidgets import QApplication, QMenu
        menu = None
        for w in QApplication.topLevelWidgets():
            if isinstance(w, QMenu) and w.isVisible():
                menu = w
                break
        if menu is None:
            print("[record] WARNING: context menu not found", flush=True)
            return
        # Qt clamps popups to the offscreen platform's 800x600 virtual
        # screen, which puts the menu far from the button that was
        # right-clicked. Move it next to the button so the video makes sense.
        btn_g = btn.mapToGlobal(QPoint(0, btn.height() // 2))
        mx = btn_g.x() - menu.width() - 10
        my = min(max(btn_g.y() - menu.height() // 2, 40),
                 window.mapToGlobal(QPoint(0, window.height())).y()
                 - menu.height() - 40)
        menu.move(mx, my)
        _hold(150)
        from PyQt5.QtWidgets import QWidgetAction
        def _act_text(act):
            if isinstance(act, QWidgetAction) and act.defaultWidget() is not None:
                w = act.defaultWidget()
                if hasattr(w, "text"):
                    return w.text()
            return act.text()

        target = None
        for act in menu.actions():
            if "knot" in _act_text(act).lower():
                target = act
                break
        if target is None:
            print("[record] WARNING: knot action not found:",
                  [_act_text(a) for a in menu.actions()], flush=True)
            menu.close()
            return
        r = menu.actionGeometry(target)
        wp = menu.mapToGlobal(r.center()) - window.mapToGlobal(QPoint(0, 0))
        mouse.glide_to_window_pos(wp.x(), wp.y(), dur_ms=800)
        _hold(500)
        rec.click_effect()
        # Menu items are QWidgetActions whose labels swallow mouse events, so
        # trigger the action directly after the cursor lands on it.
        target.trigger()
        _hold(200)
        menu.close()

    # show_context_menu blocks in menu.exec_(), so schedule the item click
    QTimer.singleShot(900, _click_menu_item)
    btn.customContextMenuRequested.emit(btn.rect().center())
    _hold(800)

    # Verify the knot closed (both ends connected)
    s12 = _strand_by_name(canvas, "1_2")
    knot_ok = bool(getattr(s12, "knot_connections", None)) or \
        bool(getattr(s12, "closed_connections", [False, False])[1])
    assert knot_ok, "knot did not close"

    rec.caption("5. The free ends snap together - you made a closed knot!")
    s12 = _strand_by_name(canvas, "1_2")
    wp = mouse._widget_to_window(canvas, (int(s12.end.x()), int(s12.end.y())))
    mouse.glide_to_window_pos(wp.x(), wp.y(), dur_ms=900)
    _hold(2600)


# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------

def encode(frames_dir, n_frames, elapsed_s, out_base):
    """Encode captured frames to H.264 mp4 (+ mov) at the real average fps."""
    fps = max(5.0, n_frames / max(elapsed_s, 0.001))
    for ext in (".mp4", ".mov"):
        out = out_base + ext
        cmd = ["ffmpeg", "-y", "-framerate", f"{fps:.3f}",
               "-i", os.path.join(frames_dir, "%05d.jpg"),
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
               "-movflags", "+faststart", out]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(res.stderr[-2000:], flush=True)
            raise RuntimeError(f"ffmpeg failed for {out}")
        print(f"[record] wrote {out} ({os.path.getsize(out)} bytes, "
              f"{n_frames} frames @ {fps:.1f} fps)", flush=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

SCENARIOS = {"settings": scenario_settings, "buttons": scenario_buttons,
             "mask": scenario_mask, "knot": scenario_knot}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), required=True)
    parser.add_argument("--test", action="store_true",
                        help="record only the first two steps (style check)")
    args = parser.parse_args()

    faulthandler.enable(all_threads=True)
    app, window = _bootstrap_real_app()

    # Canonical look for tutorials regardless of the user's saved settings
    window.set_language("en")
    window.apply_theme("default")

    # showEvent forces the window to the offscreen screen's 800x600 geometry
    # on first show; pre-set its guard flag so our size survives.
    window._initial_show_completed = True
    window.resize(WINDOW_W, WINDOW_H)
    window.show()
    window.raise_()
    window.activateWindow()
    window.resize(WINDOW_W, WINDOW_H)
    from PyQt5.QtTest import QTest
    QTest.qWait(300)
    if hasattr(window, "set_initial_splitter_sizes"):
        window.set_initial_splitter_sizes()
    QTest.qWait(300)
    print(f"[record] window size: {window.width()}x{window.height()}", flush=True)

    out_dir = os.path.join(OUT_ROOT, args.scenario + ("_test" if args.test else ""))
    os.makedirs(out_dir, exist_ok=True)
    rec = Recorder(window, out_dir)
    mouse = Mouse(rec, window)

    def run():
        ok = False
        try:
            rec.start()
            SCENARIOS[args.scenario](window, app, rec, mouse, test_only=args.test)
            ok = True
        except Exception:
            import traceback
            traceback.print_exc()
        finally:
            rec.stop()
            faulthandler.cancel_dump_traceback_later()
            try:
                if rec.n > 0:
                    encode(rec.frames_dir, rec.n, rec.elapsed,
                           os.path.join(out_dir, args.scenario))
            except Exception:
                import traceback
                traceback.print_exc()
                ok = False
            print(f"[record] {'DONE' if ok else 'FAILED'}", flush=True)
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, app.quit)

    from PyQt5.QtCore import QTimer
    QTimer.singleShot(900, run)
    app.exec_()
    os._exit(0)


if __name__ == "__main__":
    main()
