"""The agent closes tabs: only the ones the person named, never unsaved work unasked.

Run end to end in a real window: the agent's tool, the bridge, the app's own
TabManager. Closing is the one tab action that can lose the person's work,
so every hedge the app puts on it is checked here: the id and the title must
both match, an unsaved tab stays open unless the request says to discard it
and the tab is still as the agent saw it, the app's "Unsaved changes" dialog
never opens for the agent, plan mode refuses, ask mode asks, and each closed
tab can be reopened, whole, from its card.
"""
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("APPDATA", tempfile.mkdtemp(prefix="oss_close_tab_"))

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT, ROOT / "src", ROOT / "scripts"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

TIGHT = ROOT / "tests" / "mask_tools" / "tight_overhand.json"


@pytest.fixture(scope="module")
def window(tmp_path_factory):
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    old_appdata = os.environ.get("APPDATA")
    os.environ["APPDATA"] = str(tmp_path_factory.mktemp("appdata"))
    cwd = os.getcwd()
    os.chdir(ROOT / "src")
    try:
        from main_window import MainWindow
        w = MainWindow()
    finally:
        os.chdir(cwd)
    w.resize(1400, 900)
    w.show()
    app.processEvents()
    yield w
    w._confirm_close_with_dirty_tabs = lambda *a, **k: True
    w.close()
    if old_appdata is None:
        os.environ.pop("APPDATA", None)
    else:
        os.environ["APPDATA"] = old_appdata


@pytest.fixture()
def app(window, monkeypatch, tmp_path):
    """Three tabs the agent opened ("One", "Two", "Three", saved), the agent's runner answered
    by the real bridge, and the app's own Unsaved changes dialog made to fail the test."""
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from openstrand import agent
    from openstrand.app import AppError
    panel, tm = window.agent_panel, window.tab_manager
    for session in list(tm.tabs)[1:]:  # what an earlier test left open
        session.dirty = False
        tm.close_tab(session.id)
    panel.entries.clear()
    run = tmp_path / "run"
    run.mkdir()
    panel.out_dir = str(run)
    design = run / "overhand.json"
    design.write_text(TIGHT.read_text(encoding="utf-8"), encoding="utf-8")
    replies = []
    monkeypatch.setattr(panel, "answer", replies.append)
    panel.run_mode = "auto"
    bridge = panel.bridge
    for n, title in enumerate(("One", "Two", "Three"), start=1):
        assert bridge.handle({"id": n, "name": "open_in_new_tab", "args": {"path": str(design), "title": title}})["ok"]
        tm.get_active().dirty = False  # as after Save
    QApplication.processEvents()

    def no_dialog(*a, **k):
        raise AssertionError("the app's Unsaved changes dialog opened for the agent")
    monkeypatch.setattr(QMessageBox, "exec_", no_dialog)
    canvas = window.canvas
    monkeypatch.setattr(canvas, "skip_close_tab_warning", False, raising=False)  # the app's default: it would ask

    def call(name, args):
        reply = bridge.handle({"id": 100, "name": name, "args": args})
        if not reply["ok"]:
            raise AppError(reply["error"])
        return reply["result"]
    runner = agent.Agent(SimpleNamespace(), tmp_path / "out", app=SimpleNamespace(call=call))
    by_title = lambda title: next(s for s in tm.tabs if tm.title_for(s) == title)
    titles = lambda: [tm.title_for(s) for s in tm.tabs]
    listed = lambda title: next(t for t in bridge.list_tabs() if t["title"] == title)
    close = lambda title, **more: runner.app_tool("close_tab", dict({"tab_id": by_title(title).id, "title": title},
                                                                      **more))
    return SimpleNamespace(window=window, canvas=canvas, tm=tm, panel=panel, bridge=bridge, runner=runner,
                           replies=replies, by_title=by_title, titles=titles, listed=listed, close=close,
                           error=AppError)


