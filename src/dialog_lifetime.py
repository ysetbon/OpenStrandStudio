"""Dialogs that are gone once they are closed.

A dialog built with a parent belongs to that parent: Qt keeps it alive, hidden,
until the parent itself is destroyed.  For a dialog parented to the main window
or the layer panel that means until the app quits, so every colour picker,
message box or editor ever opened stayed in memory with all of its widgets,
whichever way it was closed (OK, Cancel, Esc or the window's X).

``exec_and_free``  for a dialog run with exec_(): run it, then free it.
``free_on_close``  for a dialog opened with show(): free it when it closes.
``call_later``     a delayed call about a dialog that is dropped, not run, if
                   the dialog is gone by then.
"""

from PyQt5.QtCore import Qt, QTimer


def exec_and_free(dialog):
    """Run a modal dialog and return its result; the dialog is freed after.

    The deletion is deferred to the event loop the caller returns to, so the
    code right after this call can still read the dialog (its chosen colour,
    the button that was clicked, its fields)."""
    try:
        return dialog.exec_()
    finally:
        dialog.deleteLater()


def free_on_close(dialog):
    """Have a dialog opened with show() destroyed when it closes.

    QDialog funnels every way of closing (the X, Esc, reject(), accept())
    through done(), which honours this attribute, so no path leaves the
    dialog behind."""
    dialog.setAttribute(Qt.WA_DeleteOnClose, True)
    return dialog


def call_later(owner, msec, callback):
    """Call ``callback`` after ``msec`` unless ``owner`` is destroyed first.

    QTimer.singleShot keeps a plain function or lambda alive and runs it
    whatever happened to the widgets it mentions: on a dialog closed (and
    freed) inside the delay it raises "wrapped C/C++ object has been deleted",
    which PyQt turns into a crash.  This timer belongs to ``owner`` and goes
    with it."""
    timer = QTimer(owner)
    timer.setSingleShot(True)
    timer.timeout.connect(callback)
    timer.timeout.connect(timer.deleteLater)
    timer.start(msec)
    return timer
