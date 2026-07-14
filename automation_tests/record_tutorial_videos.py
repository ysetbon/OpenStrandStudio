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

# The recorder uses the REAL Windows platform plugin (same fonts, style,
# popup positioning and DPI behavior as launching src/main.py) and keeps
# every window off the desktop with Qt.WA_DontShowOnScreen — see
# _install_headless_filter(). The old offscreen-platform approach rendered
# with a different font engine and a fake 800x600 screen, so dialogs,
# dropdown menus and font metrics did not match a real run.

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
# Headless-on-the-real-platform support
# ---------------------------------------------------------------------------

_headless_filter = None


def _install_headless_filter(app):
    """Keep every window (main window, dialogs, menus, combo popups,
    tooltips) off the real desktop while the app renders exactly as a
    normal run: sets Qt.WA_DontShowOnScreen on each widget before its
    platform window is mapped."""
    global _headless_filter
    from PyQt5.QtCore import QObject, QEvent, Qt
    from PyQt5.QtWidgets import QWidget

    class HeadlessFilter(QObject):
        def eventFilter(self, obj, ev):
            if ev.type() in (QEvent.Polish, QEvent.WinIdChange, QEvent.Show) \
                    and isinstance(obj, QWidget) \
                    and not obj.testAttribute(Qt.WA_DontShowOnScreen):
                obj.setAttribute(Qt.WA_DontShowOnScreen, True)
            return False

    _headless_filter = HeadlessFilter()
    app.installEventFilter(_headless_filter)


def _place_window(window):
    """Give the window the exact footprint of a 1920x1080 screen.

    The window is anchored to the screen's bottom-right corner so that
    Qt's popup clamping (menus, dropdowns) against the real screen edges
    happens at the window's own edges — the same places they would be on
    a true 1920x1080 monitor."""
    from PyQt5.QtWidgets import QApplication
    geo = QApplication.primaryScreen().geometry()
    # setGeometry pins the CLIENT rect (frame-independent), so a real
    # (framed) window and a headless (never-mapped, frameless) window put
    # their content at exactly the same global position.
    window.setGeometry(geo.x() + geo.width() - WINDOW_W,
                       geo.y() + geo.height() - WINDOW_H,
                       WINDOW_W, WINDOW_H)


def _sync_native(w):
    """Sync a top-level widget's QWindow to its widget geometry. A
    never-mapped (headless) window keeps the stale position from its first
    show, which breaks mapToGlobal and popup placement."""
    wh = w.windowHandle()
    if wh is not None and wh.geometry() != w.geometry():
        wh.setGeometry(w.geometry())


