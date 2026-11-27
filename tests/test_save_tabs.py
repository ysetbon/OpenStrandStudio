"""Save with several tabs open saves them together; Load brings them back.

Save (and Ctrl+S) used to write the active tab only, so a session of several
tabs had to be saved and reopened one tab at a time. Now a dialog lists the
open tabs with a checkbox each, the ticked ones go into one session file, and
loading that file opens them all. One tab alone is still an ordinary project
file ("Export tab"), and the files saved before this open as they always did.

Run in a real window, with only the file dialogs and the question boxes
answered for the user.
"""
import gc
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("APPDATA", tempfile.mkdtemp(prefix="oss_save_tabs_"))

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT, ROOT / "src"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

SAMPLES = ROOT / "src" / "samples"
BRAID = SAMPLES / "three_strand_braid.json"   # saved with its undo history
HEART = SAMPLES / "woven_heart.json"          # a plain snapshot, the older format
KNOT = SAMPLES / "overhand_knot.json"


@pytest.fixture(scope="module")
def app_window(tmp_path_factory):
    """One real window for the whole file: building one per test takes most of
    a minute by the end of the run. ``window`` hands it out with fresh tabs."""
    from PyQt5.QtWidgets import QApplication
    import sound_manager
    app = QApplication.instance() or QApplication([])
    tmp_path = tmp_path_factory.mktemp("save_tabs")
    previous_appdata = os.environ.get("APPDATA")
    os.environ["APPDATA"] = str(tmp_path / "appdata")
    # No sounds: what is checked here is the files and the tabs
    real_play = sound_manager.play
    sound_manager.play = lambda cue: None
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
    w.layer_panel.undo_redo_manager.temp_dir = str(states)
    w.resize(1400, 900)
    w.show()
    app.processEvents()
    yield w
    w._confirm_close_with_dirty_tabs = lambda *a, **k: True
    w.close()
    sound_manager.play = real_play
    if previous_appdata is None:
        os.environ.pop("APPDATA", None)
    else:
        os.environ["APPDATA"] = previous_appdata


@pytest.fixture()
def window(app_window, monkeypatch):
    """The window with one empty, unsaved-free tab and the tab bar hidden, as
    the app starts."""
    w = app_window
    tm = w.tab_manager
    # Close every tab without the "unsaved changes" question; the last one
    # closed is replaced by a fresh empty tab.
    monkeypatch.setattr(w.canvas, "skip_close_tab_warning", True, raising=False)
    tm.close_tabs([t.id for t in tm.tabs])
    assert len(tm.tabs) == 1 and not tm.tabs[0].dirty and not w.canvas.strands
    w.tab_edge.hide()
    w.tabs_button.setChecked(False)
    w._session_path = ''
    pump()
    return w


def pump():
    from PyQt5.QtWidgets import QApplication
    QApplication.processEvents()


def layer_names(window):
    return sorted(s.layer_name for s in window.canvas.strands)


def open_three_tabs(window):
    """braid | heart | knot, with the heart (the middle tab) showing.
    Returns {title: layer names}."""
    tm = window.tab_manager
    assert window.load_project_file(str(BRAID))
    tm.new_tab()
    assert window.load_project_file(str(HEART))
    tm.new_tab()
    assert window.load_project_file(str(KNOT))
    assert [tm.title_for(t) for t in tm.tabs] == ["three_strand_braid", "woven_heart", "overhand_knot"]
    names = {}
    for tab in list(tm.tabs):
        assert tm.switch_to_tab(tab.id)
        pump()
        names[tm.title_for(tab)] = layer_names(window)
        assert names[tm.title_for(tab)], "the sample opened empty"
    assert tm.switch_to_tab(tm.tabs[1].id)
    pump()
    return names


def answer_dialogs(monkeypatch, window, ticked=None, save_as=None):
    """Stand in for the user: tick ``ticked`` (titles; all when None) in the
    Save tabs dialog and type ``save_as`` in the file dialog. Returns the list
    of what the Save tabs dialog was shown, one entry per time it opened."""
    import save_tabs_dialog
    from PyQt5.QtWidgets import QFileDialog
    shown = []

    def ask(tabs, language_code='en', theme='default', parent=None):
        shown.append(tabs)
        if ticked is None:
            return [t['id'] for t in tabs]
        return [t['id'] for t in tabs if t['title'] in ticked] or None

    monkeypatch.setattr(save_tabs_dialog, "ask_which_tabs", ask)
    monkeypatch.setattr(QFileDialog, "getSaveFileName",
                        staticmethod(lambda *a, **k: (str(save_as) if save_as else "", "")))
    return shown


