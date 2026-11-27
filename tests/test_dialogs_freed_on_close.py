"""A dialog that is closed is gone, not kept hidden in memory.

Dialogs are built with a parent (the main window, the layer panel), and Qt
keeps a parented dialog alive until the parent is destroyed: until the app
quits. So every colour picker, message box and editor ever opened stayed in
memory with all its widgets, whichever way it was closed.

Each case opens one dialog in a real window, closes it once with Cancel / Esc
and once with the window's X, and counts the dialogs alive before and after.
"""
import gc
import os
import sys
import tempfile
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("APPDATA", tempfile.mkdtemp(prefix="oss_dialogs_freed_"))

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT, ROOT / "src"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

SAMPLE = ROOT / "src" / "samples" / "box_stitch.json"
GROUP = "Box Stitch"


@pytest.fixture(scope="module")
def window(tmp_path_factory):
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    tmp_path = tmp_path_factory.mktemp("dialogs_freed")
    previous_appdata = os.environ.get("APPDATA")
    os.environ["APPDATA"] = str(tmp_path / "appdata")
    cwd = os.getcwd()
    os.chdir(ROOT / "src")
    try:
        from main_window import MainWindow
        w = MainWindow()
    finally:
        os.chdir(cwd)
    # The state files go to this test's own folder, never the person's.
    states = tmp_path / "temp_states"
    states.mkdir()
    undo = w.layer_panel.undo_redo_manager
    undo.temp_dir = str(states)
    w.resize(1400, 900)
    w.show()
    app.processEvents()
    assert undo.import_history(str(SAMPLE)), "sample did not import"
    w.canvas.layer_panel.refresh()
    manager = w.layer_panel.group_layer_manager
    manager.create_group_with_params(GROUP, ["1", "2"], skip_dialog=True)
    app.processEvents()
    # The group shadow editor reads the group's strand list off the canvas,
    # which holds it only once the group has been resolved (moving the group
    # does it): resolve it here so no case depends on one that ran before it.
    resolved = manager.group_panel.resolve_group_data(GROUP)
    w.canvas.groups[GROUP]['strands'] = list(resolved['strands'])
    # Settings is built once and reused on purpose; let it make its own
    # children before anything is counted.
    w.open_settings_dialog()
    app.processEvents()
    w.settings_dialog.close()
    app.processEvents()
    yield w
    w._confirm_close_with_dirty_tabs = lambda *a, **k: True
    w.close()
    if previous_appdata is None:
        os.environ.pop("APPDATA", None)
    else:
        os.environ["APPDATA"] = previous_appdata


def _flush():
    """Let the deferred deletions happen, as returning to the event loop does."""
    from PyQt5.QtCore import QEvent
    from PyQt5.QtWidgets import QApplication
    for _ in range(4):
        QApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        QApplication.processEvents()
        gc.collect()


def _dialogs_alive():
    from PyQt5.QtWidgets import QApplication
    count = 0
    for widget in QApplication.allWidgets():
        try:
            if widget.inherits("QDialog"):
                count += 1
        except RuntimeError:
            pass
    return count


def _close_modal(how):
    from PyQt5.QtWidgets import QApplication

    def go():
        dialog = QApplication.activeModalWidget()
        if dialog is None:
            return
        if how == "cancel" and hasattr(dialog, "reject"):
            dialog.reject()
        else:
            dialog.close()
    return go


def _open_and_close(opener, how, modal):
    """Run ``opener`` and close what it shows. Returns how many dialogs it
    showed, so a case that opened nothing cannot pass by accident."""
    from PyQt5.QtCore import QTimer
    from PyQt5.QtTest import QTest
    from PyQt5.QtWidgets import QApplication, QDialog

    shown = []
    if modal:
        def close_it():
            if QApplication.activeModalWidget() is not None:
                shown.append(1)
            _close_modal(how)()
        # More than one shot: some flows show a second box after the first
        for delay in (100, 300, 500):
            QTimer.singleShot(delay, close_it)
        opener()
        QTest.qWait(550)
    else:
        before = {id(w) for w in QApplication.topLevelWidgets() if w.isVisible()}
        opener()
        QApplication.processEvents()
        for widget in QApplication.topLevelWidgets():
            if widget.isVisible() and id(widget) not in before and isinstance(widget, QDialog):
                shown.append(1)
                if how == "cancel":
                    widget.reject()
                else:
                    widget.close()
        QApplication.processEvents()
    return len(shown)


