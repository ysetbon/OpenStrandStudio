"""Dialogs the user can shrink.

Qt hands a window a minimum size big enough for everything inside it, so a
dialog laid out for a roomy screen cannot be made any smaller.  On a short
screen that is how a bottom row of OK / Cancel buttons ends up below the
edge of the display with no way to reach it.

The Stylize End Side dialog fixed that for itself by putting its body in a
scroll area and keeping the header and the buttons outside it.  These
helpers are that same treatment, packaged so the other dialogs can take it:

``make_shrinkable``  moves a dialog's whole layout into a scroll area,
                     pinning a header above it and a button row below it.
``allow_shrinking``  for a dialog whose body already scrolls (a table, a
                     list, its own scroll area): drop the floor and let the
                     body give up the space.
``relax``            stops a long or wrapped label from setting that floor.
``scroll_area``      the frameless, see-through scroll area both of the
                     above put the body in.
``fit_to_screen``    opens a dialog at its natural size, and
``cap_to_screen``    at a size of your choosing - neither larger than the
                     screen the dialog is on.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QFrame, QLayout, QScrollArea, QVBoxLayout,
                             QWidget)

# Qt's QWIDGETSIZE_MAX, which PyQt does not export
QWIDGETSIZE_MAX = 16777215

# Small enough to fit on any screen the app runs on, large enough that the
# dialog is still worth looking at
DEFAULT_MINIMUM = (380, 260)

_TRANSPARENT_AREA = "QScrollArea { background: transparent; border: none; }"


def screen_of(widget):
    """The screen ``widget`` is on, falling back to the primary one."""
    screen = None
    try:
        screen = widget.screen()
    except AttributeError:  # Qt < 5.14
        pass
    if screen is None:
        screen = QApplication.primaryScreen()
    return screen


def cap_to_screen(dialog, width, height, fraction=0.9):
    """Open at ``width`` x ``height``, capped to the screen it is on.

    Anything that no longer fits is reached by scrolling rather than by
    dragging the window off the edge of the display."""
    screen = screen_of(dialog)
    if screen is not None:
        available = screen.availableGeometry()
        width = min(width, int(available.width() * fraction))
        height = min(height, int(available.height() * fraction))
    dialog.resize(max(width, dialog.minimumWidth()), max(height, dialog.minimumHeight()))


def fit_to_screen(dialog, fraction=0.9):
    """Open at the size the content asks for, capped to the screen."""
    hint = dialog.sizeHint()
    cap_to_screen(dialog, hint.width(), hint.height(), fraction)


def relax(*widgets, width=1, height=1):
    """Let the layout squeeze these widgets below their natural size.

    A label is as wide as its text and, once it wraps, as tall as that text
    needs to be at that width, and a layout reads both as a floor the whole
    window can never go under.  An explicit minimum replaces that floor, so
    the dialog shrinks and the label is what gives way."""
    for widget in widgets:
        if widget is not None:
            widget.setMinimumSize(width, height)


def allow_shrinking(dialog, minimum=DEFAULT_MINIMUM, fit=True):
    """Free a dialog whose body already scrolls.

    Setting the minimum explicitly is also what stops Qt from replacing it
    with the layout's own, much larger, idea of a minimum."""
    dialog.setMinimumSize(*minimum)
    dialog.setMaximumSize(QWIDGETSIZE_MAX, QWIDGETSIZE_MAX)
    dialog.setSizeGripEnabled(True)
    layout = dialog.layout()
    if layout is not None:
        layout.setSizeConstraint(QLayout.SetDefaultConstraint)
    if fit:
        fit_to_screen(dialog)
    return dialog


def scroll_area(parent=None, horizontal=Qt.ScrollBarAsNeeded):
    """A frameless, see-through scroll area that borrows the dialog's theme."""
    area = QScrollArea(parent)
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.NoFrame)
    area.setHorizontalScrollBarPolicy(horizontal)
    area.setStyleSheet(_TRANSPARENT_AREA)
    area.viewport().setStyleSheet("background: transparent;")
    return area


def _take(layout, item):
    """Pull ``item`` (a widget or a nested layout) out of ``layout``."""
    for index in range(layout.count()):
        entry = layout.itemAt(index)
        if entry is item or entry.widget() is item or entry.layout() is item:
            return layout.takeAt(index)
    return None


def _re_add(layout, item):
    if item is None:
        return
    widget = item.widget()
    if widget is not None:
        layout.addWidget(widget)
        return
    nested = item.layout()
    if nested is not None:
        layout.addLayout(nested)


def make_shrinkable(dialog, minimum=DEFAULT_MINIMUM, header=(), pinned=(),
                    horizontal=Qt.ScrollBarAsNeeded, fit=True):
    """Move ``dialog``'s layout into a scroll area so the window can shrink.

    ``header`` items stay above the scroll area and ``pinned`` items — the
    button row, normally — stay below it, so they are reachable at any size;
    everything else scrolls.  Each is a widget or a nested layout that the
    dialog's own top-level layout already holds.  Returns the scroll area.
    """
    body = dialog.layout()
    if body is None:
        return None

    taken_header = [_take(body, item) for item in header]
    taken_pinned = [_take(body, item) for item in pinned]

    left, top, right, bottom = body.getContentsMargins()
    spacing = body.spacing()
    body.setContentsMargins(0, 0, 0, 0)

    content = QWidget()
    content.setObjectName('shrinkableBody')
    content.setStyleSheet("#shrinkableBody { background: transparent; }")
    # QWidget.setLayout steals a layout off its previous widget parent, which
    # leaves the dialog free to take the outer layout below
    content.setLayout(body)

    area = scroll_area(dialog, horizontal)
    area.setWidget(content)

    outer = QVBoxLayout(dialog)
    outer.setContentsMargins(left, top, right, bottom)
    outer.setSpacing(max(spacing, 6))
    for item in taken_header:
        _re_add(outer, item)
    outer.addWidget(area, 1)
    for item in taken_pinned:
        _re_add(outer, item)

    dialog.setMinimumSize(*minimum)
    dialog.setMaximumSize(QWIDGETSIZE_MAX, QWIDGETSIZE_MAX)
    dialog.setSizeGripEnabled(True)
    if fit:
        fit_to_screen(dialog)
    return area