def _center_dialog(window, dlg):
    """Deterministically center a dialog's client area over the window's
    client area. Qt's own first-show centering uses frame geometry, which
    differs between a mapped (framed) and a headless window."""
    from PyQt5.QtCore import QPoint
    wc = QPoint(window.geometry().x() + window.width() // 2,
                window.geometry().y() + window.height() // 2)
    dlg.setGeometry(wc.x() - dlg.width() // 2, wc.y() - dlg.height() // 2,
                    dlg.width(), dlg.height())
    _sync_native(dlg)


def _normalize_popup(w):
    """Clamp a popup window to the screen exactly like Qt does for a mapped
    popup — a never-mapped popup skips the clamping — and sync its QWindow.
    Identical (idempotent) for a real visible run."""
    from PyQt5.QtWidgets import QApplication
    scr = QApplication.primaryScreen().geometry()
    g = w.geometry()
    x = min(max(g.x(), scr.x()), scr.x() + scr.width() - g.width())
    y = min(max(g.y(), scr.y()), scr.y() + scr.height() - g.height())
    if (x, y) != (g.x(), g.y()):
        w.move(x, y)
    _sync_native(w)


def _composite_frame(window):
    """Grab the window plus every visible popup window (menus, dialogs,
    dropdowns, tooltips) composited at their real on-screen offsets."""
    from PyQt5.QtCore import QPoint, Qt
    from PyQt5.QtGui import QPainter
    from PyQt5.QtWidgets import QApplication, QMenu, QDialog

    pm = window.grab()
    painter = QPainter(pm)
    win_origin = window.mapToGlobal(QPoint(0, 0))
    for w in QApplication.topLevelWidgets():
        if w is window or not w.isVisible():
            continue
        if isinstance(w, (QMenu, QDialog)) or \
                w.windowType() in (Qt.Popup, Qt.ToolTip, Qt.Tool, Qt.Sheet):
            try:
                off = w.mapToGlobal(QPoint(0, 0)) - win_origin
                painter.drawPixmap(off, w.grab())
            except Exception:
                pass
    painter.end()
    return pm


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
        from PyQt5.QtGui import QPainter

        pm = _composite_frame(self.window)
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.Antialiasing)
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
    """Open a QComboBox dropdown for real, glide to the matching item and
    click it — the popup opens exactly where it would in a normal run."""
    from PyQt5.QtCore import QPoint, Qt
    from PyQt5.QtTest import QTest
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

    # A QTest press+release on an unmapped combo can land the release on a
    # popup item and select it instantly; open the popup the way the click
    # handler would instead, so the dropdown stays visibly open.
    mouse.glide_to_widget(combo)
    _hold(150)
    rec.click_effect()
    _hold(250)
    combo.showPopup()
    _hold(700)
    view = combo.view()
    popup = view.window()
    _normalize_popup(popup)
    mi = view.model().index(idx, 0)
    view.scrollTo(mi)
    _hold(200)
    r = view.visualRect(mi)
    gp = view.viewport().mapToGlobal(r.center()) \
        - window.mapToGlobal(QPoint(0, 0))
    mouse.glide_to_window_pos(gp.x(), gp.y(), dur_ms=700)
    _hold(300)
    rec.click_effect()
    QTest.mouseClick(view.viewport(), Qt.LeftButton, pos=r.center())
    _hold(500)
    if combo.currentIndex() != idx:  # safety net, should not trigger
        print(f"[record] WARNING: popup click missed, selecting {idx} "
              "programmatically", flush=True)
        combo.hidePopup()
        combo.setCurrentIndex(idx)
        _hold(400)


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
    """Click the gear button and center the dialog over the window (same
    place Qt's own parent-centering puts it, but frame-independent)."""
    from PyQt5.QtWidgets import QApplication
    mouse.click_widget(window.settings_button)
    _hold(900)
    dlg = window._settings_dialog
    assert dlg is not None and dlg.isVisible(), "settings dialog not shown"
    _center_dialog(window, dlg)
    QApplication.setActiveWindow(dlg)
    _hold(300)
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
        _normalize_popup(menu)
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


def _launch(headless):
    """Bootstrap the real app exactly like src/main.py and show it as a
    1920x1080 window. With headless=True nothing appears on the desktop."""
    faulthandler.enable(all_threads=True)
    app, window = _bootstrap_real_app()
    if headless:
        _install_headless_filter(app)

    # Canonical look for tutorials regardless of the user's saved settings
    window.set_language("en")
    window.apply_theme("default")

    # showEvent's first-show hook re-applies the full screen geometry and
    # maximizes; pre-set its guard flag so the exact 1080p footprint sticks.
    window._initial_show_completed = True
    _place_window(window)
    window.show()
    window.raise_()
    window.activateWindow()
    if headless:
        from PyQt5.QtWidgets import QApplication
        # Unmapped windows never become natively active; activate in-process
        # so focus-dependent styling matches a real (visible) run.
        QApplication.setActiveWindow(window)
        # The canvas skips its supersampled buffer blit when the top-level
        # window is not exposed (strand_drawing_canvas blit guard), which
        # changes antialiasing. A DontShowOnScreen window is never exposed,
        # so report exposure to render exactly like a real run. Patch the
        # class (an instance patch dies when sip garbage-collects the
        # windowHandle() wrapper between calls).
        from PyQt5.QtGui import QWindow
        QWindow.isExposed = lambda self: True
    _sync_native(window)
    _place_window(window)
    from PyQt5.QtTest import QTest
    QTest.qWait(300)
    if hasattr(window, "set_initial_splitter_sizes"):
        window.set_initial_splitter_sizes()
    QTest.qWait(300)
    print(f"[record] window size: {window.width()}x{window.height()}"
          f" at {window.x()},{window.y()} headless={headless}", flush=True)
    return app, window


