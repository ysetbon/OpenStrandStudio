"""Every tab keeps its own undo session on disk, so the Settings > History page
still has each tab after the app closes without saving.

Before, every tab switch wiped all the state files in temp_states and every tab
shared one clock-second id: after the agent opened its step tabs (several in one
second) only the last tab's files were left, and the earlier runs were gone too.
These run the agent's open_in_new_tab in a real window, auto mode, as the agent
panel does."""
import os
import sys
import tempfile
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("APPDATA", tempfile.mkdtemp(prefix="oss_tab_history_"))

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT, ROOT / "src", ROOT / "scripts"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

TIGHT = ROOT / "tests" / "mask_tools" / "tight_overhand.json"


@pytest.fixture()
def window(tmp_path, monkeypatch):
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
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


def sessions_on_disk(window):
    folder = window.layer_panel.undo_redo_manager.temp_dir
    return {name.split("_")[0] for name in os.listdir(folder) if name.endswith(".json")}


def open_designs(window, tmp_path, count, mode="auto"):
    from PyQt5.QtWidgets import QApplication
    panel = window.agent_panel
    run = tmp_path / "run"
    run.mkdir(exist_ok=True)
    panel.out_dir = str(run)
    panel.answer = lambda reply: None
    panel.run_mode = mode
    replies = []
    for i in range(1, count + 1):
        design = run / f"step_{i}.json"
        design.write_text(TIGHT.read_text(encoding="utf-8"), encoding="utf-8")
        replies.append(panel.bridge.handle(
            {"id": i, "name": "open_in_new_tab", "args": {"path": str(design), "title": f"Step {i}"}}))
        QApplication.processEvents()
    return replies


def history_rows(window):
    dialog = window.settings_dialog
    dialog.populate_history_list()
    rows = [dialog.history_list.item(i) for i in range(dialog.history_list.count())]
    return [os.path.basename(r.data(0x0100)).split("_")[0] for r in rows if r.data(0x0100)]


def test_auto_mode_opens_every_design_in_a_tab_of_its_own(window, tmp_path):
    replies = open_designs(window, tmp_path, 4)
    assert all(r["ok"] and r["result"]["opened"] for r in replies)
    titles = [window.tab_manager.title_for(t) for t in window.tab_manager.tabs]
    assert titles[-4:] == ["Step 1", "Step 2", "Step 3", "Step 4"]


def test_ask_mode_leaves_designs_as_cards(window, tmp_path, monkeypatch):
    cards = []
    monkeypatch.setattr(window.agent_panel, "add_design_card", lambda path, title: cards.append(title))
    before = len(window.tab_manager.tabs)
    replies = open_designs(window, tmp_path, 2, mode="ask")
    assert all(r["ok"] and not r["result"]["opened"] for r in replies)
    assert cards == ["Step 1", "Step 2"]
    assert len(window.tab_manager.tabs) == before


def test_each_tab_opened_in_one_second_keeps_its_own_files(window, tmp_path):
    earlier = window.layer_panel.undo_redo_manager.temp_dir
    Path(earlier, "20200101120000_1.json").write_text("{}", encoding="utf-8")  # an earlier run

    open_designs(window, tmp_path, 4)
    tabs = window.tab_manager.tabs[-4:]
    ids = [t.undo_session_id for t in tabs]
    ids[-1] = window.layer_panel.undo_redo_manager.session_id  # the showing tab
    assert len(set(ids)) == 4
    assert set(ids) <= sessions_on_disk(window)
    assert "20200101120000" in sessions_on_disk(window)  # switching tabs left it alone


def test_switching_back_keeps_the_tab_its_design_and_its_id(window, tmp_path):
    open_designs(window, tmp_path, 3)
    tm, undo = window.tab_manager, window.layer_panel.undo_redo_manager
    first = tm.tabs[-3]
    strands = len(window.canvas.strands)
    assert tm.switch_to_tab(first.id)
    assert undo.session_id == first.undo_session_id
    assert len(window.canvas.strands) == strands
    assert undo.current_step >= 1
    assert len(sessions_on_disk(window)) >= 3


def test_history_lists_closed_tabs_but_not_open_ones(window, tmp_path):
    open_designs(window, tmp_path, 3)
    tm = window.tab_manager
    agent_tabs = tm.tabs[-3:]
    assert not set(history_rows(window)) & tm.open_undo_session_ids()

    window.canvas.skip_close_tab_warning = True
    ids = set()
    for tab in agent_tabs:
        if tab.id == tm.active_tab_id:
            ids.add(window.layer_panel.undo_redo_manager.session_id)
        ids.add(tab.undo_session_id)
        assert tm.close_tab(tab.id)
    ids.discard(None)
    assert len(ids) == 3
    assert ids <= set(history_rows(window))  # what is left after closing without saving


def test_clear_history_keeps_the_open_tabs(window, tmp_path, monkeypatch):
    from PyQt5.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    open_designs(window, tmp_path, 3)
    open_with_files = window.tab_manager.open_undo_session_ids() & sessions_on_disk(window)
    assert len(open_with_files) >= 3
    Path(window.layer_panel.undo_redo_manager.temp_dir, "20200101120000_1.json").write_text("{}", encoding="utf-8")
    window.settings_dialog.clear_all_history_action()
    on_disk = sessions_on_disk(window)
    assert "20200101120000" not in on_disk
    assert open_with_files <= on_disk
