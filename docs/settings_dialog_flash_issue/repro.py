"""Reproduce the settings-dialog position flash with a millisecond event timeline."""
import sys, os, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
SRC = r"C:\Users\YonatanSetbon\projects\OpenStrandStudio\src"
sys.path.insert(0, SRC)
os.chdir(SRC)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QElapsedTimer, QTimer, QEvent, QObject

from main_window import MainWindow

app = QApplication(sys.argv)
window = MainWindow()
window.showMaximized()

clock = QElapsedTimer()
clock.start()
log = []

EVENT_NAMES = {
    QEvent.Show: 'Show',
    QEvent.Hide: 'Hide',
    QEvent.Move: 'Move',
    QEvent.Resize: 'Resize',
    QEvent.WinIdChange: 'WinIdChange',
    QEvent.ShowToParent: 'ShowToParent',
    QEvent.HideToParent: 'HideToParent',
    QEvent.WindowStateChange: 'WindowStateChange',
    QEvent.ParentChange: 'ParentChange',
}


class SpyFilter(QObject):
    def eventFilter(self, obj, ev):
        name = EVENT_NAMES.get(ev.type())
        if name:
            g = obj.geometry()
            fg = obj.frameGeometry()
            log.append(
                f"{clock.elapsed():6d} ms  {name:17s} pos=({g.x():5d},{g.y():5d}) "
                f"frame=({fg.x():5d},{fg.y():5d}) size={g.width()}x{g.height()} "
                f"visible={obj.isVisible()}"
            )
        return False


spy = SpyFilter()

def poll():
    d = getattr(window, '_settings_dialog', None)
    if d is not None and d.isVisible():
        fg = d.frameGeometry()
        entry = f"poll frame=({fg.x()},{fg.y()}) size={fg.width()}x{fg.height()}"
        # Only log position changes to keep the timeline readable
        if not hasattr(poll, 'last') or poll.last != entry:
            poll.last = entry
            log.append(f"{clock.elapsed():6d} ms  {entry}")


poll_timer = QTimer()
poll_timer.setInterval(5)
poll_timer.timeout.connect(poll)


def open_once(label):
    mw = window.frameGeometry()
    log.append(f"--- {label} at {clock.elapsed()} ms (main window frame=({mw.x()},{mw.y()}) {mw.width()}x{mw.height()}) ---")
    dlg = window.settings_dialog
    dlg.installEventFilter(spy)
    window.open_settings_dialog()
    d = window._settings_dialog
    fg = d.frameGeometry()
    log.append(f"{clock.elapsed():6d} ms  open() returned    frame=({fg.x()},{fg.y()}) size={fg.width()}x{fg.height()}")


def stage1():
    poll_timer.start()
    open_once('FIRST OPEN')
    QTimer.singleShot(1500, stage2)


def stage2():
    log.append(f"--- closing dialog at {clock.elapsed()} ms ---")
    window._settings_dialog.close()
    QTimer.singleShot(500, stage3)


def stage3():
    open_once('SECOND OPEN')
    QTimer.singleShot(1500, finish)


def finish():
    print("\n".join(log))
    app.quit()


QTimer.singleShot(1500, stage1)
sys.exit(app.exec_())