def test_the_agent_closes_the_tab_it_names_and_no_other(app):
    two = app.by_title("Two")
    summary, text = app.close("Two")
    assert summary == "Close tab · Two" and 'closed "Two"' in text and "reopen it from the card" in text
    assert app.titles() == ["Untitled 1", "One", "Three"] and app.tm.find(two.id) is None
    # The tab showing ("Three") was not the one closed: it still shows.
    assert app.tm.title_for(app.tm.get_active()) == "Three"
    card = app.panel.entries[-1]
    assert card["kind"] == "closed_tab" and card["title"] == "Two" and card["unsaved"] is False
    assert "The agent closed the tab “Two”." in app.panel.transcript.toPlainText()


def test_an_id_and_a_title_that_do_not_match_close_nothing(app):
    """The agent has the id of one tab and the name of another (a remembered id, an
    off-by-one): neither closes."""
    before = app.titles()
    with pytest.raises(app.error, match='is titled "One", not "Two": nothing was closed'):
        app.runner.app_tool("close_tab", {"tab_id": app.by_title("One").id, "title": "Two"})
    with pytest.raises(app.error, match="nothing was closed"):
        app.runner.app_tool("close_tab", {"tab_id": app.by_title("One").id})  # no title at all
    with pytest.raises(app.error, match="no tab tab-999"):
        app.runner.app_tool("close_tab", {"tab_id": "tab-999", "title": "One"})
    assert app.titles() == before and not [e for e in app.panel.entries if e["kind"] == "closed_tab"]
    app.runner.app_tool("close_tab", {"tab_id": app.by_title("One").id, "title": "  one "})  # spacing and case aside
    assert "One" not in app.titles()


def test_a_tab_with_unsaved_changes_stays_open_unless_the_person_said_to_discard(app):
    one = app.by_title("One")
    one.dirty = True
    assert app.listed("One")["unsaved"] is True
    before = app.titles()
    with pytest.raises(app.error, match='"One" has unsaved changes, so it stays open') as refused:
        app.close("One")
    assert "discard_unsaved: true" in str(refused.value) and "app_window save" in str(refused.value)
    # Anything but true itself discards nothing.
    for value in ("true", 1, "yes", None, False):
        with pytest.raises(app.error, match="has unsaved changes"):
            app.close("One", discard_unsaved=value, version=app.listed("One")["version"])
    # Told to discard, but without having looked at the tab as it is now.
    with pytest.raises(app.error, match="also give its version"):
        app.close("One", discard_unsaved=True)
    assert app.titles() == before and one.dirty
    # The person said so, and the tab is as the agent saw it: closed, without the app's dialog.
    summary, text = app.close("One", discard_unsaved=True, version=app.listed("One")["version"])
    assert 'closed "One" without saving it' in text and "One" not in app.titles()
    card = app.panel.entries[-1]
    assert card["unsaved"] is True and "without saving it. It had unsaved changes." in app.panel.transcript.toPlainText()


def test_unsaved_work_the_person_did_since_the_agent_looked_is_not_closed(app):
    """The agent listed the tabs, the person went on drawing in one, then the agent closes it."""
    assert app.tm.switch_to_tab(app.by_title("Two").id)
    seen = app.listed("Two")["version"]
    victim = next(s for s in app.canvas.strands if not hasattr(s, "get_mask_path"))
    victim.end.setX(victim.end.x() + 40)  # the person moved a point
    app.by_title("Two").dirty = True
    assert app.listed("Two")["version"] != seen
    with pytest.raises(app.error, match='"Two" changed since you listed it .* it stays\\s+open'):
        app.close("Two", discard_unsaved=True, version=seen)
    assert "Two" in app.titles()


def test_plan_mode_never_closes_and_ask_mode_asks_for_each_tab(app):
    from PyQt5.QtCore import QUrl
    panel, bridge = app.panel, app.bridge
    one = app.by_title("One")
    args = {"tab_id": one.id, "title": "One"}
    panel.run_mode = "plan"
    assert "plan mode" in bridge.handle({"id": 1, "name": "close_tab", "args": args})["error"]
    panel.run_mode = "ask"
    assert bridge.handle({"id": 2, "name": "close_tab", "args": args}) is None and "One" in app.titles()
    card = panel.entries[-1]
    assert card["kind"] == "confirm" and "The agent wants to close the tab “One”." in panel.transcript.toPlainText()
    panel.follow_link(QUrl(f"os:deny/{panel.entries.index(card)}"))
    assert not app.replies[-1]["ok"] and "declined" in app.replies[-1]["error"] and "One" in app.titles()
    # An unsaved tab: the card says so, and Allow is checked again when it comes.
    one.dirty = True
    with_version = dict(args, discard_unsaved=True, version=bridge.version(one))
    assert bridge.handle({"id": 3, "name": "close_tab", "args": with_version}) is None
    card = panel.entries[-1]
    assert "without saving it. It has unsaved changes." in panel.transcript.toPlainText()
    panel.follow_link(QUrl(f"os:allow/{panel.entries.index(card)}"))
    assert app.replies[-1]["ok"] and app.replies[-1]["result"]["unsaved"] is True and "One" not in app.titles()
    panel.run_mode = "auto"


