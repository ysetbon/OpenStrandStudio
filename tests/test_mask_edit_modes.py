"""Edit Mask works whatever mode it starts from.

While a mask is being edited, a left-drag on the canvas draws the erase box
and erases, in every mode: View mode and the Pan hand never take the drag to
pan. Esc then goes back to the mode Edit Mask started from.

Runs the real MainWindow offscreen on tests/levels/continue_2x2.json.
"""
import pytest
from PyQt5.QtCore import QEvent, QPointF, Qt
from PyQt5.QtGui import QKeyEvent, QMouseEvent

from test_layer_levels import pump, window  # noqa: F401
from masked_strand import MaskedStrand


def mouse(canvas, event_type, pos, button, buttons):
    event = QMouseEvent(event_type, QPointF(*pos), button, buttons, Qt.NoModifier)
    {QEvent.MouseButtonPress: canvas.mousePressEvent,
     QEvent.MouseMove: canvas.mouseMoveEvent,
     QEvent.MouseButtonRelease: canvas.mouseReleaseEvent}[event_type](event)


def drag(canvas, start, end):
    mouse(canvas, QEvent.MouseButtonPress, start, Qt.LeftButton, Qt.LeftButton)
    mouse(canvas, QEvent.MouseMove, end, Qt.NoButton, Qt.LeftButton)
    mouse(canvas, QEvent.MouseButtonRelease, end, Qt.LeftButton, Qt.NoButton)


def press_escape(win):
    win.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier))
    pump()


@pytest.mark.parametrize("pan_hand", [False, True])
def test_edit_mask_erases_in_every_mode(window, pan_hand):  # noqa: F811
    canvas = window.canvas
    lp = window.layer_panel
    index = next(i for i, s in enumerate(canvas.strands) if isinstance(s, MaskedStrand))
    mask = canvas.strands[index]
    for mode in ("attach", "move", "select", "view", "rotate", "mask"):
        getattr(window, "set_{}_mode".format(mode))()
        pump()
        if pan_hand and not canvas.pan_mode:
            canvas.toggle_pan_mode()
        lp.request_edit_mask(index)
        assert canvas.mask_edit_mode and lp.mask_editing, mode
        erased = len(getattr(mask, "deletion_rectangles", []))
        pan = (canvas.pan_offset_x, canvas.pan_offset_y)

        drag(canvas, (300, 300), (360, 350))

        assert len(mask.deletion_rectangles) == erased + 1, mode
        assert (canvas.pan_offset_x, canvas.pan_offset_y) == pan, mode
        assert canvas.cursor().shape() == Qt.CrossCursor, mode
        assert not canvas.view_mode_panning, mode

        press_escape(window)
        assert not canvas.mask_edit_mode and not lp.mask_editing, mode
        # Back to the mode Edit Mask started from
        assert window.current_mode == mode
        if pan_hand:
            assert canvas.cursor().shape() == Qt.OpenHandCursor, mode
            canvas.exit_pan_mode()


def test_a_plain_click_while_editing_changes_nothing(window):  # noqa: F811
    canvas = window.canvas
    lp = window.layer_panel
    index = next(i for i, s in enumerate(canvas.strands) if isinstance(s, MaskedStrand))
    mask = canvas.strands[index]
    window.set_select_mode()
    pump()
    lp.request_edit_mask(index)
    erased = len(getattr(mask, "deletion_rectangles", []))
    mouse(canvas, QEvent.MouseButtonPress, (300, 300), Qt.LeftButton, Qt.LeftButton)
    mouse(canvas, QEvent.MouseButtonRelease, (300, 300), Qt.LeftButton, Qt.NoButton)
    assert len(getattr(mask, "deletion_rectangles", [])) == erased
    assert canvas.mask_edit_mode and canvas.editing_masked_strand is mask
    press_escape(window)


def test_mode_buttons_stay_off_while_editing(window):  # noqa: F811
    canvas = window.canvas
    lp = window.layer_panel
    index = next(i for i, s in enumerate(canvas.strands) if isinstance(s, MaskedStrand))
    window.set_attach_mode()
    pump()
    lp.request_edit_mask(index)
    for button in (window.view_button, window.attach_button, window.move_button,
                   window.rotate_button, window.select_strand_button,
                   window.save_button, window.load_button, window.save_image_button):
        assert not button.isEnabled()
    press_escape(window)
    assert window.view_button.isEnabled() and not window.attach_button.isEnabled()