def _first_strand(w):
    return w.canvas.strands[0]


def _button(w):
    return w.layer_panel.layer_buttons[0]


def _dirty(w):
    w.tab_manager.mark_active_dirty()


# name, opener(window), modal, prepare(window) or None
CASES = [
    ("move group", lambda w: w.layer_panel.group_layer_manager.group_panel.start_group_move(GROUP), True, None),
    ("rotate group", lambda w: w.layer_panel.group_layer_manager.group_panel.start_group_rotation(GROUP), True, None),
    ("rename group", lambda w: w.layer_panel.group_layer_manager.group_panel.rename_group(GROUP), True, None),
    ("edit strand angles", lambda w: w.layer_panel.group_layer_manager.group_panel.edit_strand_angles(GROUP), True, None),
    ("group shadow editor", lambda w: w.layer_panel.group_layer_manager.group_panel.open_group_shadow_editor(GROUP), False, None),
    ("create mask grid", lambda w: w.layer_panel.group_layer_manager.group_panel.create_mask_grid(GROUP), False, None),
    ("select strands for a group", lambda w: w.layer_panel.group_layer_manager.open_main_strand_selection_dialog(["1", "2"]), True, None),
    ("yes / no question", lambda w: w.layer_panel._ask_yes_no("Title", "Question?"), True, None),
    ("delete all layers", lambda w: w.layer_panel.request_delete_all(), True, None),
    ("layer state log", lambda w: w.show_layer_state_log(), True, lambda w: w.layer_state_button.setChecked(True)),
    ("layer state info", lambda w: w.show_layer_state_info(), True, None),
    ("unsaved changes on load", lambda w: w.load_project(), True, _dirty),
    ("unsaved changes on quit", lambda w: w._confirm_close_with_dirty_tabs(), True, _dirty),
    ("unsaved changes on close tab", lambda w: w.tab_manager.close_tab(w.tab_manager.get_active().id), True, _dirty),
    ("layer colour", lambda w: _button(w).change_color(), True, None),
    ("strand stroke colour", lambda w: _button(w).change_stroke_color(_first_strand(w), w.layer_panel), True, None),
    ("layer stroke colour", lambda w: _button(w).change_layer_stroke_color(_first_strand(w), w.layer_panel), True, None),
    ("layer colour from the menu", lambda w: _button(w).change_layer_color(_first_strand(w), w.layer_panel), True, None),
    ("strand width", lambda w: _button(w).change_width(_first_strand(w), w.layer_panel), True, None),
    ("layer width", lambda w: _button(w).change_layer_width(_first_strand(w), w.layer_panel), True, None),
    ("stylize end side", lambda w: _button(w).open_end_style_dialog(_first_strand(w), 1, w.layer_panel), True, None),
    ("strand shadow editor", lambda w: _button(w).open_shadow_editor(w.layer_panel, 0), False, None),
    ("settings: shadow colour", lambda w: w.settings_dialog.choose_shadow_color(), True, None),
    ("settings: default strand colour", lambda w: w.settings_dialog.choose_default_strand_color(), True, None),
    ("settings: default stroke colour", lambda w: w.settings_dialog.choose_default_stroke_color(), True, None),
    ("settings: default arrow colour", lambda w: w.settings_dialog.choose_default_arrow_color(), True, None),
    ("settings: default level colour", lambda w: w.settings_dialog.choose_default_level_color(), True, None),
    ("settings: highlight colour", lambda w: w.settings_dialog.choose_highlight_color(), True, None),
    ("settings: default width", lambda w: w.settings_dialog.open_default_width_dialog(), True, None),
]


@pytest.mark.parametrize("how", ["cancel", "x"])
@pytest.mark.parametrize("name, opener, modal, prepare", CASES, ids=[c[0] for c in CASES])
def test_a_closed_dialog_is_freed(window, name, opener, modal, prepare, how):
    _flush()
    before = _dialogs_alive()
    if prepare:
        prepare(window)
    shown = _open_and_close(lambda: opener(window), how, modal)
    assert shown, "%s showed no dialog, so this proves nothing" % name
    _flush()
    assert _dialogs_alive() == before, "%s is still in memory after %s" % (name, how)