def test_a_closed_tab_reopens_from_its_card_as_it_was(app):
    from PyQt5.QtCore import QUrl
    from PyQt5.QtWidgets import QApplication
    tm, panel = app.tm, app.panel
    assert tm.switch_to_tab(app.by_title("Two").id)
    two = app.by_title("Two")
    strands = len(app.canvas.strands)
    moved = next(s for s in app.canvas.strands if not hasattr(s, "get_mask_path"))
    moved.end.setX(moved.end.x() + 40)  # unsaved work, on the canvas only
    where, name = moved.end.x(), moved.layer_name
    two.dirty = True
    place = tm.tabs.index(two)
    app.close("Two", discard_unsaved=True, version=app.listed("Two")["version"])
    assert "Two" not in app.titles() and tm.get_active() is not two
    card = panel.entries[-1]
    assert "Reopen" in panel.transcript.toPlainText()
    panel.follow_link(QUrl(f"os:reopen/{panel.entries.index(card)}"))
    QApplication.processEvents()
    assert app.titles().index("Two") == place and tm.get_active() is two and two.dirty  # back, showing, still unsaved
    assert len(app.canvas.strands) == strands
    again = next(s for s in app.canvas.strands if s.layer_name == name and not hasattr(s, "get_mask_path"))
    assert again.end.x() == pytest.approx(where)  # with the work that was never saved
    assert card["state"] == "reopened" and "Reopened" in panel.transcript.toPlainText()
    panel.follow_link(QUrl(f"os:reopen/{panel.entries.index(card)}"))  # a second click does nothing
    assert app.titles().count("Two") == 1


def test_closing_the_last_tab_leaves_an_empty_one(app):
    for session in list(app.tm.tabs):
        app.runner.app_tool("close_tab", {"tab_id": session.id, "title": app.tm.title_for(session)})
    assert len(app.tm.tabs) == 1 and not app.canvas.strands
    assert len([e for e in app.panel.entries if e["kind"] == "closed_tab"]) == 4


def test_the_agent_is_told_when_it_may_close_a_tab():
    from openstrand.app import APP_INSTRUCTIONS, APP_TOOLS, LOOK_ONLY
    import agent_panel
    from agent_translations import AGENT_TRANSLATIONS
    tool = next(t for t in APP_TOOLS if t["name"] == "close_tab")
    assert tool["input_schema"]["required"] == ["tab_id", "title"] and "close_tab" not in LOOK_ONLY
    assert "only a tab the person asked, in this request" in tool["description"]
    assert "only when the person asks, in this request" in APP_INSTRUCTIONS
    assert "Never close a tab because it\n  looks finished, empty or left over" in APP_INSTRUCTIONS
    assert '"Close all tabs" alone\n  does not say that' in APP_INSTRUCTIONS
    assert "close\n  none and ask which" in APP_INSTRUCTIONS
    assert agent_panel.TOOL_CHIPS["close_tab"] == agent_panel.TOOL_CHIPS["switch_tab"]
    keys = ("agent_confirm_close", "agent_confirm_close_unsaved", "agent_tab_closed", "agent_tab_closed_unsaved",
            "agent_reopen_tab", "agent_tab_reopened")
    for language, table in AGENT_TRANSLATIONS.items():
        for key in keys:
            assert table.get(key), (language, key)
        assert "{old}" in table["agent_confirm_close"] and "{old}" in table["agent_confirm_close_unsaved"]
        assert "{name}" in table["agent_tab_closed"] and "{name}" in table["agent_tab_closed_unsaved"]
