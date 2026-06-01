"""VISUAL demo of the 1.108 tab fixes: launches the real MainWindow, shows the
tab edge, and scripts the workflow with pauses so a human can watch. Real
dialogs appear on screen and DWELL before being auto-clicked, while the terminal
narrates each step.

Run from anywhere:
    <src>\\build_env\\Scripts\\python.exe tests\\1.108\\demo_tab_fixes.py        (English)
    <src>\\build_env\\Scripts\\python.exe tests\\1.108\\demo_tab_fixes.py he     (Hebrew / RTL)

Safety: APPDATA is redirected to a temp dir before any import, so your real
user_settings.txt is untouched.
"""

import os
import sys
import tempfile

# Windows consoles default to cp1252, which can't encode Hebrew narration.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

_TMP_APPDATA = tempfile.mkdtemp(prefix="oss_demo_appdata_")
os.environ['APPDATA'] = _TMP_APPDATA

_SRC = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
sys.path.insert(0, _SRC)

from PyQt5.QtWidgets import QApplication, QMessageBox, QFileDialog
from PyQt5.QtCore import QTimer
from main_window import MainWindow

# Slower pacing so the clicking is easy to follow.
STEP_MS = 3200          # pause between scripted steps
DIALOG_DWELL_MS = 2600  # how long a dialog stays on screen before auto-click

LANG = (sys.argv[1].strip().lower() if len(sys.argv) > 1 else 'en')


def log(msg):
    print(msg, flush=True)


class AutoResponder:
    """Lets a real QMessageBox stay visible for DIALOG_DWELL_MS, then clicks the
    button with the requested role (role-based, so it is language-independent)."""

    def __init__(self):
        self.timer = QTimer()
        self.timer.setInterval(120)
        self.timer.timeout.connect(self._tick)
        self.role = None
        self.label = ""
        self._scheduled = False

    def arm(self, role, label):
        self.role = role
        self.label = label
        self._scheduled = False
        self.timer.start()

    def _tick(self):
        if self.role is None or self._scheduled:
            return
        w = QApplication.activeModalWidget()
        if isinstance(w, QMessageBox):
            self._scheduled = True
            self.timer.stop()
            log("    [dialog on screen] holding %.1fs before clicking \"%s\"..."
                % (DIALOG_DWELL_MS / 1000.0, self.label))
            QTimer.singleShot(DIALOG_DWELL_MS, self._click)

    def _click(self):
        w = QApplication.activeModalWidget()
        if isinstance(w, QMessageBox):
            for btn in w.buttons():
                if w.buttonRole(btn) == self.role:
                    log("    [auto-click] \"%s\"  (%s)" % (btn.text(), self.label))
                    btn.click()
                    break
        self.role = None
        self._scheduled = False


def active_title(tm):
    s = tm.get_active()
    return tm.title_for(s) if s else "<none>"


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    tmp_proj = os.path.join(_TMP_APPDATA, "demo.json")
    QFileDialog.getSaveFileName = staticmethod(
        lambda *a, **k: (tmp_proj, "JSON Files (*.json)"))

    responder = AutoResponder()

    window = MainWindow()
    if LANG != 'en':
        window.set_language(LANG)  # Hebrew -> mirrors the whole window (RTL)
    window.resize(1150, 760)
    window.show()
    window.raise_()
    window.activateWindow()
    tm = window.tab_manager
    ctx = {}

    def s_intro():
        log("=" * 60)
        log("VISUAL DEMO (lang=%s) — watch the window" % LANG)
        if LANG == 'he':
            log("Hebrew: the window is mirrored RTL; dialog buttons are Hebrew.")
        log("=" * 60)
        log("STEP 1: show the floating tab edge")
        window.toggle_tabs_edge()

    def s_new2():
        log("STEP 2: click + to create a 2nd tab")
        tm.new_tab()

    def s_new3():
        log("STEP 3: click + to create a 3rd tab  (tabs: 1, 2, 3)")
        tm.new_tab()

    def s_dirty2():
        ids = [t.id for t in tm.tabs]
        ctx['A'], ctx['B'], ctx['C'] = ids[-3], ids[-2], ids[-1]
        log("STEP 4: mark tab 2 as UNSAVED (a dirty dot appears on its chip)")
        tm.find(ctx['B']).dirty = True
        tm.changed.emit()

    def s_switchA():
        log("STEP 5: switch to tab 1 — the tab we're 'working on'")
        tm.switch_to_tab(ctx['A'])
        log("        active tab is now: %s" % active_title(tm))

    def s_close_bg():
        log("STEP 6: close the BACKGROUND dirty tab 2 -> a Save dialog appears")
        responder.arm(QMessageBox.AcceptRole, "Save")
        tm.close_tab(ctx['B'])
        log("        >>> after close, active tab is: %s" % active_title(tm))
        log("        >>> FIX #2a: back on tab 1, NOT tab 3")

    def s_dirty_active():
        log("STEP 7: make the current tab UNSAVED, then try to quit")
        tm.get_active().dirty = True
        tm.changed.emit()

    def s_quit_cancel():
        log("STEP 8: close the window -> exit WARNING appears (FIX #1)")
        responder.arm(QMessageBox.RejectRole, "Cancel")
        window.close()
        log("        >>> window still visible: %s" % window.isVisible())

    def s_quit_for_real():
        log("STEP 9: close again -> 'Quit anyway' to end the demo")
        responder.arm(QMessageBox.DestructiveRole, "Quit anyway")
        window.close()

    def s_finish():
        log("-" * 60)
        log("Demo complete (lang=%s)." % LANG)
        log("=" * 60)
        app.quit()

    steps = [s_intro, s_new2, s_new3, s_dirty2, s_switchA, s_close_bg,
             s_dirty_active, s_quit_cancel, s_quit_for_real, s_finish]

    def run(i=0):
        if i >= len(steps):
            return
        steps[i]()
        QTimer.singleShot(STEP_MS, lambda: run(i + 1))

    # Safety net: force-quit if anything stalls.
    QTimer.singleShot(STEP_MS * len(steps) + DIALOG_DWELL_MS * 3 + 8000, app.quit)

    QTimer.singleShot(700, run)
    app.exec_()
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