def test_settings_is_one_dialog_reused(window):
    """Settings is the exception, on purpose: built once, shown again."""
    from PyQt5.QtWidgets import QApplication
    _flush()
    before = _dialogs_alive()
    for _ in range(3):
        window.open_settings_dialog()
        QApplication.processEvents()
        window.settings_dialog.close()
        QApplication.processEvents()
    _flush()
    assert _dialogs_alive() == before


def test_a_mask_grid_never_shown_is_freed(window):
    """A group with no strands builds the dialog and never shows it."""
    panel = window.layer_panel.group_layer_manager.group_panel
    _flush()
    before = _dialogs_alive()
    panel.create_mask_grid("no such group")
    _flush()
    assert _dialogs_alive() == before


@pytest.mark.parametrize("how", ["cancel", "x"])
def test_mask_grid_stops_listening_however_it_is_closed(window, how):
    """Esc goes straight to reject(), with no close event: the dialog used to
    stay connected to the canvas and rebuild its grid, hidden, on every mask
    change."""
    from PyQt5.QtWidgets import QApplication
    canvas = window.canvas
    panel = window.layer_panel.group_layer_manager.group_panel
    _flush()
    listening = canvas.receivers(canvas.masked_layer_created)
    panel.create_mask_grid(GROUP)
    QApplication.processEvents()
    dialog = panel._mask_grid_dialog
    assert canvas.receivers(canvas.masked_layer_created) == listening + 1
    if how == "cancel":
        dialog.reject()
    else:
        dialog.close()
    QApplication.processEvents()
    assert canvas.receivers(canvas.masked_layer_created) == listening
    assert panel._mask_grid_dialog is None, "the panel still holds the closed dialog"
    _flush()


@pytest.mark.parametrize("how", ["cancel", "x"])
def test_shadow_editor_clears_the_canvas_however_it_is_closed(window, how):
    """The shadow outline a row shows on the canvas is removed on Esc too."""
    from PyQt5.QtWidgets import QApplication, QDialog
    canvas = window.canvas
    cleared = []
    original = canvas.set_highlighted_shadow
    canvas.set_highlighted_shadow = lambda *a, **k: (cleared.append(a), original(*a, **k))[1]
    try:
        before = {id(w) for w in QApplication.topLevelWidgets() if w.isVisible()}
        _button(window).open_shadow_editor(window.layer_panel, 0)
        QApplication.processEvents()
        dialogs = [w for w in QApplication.topLevelWidgets()
                   if w.isVisible() and id(w) not in before and isinstance(w, QDialog)]
        assert len(dialogs) == 1
        del cleared[:]
        if how == "cancel":
            dialogs[0].reject()
        else:
            dialogs[0].close()
        QApplication.processEvents()
        assert cleared == [(None, None)], "closing with %s did not clear the canvas once" % how
    finally:
        canvas.set_highlighted_shadow = original
        _flush()


NON_MODAL = [c for c in CASES if not c[2]]


@pytest.mark.parametrize("name, opener, modal, prepare", NON_MODAL, ids=[c[0] for c in NON_MODAL])
def test_a_dialog_closed_before_its_first_timers_fire_is_safe(window, name, opener, modal, prepare):
    """The editors queue zero-delay work when they open (sizing their columns,
    scrolling a row into view). Closed, and freed, before the event loop gets
    to it, that work must be dropped, not run on a dialog that is gone."""
    from PyQt5.QtWidgets import QApplication, QDialog
    _flush()
    alive = _dialogs_alive()
    before = {id(w) for w in QApplication.topLevelWidgets() if w.isVisible()}
    opener(window)  # no event is processed between opening and closing
    opened = [w for w in QApplication.topLevelWidgets()
              if w.isVisible() and id(w) not in before and isinstance(w, QDialog)]
    assert len(opened) == 1
    opened[0].close()
    del opened
    _flush()
    QApplication.processEvents()
    assert _dialogs_alive() == alive