# ---------------------------------------------------------------- the file

def test_a_session_file_is_told_apart_from_a_project_file():
    from tab_session_file import build_session, is_session_file
    assert is_session_file(build_session([("a", {"strands": []})]))
    assert not is_session_file(json.loads(BRAID.read_text(encoding="utf-8")))
    assert not is_session_file(json.loads(HEART.read_text(encoding="utf-8")))
    assert not is_session_file(None)
    assert not is_session_file({"type": "OpenStrandStudioSession"})  # no tabs


def test_each_tab_in_a_session_file_is_a_whole_project_file():
    """So one tab can be lifted out and opened on its own."""
    from tab_session_file import build_session, split_project_data, tab_project_data
    history = json.loads(BRAID.read_text(encoding="utf-8"))
    snapshot = json.loads(HEART.read_text(encoding="utf-8"))
    settings = {"version": 1}
    with_history = tab_project_data(history, {"strands": []}, settings)
    assert with_history["states"] == history["states"]
    assert with_history["project_settings"] == settings
    assert "project_settings" not in history, "the tab's own snapshot was changed"
    only_snapshot = tab_project_data(None, snapshot, None)
    assert only_snapshot["strands"] == snapshot["strands"]
    assert tab_project_data(None, None, settings) is None

    session = build_session([("braid", with_history), ("heart", only_snapshot)], active_index=7)
    assert session["active_index"] == 1, "an index past the end is clamped"
    assert split_project_data(session["tabs"][0]["project"]) == (with_history, None, settings)
    assert split_project_data(session["tabs"][1]["project"]) == (None, only_snapshot, None)
    assert split_project_data("nonsense") == (None, None, None)


def test_a_failed_write_leaves_the_existing_file_alone(tmp_path):
    from tab_session_file import write_json
    target = tmp_path / "kept.json"
    target.write_text("{}", encoding="utf-8")
    loop = []
    loop.append(loop)
    assert write_json(str(target), {"tabs": loop}) is False
    assert target.read_text(encoding="utf-8") == "{}"
    assert write_json(str(tmp_path / "no_such_folder" / "x.json"), {}) is False


# ------------------------------------------------------ save, then load

def test_save_writes_every_tab_and_load_brings_them_back(window, tmp_path, monkeypatch):
    tm = window.tab_manager
    names = open_three_tabs(window)
    target = tmp_path / "knots_session.json"
    shown = answer_dialogs(monkeypatch, window, save_as=target)

    assert window.save_tabs() is True
    assert [t['title'] for t in shown[0]] == ["three_strand_braid", "woven_heart", "overhand_knot"]
    assert [t['active'] for t in shown[0]] == [False, True, False]
    assert [t['layers'] for t in shown[0]] == [len(names[t['title']]) for t in shown[0]]
    assert not any(t.dirty for t in tm.tabs)

    saved = json.loads(target.read_text(encoding="utf-8"))
    assert saved["type"] == "OpenStrandStudioSession"
    assert [t["title"] for t in saved["tabs"]] == ["three_strand_braid", "woven_heart", "overhand_knot"]
    assert saved["active_index"] == 1

    # Start over with one empty tab, as after a restart, and load the file
    tm.close_tabs([t.id for t in tm.tabs])
    assert len(tm.tabs) == 1 and layer_names(window) == []
    window.tab_edge.hide()
    assert window.load_project_file(str(target)) is True
    pump()

    assert [tm.title_for(t) for t in tm.tabs] == ["three_strand_braid", "woven_heart", "overhand_knot"]
    assert tm.title_for(tm.get_active()) == "woven_heart", "the tab that was showing is showing again"
    assert layer_names(window) == names["woven_heart"]
    assert not any(t.dirty for t in tm.tabs)
    assert window.tab_edge.isVisible(), "several tabs came in but the tab bar stayed hidden"
    for tab in list(tm.tabs):
        assert tm.switch_to_tab(tab.id)
        pump()
        assert layer_names(window) == names[tm.title_for(tab)]
    assert not any(t.dirty for t in tm.tabs), "looking through the loaded tabs marked them unsaved"


