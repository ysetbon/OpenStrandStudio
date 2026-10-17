"""End-to-end check of every UI sound, run through the real main.py.

    python tests/ui_sound_check.py [--report report.json]

Starts the app exactly as main.py does (offscreen, with a throwaway settings
folder), but where main.py would hand control to the user it runs the checks
below against the real window instead, then exits 0 when everything passed.

Each check performs a real user action (mouse click, hover, drag, key press)
and records which sounds the sound manager actually played. When an audio
device is available (a PulseAudio null sink is enough), it also confirms that
every sound really started playing.

Covered:
  * every sound file: present, valid format, length, not silent, loads
  * every button in the main window and the layer panel (click and hover)
  * every sub-window: open/close and every checkbox, toggle, slider,
    dropdown, +/- stepper and button inside it
  * canvas: drawing a new strand, attaching, dragging, grid snapping, hover
  * keyboard shortcuts, tabs, right-click menus, warnings, saving
  * the Sound settings (off, volume 0, hover off) and repeat limits
"""
import json
import os
import re
import runpy
import shutil
import sys
import tempfile
import time
import traceback
import wave
from pathlib import Path

# On Linux without a display, rerun under a 1920x1080 virtual X display when one is
# available: Qt's offscreen screen is only 800x600, too small for the pointer to reach
# every button. Everywhere else the window stays hidden (offscreen).
if (__name__ == "__main__" and sys.platform.startswith("linux") and "DISPLAY" not in os.environ
        and "QT_QPA_PLATFORM" not in os.environ and shutil.which("xvfb-run")):
    os.execvp("xvfb-run", ["xvfb-run", "-a", "-s", "-screen 0 1920x1080x24", sys.executable, *sys.argv])
if "DISPLAY" not in os.environ or not sys.platform.startswith("linux"):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
SETTINGS_DIR = tempfile.mkdtemp(prefix="oss_sound_check_")
os.environ["APPDATA"] = SETTINGS_DIR  # where the app keeps its settings on Windows and Linux
if sys.platform.startswith("darwin"):
    # on macOS the app uses ~/Library/Application Support: point ~ at the temp folder
    # so a run can never touch the real settings
    os.environ["HOME"] = SETTINGS_DIR

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
SAMPLE = REPO / "tests" / "levels" / "continue_2x2.json"
REPORT_PATH = None
if "--report" in sys.argv:
    REPORT_PATH = sys.argv[sys.argv.index("--report") + 1]

sys.path.insert(0, str(SRC))
os.chdir(SRC)

import numpy as np  # noqa: E402
from PyQt5.QtCore import QEvent, QPoint, QPointF, Qt, QTimer  # noqa: E402
from PyQt5.QtGui import QContextMenuEvent, QMouseEvent  # noqa: E402
from PyQt5.QtMultimedia import QSoundEffect  # noqa: E402
from PyQt5.QtTest import QTest  # noqa: E402
from PyQt5.QtWidgets import (QAbstractButton, QAbstractSlider, QApplication, QCheckBox,  # noqa: E402
                             QComboBox, QDialog, QFileDialog, QListWidget, QMenu, QMessageBox,
                             QPushButton, QToolButton, QWidget, QWidgetAction)

# The settings dialog also writes a copy into the repository: back it up and restore it.
USER_SETTINGS_COPY = REPO / "user_settings.txt"
USER_SETTINGS_BACKUP = USER_SETTINGS_COPY.read_bytes() if USER_SETTINGS_COPY.exists() else None

RESULTS = []
HOVER_CUES = {"hover_toolbar", "hover_panel_top", "hover_layer", "hover_level", "hover_level_fold", "hover_panel_bottom", "hover_group",
              "hover_dialog", "hover_menu", "hover_menu_group", "hover_menu_level", "hover_settings", "hover_attach_point",
              "hover_move_point"}
STEPPER_TEXT = {"+", "++", "-", "--", "−", "−−"}


# --------------------------------------------------------------------------- helpers
def pump(ms=60):
    app = QApplication.instance()
    end = time.monotonic() + ms / 1000
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(0.004)


def record(area, control, action, expected, got, ok, note=""):
    RESULTS.append({"area": area, "control": control, "action": action,
                    "expected": expected, "got": got, "ok": bool(ok), "note": note})
    if os.environ.get("SOUND_CHECK_PROGRESS"):
        print(f"  {'ok ' if ok else 'BAD'} {area} | {control} | {action} | got {got}", flush=True)


class Recorder:
    """Records every sound the manager plays, and which ones really reached the speakers."""

    def __init__(self, manager):
        self.requested = []
        self.audible = set()
        self.ever = set()
        for cue, effect in manager._effects.items():
            real_play = effect.play

            def play(cue=cue, real_play=real_play):
                self.requested.append(cue)
                self.ever.add(cue)
                real_play()

            effect.play = play
            effect.playingChanged.connect(
                lambda cue=cue, effect=effect: effect.isPlaying() and self.audible.add(cue))

    def clear(self):
        self.requested = []


class ModalWatcher:
    """Closes dialogs and popups that a click opens (colour pickers, file pickers,
    confirmations, menus) so a modal exec_() never blocks the run."""

    def __init__(self, app, main_window):
        self.app = app
        self.main_window = main_window
        self.keep = set()
        self.closed = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(40)

    def tick(self):
        try:
            popup = self.app.activePopupWidget()
            if popup is not None and id(popup) not in self.keep:
                self.closed.append(type(popup).__name__)
                popup.close()
            modal = self.app.activeModalWidget()
            if modal is not None and modal is not self.main_window and id(modal) not in self.keep:
                self.closed.append(type(modal).__name__)
                if isinstance(modal, QDialog):
                    modal.reject()
                else:
                    modal.close()
        except RuntimeError:
            pass


def mouse(widget, kind, pos, button=Qt.LeftButton, buttons=None):
    if buttons is None:
        buttons = Qt.NoButton if kind == QEvent.MouseMove else button
    event = QMouseEvent(kind, QPointF(pos), button if kind != QEvent.MouseMove else Qt.NoButton,
                        buttons, Qt.NoModifier)
    QApplication.sendEvent(widget, event)


MANAGER = None


def wait_between():
    """Start each check clean: forget the per-sound repeat limits and let events settle."""
    if MANAGER is not None:
        MANAGER._last_played.clear()
    pump(25)


def run_check(rec, area, control, action, fn, expected=None, exact=None, forbidden=(), note=""):
    """expected: cue or set of cues that must all play. exact: the full list that must play.
    forbidden: cues that must not play. expected=None and exact=None means silence."""
    wait_between()
    rec.clear()
    try:
        fn()
    except Exception as e:  # report the crash as a failed check, keep going
        pump(150)
        record(area, control, action, describe(expected, exact), rec.requested, False,
               f"error: {type(e).__name__}: {e}")
        return False
    pump(110)
    got = list(rec.requested)
    wanted = set(exact or ()) | ({expected} if isinstance(expected, str) else set(expected or ()))
    if not wanted & HOVER_CUES:
        # with a real pointer, a window closing or moving can leave the pointer on a
        # button, which rightly plays its hover sound; that is not what is tested here
        got = [c for c in got if c not in HOVER_CUES]
    if exact is not None:
        ok = got == list(exact)
    elif expected is None:
        ok = not got
    else:
        need = {expected} if isinstance(expected, str) else set(expected)
        ok = need.issubset(got)
    if ok and forbidden:
        ok = not (set(forbidden) & set(got))
    record(area, control, action, describe(expected, exact), got, ok, note)
    return ok


def describe(expected, exact):
    if exact is not None:
        return "exactly " + (", ".join(exact) if exact else "silence")
    if expected is None:
        return "silence"
    return expected if isinstance(expected, str) else " + ".join(sorted(expected))