# ---------------------------------------------------------------------------
# Verification: prove the headless run is pixel-identical to a real run
# ---------------------------------------------------------------------------

VERIFY_ROOT = os.path.join(OUT_ROOT, "verify")


def _verify_states(window, app, out_dir):
    """Walk the app through reference states (dialog, dropdown, context
    menu, tooltip) and save a composite screenshot of each."""
    from PyQt5.QtCore import QPoint, Qt, QTimer
    from PyQt5.QtTest import QTest
    os.makedirs(out_dir, exist_ok=True)
    canvas = window.canvas

    def shot(name):
        from PyQt5.QtWidgets import QApplication
        _composite_frame(window).save(os.path.join(out_dir, name + ".png"))
        tops = []
        for w in QApplication.topLevelWidgets():
            if w is not window and w.isVisible():
                tops.append(f"{type(w).__name__}@{w.geometry().getRect()}")
        print(f"[verify] captured {name} win={window.geometry().getRect()} "
              f"tops={tops}", flush=True)

    QTest.qWait(600)
    shot("01_main_window")

    # Draw 1_1 and attach 1_2 with fixed coordinates
    canvas.start_new_strand_mode(1)
    QTest.qWait(300)
    QTest.mousePress(canvas, Qt.LeftButton, pos=QPoint(520, 300))
    QTest.qWait(200)
    from test_menu_strand_flow import _strand_by_name
    ev_steps = 6
    for i in range(1, ev_steps + 1):
        x = 520 + (980 - 520) * i / ev_steps
        from PyQt5.QtCore import QPointF, QEvent
        from PyQt5.QtGui import QMouseEvent
        from PyQt5.QtWidgets import QApplication
        QApplication.sendEvent(canvas, QMouseEvent(
            QEvent.MouseMove, QPointF(x, 300), Qt.LeftButton, Qt.LeftButton,
            Qt.NoModifier))
        QTest.qWait(40)
    QTest.mouseRelease(canvas, Qt.LeftButton, pos=QPoint(980, 300))
    QTest.qWait(500)
    s11 = _strand_by_name(canvas, "1_1")
    assert s11 is not None, "verify: 1_1 missing"
    window.set_attach_mode()
    QTest.qWait(200)
    end11 = QPoint(int(s11.end.x()), int(s11.end.y()))
    QTest.mousePress(canvas, Qt.LeftButton, pos=end11)
    QTest.qWait(200)
    QTest.mouseRelease(canvas, Qt.LeftButton,
                       pos=QPoint(end11.x(), end11.y() + 280))
    QTest.qWait(600)
    shot("02_strands")

    # Settings dialog
    QTest.mouseClick(window.settings_button, Qt.LeftButton)
    QTest.qWait(900)
    dlg = window._settings_dialog
    assert dlg is not None and dlg.isVisible(), "verify: settings not shown"
    _center_dialog(window, dlg)
    from PyQt5.QtWidgets import QApplication
    QApplication.setActiveWindow(dlg)
    QTest.qWait(400)
    shot("03_settings_dialog")

    # Theme dropdown open
    QTest.mouseClick(dlg.theme_combobox, Qt.LeftButton)
    QTest.qWait(800)
    shot("04_theme_dropdown")
    dlg.theme_combobox.hidePopup()
    QTest.qWait(300)

    # Language page + dropdown open
    item = dlg.categories_list.item(3)
    r = dlg.categories_list.visualItemRect(item)
    QTest.mouseClick(dlg.categories_list.viewport(), Qt.LeftButton,
                     pos=r.center())
    QTest.qWait(500)
    QTest.mouseClick(dlg.language_combobox, Qt.LeftButton)
    QTest.qWait(800)
    shot("05_language_dropdown")
    dlg.language_combobox.hidePopup()
    QTest.qWait(300)
    dlg.close()
    QTest.qWait(500)

    # Layer button context menu (blocking exec_ -> grab from a timer)
    btn = _layer_button(window, "1_2")
    assert btn is not None, "verify: layer button 1_2 missing"

    def _menu_shot():
        from PyQt5.QtWidgets import QApplication, QMenu
        menu = next((w for w in QApplication.topLevelWidgets()
                     if isinstance(w, QMenu) and w.isVisible()), None)
        if menu is None:
            print("[verify] WARNING: menu not open", flush=True)
            return
        _normalize_popup(menu)
        QTest.qWait(300)
        shot("06_context_menu")
        menu.close()

    QTimer.singleShot(900, _menu_shot)
    btn.customContextMenuRequested.emit(btn.rect().center())
    QTest.qWait(500)

    # Right-click tooltip on a layer panel round button
    tb = window.layer_panel.reset_states_button
    c = tb.rect().center()
    QTest.mousePress(tb, Qt.RightButton, pos=QPoint(c.x(), c.y()))
    QTest.qWait(600)
    shot("07_button_tooltip")
    QTest.mouseRelease(tb, Qt.RightButton, pos=QPoint(c.x(), c.y()))
    QTest.qWait(300)