def test_a_loaded_tab_keeps_its_undo_history(window, tmp_path, monkeypatch):
    tm = window.tab_manager
    open_three_tabs(window)
    target = tmp_path / "session.json"
    answer_dialogs(monkeypatch, window, save_as=target)
    assert window.save_tabs()
    assert window.load_project_file(str(target))
    assert tm.switch_to_tab(tm.tabs[0].id)  # the braid was saved with its history
    pump()
    undo = window.layer_panel.undo_redo_manager
    steps = json.loads(BRAID.read_text(encoding="utf-8"))["max_step"]
    assert undo.max_step >= steps > 1


def test_only_the_ticked_tabs_are_saved(window, tmp_path, monkeypatch):
    tm = window.tab_manager
    open_three_tabs(window)
    for tab in tm.tabs:
        tab.dirty = True
    target = tmp_path / "two.json"
    answer_dialogs(monkeypatch, window, ticked={"three_strand_braid", "overhand_knot"}, save_as=target)

    assert window.save_tabs() is True
    saved = json.loads(target.read_text(encoding="utf-8"))
    assert [t["title"] for t in saved["tabs"]] == ["three_strand_braid", "overhand_knot"]
    assert saved["active_index"] == 0, "the active tab was left out, so the first one shows"
    assert [t.dirty for t in tm.tabs] == [False, True, False], "only the saved tabs are clean"
    assert [tm.title_for(t) for t in tm.tabs] == ["three_strand_braid", "woven_heart", "overhand_knot"]


def test_one_ticked_tab_is_saved_as_an_ordinary_project(window, tmp_path, monkeypatch):
    tm = window.tab_manager
    names = open_three_tabs(window)
    target = tmp_path / "just_the_knot.json"
    answer_dialogs(monkeypatch, window, ticked={"overhand_knot"}, save_as=target)

    assert window.save_tabs() is True
    from tab_session_file import is_session_file
    assert not is_session_file(json.loads(target.read_text(encoding="utf-8")))
    assert [tm.title_for(t) for t in tm.tabs] == ["three_strand_braid", "woven_heart", "just_the_knot"]
    assert tm.title_for(tm.get_active()) == "woven_heart", "saving a background tab switched tabs"

    # It opens like any project: into the active tab, the others untouched
    assert window.load_project_file(str(target)) is True
    pump()
    assert len(tm.tabs) == 3
    assert layer_names(window) == names["overhand_knot"]


def test_cancelling_saves_nothing(window, tmp_path, monkeypatch):
    tm = window.tab_manager
    open_three_tabs(window)
    tm.tabs[0].dirty = True
    answer_dialogs(monkeypatch, window, ticked=set(), save_as=tmp_path / "never.json")
    assert window.save_tabs() is False          # the Save tabs dialog was cancelled
    answer_dialogs(monkeypatch, window, save_as=None)
    assert window.save_tabs() is False          # the file dialog was cancelled
    assert not (tmp_path / "never.json").exists()
    assert tm.tabs[0].dirty


def test_a_write_that_fails_says_so_and_keeps_the_tabs_unsaved(window, tmp_path, monkeypatch):
    from PyQt5.QtWidgets import QMessageBox
    tm = window.tab_manager
    open_three_tabs(window)
    tm.tabs[0].dirty = True
    answer_dialogs(monkeypatch, window, save_as=tmp_path / "no_such_folder" / "x.json")
    told = []
    monkeypatch.setattr(QMessageBox, "warning", staticmethod(lambda *a, **k: told.append(a[2])))
    assert window.save_tabs() is False
    assert told == ["The file could not be saved."]
    assert tm.tabs[0].dirty


def test_with_one_tab_save_is_what_it_always_was(window, tmp_path, monkeypatch):
    assert window.load_project_file(str(BRAID))
    target = tmp_path / "alone.json"
    shown = answer_dialogs(monkeypatch, window, save_as=target)
    assert window.save_tabs() is True
    assert shown == [], "one tab: there is nothing to choose between"
    from tab_session_file import is_session_file
    assert not is_session_file(json.loads(target.read_text(encoding="utf-8")))


# -------------------------------------------------------------- export tab

def test_export_writes_a_background_tab_without_switching_to_it(window, tmp_path, monkeypatch):
    tm = window.tab_manager
    names = open_three_tabs(window)
    target = tmp_path / "braid_for_a_friend.json"
    answer_dialogs(monkeypatch, window, save_as=target)
    braid = tm.tabs[0]
    braid.dirty = True

    assert window.export_tab(braid.id) is True
    assert tm.title_for(tm.get_active()) == "woven_heart"
    assert layer_names(window) == names["woven_heart"]
    assert not braid.dirty and tm.title_for(braid) == "braid_for_a_friend"

    tm.new_tab()
    assert window.load_project_file(str(target)) is True
    pump()
    assert layer_names(window) == names["three_strand_braid"]