def label(widget):
    text = ""
    for attr in ("text", "windowTitle", "accessibleName", "objectName"):
        try:
            value = getattr(widget, attr)()
        except Exception:
            continue
        if value:
            text = value
            break
    text = " ".join(str(text).split())[:40]
    return f"{type(widget).__name__} '{text}'" if text else type(widget).__name__


MAX_CONTROLS_PER_WINDOW = 120


def control_key(widget):
    """Identify a control by what it is and where it sits, so a window that rebuilds
    its widgets after a click does not hand us the same control again and again."""
    try:
        pos = widget.mapTo(widget.window(), QPoint(0, 0))
        return (type(widget).__name__, label(widget), pos.x() // 4, pos.y() // 4)
    except RuntimeError:
        return id(widget)


def click(widget, pos=None):
    if pos is None:
        pos = widget.rect().center()
    QTest.mouseClick(widget, Qt.LeftButton, Qt.NoModifier, pos)


def checkbox_pos(cb):
    # the indicator sits at the leading edge
    x = min(9, max(1, cb.width() // 2))
    if cb.layoutDirection() == Qt.RightToLeft:
        x = cb.width() - x
    return QPoint(x, cb.height() // 2)


def stepper_cue(button):
    text = button.text().strip()
    if text in ("+", "++"):
        return "stepper_plus"
    if text in ("-", "--", "−", "−−"):
        return "stepper_minus"
    return None


def close_stray_dialogs(main_window, keep=()):
    closed = False
    for w in QApplication.topLevelWidgets():
        try:
            if w is main_window or w in keep or not w.isVisible():
                continue
            if isinstance(w, (QDialog, QMenu)):
                w.close()
                closed = True
        except RuntimeError:
            pass
    if closed:
        pump(80)


# --------------------------------------------------------------------------- checks
def check_files(manager):
    import sound_manager
    folder = Path(sound_manager.sounds_dir())
    files = {p.stem for p in folder.glob("*.wav")}
    cues = set(sound_manager.CUES)
    record("Files", "sound list", "every sound has a file", f"{len(cues)} files",
           sorted(cues - files) or "all present", not (cues - files))
    record("Files", "sound list", "no unused files", "none", sorted(files - cues) or "none", not (files - cues))
    for cue in sorted(cues & files):
        path = folder / f"{cue}.wav"
        with wave.open(str(path)) as w:
            params = (w.getframerate(), w.getnchannels(), w.getsampwidth())
            frames = w.readframes(w.getnframes())
            ms = 1000 * w.getnframes() / w.getframerate()
        x = np.frombuffer(frames, dtype="<i2").astype(float) / 32768
        peak = 20 * np.log10(np.abs(x).max() + 1e-9)
        ok = params == (44100, 1, 2) and 20 <= ms <= 300 and peak > -40
        record("Files", cue, "format, length, level", "44.1 kHz mono 16-bit, 20-300 ms, audible",
               f"{params[0]} Hz, {params[1]} ch, {8 * params[2]}-bit, {ms:.0f} ms, peak {peak:.1f} dB", ok)


def check_loading(manager):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if all(e.status() in (QSoundEffect.Ready, QSoundEffect.Error) for e in manager._effects.values()):
            break
        pump(50)
    names = {0: "not loaded", 1: "still loading", 2: "loaded", 3: "error"}
    statuses = {cue: names[e.status()] for cue, e in manager._effects.items()}
    bad = {c: s for c, s in statuses.items() if s != "loaded"}
    audio = not bad or any(s == "loaded" for s in statuses.values())
    record("Files", "audio player", "every sound loads into QSoundEffect", "all loaded",
           bad or "all loaded", not bad,
           "" if audio else "no audio device here: start a PulseAudio null sink to test playback")
    return not bad


def check_canvas(w, rec):
    canvas = w.canvas
    lp = w.layer_panel
    grid = getattr(canvas, "grid_size", 28)

    def at(point):
        return canvas.canvas_to_screen(point).toPoint()

    def drag(start, end, steps=6):
        mouse(canvas, QEvent.MouseButtonPress, start)
        for i in range(1, steps + 1):
            p = start + (end - start) * i / steps
            mouse(canvas, QEvent.MouseMove, p, buttons=Qt.LeftButton)
            pump(70)
        mouse(canvas, QEvent.MouseButtonRelease, end, buttons=Qt.NoButton)

    # 1. draw a new strand
    run_check(rec, "Canvas", "Add new strand button", "click", lambda: click(lp.add_new_strand_button), "new_strand")
    start = QPoint(canvas.width() // 2 - 4 * grid, canvas.height() // 2)
    end = QPoint(canvas.width() // 2 + 2 * grid, canvas.height() // 2)
    before = len(canvas.strands)
    run_check(rec, "Canvas", "new strand", "drag to draw a new strand", lambda: drag(start, end), "attach_complete",
              note="the moment a new strand is placed")
    created = len(canvas.strands) > before
    record("Canvas", "new strand", "strand was created", "1 new strand", f"{len(canvas.strands) - before} new", created)
    if not created:
        return
    strand = canvas.strands[-1]

    # 2. attach a strand to its end
    if w.attach_button.isEnabled():
        run_check(rec, "Canvas", "Attach mode button", "click", lambda: click(w.attach_button), "mode_attach")
    else:
        # Drawing a strand switches to Attach mode and disables its button
        run_check(rec, "Canvas", "Attach mode button (already active, disabled)", "click",
                  lambda: click(w.attach_button), None, note="a disabled button does nothing, so it stays silent")
    end_pt = at(strand.end)
    run_check(rec, "Canvas", "attach circle", "hover over a strand end",
              lambda: (mouse(canvas, QEvent.MouseMove, end_pt + QPoint(40, 40)), pump(60),
                       mouse(canvas, QEvent.MouseMove, end_pt)), "hover_attach_point")
    before = len(canvas.strands)
    target = end_pt + QPoint(0, 4 * int(grid * canvas.zoom_factor))
    run_check(rec, "Canvas", "attach circle", "press on a strand end", lambda: mouse(canvas, QEvent.MouseButtonPress, end_pt),
              "attach_start")

    def finish_attach():
        for i in range(1, 7):
            mouse(canvas, QEvent.MouseMove, end_pt + (target - end_pt) * i / 6, buttons=Qt.LeftButton)
            pump(70)
        mouse(canvas, QEvent.MouseButtonRelease, target, buttons=Qt.NoButton)

    run_check(rec, "Canvas", "attached strand", "drag out and release", finish_attach, "attach_complete")
    record("Canvas", "attached strand", "strand was attached", "1 new strand",
           f"{len(canvas.strands) - before} new", len(canvas.strands) > before)
    attached = canvas.strands[-1]

    # 3. move mode: hover, pick up, drag across the grid, drop
    run_check(rec, "Canvas", "Move mode button", "click", lambda: click(w.move_button), "mode_move")
    canvas.snap_to_grid_enabled = True
    point = at(attached.end)
    run_check(rec, "Canvas", "strand end", "hover over a point you can grab",
              lambda: (mouse(canvas, QEvent.MouseMove, point + QPoint(60, -60)), pump(60),
                       mouse(canvas, QEvent.MouseMove, point)), "hover_move_point")
    run_check(rec, "Canvas", "strand end", "press to grab", lambda: mouse(canvas, QEvent.MouseButtonPress, point),
              "drag_pickup")
    step = int(grid * canvas.zoom_factor)

    def drag_across_grid():
        for i in range(1, 6):
            mouse(canvas, QEvent.MouseMove, point + QPoint(step * i, 0), buttons=Qt.LeftButton)
            pump(90)

    run_check(rec, "Canvas", "strand end", "drag across grid cells", drag_across_grid, "snap_grid")
    run_check(rec, "Canvas", "strand end", "release",
              lambda: mouse(canvas, QEvent.MouseButtonRelease, point + QPoint(step * 5, 0), buttons=Qt.NoButton),
              "drag_drop")
    dropped = point + QPoint(step * 5, 0)

    def no_hover(control, action, fn, note):
        """run_check ignores hover sounds when it expects silence; here the hover is the point."""
        wait_between()
        rec.clear()
        fn()
        pump(110)
        record("Canvas", control, action, "no hover_move_point", list(rec.requested),
               "hover_move_point" not in rec.requested, note)

    no_hover("dropped strand end", "pointer moves a little, still on it",
             lambda: (mouse(canvas, QEvent.MouseMove, dropped + QPoint(2, 1)), pump(40),
                      mouse(canvas, QEvent.MouseMove, dropped + QPoint(3, 2))),
             "the point was just dropped: no second hover until the pointer leaves it")
    run_check(rec, "Canvas", "dropped strand end", "pointer leaves it and comes back",
              lambda: (mouse(canvas, QEvent.MouseMove, dropped + QPoint(60, -60)), pump(60),
                       mouse(canvas, QEvent.MouseMove, dropped)), "hover_move_point")

    # A control point dropped back onto its strand's start point: the start point does not hover either
    points_were_shown = canvas.show_control_points
    if not points_were_shown:
        click(w.toggle_control_points_button)
        pump(150)
    cp = at(attached.control_point1)
    away = cp + QPoint(3 * step, -3 * step)

    def drag_point(a, b):
        mouse(canvas, QEvent.MouseButtonPress, a)
        for i in range(1, 6):
            mouse(canvas, QEvent.MouseMove, a + (b - a) * i / 5, buttons=Qt.LeftButton)
            pump(50)
        mouse(canvas, QEvent.MouseButtonRelease, b, buttons=Qt.NoButton)
        pump(100)

    drag_point(cp, away)
    mouse(canvas, QEvent.MouseMove, away + QPoint(0, 8 * step))  # leave every point
    pump(60)
    start_pt = at(attached.start)
    run_check(rec, "Canvas", "control point", "drag it onto the start point and let go",
              lambda: drag_point(away, start_pt), "drag_drop")
    no_hover("control point on the start point", "pointer moves around on it",
             lambda: [(mouse(canvas, QEvent.MouseMove, start_pt + QPoint(dx, dy)), pump(30))
                      for dx, dy in ((2, 1), (8, -4), (-6, 6))],
             "neither the control point nor the start point under it hovers after the drop")
    if not points_were_shown:
        click(w.toggle_control_points_button)
        pump(150)

    # 4. keyboard shortcuts
    run_check(rec, "Keyboard", "Z", "undo the move", lambda: QTest.keyClick(canvas, Qt.Key_Z), "undo")
    run_check(rec, "Keyboard", "X", "redo the move", lambda: QTest.keyClick(canvas, Qt.Key_X), "redo")
    um = lp.undo_redo_manager
    run_check(rec, "Keyboard", "undo button", "click", lambda: click(um.undo_button), exact=["undo"],
              note="the button itself adds no click on top")
    run_check(rec, "Keyboard", "redo button", "click", lambda: click(um.redo_button), exact=["redo"])
    while um.redo_button.isEnabled():
        um.redo()
    pump(100)
    run_check(rec, "Keyboard", "X", "nothing left to redo", lambda: QTest.keyClick(canvas, Qt.Key_X), None)
    run_check(rec, "Keyboard", "N", "new strand shortcut", lambda: QTest.keyClick(w, Qt.Key_N), "new_strand")
    w.canvas.set_mode("select")
    pump(100)


def expected_main_cue(w, b, checked_after):
    from level_button import LevelButton
    from numbered_layer_button import NumberedLayerButton
    lp = w.layer_panel
    modes = {id(w.view_button): "mode_view", id(w.select_strand_button): "mode_select",
             id(w.rotate_button): "mode_rotate", id(w.angle_adjust_button): "mode_angle",
             id(w.move_button): "mode_move", id(w.attach_button): "mode_attach",
             id(w.load_button): "toolbar_action", id(w.save_image_button): "toolbar_image"}
    if id(b) in modes:
        return modes[id(b)]
    if b in (lp.add_new_strand_button, lp.new_mask_button):
        return "new_strand"
    if b in (lp.delete_strand_button, lp.delete_all_button, lp.delete_mask_button, lp.delete_all_masks_button):
        return "delete"
    if b in (lp.strands_tab_button, lp.masks_tab_button):
        return "tab_switch"
    if isinstance(b, LevelButton):
        # a level name cannot be selected on the Masks tab, so the click does nothing there
        return "level_select" if lp.level_selection_allowed() else None
    if b in (lp.group_layer_manager.create_group_button, lp.group_rail.create_tile):
        return "group_new"
    if b is lp.group_toggle_button:
        return "group_panel_off" if lp.group_panel_collapsed else "group_panel_on"
    if lp.group_rail.isAncestorOf(b):
        return "group_panel_on"  # a group tile unfolds the panel
    if isinstance(b, NumberedLayerButton):
        return "layer_select"
    if b is w.layer_state_button:
        # turns on to open the layer state window; closing that window turns it off again
        return "layer_state_on"
    state = "on" if checked_after else "off"
    if b is w.toggle_shadow_button:
        return f"toggle_shadow_{state}"
    if b is w.tabs_button:
        return f"toggle_tabs_{state}"
    if b is w.toggle_control_points_button:
        return f"toggle_points_{state}"
    if b.isCheckable():
        return f"ui_toggle_{state}"
    return "ui_click"


def main_window_buttons(w):
    lp = w.layer_panel
    um = lp.undo_redo_manager
    skip = {id(um.undo_button), id(um.redo_button)}
    out = []
    for b in w.findChildren(QAbstractButton):
        try:
            if (b.window() is w and b.isVisible() and id(b) not in skip
                    and not stepper_cue(b) and b.width() > 2):
                out.append(b)
        except RuntimeError:
            pass
    return out


def check_main_buttons(w, rec, tested):
    # The layer panel rebuilds its buttons after some clicks, so look them up again
    # before every click instead of working from a list made at the start.
    for _ in range(300):
        pending = [b for b in main_window_buttons(w) if control_key(b) not in tested]
        if not pending:
            break
        b = pending[0]
        tested.add(control_key(b))
        name = label(b)
        if b is w.settings_button:
            run_check(rec, "Main window", name, "click", lambda: click(b), {"toolbar_settings", "dialog_open"})
            close_stray_dialogs(w)
            continue
        if b in (w.layer_panel.delete_all_button, w.layer_panel.delete_all_masks_button,
                 w.layer_panel.delete_strand_button, w.layer_panel.delete_mask_button):
            if b.isEnabled():
                run_check(rec, "Main window", name, "click", lambda: click(b), "delete",
                          note="any confirmation is dismissed by the test")
            else:
                run_check(rec, "Main window", name + " (disabled right now)", "click", lambda: click(b), None,
                          note="a disabled button does nothing, so it stays silent")
            continue
        if not b.isVisible() or not b.isEnabled():
            run_check(rec, "Main window", name + " (disabled right now)", "click", lambda: click(b), None,
                      note="a disabled button does nothing, so it stays silent")
            continue
        wait_between()
        rec.clear()
        try:
            mode_before = w.current_mode
            click(b)
            checked = b.isChecked()  # the state the click produced, before any follow-up changes it
            pump(150)
            expected = expected_main_cue(w, b, checked)
            if b is w.angle_adjust_button and w.current_mode not in ("angle_adjust", mode_before):
                # no strand selected: the app falls back to another mode, and that mode plays
                expected = w.MODE_ON_CUES[w.current_mode]
            got = [cue for cue in rec.requested if cue not in HOVER_CUES]
            ok = expected in got if expected else not got
            record("Main window", name, "click", expected or "silence", got, ok)
            if (expected and b.isCheckable() and expected.startswith(("ui_toggle", "toggle_")) and b.isVisible()
                    and b is not w.layer_state_button):
                run_check(rec, "Main window", name, "click again", lambda: click(b),
                          expected_main_cue(w, b, not checked))
        except RuntimeError:
            record("Main window", name, "click", "-", "-", True, "button removed by its own click")
        close_stray_dialogs(w)


def expected_hover_cue(w, b):
    """Each area of the main window has its own hover sound (all takes of one prompt)."""
    from level_button import LevelButton
    from numbered_layer_button import NumberedLayerButton
    lp = w.layer_panel
    if isinstance(b, LevelButton):
        return "hover_level"  # the hover moves onto the name, not the fold control
    if isinstance(b, NumberedLayerButton):
        return "hover_layer"
    areas = [((lp.top_header, lp.zoom_panel, lp.refresh_panel), "hover_panel_top"),
             ((lp.delete_strand_button.parentWidget(),), "hover_panel_bottom"),
             ((lp.right_panel,), "hover_group")]
    for containers, cue in areas:
        if any(c.isAncestorOf(b) for c in containers):
            return cue
    return "hover_toolbar"


def check_hover(w, rec):
    for b in [b for b in main_window_buttons(w) if b.isEnabled()]:
        name = label(b)
        cue = expected_hover_cue(w, b)
        centre = b.mapToGlobal(b.rect().center())
        if QApplication.widgetAt(centre) is b:
            run_check(rec, "Hover", name, "move the pointer onto it",
                      lambda: (QTest.mouseMove(w, QPoint(1, 1)), pump(30), QTest.mouseMove(b)), cue)
        else:
            run_check(rec, "Hover", name, "pointer enters it", lambda: QApplication.sendEvent(b, QEvent(QEvent.Enter)),
                      cue, note="scrolled out of view or covered, so the Enter event is sent directly")


def sweep_dialog(rec, w, make, area, colour):
    """Open a sub-window and use every control in it."""
    dialog = make()
    WATCHER.keep.add(id(dialog))
    dialog.show()
    pump(250)
    hover = "hover_settings" if type(dialog).__name__ == "SettingsDialog" else "hover_dialog"
    done = set()
    closed_checked = False
    for _ in range(MAX_CONTROLS_PER_WINDOW):
        controls = [c for c in dialog.findChildren(QWidget)
                    if isinstance(c, (QAbstractButton, QAbstractSlider, QComboBox))
                    and control_key(c) not in done and c.isVisible() and c.isEnabled() and c.window() is dialog]
        controls = [c for c in controls if not (isinstance(c, QAbstractSlider) and c.parent() is not None
                                                and type(c.parent()).__name__.endswith("ScrollBar"))]
        controls = [c for c in controls if type(c).__name__ != "QScrollBar"]
        if not controls:
            break
        c = controls[0]
        done.add(control_key(c))
        name = label(c)
        try:
            if isinstance(c, QAbstractButton):
                run_check(rec, area, name, "pointer enters it", lambda: QApplication.sendEvent(c, QEvent(QEvent.Enter)),
                          hover)
            if isinstance(c, QCheckBox):
                was = c.isChecked()
                run_check(rec, area, name, "tick", lambda: click(c, checkbox_pos(c)),
                          f"toggle_{colour}_{'off' if was else 'on'}")
                if c.isVisible():
                    run_check(rec, area, name, "untick", lambda: click(c, checkbox_pos(c)),
                              f"toggle_{colour}_{'on' if was else 'off'}")
            elif isinstance(c, QAbstractSlider):
                value = c.value()
                run_check(rec, area, name, "click the track", lambda: click(c, QPoint(c.width() - 4, c.height() // 2)
                          if c.orientation() == Qt.Horizontal else QPoint(c.width() // 2, 4)), "snap_grid")
                c.setValue(value)
            elif isinstance(c, QComboBox):
                run_check(rec, area, name, "open", lambda: QTest.mousePress(c, Qt.LeftButton), "menu_open")
                view = c.view()
                index = c.model().index(c.currentIndex(), 0)
                rect = view.visualRect(index)
                if view.isVisible() and rect.isValid():
                    run_check(rec, area, name, "pick the current value",
                              lambda: click(view.viewport(), rect.center()), "ui_click")
                c.hidePopup()
            elif stepper_cue(c):
                run_check(rec, area, name, "click", lambda: click(c), stepper_cue(c))
            elif c.isCheckable():
                was = c.isChecked()
                group = getattr(c, "group", lambda: None)()
                exclusive = group is not None and group.exclusive()
                state = "on" if (exclusive or not was) else "off"
                run_check(rec, area, name, "toggle", lambda: click(c), f"toggle_{colour}_{state}")
                if not exclusive and c.isVisible():
                    run_check(rec, area, name, "toggle back", lambda: click(c), f"toggle_{colour}_{'on' if was else 'off'}")
            else:
                wait_between()
                rec.clear()
                click(c)
                pump(200)
                got = [cue for cue in rec.requested if cue not in HOVER_CUES]
                still_open = False
                try:
                    still_open = dialog.isVisible()
                except RuntimeError:
                    pass
                if not still_open:
                    ok = got == ["dialog_close"]
                    record(area, name, "click (closes the window)", "exactly dialog_close", got, ok,
                           "a closing button plays only the close sound")
                    closed_checked = True
                    dialog = make()
                    WATCHER.keep.add(id(dialog))
                    dialog.show()
                    pump(250)
                else:
                    record(area, name, "click", "ui_click", got, "ui_click" in got)
            close_stray_dialogs(w, keep=(dialog,))
        except RuntimeError:
            record(area, name, "use", "-", "-", True, "control removed by the action itself")
    if not closed_checked:
        run_check(rec, area, "window", "close with the X", lambda: dialog.close(), exact=["dialog_close"])
    else:
        dialog.close()
        pump(150)
    return dialog


def check_dialogs(w, rec):
    from end_style_dialog import EndStyleDialog
    from group_layers import GroupMoveDialog, GroupRotateDialog, StrandAngleEditDialog
    from group_shadow_editor_dialog import GroupShadowEditorDialog
    from mask_grid_dialog import MaskGridDialog
    from numbered_layer_button import WidthConfigDialog
    from shadow_editor_dialog import ShadowEditorDialog
    canvas, lp = w.canvas, w.layer_panel
    strand = next(s for s in canvas.strands if type(s).__name__ == "Strand")
    gp = lp.group_layer_manager.group_panel
    gp.create_group("SoundTest", list(canvas.strands))
    pump(200)
    group_strands = list(canvas.strands)
    # the same data GroupPanel.edit_strand_angles hands the dialog
    group_data = {"strands": group_strands, "layers": [s.layer_name for s in group_strands],
                  "editable_layers": [s.layer_name for s in group_strands]}

    dialogs = [
        ("Shadow editor", lambda: ShadowEditorDialog(canvas, strand, parent=lp)),
        ("Width", lambda: WidthConfigDialog(strand, lp, lp)),
        ("Width (elliptical)", lambda: WidthConfigDialog(strand, lp, lp, show_elliptical=True)),
        ("End style", lambda: EndStyleDialog(strand, 1, lp, lp)),
        ("Group shadow", lambda: GroupShadowEditorDialog(canvas, "SoundTest", group_strands, parent=gp)),
        ("Mask grid", lambda: MaskGridDialog(canvas, "SoundTest", parent=lp)),
        ("Move group", lambda: GroupMoveDialog(canvas, "SoundTest", parent=w)),
        ("Rotate group", lambda: GroupRotateDialog("SoundTest", group_panel=gp, parent=w)),
        ("Edit strand angles", lambda: StrandAngleEditDialog("SoundTest", group_data, canvas=canvas)),
    ]

    for area, make in dialogs:
        try:
            opened = []

            def open_it():
                d = make()
                WATCHER.keep.add(id(d))
                opened.append(d)
                d.show()

            run_check(rec, area, "window", "open", open_it, "dialog_open")
            for d in opened:
                d.close()
            pump(80)
            sweep_dialog(rec, w, make, area, "blue")
        except Exception as e:
            record(area, "window", "open", "dialog_open", "-", False, f"error: {type(e).__name__}: {e}")
            traceback.print_exc()
        close_stray_dialogs(w)


def check_mode_off_sounds(w, rec):
    """Leaving View, Select or Attach by clicking another mode button plays that mode's off
    sound first; leaving the other modes plays only the new mode's sound."""
    OFF = ("mode_view_off", "mode_select_off", "mode_attach_off")
    click(w.move_button)
    pump(200)
    steps = [
        (w.view_button, "View", "mode_view", None),
        (w.select_strand_button, "Select", "mode_select", "mode_view_off"),
        (w.attach_button, "Attach", "mode_attach", "mode_select_off"),
        (w.view_button, "View", "mode_view", "mode_attach_off"),
        (w.move_button, "Move", "mode_move", "mode_view_off"),
        (w.rotate_button, "Rotate", "mode_rotate", None),
    ]
    for button, name, on, off in steps:
        before = w.current_mode
        if off:
            run_check(rec, "Mode switching", name, f"click, leaving {before}", lambda b=button: click(b), exact=[off, on])
        else:
            run_check(rec, "Mode switching", name, f"click, leaving {before}", lambda b=button: click(b), on,
                      forbidden=OFF)

    # Two quick mode clicks: the first click's delayed sound must not play after the second.
    # A real second click arrives through the event loop, so let it run briefly in between
    # (10 ms, well inside the 70 ms gap before Select's own sound).
    click(w.view_button)
    pump(200)
    run_check(rec, "Mode switching", "Select, then Attach at once", "two clicks within the off-sound gap",
              lambda: (click(w.select_strand_button), pump(10), click(w.attach_button)),
              exact=["mode_view_off", "mode_select_off", "mode_attach"])

    # Angle Adjust with a strand selected enters Angle Adjust and plays its own sound
    click(w.attach_button)
    pump(200)
    if w.canvas.strands:
        w.select_strand(0)
        pump(150)
        # its dialog opens on the click, so the sounds must play then, not once it closes
        wait_between()
        rec.clear()
        click(w.angle_adjust_button)
        pump(150)
        got = [c for c in rec.requested if c not in HOVER_CUES]
        modes = [c for c in got if c.startswith("mode_")]
        # the test closes the dialog within a few ms, so only the off sound (played at once) is
        # checked against it; the on sound follows 70 ms later
        ok = modes == ["mode_attach_off", "mode_angle"] and (
            "dialog_close" not in got or got.index("mode_attach_off") < got.index("dialog_close"))
        record("Mode switching", "Angle Adjust, strand selected", "click, leaving attach",
               "mode_attach_off (before its dialog closes), mode_angle", got, ok)
        close_stray_dialogs(w)
        click(w.attach_button)
        pump(200)

    # Angle Adjust with no strand selected does not enter Angle Adjust: the mode the app falls
    # back to plays, and an off sound plays only if a mode was really left
    click(w.view_button)
    pump(200)
    w.canvas.deselect_all_strands()
    pump(100)
    wait_between()
    rec.clear()
    click(w.angle_adjust_button)
    pump(150)
    got = [c for c in rec.requested if c not in HOVER_CUES]
    after = w.current_mode
    expected = ([] if after == "view" else ["mode_view_off", w.MODE_ON_CUES[after]]) if after != "angle_adjust" else None
    if after == "view":
        ok = "mode_view_off" not in got
    else:
        ok = expected is not None and got == expected
    record("Mode switching", "Angle Adjust, no strand selected", f"click, leaving view (ends in {after})",
           "no off sound" if after == "view" else ", ".join(expected or ["-"]), got, ok)
    click(w.attach_button)
    pump(200)


def check_row_hover(rec, area, view, cue):
    """Rows of a list or tree hover once per row."""
    if hasattr(view, "expandAll"):
        view.expandAll()
        pump(100)
    rows = []

    def walk(parent):
        for r in range(view.model().rowCount(parent)):
            index = view.model().index(r, 0, parent)
            rect = view.visualRect(index)
            if rect.isValid() and view.viewport().rect().contains(rect.center()):
                rows.append(rect)
            walk(index)

    walk(view.rootIndex())
    if len(rows) < 2:
        record(area, "rows", "hover", cue, "-", False, f"only {len(rows)} visible rows to hover")
        return
    QTest.mouseMove(view.viewport(), QPoint(1, view.viewport().height() - 1))
    pump(100)
    run_check(rec, area, "a row", "pointer reaches it", lambda: QTest.mouseMove(view.viewport(), rows[0].center()), cue)
    wait_between()
    rec.clear()
    QTest.mouseMove(view.viewport(), rows[0].center() + QPoint(4, 0))
    pump(110)
    record(area, "the same row", "pointer moves within it", f"no {cue}", list(rec.requested),
           cue not in rec.requested, "one hover per row, not one per mouse move")
    run_check(rec, area, "the next row", "pointer reaches it", lambda: QTest.mouseMove(view.viewport(), rows[1].center()), cue)


def check_group_rows(w, rec):
    from PyQt5.QtWidgets import QAbstractItemView
    view = next((v for v in w.layer_panel.right_panel.findChildren(QAbstractItemView) if v.isVisible()), None)
    if view is None:
        record("Group panel", "group tree", "hover", "hover_group", "-", False, "no visible group tree")
        return
    check_row_hover(rec, "Group panel", view, "hover_group")


def check_levels(w, rec):
    """Level rows sound like close cousins of layer buttons: the name and the fold control
    at its left edge each have their own hover and click."""
    from level_button import FOLD_ZONE_WIDTH, LevelButton
    lp = w.layer_panel
    if not any(b.isVisible() for b in lp.findChildren(LevelButton)):
        click(lp.new_level_button)
        pump(400)
    button = next((b for b in lp.findChildren(LevelButton) if b.isVisible() and b.row.level > 0), None)
    if button is None:
        record("Levels", "level row", "create", "a level row", "-", False, "New Level made no level row")
        return
    lp.scroll_area.ensureWidgetVisible(button)
    pump(150)
    name_pt = QPoint(FOLD_ZONE_WIDTH + (button.width() - FOLD_ZONE_WIDTH) // 2, button.height() // 2)
    fold_pt = QPoint(FOLD_ZONE_WIDTH // 2, button.height() // 2)
    QTest.mouseMove(w, QPoint(1, 1))
    pump(150)
    run_check(rec, "Levels", "level name", "pointer enters it", lambda: QTest.mouseMove(button, name_pt), "hover_level")
    run_check(rec, "Levels", "fold control", "pointer moves onto it", lambda: QTest.mouseMove(button, fold_pt),
              "hover_level_fold")
    run_check(rec, "Levels", "level name", "pointer moves back onto it", lambda: QTest.mouseMove(button, name_pt),
              "hover_level")
    run_check(rec, "Levels", "fold control", "click (collapse)", lambda: click(button, fold_pt), "level_fold")
    run_check(rec, "Levels", "fold control", "click (expand)", lambda: click(button, fold_pt), "level_fold")
    if lp.level_selection_allowed():
        run_check(rec, "Levels", "level name", "click (select the level)", lambda: click(button, name_pt), "level_select")
        run_check(rec, "Levels", "level name", "click again", lambda: click(button, name_pt), "level_select")


def check_level_menu(w, rec):
    """The level right-click menu opens, hovers and picks with its own sounds, close cousins
    of the other menus' sounds; the Recolor menu it opens sounds the same."""
    from level_button import LevelButton
    lp = w.layer_panel
    button = next((b for b in lp.findChildren(LevelButton) if b.isVisible() and b.row.level > 0), None)
    if button is None:
        record("Level menu", "level row", "right-click", "a level row", "-", False, "no level row to right-click")
        return
    lp.scroll_area.ensureWidgetVisible(button)
    pump(150)

    def row(menu, key):
        text = lp.level_text(key)
        return next((a for a in menu.actions() if isinstance(a, QWidgetAction) and a.defaultWidget() is not None
                     and a.defaultWidget().text() == text), None)

    def when_menu_opens(after, then):
        """Run *then* with the next menu that pops up (not *after*) while it is open."""
        def poll(tries=50):
            menu = QApplication.activePopupWidget()
            if isinstance(menu, QMenu) and menu is not after and menu.isVisible():
                then(menu)
                menu.close()
            elif tries:
                QTimer.singleShot(20, lambda: poll(tries - 1))
        QTimer.singleShot(0, poll)

    def check_open_and_hover(menu, name):
        record("Level menu", name, "opens", "menu_open_level", list(rec.requested),
               "menu_open_level" in rec.requested and "menu_open" not in rec.requested)
        items = [a for a in menu.actions() if a.isEnabled() and not a.isSeparator()]
        for action in items[:2]:
            text = action.defaultWidget().text() if isinstance(action, QWidgetAction) else action.text()
            run_check(rec, "Level menu", f"{name} item '{' '.join(re.sub('<[^>]+>|&nbsp;', ' ', text).split())}'", "pointer reaches it",
                      lambda a=action: menu.setActiveAction(a), "hover_menu_level", forbidden=("hover_menu",))

    def right_click():
        centre = button.rect().center()
        QApplication.sendEvent(button, QContextMenuEvent(QContextMenuEvent.Mouse, centre, button.mapToGlobal(centre)))
        pump(150)

    def open_and_pick(key, then=None):
        """Open the level menu, check it, pick the row *key*; *then* checks a menu the pick opens."""
        def inside(menu):
            check_open_and_hover(menu, "level menu")
            action = row(menu, key)
            if action is None:
                record("Level menu", key, "pick it", "menu_pick_level", "-", False, "row not found")
                return
            if then is not None:
                when_menu_opens(menu, then)
            run_check(rec, "Level menu", lp.level_text(key), "pick it",
                      lambda: click(menu, menu.actionGeometry(action).center()), "menu_pick_level",
                      forbidden=("ui_click",))
        wait_between()
        rec.clear()
        when_menu_opens(None, inside)
        right_click()

    WATCHER.timer.stop()  # the test closes these menus itself
    try:
        folded = lp.is_level_folded(button.row.level)
        open_and_pick('level_unfold_above' if folded else 'level_fold_above')
        open_and_pick('level_fold_above' if folded else 'level_unfold_above')  # back as it was

        def recolor(menu):
            check_open_and_hover(menu, "Recolor menu")
        open_and_pick('level_recolor', then=recolor)
    finally:
        WATCHER.timer.start(40)
    close_stray_dialogs(w)


def check_select_mode(w, rec):
    """Select mode is one click long: a click on a strand selects it and a click on the empty
    canvas clears the selection, then the app goes back to Attach."""
    canvas = w.canvas
    strand = next((s for s in canvas.strands if not getattr(s, "is_hidden", False)), None)
    if strand is None:
        record("Select mode", "strand", "click", "a strand", "-", False, "no strand on the canvas")
        return
    on_strand = canvas.canvas_to_screen((strand.start + strand.end) / 2).toPoint()
    empty = QPoint(3, 3)

    def tap(pos):
        if canvas.current_mode is not canvas.select_mode:
            canvas.set_mode("select")
            pump(50)
        mouse(canvas, QEvent.MouseButtonPress, pos)
        mouse(canvas, QEvent.MouseButtonRelease, pos, buttons=Qt.NoButton)

    run_check(rec, "Select mode", "a strand", "click", lambda: tap(on_strand), "strand_select")
    run_check(rec, "Select mode", "empty canvas", "click (a strand was selected)", lambda: tap(empty),
              "strand_deselect")
    run_check(rec, "Select mode", "empty canvas", "click (nothing selected)", lambda: tap(empty), None,
              note="nothing to clear, so it stays silent")


def check_layer_state(w, rec):
    """State turns on and opens its window; the window is modal, so it closes before State
    can be clicked again, and closing it plays State's off sound instead of dialog_close."""
    close_stray_dialogs(w)
    run_check(rec, "Main window", "State", "click, then its window closes", lambda: click(w.layer_state_button),
              {"layer_state_on", "dialog_open", "layer_state_off"}, forbidden=("dialog_close",))
    close_stray_dialogs(w)


def check_settings(w, rec):
    from settings_dialog import DefaultWidthConfigDialog
    run_check(rec, "Settings", "settings button", "click", lambda: click(w.settings_button), {"toolbar_settings", "dialog_open"})
    sd = w.settings_dialog
    WATCHER.keep.add(id(sd))
    pump(200)
    button = next((b for b in sd.findChildren(QPushButton) if b.isVisible() and b.isEnabled()), None)
    if button is not None:
        run_check(rec, "Settings", label(button), "pointer enters it",
                  lambda: QApplication.sendEvent(button, QEvent(QEvent.Enter)), "hover_settings")
    check_row_hover(rec, "Settings sidebar", sd.categories_list, "hover_settings")
    lst = sd.categories_list
    skip_pages = set()
    for i in range(lst.count()):
        item = lst.item(i)
        title = item.text()
        if i == lst.currentRow():
            pass
        run_check(rec, "Settings sidebar", title, "click", lambda: click(lst.viewport(), lst.visualItemRect(item).center()),
                  "tab_switch" if i != lst.currentRow() else "tab_switch")
        pump(150)
        # Language buttons would change the whole UI language, sample buttons replace the canvas
        page = sd.stacked_widget.currentWidget()
        if page in (getattr(sd, "change_language_widget", None), getattr(sd, "samples_widget", None),
                    getattr(sd, "tutorial_widget", None)):
            skip_pages.add(title)
            continue
        def reopen(row=i):
            click(w.settings_button)
            pump(250)
            lst.setCurrentRow(row)
            sd.change_category(lst.item(row))  # the sidebar switches pages on itemClicked
            pump(150)

        sweep_page(rec, w, sd, page, f"Settings: {title}", reopen)
    record("Settings", "pages", "not swept", "-", sorted(skip_pages), True,
           "language buttons change the whole UI, samples replace the canvas, tutorials play video")
    sweep_dialog(rec, w, lambda: DefaultWidthConfigDialog(sd, sd), "Default width", "blue")
    if not sd.isVisible():
        click(w.settings_button)
        pump(250)
    run_check(rec, "Settings", "window", "close", lambda: sd.close(), exact=["dialog_close"])


def sweep_page(rec, w, sd, page, area, reopen):
    done = set()
    for _ in range(MAX_CONTROLS_PER_WINDOW):
        controls = [c for c in page.findChildren(QWidget)
                    if isinstance(c, (QAbstractButton, QAbstractSlider, QComboBox))
                    and control_key(c) not in done and c.isVisible() and c.isEnabled()
                    and type(c).__name__ != "QScrollBar"]
        if not controls:
            break
        c = controls[0]
        done.add(control_key(c))
        name = label(c)
        try:
            if isinstance(c, QCheckBox):
                was = c.isChecked()
                run_check(rec, area, name, "tick", lambda: click(c, checkbox_pos(c)), f"toggle_green_{'off' if was else 'on'}")
                run_check(rec, area, name, "untick", lambda: click(c, checkbox_pos(c)), f"toggle_green_{'on' if was else 'off'}")
            elif isinstance(c, QAbstractSlider):
                value = c.value()
                run_check(rec, area, name, "click the track", lambda: click(c, QPoint(c.width() - 4, c.height() // 2)),
                          "snap_grid")
                c.setValue(value)
            elif isinstance(c, QComboBox):
                run_check(rec, area, name, "open", lambda: QTest.mousePress(c, Qt.LeftButton), "menu_open")
                view = c.view()
                rect = view.visualRect(c.model().index(c.currentIndex(), 0))
                if view.isVisible() and rect.isValid():
                    run_check(rec, area, name, "pick the current value", lambda: click(view.viewport(), rect.center()),
                              "ui_click")
                c.hidePopup()
            elif stepper_cue(c):
                run_check(rec, area, name, "click", lambda: click(c), stepper_cue(c))
            elif c.isCheckable():
                was = c.isChecked()
                run_check(rec, area, name, "toggle", lambda: click(c), f"toggle_green_{'off' if was else 'on'}")
                run_check(rec, area, name, "toggle back", lambda: click(c), f"toggle_green_{'on' if was else 'off'}")
            else:
                wait_between()
                rec.clear()
                click(c)
                pump(200)
                got = [cue for cue in rec.requested if cue not in HOVER_CUES]
                if not sd.isVisible():
                    record(area, name, "click (closes Settings)", "exactly dialog_close", got, got == ["dialog_close"],
                           "a closing button plays only the close sound")
                    reopen()
                else:
                    record(area, name, "click", "ui_click", got, "ui_click" in got,
                           "pop-ups it opens are dismissed by the test")
            close_stray_dialogs(w, keep=(sd,))
        except RuntimeError:
            record(area, name, "use", "-", "-", True, "control removed by the action itself")


def check_menus_and_popups(w, rec):
    from numbered_layer_button import NumberedLayerButton
    lp = w.layer_panel
    layer = next((b for b in lp.findChildren(NumberedLayerButton) if b.isVisible()), None)
    if layer is not None:
        def right_click():
            QTest.mousePress(layer, Qt.RightButton)
            QTest.mouseRelease(layer, Qt.RightButton)
            QApplication.sendEvent(layer, QContextMenuEvent(QContextMenuEvent.Mouse, layer.rect().center(),
                                                            layer.mapToGlobal(layer.rect().center())))

        run_check(rec, "Menus", "layer button", "right-click", right_click,
                  "menu_open", note="the menu is closed again by the test")
    menu = QMenu(w)
    menu.addAction("first item")
    menu.addAction("second item")
    WATCHER.keep.add(id(menu))
    run_check(rec, "Menus", "a QMenu", "open", lambda: menu.popup(w.mapToGlobal(QPoint(200, 200))), "menu_open")
    first, second = menu.actions()[0], menu.actions()[1]
    # Qt ignores the first mouse move after a menu opens, so move once before checking
    QTest.mouseMove(menu, menu.actionGeometry(second).center())
    pump(150)
    run_check(rec, "Menus", "a QMenu item", "pointer reaches it",
              lambda: QTest.mouseMove(menu, menu.actionGeometry(first).center()), "hover_menu")
    wait_between()
    rec.clear()
    QTest.mouseMove(menu, menu.actionGeometry(first).center() + QPoint(3, 0))
    pump(110)
    record("Menus", "the same item", "pointer moves within it", "no hover_menu", list(rec.requested),
           "hover_menu" not in rec.requested, "one hover per item, not one per mouse move")
    run_check(rec, "Menus", "the next item", "pointer reaches it",
              lambda: QTest.mouseMove(menu, menu.actionGeometry(second).center()), "hover_menu")
    # A row made of its own buttons (like Dash: Show Start Dash | Show End Dash): the row is
    # silent, each button hovers
    from PyQt5.QtWidgets import QHBoxLayout, QLabel
    row = QWidget()
    row_layout = QHBoxLayout(row)
    row_layout.addWidget(QLabel("Dash"))
    start_btn, end_btn = QPushButton("Show Start Dash"), QPushButton("Show End Dash")
    row_layout.addWidget(start_btn)
    row_layout.addWidget(end_btn)
    row_action = QWidgetAction(menu)
    row_action.setDefaultWidget(row)
    menu.addAction(row_action)
    pump(100)
    wait_between()
    rec.clear()
    menu.setActiveAction(row_action)
    pump(110)
    record("Menus", "a row of buttons", "pointer reaches the row", "no row hover",
           list(rec.requested), "hover_menu" not in rec.requested, "its buttons hover instead")
    run_check(rec, "Menus", "Show Start Dash", "pointer enters it",
              lambda: QApplication.sendEvent(start_btn, QEvent(QEvent.Enter)), "hover_menu")
    run_check(rec, "Menus", "Show End Dash", "pointer enters it",
              lambda: QApplication.sendEvent(end_btn, QEvent(QEvent.Enter)), "hover_menu")
    action = menu.actions()[0]
    run_check(rec, "Menus", "a QMenu item", "pick it", lambda: click(menu, menu.actionGeometry(action).center()), "ui_click")
    WATCHER.keep.discard(id(menu))
    menu.close()
    # Group menus hover with their own sound
    group_menu = QMenu(w)
    group_menu.setProperty("hoverCue", "hover_menu_group")
    g1, g2 = group_menu.addAction("Move Group"), group_menu.addAction("Rotate Group")
    WATCHER.keep.add(id(group_menu))
    group_menu.popup(w.mapToGlobal(QPoint(260, 260)))
    pump(150)
    # highlight the items directly: a synthetic pointer move into a fresh popup is sometimes ignored
    group_menu.setActiveAction(g2)
    pump(150)
    run_check(rec, "Menus", "a group menu item", "pointer reaches it",
              lambda: group_menu.setActiveAction(g1), "hover_menu_group")
    WATCHER.keep.discard(id(group_menu))
    group_menu.close()
    warn = QMessageBox(QMessageBox.Warning, "Warning", "Something was blocked", parent=w)
    WATCHER.keep.add(id(warn))
    run_check(rec, "Pop-ups", "warning", "shows", lambda: warn.show(), "denied")
    run_check(rec, "Pop-ups", "warning", "closes", lambda: warn.close(), exact=["dialog_close"])
    info = QMessageBox(QMessageBox.Information, "Info", "Done", parent=w)
    WATCHER.keep.add(id(info))
    run_check(rec, "Pop-ups", "information", "shows", lambda: info.show(), "dialog_open")
    info.close()


def check_padlock(w, rec):
    from numbered_layer_button import NumberedLayerButton
    lp = w.layer_panel
    if not lp.lock_mode:
        click(lp.lock_layers_button)
        pump(300)

    def layer():
        return next(b for b in lp.findChildren(NumberedLayerButton) if b.isVisible())

    run_check(rec, "Lock mode", "layer padlock", "click to lock",
              lambda: click(layer(), layer().lock_button_rect().center()), "ui_toggle_on")
    run_check(rec, "Lock mode", "layer padlock", "click to unlock",
              lambda: click(layer(), layer().lock_button_rect().center()), "ui_toggle_off")
    click(lp.lock_layers_button)
    pump(300)


def check_tabs(w, rec):
    from tab_bar_widget import IconButton, TabChip
    if not w.tabs_button.isChecked():
        click(w.tabs_button)
        pump(300)
    edge = getattr(w, "tab_edge", None)
    if edge is None or not edge.isVisible():
        record("Tabs", "tab bar", "shown", "visible", "hidden", False)
        return
    plus = edge.plus_btn
    run_check(rec, "Tabs", "+ (new tab)", "click", lambda: click(plus), "new_strand")
    pump(300)
    chips = [c for c in edge.findChildren(TabChip) if c.isVisible()]
    if len(chips) >= 2:
        run_check(rec, "Tabs", "a tab", "click to switch", lambda: click(chips[0], QPoint(12, chips[0].height() // 2)),
                  "tab_switch")
        pump(200)
        chips = [c for c in edge.findChildren(TabChip) if c.isVisible()]
    dup = next((b for b in edge.findChildren(IconButton) if b.kind == "duplicate" and b.isVisible()), None)
    if dup is not None:
        run_check(rec, "Tabs", "duplicate tab", "click", lambda: click(dup), "new_strand")
        pump(300)
    close = next((b for b in reversed(edge.findChildren(IconButton)) if b.kind == "close" and b.isVisible()), None)
    if close is not None:
        run_check(rec, "Tabs", "close tab", "click", lambda: click(close), "delete",
                  note="any 'unsaved changes' prompt is dismissed by the test")
        pump(300)


def check_save(w, rec):
    target = os.path.join(SETTINGS_DIR, "sound_check_project.json")
    original = QFileDialog.getSaveFileName
    QFileDialog.getSaveFileName = staticmethod(lambda *a, **k: (target, "JSON Files (*.json)"))
    try:
        run_check(rec, "Saving", "Save button", "click and save", lambda: click(w.save_button), {"ui_click", "save_done"})
    finally:
        QFileDialog.getSaveFileName = original
    record("Saving", "Save button", "file written", "exists", os.path.exists(target), os.path.exists(target))


def check_settings_behaviour(w, rec):
    import sound_manager
    m = sound_manager.manager()
    b = w.view_button
    m.set_enabled(False)
    run_check(rec, "Sound settings", "sounds off", "click a button", lambda: click(b), None)
    m.set_enabled(True)
    volume = m.volume
    m.set_volume(0)
    run_check(rec, "Sound settings", "volume 0", "click a button", lambda: click(b), None)
    m.set_volume(volume)
    m.set_hover_enabled(False)
    run_check(rec, "Sound settings", "hover sounds off", "hover a button",
              lambda: (QTest.mouseMove(w, QPoint(1, 1)), pump(30), QTest.mouseMove(w.move_button)), None)
    m.set_hover_enabled(True)
    run_check(rec, "Sound settings", "repeat limit", "5 clicks within 10 ms",
              lambda: [sound_manager.play("ui_click") for _ in range(5)], exact=["ui_click"])
    run_check(rec, "Sound settings", "repeat limit", "two different sounds at once",
              lambda: (sound_manager.play("ui_click"), sound_manager.play("tab_switch")), exact=["ui_click", "tab_switch"])
    m.set_volume(30)
    m.set_hover_enabled(False)
    path = Path(sound_manager.settings_file_path())
    w.settings_dialog.save_settings_to_file()
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    ok = "SoundVolume: 30" in text and "SoundHover: false" in text and "SoundEnabled: true" in text
    reloaded = sound_manager.SoundManager()
    ok = ok and reloaded.volume == 30 and reloaded.hover_enabled is False
    record("Sound settings", "user_settings.txt", "save and load", "volume 30, hover off, enabled",
           f"volume {reloaded.volume}, hover {reloaded.hover_enabled}, enabled {reloaded.enabled}", ok)
    m.set_volume(volume)
    m.set_hover_enabled(True)


def check_coverage(rec, audio_ok):
    import sound_manager
    never = sorted(set(sound_manager.CUES) - rec.ever)
    record("Coverage", f"all {len(sound_manager.CUES)} sounds", "each one played by a real action", "none missing", never or "none missing",
           not never)
    if audio_ok:
        silent = sorted(rec.ever - rec.audible)
        record("Coverage", "speakers", "each sound that played really started", "all started",
               silent or "all started", not silent)


# --------------------------------------------------------------------------- driver
WATCHER = None


def load_sample(w):
    from save_load_manager import apply_loaded_strands, load_strands_from_data
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    loaded = load_strands_from_data(data, w.canvas)
    apply_loaded_strands(w.canvas, loaded[0], loaded[1])
    w.canvas.selected_strand = None
    pump(400)


def run_checks(app):
    global WATCHER
    from main_window import MainWindow
    import sound_manager
    w = next(t for t in app.topLevelWidgets() if isinstance(t, MainWindow))
    w.showNormal()
    w.resize(1600, 1000)
    pump(600)
    global MANAGER
    m = sound_manager.manager()
    MANAGER = m
    # quiet but not muted: volume 0 would stop the sounds from being played at all
    m.set_volume(int(os.environ.get("SOUND_CHECK_VOLUME", "1")))
    rec = Recorder(m)
    WATCHER = ModalWatcher(app, w)

    steps = [
        ("files", lambda: check_files(m)),
        ("canvas", lambda: check_canvas(w, rec)),
        ("sample", lambda: load_sample(w)),
        ("main buttons", lambda: check_main_buttons(w, rec, set())),
        ("masks tab buttons", lambda: (click(w.layer_panel.masks_tab_button), pump(200),
                                       check_main_buttons(w, rec, set()),
                                       click(w.layer_panel.strands_tab_button), pump(200))),
        ("hover", lambda: check_hover(w, rec)),
        ("padlock", lambda: check_padlock(w, rec)),
        ("menus", lambda: check_menus_and_popups(w, rec)),
        ("dialogs", lambda: check_dialogs(w, rec)),
        ("mode off sounds", lambda: check_mode_off_sounds(w, rec)),
        ("group rows", lambda: check_group_rows(w, rec)),
        ("levels", lambda: check_levels(w, rec)),
        ("level menu", lambda: check_level_menu(w, rec)),
        ("select mode", lambda: check_select_mode(w, rec)),
        ("layer state", lambda: check_layer_state(w, rec)),
        ("settings", lambda: check_settings(w, rec)),
        ("tabs", lambda: check_tabs(w, rec)),
        ("save", lambda: check_save(w, rec)),
        ("settings behaviour", lambda: check_settings_behaviour(w, rec)),
    ]
    audio_ok = check_loading(m)
    for name, step in steps:
        try:
            step()
        except Exception as e:
            record("Run", name, "step", "completes", f"{type(e).__name__}: {e}", False)
            traceback.print_exc()
        close_stray_dialogs(w)
    pump(400)
    check_coverage(rec, audio_ok)


def report():
    failed = [r for r in RESULTS if not r["ok"]]
    width = max(len(r["area"]) for r in RESULTS)
    for r in RESULTS:
        mark = "PASS" if r["ok"] else "FAIL"
        print(f"{mark}  {r['area']:<{width}}  {r['control']} | {r['action']} | expected {r['expected']} | got {r['got']}"
              + (f" | {r['note']}" if r["note"] else ""))
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed, {len(failed)} failed")
    if REPORT_PATH:
        Path(REPORT_PATH).write_text(json.dumps(RESULTS, indent=1, default=str), encoding="utf-8")
    return 1 if failed else 0


def patched_exec(*_args, **_kwargs):
    app = QApplication.instance()
    code = 1
    try:
        run_checks(app)
        code = report()
    except Exception:
        traceback.print_exc()
    finally:
        if USER_SETTINGS_BACKUP is not None:
            USER_SETTINGS_COPY.write_bytes(USER_SETTINGS_BACKUP)
        elif USER_SETTINGS_COPY.exists():
            USER_SETTINGS_COPY.unlink()
        shutil.rmtree(SETTINGS_DIR, ignore_errors=True)
        sys.stdout.flush()
    return code


if __name__ == "__main__":
    QApplication.exec_ = patched_exec
    QApplication.exec = patched_exec
    sys.argv = [str(SRC / "main.py")]
    runpy.run_path(str(SRC / "main.py"), run_name="__main__")