def _run_verify_capture(mode):
    """Subprocess body: capture all reference states in one mode."""
    headless = (mode == "headless")
    app, window = _launch(headless)
    out_dir = os.path.join(VERIFY_ROOT, mode)
    from PyQt5.QtCore import QTimer

    def run():
        try:
            if not headless:
                from PyQt5.QtGui import QCursor
                # Park the real cursor off the window so no hover styling
                # sneaks into the reference screenshots.
                QCursor.setPos(10, 540)
            _verify_states(window, app, out_dir)
            print("[verify] capture complete", flush=True)
        except Exception:
            import traceback
            traceback.print_exc()
        finally:
            faulthandler.cancel_dump_traceback_later()
            QTimer.singleShot(0, app.quit)

    QTimer.singleShot(900, run)
    app.exec_()
    os._exit(0)


def _compare_verify_runs():
    """Spawn a visible (real) run and a headless run, then pixel-diff."""
    for mode in ("visible", "headless"):
        print(f"[verify] running {mode} capture...", flush=True)
        res = subprocess.run([sys.executable, os.path.abspath(__file__),
                              "--verify-run", mode],
                             capture_output=True, text=True)
        tail = "\n".join(res.stdout.splitlines()[-8:])
        print(tail, flush=True)
        if "capture complete" not in res.stdout:
            print(res.stderr[-1500:], flush=True)
            raise RuntimeError(f"{mode} capture failed")

    from PIL import Image, ImageChops
    vis_dir = os.path.join(VERIFY_ROOT, "visible")
    hl_dir = os.path.join(VERIFY_ROOT, "headless")
    names = sorted(f for f in os.listdir(vis_dir) if f.endswith(".png"))
    all_ok = True
    for name in names:
        a = Image.open(os.path.join(vis_dir, name)).convert("RGB")
        b = Image.open(os.path.join(hl_dir, name)).convert("RGB")
        if a.size != b.size:
            print(f"[verify] {name}: SIZE MISMATCH {a.size} vs {b.size}",
                  flush=True)
            all_ok = False
            continue
        diff = ImageChops.difference(a, b)
        bbox = diff.getbbox()
        if bbox is None:
            print(f"[verify] {name}: identical (diff=0)", flush=True)
        else:
            hist = diff.convert("L").histogram()
            n_diff = sum(hist[1:])
            print(f"[verify] {name}: DIFFERS - {n_diff} px, bbox={bbox}",
                  flush=True)
            diff.save(os.path.join(VERIFY_ROOT, "diff_" + name))
            all_ok = False
    print(f"[verify] RESULT: {'PASS - pixel diff=0' if all_ok else 'FAIL'}",
          flush=True)
    return all_ok


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=sorted(SCENARIOS))
    parser.add_argument("--test", action="store_true",
                        help="record only the first two steps (style check)")
    parser.add_argument("--verify", action="store_true",
                        help="compare a real (visible) run against the "
                             "headless run pixel by pixel")
    parser.add_argument("--verify-run", choices=("visible", "headless"),
                        help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.verify_run:
        _run_verify_capture(args.verify_run)
        return
    if args.verify:
        ok = _compare_verify_runs()
        sys.exit(0 if ok else 1)
    if not args.scenario:
        parser.error("--scenario is required unless --verify is given")

    app, window = _launch(headless=True)

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