def test_export_of_the_active_tab_is_save(window, tmp_path, monkeypatch):
    tm = window.tab_manager
    open_three_tabs(window)
    target = tmp_path / "heart.json"
    answer_dialogs(monkeypatch, window, save_as=target)
    assert window.export_tab(tm.active_tab_id) is True
    assert tm.title_for(tm.get_active()) == "heart"
    assert json.loads(target.read_text(encoding="utf-8")).get("type") == "OpenStrandStudioHistory"


def test_the_active_tab_carries_an_export_icon(window, monkeypatch):
    from tab_bar_widget import TAB_MIN_WIDTH, TAB_MIN_WIDTH_ACTIVE
    open_three_tabs(window)
    window.tab_edge.show_edge()
    pump()
    exported = []
    monkeypatch.setattr(window, "export_tab", lambda tab_id: exported.append(tab_id), raising=False)
    chips = window.tab_edge._chips
    assert len(chips) == 3
    for chip in chips:
        assert (chip.export_btn is not None) == chip.active
        assert chip.min_width() == (TAB_MIN_WIDTH_ACTIVE if chip.active else TAB_MIN_WIDTH)
    active = next(c for c in chips if c.active)
    assert active.export_btn.toolTip() == "Export tab"
    # Left of duplicate, which is left of close
    assert active.export_btn.x() < active.dup_btn.x() < active.close_btn.x()
    active.export_btn.clicked.emit()
    assert exported == [], "the file dialog must not run inside the icon's click"
    pump()
    assert exported == [window.tab_manager.active_tab_id]


# --------------------------------------------- loading over open tabs

def click_in_question(label):
    """Click the button reading ``label`` in the question box about to open."""
    from PyQt5.QtCore import QTimer
    from PyQt5.QtWidgets import QApplication
    seen = []

    def click():
        box = QApplication.activeModalWidget()
        if box is None:
            return
        seen.append(box.text())
        for button in box.buttons():
            if button.text() == label:
                button.click()
                return
        box.reject()
    QTimer.singleShot(100, click)
    return seen


def test_loading_a_session_asks_before_dropping_unsaved_tabs(window, tmp_path, monkeypatch):
    tm = window.tab_manager
    open_three_tabs(window)
    target = tmp_path / "session.json"
    answer_dialogs(monkeypatch, window, ticked={"three_strand_braid", "overhand_knot"}, save_as=target)
    assert window.save_tabs()
    tm.tabs[0].dirty = True
    tm.tabs[2].dirty = True

    seen = click_in_question("Cancel")
    assert window.load_project_file(str(target)) is False
    assert "three_strand_braid" in seen[0] and "overhand_knot" in seen[0] and "woven_heart" not in seen[0]
    assert [tm.title_for(t) for t in tm.tabs] == ["three_strand_braid", "woven_heart", "overhand_knot"]
    assert tm.tabs[0].dirty, "Cancel must leave everything as it was"

    seen = click_in_question("Open anyway")
    assert window.load_project_file(str(target)) is True
    pump()
    assert [tm.title_for(t) for t in tm.tabs] == ["three_strand_braid", "overhand_knot"]


def test_load_does_not_ask_twice_about_the_active_tab(window, tmp_path, monkeypatch):
    """Load has already asked Save / Discard / Cancel about the tab showing."""
    tm = window.tab_manager
    open_three_tabs(window)
    target = tmp_path / "session.json"
    answer_dialogs(monkeypatch, window, save_as=target)
    assert window.save_tabs()
    tm.get_active().dirty = True
    asked = []
    from PyQt5.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox, "exec_", lambda self: asked.append(self.text()) or 0)
    assert window.load_project_file(str(target), asked_about_active=True) is True
    assert asked == []


def test_a_session_with_no_tabs_changes_nothing(window):
    tm = window.tab_manager
    names = open_three_tabs(window)
    assert window.load_session({"type": "OpenStrandStudioSession", "version": 1, "tabs": []}) is False
    assert len(tm.tabs) == 3 and layer_names(window) == names["woven_heart"]


def test_a_broken_tab_in_a_session_opens_empty_beside_the_good_ones(window):
    tm = window.tab_manager
    heart = json.loads(HEART.read_text(encoding="utf-8"))
    data = {"type": "OpenStrandStudioSession", "version": 1, "active_index": "x",
            "tabs": [{"title": "good", "project": heart}, {"title": "", "project": 5}, "junk"]}
    assert window.load_session(data) is True
    pump()
    assert len(tm.tabs) == 2
    assert tm.title_for(tm.tabs[0]) == "good" and layer_names(window)
    assert tm.tabs[1].untitled_index is not None, "a tab with no title is an Untitled one"
    assert tm.switch_to_tab(tm.tabs[1].id)
    pump()
    assert layer_names(window) == []


# ------------------------------------------------------------- shortcuts

def test_ctrl_s_and_ctrl_o_press_save_and_load(window, monkeypatch):
    from PyQt5.QtWidgets import QFileDialog, QShortcut
    pressed = []
    # One clean tab: Save goes straight to its file dialog, Load to its own
    monkeypatch.setattr(QFileDialog, "getSaveFileName",
                        staticmethod(lambda *a, **k: (pressed.append("save"), ("", ""))[1]))
    monkeypatch.setattr(QFileDialog, "getOpenFileName",
                        staticmethod(lambda *a, **k: (pressed.append("load"), ("", ""))[1]))
    shortcuts = {s.key().toString(): s for s in window.findChildren(QShortcut)}
    assert "Ctrl+S" in shortcuts and "Ctrl+O" in shortcuts
    shortcuts["Ctrl+S"].activated.emit()
    shortcuts["Ctrl+O"].activated.emit()
    assert pressed == ["save", "load"]
    # Disabled buttons (a mask is being edited): the keys do nothing either
    window.save_button.setEnabled(False)
    window.load_button.setEnabled(False)
    try:
        shortcuts["Ctrl+S"].activated.emit()
        shortcuts["Ctrl+O"].activated.emit()
        assert pressed == ["save", "load"]
    finally:
        window.save_button.setEnabled(True)
        window.load_button.setEnabled(True)


# ---------------------------------------------------------- the dialog

TABS = [
    {'id': 'a', 'title': 'woven_heart', 'layers': 14, 'dirty': False, 'active': False},
    {'id': 'b', 'title': 'chinese_cloverleaf', 'layers': 22, 'dirty': True, 'active': True},
    {'id': 'c', 'title': 'three_strand_braid', 'layers': None, 'dirty': False, 'active': False},
]


def labels_of(dialog):
    from PyQt5.QtWidgets import QLabel
    return [label.text() for label in dialog.findChildren(QLabel)]


def test_the_dialog_starts_with_every_tab_ticked(window):
    from PyQt5.QtCore import Qt
    from save_tabs_dialog import SaveTabsDialog
    dialog = SaveTabsDialog(TABS, 'en', 'default', window)
    try:
        assert dialog.selected_ids() == ['a', 'b', 'c']
        assert dialog.all_checkbox.checkState() == Qt.Checked
        assert dialog.count_label.text() == "3 of 3"
        assert dialog.save_button.text() == "Save 3 tabs" and dialog.save_button.isEnabled()
        texts = labels_of(dialog)
        assert "Layers: 14" in texts
        assert "Layers: 22  •  unsaved" in texts
        assert texts.count("active") == 1
        assert not any(t.startswith("Layers: None") for t in texts), "an unknown count is left out"
    finally:
        dialog.deleteLater()


def test_ticking_drives_the_all_tabs_box_and_the_button(window):
    from PyQt5.QtCore import Qt
    from save_tabs_dialog import SaveTabsDialog
    dialog = SaveTabsDialog(TABS, 'en', 'default', window)
    try:
        dialog.checkboxes[1].setChecked(False)
        assert dialog.selected_ids() == ['a', 'c']
        assert dialog.all_checkbox.checkState() == Qt.PartiallyChecked
        assert dialog.count_label.text() == "2 of 3" and dialog.save_button.text() == "Save 2 tabs"
        dialog.checkboxes[0].setChecked(False)
        assert dialog.save_button.text() == "Save 1 tab"
        dialog.checkboxes[2].setChecked(False)
        assert dialog.all_checkbox.checkState() == Qt.Unchecked
        assert dialog.save_button.text() == "Save" and not dialog.save_button.isEnabled()
        dialog.all_checkbox.click()                      # none ticked -> all
        assert dialog.selected_ids() == ['a', 'b', 'c']
        dialog.all_checkbox.click()                      # all ticked -> none
        assert dialog.selected_ids() == []
        dialog.checkboxes[0].setChecked(True)
        dialog.all_checkbox.click()                      # some ticked -> all
        assert dialog.selected_ids() == ['a', 'b', 'c']
        assert dialog.all_checkbox.checkState() == Qt.Checked
    finally:
        dialog.deleteLater()


def test_a_click_anywhere_on_a_row_ticks_it(window):
    from PyQt5.QtCore import QPoint, Qt
    from PyQt5.QtTest import QTest
    from save_tabs_dialog import SaveTabsDialog
    dialog = SaveTabsDialog(TABS, 'en', 'default', window)
    try:
        dialog.show()
        pump()
        row = dialog.checkboxes[0].parentWidget()
        QTest.mouseClick(row, Qt.LeftButton, pos=QPoint(row.width() - 20, row.height() // 2))
        assert dialog.selected_ids() == ['b', 'c']
    finally:
        dialog.close()
        dialog.deleteLater()


def test_hebrew_mirrors_the_dialog(window):
    from PyQt5.QtCore import Qt
    from save_tabs_dialog import SaveTabsDialog
    dialog = SaveTabsDialog(TABS, 'he', 'dark', window)
    try:
        dialog.resize(420, 400)
        dialog.show()
        pump()
        assert dialog.layoutDirection() == Qt.RightToLeft
        box, count = dialog.all_checkbox, dialog.count_label
        assert box.mapTo(dialog, box.rect().center()).x() > count.mapTo(dialog, count.rect().center()).x(), \
            "the checkbox belongs on the right in Hebrew"
        # The button row moves to the left and reads right to left: Save, then Cancel
        save, cancel = dialog.save_button, dialog.cancel_button
        save_x = save.mapTo(dialog, save.rect().center()).x()
        cancel_x = cancel.mapTo(dialog, cancel.rect().center()).x()
        assert cancel_x < save_x < dialog.width() / 2
        assert dialog.save_button.text() == "שמור 3 לשוניות"
        dialog.checkboxes[0].setChecked(False)
        dialog.checkboxes[1].setChecked(False)
        assert dialog.save_button.text() == "שמור לשונית אחת"
    finally:
        dialog.close()
        dialog.deleteLater()


def test_many_tabs_scroll_and_the_buttons_stay_on_screen(window):
    from PyQt5.QtWidgets import QApplication
    from save_tabs_dialog import SaveTabsDialog
    many = [{'id': str(i), 'title': 'design %d' % i, 'layers': i, 'dirty': False, 'active': i == 0}
            for i in range(80)]
    dialog = SaveTabsDialog(many, 'en', 'default', window)
    try:
        dialog.show()
        pump()
        screen = QApplication.primaryScreen().availableGeometry()
        assert dialog.height() <= screen.height()
        assert dialog.rows_area.verticalScrollBar().maximum() > 0, "the list does not scroll"
        bottom = dialog.save_button.mapTo(dialog, dialog.save_button.rect().bottomLeft()).y()
        assert bottom <= dialog.height()
    finally:
        dialog.close()
        dialog.deleteLater()


def _dialogs_alive():
    from PyQt5.QtCore import QEvent
    from PyQt5.QtWidgets import QApplication
    for _ in range(4):
        QApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        QApplication.processEvents()
        gc.collect()
    return sum(1 for w in QApplication.allWidgets() if w.inherits("QDialog"))


@pytest.mark.parametrize("how", ["save", "cancel", "escape", "x"])
def test_the_dialog_is_gone_from_memory_once_closed(window, how):
    """Cancel, Esc and the window's X all leave nothing behind, and so does Save."""
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtTest import QTest
    from PyQt5.QtWidgets import QApplication
    from save_tabs_dialog import ask_which_tabs
    before = _dialogs_alive()

    def close():
        dialog = QApplication.activeModalWidget()
        assert dialog is not None
        if how == "save":
            dialog.save_button.click()
        elif how == "cancel":
            dialog.cancel_button.click()
        elif how == "escape":
            QTest.keyClick(dialog, Qt.Key_Escape)
        else:
            dialog.close()
    QTimer.singleShot(100, close)
    answer = ask_which_tabs(TABS, 'en', 'default', window)
    assert answer == (['a', 'b', 'c'] if how == "save" else None)
    assert _dialogs_alive() == before, "the Save tabs dialog is still in memory after %s" % how
