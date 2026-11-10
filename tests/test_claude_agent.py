"""The Claude agent harness, its settings, and the app's Claude panel.

Claude itself is replaced by a scripted client: the tests check what the
harness sends, how it runs the tools, and that a finished design loads into
the real main window (canvas, layer panel, groups) through the Load path.
"""
import json
import re
import os
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# Settings for this test run only: never the user's own.
os.environ["APPDATA"] = tempfile.mkdtemp(prefix="oss_claude_test_")

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT, ROOT / "src"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from openstrand import agent, project  # noqa: E402


# ---------------------------------------------------------------- fake Claude
def usage(inp=1000, out=200, write=0, read=0):
    return SimpleNamespace(input_tokens=inp, output_tokens=out,
                           cache_creation_input_tokens=write, cache_read_input_tokens=read)


def text(t):
    return SimpleNamespace(type="text", text=t)


def tool(id_, name, **inp):
    return SimpleNamespace(type="tool_use", id=id_, name=name, input=inp)


def reply(*blocks, stop="tool_use"):
    return SimpleNamespace(content=list(blocks), stop_reason=stop, usage=usage())


class ScriptedClient:
    """Answers each call with the next scripted reply and records the request."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []
        self.messages = SimpleNamespace(create=self._create)
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create_beta))

    def _create(self, **params):
        # The harness keeps appending to one list, so record what was sent then.
        self.calls.append(("messages", dict(params, messages=list(params["messages"]))))
        return self.replies.pop(0)

    def _create_beta(self, **params):
        self.calls.append(("beta", dict(params, messages=list(params["messages"]))))
        return self.replies.pop(0)


def bracelet_script():
    return [
        reply(text("A 5×3 right-hand stitch."), tool("t1", "make_mxn", m=5, n=3, hand="rh")),
        reply(tool("t2", "describe")),
        reply(tool("t3", "recolor", sets=[4, 5, 6, 7, 8], color="teal"),
              tool("t4", "recolor", sets=[1, 2, 3], color="gold"), tool("t5", "validate")),
        reply(tool("t6", "render")),
        reply(text("Done: a 5×3 right-hand weave, teal vertical and gold horizontal ribbons."), stop="end_turn"),
    ]


def test_agent_builds_checks_and_renders_a_design(tmp_path):
    client = ScriptedClient(bracelet_script())
    events = []
    result = agent.Agent(client, tmp_path, model="claude-sonnet-5-5", on_event=events.append).run(
        "5x3 right hand bracelet in teal and gold")

    assert result["ok"] and result["error"] is None and result["changed"] is True
    assert "teal vertical" in result["text"]
    info = project.describe(project.read(result["project"]))
    assert len(info["sets"]) == 8
    assert all(s["colors"] == ["#257d98"] for n, s in info["sets"].items() if s["runs"] == "vertical")
    assert all(s["colors"] == ["#e5a13b"] for n, s in info["sets"].items() if s["runs"] == "horizontal")
    assert Path(result["png"]).stat().st_size > 10_000

    ends = [e for e in events if e["type"] == "tool_end"]
    assert [e["name"] for e in ends] == ["make_mxn", "describe", "recolor", "recolor", "validate", "render"]
    assert all(e["ok"] for e in ends)
    assert result["cost"] == pytest.approx(5 * (1000 * 2 + 200 * 10) / 1e6)


def test_sonnet_requests_use_fallback_cached_guides_web_tools_and_visible_thinking(tmp_path):
    client = ScriptedClient(bracelet_script())
    agent.Agent(client, tmp_path, model="claude-sonnet-5-5").run("bracelet")
    kind, params = client.calls[0]
    assert kind == "beta" and params["fallbacks"] == "default"
    assert params["betas"] == [agent.FALLBACK_BETA]
    assert params["model"] == "claude-sonnet-5-5"
    assert params["output_config"] == {"effort": "high"}
    assert params["thinking"] == {"type": "adaptive", "display": "summarized"}
    assert params["max_tokens"] <= 21333  # above that the SDK insists on streaming
    assert params["system"][0]["cache_control"] == {"type": "ephemeral"}
    system = params["system"][0]["text"]
    assert "Turk's heads" in system and "Drawing your own designs" in system  # both guides
    assert "web_search" in system and "first principles" in system
    types = [t.get("type") for t in params["tools"]]
    assert "web_search_20260209" in types and "web_fetch_20260209" in types
    assert "draw_design" in [t.get("name") for t in params["tools"]]
    assert "temperature" not in params and "tool_choice" not in params


def test_haiku_requests_have_no_fallback_and_basic_web_tools(tmp_path):
    client = ScriptedClient(bracelet_script())
    agent.Agent(client, tmp_path, model="claude-haiku-5-5").run("bracelet")
    kind, params = client.calls[0]
    assert kind == "messages" and "fallbacks" not in params and params["model"] == "claude-haiku-5-5"
    types = [t.get("type") for t in params["tools"]]
    assert "web_search_20250305" in types and "web_fetch_20250910" in types


def test_without_web_the_web_tools_are_left_out(tmp_path):
    client = ScriptedClient(bracelet_script())
    agent.Agent(client, tmp_path, model="claude-sonnet-5-5", web=False, effort="medium").run("bracelet")
    params = client.calls[0][1]
    assert not [t for t in params["tools"] if "web" in t.get("name", "")]
    assert params["output_config"] == {"effort": "medium"}


def test_conversation_is_append_only_and_renders_go_back_as_images(tmp_path):
    client = ScriptedClient(bracelet_script())
    agent.Agent(client, tmp_path, model="claude-sonnet-5-5").run("bracelet")
    last = client.calls[-1][1]["messages"]
    first = client.calls[0][1]["messages"]
    assert last[:len(first)] == first
    render_result = [b for m in last if m["role"] == "user" and isinstance(m["content"], list)
                     for b in m["content"] if b.get("tool_use_id") == "t6"][0]
    assert render_result["content"][0]["type"] == "image"


def test_a_bad_tool_call_goes_back_to_claude_as_an_error(tmp_path):
    client = ScriptedClient([
        reply(tool("t1", "make_turks_head", leads=3, bights=6)),
        reply(tool("t2", "recolor", sets=[1], color="red")),
        reply(text("I could not make that size."), stop="end_turn"),
    ])
    result = agent.Agent(client, tmp_path, model="claude-haiku-5-5").run("3 by 6 mat")
    results = [b for b in client.calls[1][1]["messages"][-1]["content"]]
    assert results[0]["is_error"] and "share a factor" in results[0]["content"]
    second = client.calls[2][1]["messages"][-1]["content"][0]
    assert second["is_error"] and "no design yet" in second["content"]
    assert result["ok"] and result["project"] is None


def test_refusal_and_limits_end_the_run_with_a_reason(tmp_path):
    client = ScriptedClient([reply(text(""), stop="refusal")])
    result = agent.Agent(client, tmp_path, model="claude-sonnet-5-5").run("x")
    assert not result["ok"] and "declined" in result["error"]

    looping = ScriptedClient([reply(tool(f"t{i}", "search_samples", text="ring")) for i in range(3)])
    result = agent.Agent(looping, tmp_path, model="claude-haiku-5-5", max_rounds=3).run("x")
    assert not result["ok"] and "3 rounds" in result["error"]


def test_start_design_is_loaded_and_described(tmp_path):
    start = project.read(ROOT / "knot_samples/links/json/hopf_link.json")
    client = ScriptedClient([reply(tool("t1", "describe")), reply(text("Two linked rings."), stop="end_turn")])
    result = agent.Agent(client, tmp_path, model="claude-haiku-5-5").run("what is this?", start=start)
    prompt = client.calls[0][1]["messages"][0]["content"][-1]["text"]
    assert "already loaded" in prompt and "2 sets" in prompt
    described = client.calls[1][1]["messages"][-1]["content"][0]["content"]
    assert "set 1" in described and "set 2" in described
    assert result["project"]
    assert result["changed"] is False  # only looked at: still the person's canvas, never shared as Claude's
    assert result["new"] is False
    recolored = ScriptedClient([reply(tool("t1", "recolor", sets=[1], color="gold")),
                                reply(text("Gold now."), stop="end_turn")])
    result = agent.Agent(recolored, tmp_path, model="claude-haiku-5-5").run("make it gold", start=start)
    assert result["ok"] and result["changed"] is True  # Claude's work now
    assert result["new"] is False  # but made from the person's own canvas: never for the gallery


def test_a_tab_or_a_past_step_of_one_is_the_person_s_never_claude_s_work(tmp_path):
    """After read_tab or read_tab_step the current design is the person's own, even when Claude
    made and opened a design of its own earlier in the request: changed is False, so the panel
    never shares it as Claude's. A tool that stores a new design makes it Claude's work again."""
    hopf = ROOT / "knot_samples/links/json/hopf_link.json"

    def call(name, args):  # the app, through the bridge
        if name == "read_tab_step":
            return {"file": str(hopf), "title": "Mine", "step": args["step"], "what": "moved a strand",
                    "current_step": 4, "max_step": 4}
        if name == "read_tab":
            return {"file": str(hopf), "title": "Mine", "version": 7, "history": []}
        return {"opened": True}
    app = SimpleNamespace(call=call)

    def run(*steps):
        load = SimpleNamespace(type="tool_use", id="t1", name="load_sample", input={"name": "hopf_link"})
        client = ScriptedClient([reply(load),
                                 reply(tool("t2", "open_in_new_tab", design="current", title="Rings")),
                                 *[reply(tool(f"t{3 + i}", name, **args)) for i, (name, args) in enumerate(steps)],
                                 reply(text("Done."), stop="end_turn")])
        return agent.Agent(client, tmp_path, model="claude-haiku-5-5", app=app).run("x")
    made = run()
    assert made["ok"] and made["opened_tabs"] == ["Rings"] and made["project"] and made["changed"] is True
    assert made["new"] is True  # made from nothing of the person's: it may go in the gallery
    past = run(("read_tab_step", {"tab_id": "1", "step": 2}))
    assert past["ok"] and past["opened_tabs"] == ["Rings"] and past["project"]  # a copy, in the workspace
    assert past["changed"] is False  # the person's tab two steps ago: never shared as Claude's design
    assert past["new"] is False
    tab = run(("read_tab", {"tab_id": "1"}))
    assert tab["ok"] and tab["changed"] is False and tab["in_tab"] == "1" and tab["project"] is None
    recolored = run(("read_tab_step", {"tab_id": "1", "step": 2}), ("recolor", {"sets": [1], "color": "gold"}))
    assert recolored["ok"] and recolored["changed"] is True  # Claude changed it: its work now


def test_agent_draws_its_own_design_and_reports_thinking_and_searches(tmp_path):
    with_search = SimpleNamespace(input_tokens=1000, output_tokens=200, cache_creation_input_tokens=0,
                                  cache_read_input_tokens=0,
                                  server_tool_use=SimpleNamespace(web_search_requests=2))
    first = SimpleNamespace(stop_reason="tool_use", usage=with_search, content=[
        SimpleNamespace(type="thinking", thinking="Rings that overlap will link.", signature="s"),
        SimpleNamespace(type="server_tool_use", id="srv1", name="web_search", input={"query": "hopf link"}),
        SimpleNamespace(type="web_search_tool_result", tool_use_id="srv1", content=[SimpleNamespace(type="r")]),
        SimpleNamespace(type="server_tool_use", id="srv2", name="web_fetch", input={"url": "https://x.org"}),
        SimpleNamespace(type="web_fetch_tool_result", tool_use_id="srv2",
                        content=SimpleNamespace(type="web_fetch_tool_error", error_code="url_not_accessible")),
        SimpleNamespace(type="tool_use", id="t1", name="draw_design", input={"name": "rings", "cords": [
            {"shape": "circle", "center": [480, 400], "radius": 180, "label": "Left"},
            {"shape": "circle", "center": [720, 400], "radius": 180, "label": "Right"}]})])
    client = ScriptedClient([first, reply(tool("t2", "render")), reply(text("Linked rings."), stop="end_turn")])
    events = []
    result = agent.Agent(client, tmp_path, model="claude-sonnet-5-5", on_event=events.append).run("rings")

    assert result["ok"] and result["searches"] == 2
    assert {"type": "thinking", "text": "Rings that overlap will link."} in events
    assert {"type": "search", "name": "web_search", "query": "hopf link"} in events
    assert {"type": "search", "name": "web_fetch", "query": "https://x.org"} in events
    fetched = [e for e in events if e["type"] == "search_result" and e["name"] == "web_fetch"][0]
    assert not fetched["ok"] and fetched["error"] == "url_not_accessible"
    report = client.calls[1][1]["messages"][-1]["content"][0]["content"]
    assert "2 crossings in all" in report and "render" in report
    assert set(project.describe(project.read(result["project"]))["groups"]) == {"Left", "Right"}
    assert result["cost"] == pytest.approx(3 * (1000 * 2 + 200 * 10) / 1e6 + 2 * agent.WEB_SEARCH_PRICE)


def test_a_drawing_problem_goes_back_to_claude(tmp_path):
    client = ScriptedClient([
        reply(tool("t1", "draw_design", cords=[{"shape": "circle", "center": [600, 400], "radius": 100}])),
        reply(text("That needs a crossing."), stop="end_turn")])
    agent.Agent(client, tmp_path, model="claude-haiku-5-5").run("a ring")
    result = client.calls[1][1]["messages"][-1]["content"][0]
    assert result["is_error"] and "crosses nothing" in result["content"]


def test_web_tools_switched_off_by_the_organization_are_dropped_with_a_note(tmp_path):
    class NoWebClient(ScriptedClient):
        def _create_beta(self, **params):
            if any(t.get("name") == "web_search" for t in params["tools"]):
                error = Exception("tools.10.web_search_20260209: web search is not enabled for this organization")
                error.status_code = 400
                raise error
            return super()._create_beta(**params)

    client = NoWebClient([reply(text("Done."), stop="end_turn")])
    events = []
    result = agent.Agent(client, tmp_path, model="claude-sonnet-5-5", on_event=events.append).run("x")
    assert result["ok"] and len(client.calls) == 1
    assert not [t for t in client.calls[0][1]["tools"] if "web" in t.get("name", "")]
    assert any(e["type"] == "note" and "Web search" in e["text"] for e in events)


def test_other_api_errors_are_not_swallowed(tmp_path):
    class Broken(ScriptedClient):
        def _create_beta(self, **params):
            error = Exception("overloaded")
            error.status_code = 529
            raise error

    with pytest.raises(Exception, match="overloaded"):
        agent.Agent(Broken([]), tmp_path, model="claude-sonnet-5-5").run("x")


# -------------------------------------------------------------- settings
def test_settings_keep_the_key_private_and_the_model_known(tmp_path, monkeypatch):
    import claude_settings
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert claude_settings.load() == {"api_key": "", "keys": {}, "catalog": {}, "model": "claude-sonnet-5-5", "web": True,
                                      "max_cost": 2.0, "spent": 0.0, "spent_since": "",
                                      "show_button": True, "effort": "high", "session_limit": 10.0, "mode": "auto",
                                      "share": None, "gallery": None, "models_on": True, "allow_china": False}
    claude_settings.save(api_key="  sk-ant-test-1234567890  ", model="claude-haiku-5-5", web=False, max_cost=5)
    assert claude_settings.load() == {"api_key": "sk-ant-test-1234567890",
                                      "keys": {"anthropic": "sk-ant-test-1234567890"}, "catalog": {},
                                      "model": "claude-haiku-5-5",
                                      "web": False, "max_cost": 5.0, "spent": 0.0, "spent_since": "",
                                      "show_button": True,
                                      "effort": "high", "session_limit": 10.0, "mode": "auto", "share": None,
                                      "gallery": None, "models_on": True, "allow_china": False}
    # Every provider has its key; the model can be any provider's.
    claude_settings.save(provider_key=("xai", " xai-test-123456789 "), model="grok-4.7")
    saved = claude_settings.load()
    assert saved["keys"] == {"anthropic": "sk-ant-test-1234567890", "xai": "xai-test-123456789"}
    assert saved["model"] == "grok-4.7" and claude_settings.provider_of("grok-4.7") == "xai"
    claude_settings.save(provider_key=("xai", ""))
    assert claude_settings.load()["keys"] == {"anthropic": "sk-ant-test-1234567890"}
    claude_settings.save(max_cost=1000)
    assert claude_settings.load()["max_cost"] == claude_settings.MAX_COST_RANGE[1]
    if os.name == "posix":
        assert stat.S_IMODE(os.stat(claude_settings.settings_path()).st_mode) == 0o600
    with pytest.raises(ValueError):
        claude_settings.save(model="claude-opus-1")
    claude_settings.save(api_key="")
    assert "api_key" not in json.loads(Path(claude_settings.settings_path()).read_text())
    assert claude_settings.masked("sk-ant-test-1234567890") == "sk-ant-…7890"


def test_refresh_models_is_a_button_that_shows_what_the_providers_said(tmp_path, monkeypatch):
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])  # noqa: F841 (kept alive for the page)
    import claude_settings
    from claude_panel import ClaudeSettingsPage
    from openstrand import providers
    monkeypatch.setenv("APPDATA", str(tmp_path))
    page = ClaudeSettingsPage("en")
    assert page.refresh_button.text() == "Refresh models" and "Built-in list" in page.refresh_status.text()
    found = {"refreshed": "2026-11-07 10:00", "providers": {
        "xai": {"models": [{"id": "grok-4.7"}, {"id": "grok-4.8", "label": "Grok 4.8", "prices": [2.5, 8.0, 2.5, 0.5]}]},
        "openai": {"error": "Incorrect API key provided"}}}
    monkeypatch.setattr(claude_settings, "fetch_catalog", lambda: found)
    try:
        page.refresh_models()
        for _ in range(100):  # the asking runs in a thread; its answer comes back as a signal
            QApplication.processEvents()
            if page.refresh_button.isEnabled():
                break
            time.sleep(0.02)
        assert page.refresh_button.isEnabled()
        status = page.refresh_status.text()
        assert "1 new, 0 retiring, 0 no longer offered" in status and "OpenAI (GPT): Incorrect API key" in status
        labels = [page.model_combo.itemText(i) for i in range(page.model_combo.count())]
        assert any(label.startswith("Grok 4.8") and "new" in label for label in labels)
        assert claude_settings.load()["catalog"]["refreshed"] == "2026-11-07 10:00"
    finally:
        providers.use_catalog({})


def test_models_refresh_on_their_own_once_a_day_without_a_word(window, tmp_path, monkeypatch):
    import datetime
    from PyQt5.QtWidgets import QApplication
    import claude_settings
    from openstrand import providers
    monkeypatch.setenv("APPDATA", str(tmp_path))
    for spec in claude_settings.PROVIDERS.values():
        monkeypatch.delenv(spec.env, raising=False)
    assert not claude_settings.refresh_due()  # no key: nobody to ask
    claude_settings.save(provider_key=("xai", "xai-test-123456789"))
    assert claude_settings.refresh_due()  # never refreshed
    asked = []
    found = {"refreshed": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "providers": {
        "xai": {"models": [{"id": "grok-4.7"}, {"id": "grok-4.8", "label": "Grok 4.8", "prices": [2.5, 8.0, 2.5, 0.5]}]}}}
    monkeypatch.setattr(claude_settings, "fetch_catalog", lambda: asked.append(1) or found)
    panel = window.claude_panel
    panel.entries.clear()
    try:
        panel.auto_refresh_models()
        for _ in range(100):  # asked in a thread, applied when its answer comes back
            QApplication.processEvents()
            if not panel.fetching_models:
                break
            time.sleep(0.02)
        assert asked == [1] and not panel.fetching_models
        assert panel.entries == []  # silent: nothing said in the conversation
        panel.choose(model="grok-4.7")  # the model drop-down lists xAI's models now
        assert any("Grok 4.8" in a.text() for a in panel.model_menu.actions())
        assert not claude_settings.refresh_due()  # done for today
        panel.auto_refresh_models()
        assert asked == [1]
        # A day later, a provider that fails keeps what it offered last time.
        stale = dict(found, refreshed=(datetime.datetime.now() - datetime.timedelta(hours=25)).strftime("%Y-%m-%d %H:%M"))
        claude_settings.apply_catalog(stale)
        assert claude_settings.refresh_due()
        claude_settings.apply_catalog({"refreshed": found["refreshed"], "providers": {"xai": {"error": "timed out"}}})
        assert "grok-4.8" in dict(claude_settings.models())
    finally:
        providers.use_catalog({})


def test_the_mouse_over_the_assistant_is_an_arrow_whatever_the_canvas_mode(window):
    from PyQt5.QtCore import Qt
    panel = window.claude_panel
    panel.set_open(True)
    for mode_cursor in (Qt.CrossCursor, Qt.OpenHandCursor, Qt.SizeAllCursor):
        window.canvas.setCursor(mode_cursor)  # what a canvas mode sets
        for widget in (panel, panel.transcript, panel.model_button, panel.send_button):
            assert widget.cursor().shape() == Qt.ArrowCursor
        assert panel.transcript.viewport().cursor().shape() == Qt.ArrowCursor
        assert panel.prompt_edit.viewport().cursor().shape() == Qt.IBeamCursor  # the box you type in
    window.canvas.setCursor(Qt.ArrowCursor)


def test_cli_agent_without_a_key_says_where_to_add_it(tmp_path):
    env = dict(os.environ, APPDATA=str(tmp_path))
    env.pop("ANTHROPIC_API_KEY", None)
    result = subprocess.run([sys.executable, "-m", "openstrand", "agent", "a heart"], cwd=ROOT, env=env,
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 1 and "Settings > Models" in result.stderr and "ANTHROPIC_API_KEY" in result.stderr
    env.pop("XAI_API_KEY", None)
    result = subprocess.run([sys.executable, "-m", "openstrand", "agent", "a heart", "--model", "grok"], cwd=ROOT,
                            env=env, capture_output=True, text=True, timeout=120)
    assert result.returncode == 1 and "no xAI (Grok) API key: set XAI_API_KEY" in result.stderr
    result = subprocess.run([sys.executable, "-m", "openstrand", "agent", "a heart", "--model", "gpt-9"], cwd=ROOT,
                            env=env, capture_output=True, text=True, timeout=120)
    assert result.returncode == 1 and "unknown model gpt-9" in result.stderr


# ------------------------------------------------------------------ app
@pytest.fixture(scope="module")
def window(tmp_path_factory):
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    # Claude saves whether it is open, and what it cost, in the settings folder.
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


def unfolded(panel):
    """The transcript's text with every step group and thought opened."""
    for entry in panel.entries:
        if entry["kind"] == "group":
            entry["open"] = True
            for step in entry["steps"]:
                if step["kind"] == "thinking":
                    step["open"] = True
    panel.render_transcript()
    return panel.transcript.toPlainText()


def run_events(panel, events, tmp_path, prompt="two linked rings"):
    """Feed a finished run through the panel as the agent process would."""
    panel.out_dir, panel.prompt, panel.shown_prompt = str(tmp_path), prompt, prompt  # as send() sets them
    panel.run_cost, panel.total_before, panel.run_texts = 0.0, 0.0, []
    panel.run_mode = panel.mode
    panel.done_event = None
    for event in events:
        panel.handle_event(event)
    panel.finished()


def test_a_claude_design_opens_in_a_new_tab_with_layers_and_groups(window, tmp_path):
    source = ROOT / "knot_samples/turks_heads/json/turks_head_3x5.json"
    expected = project.read(source)
    tabs_before = len(window.tab_manager.tabs)
    assert window.open_claude_design(str(source))
    assert len(window.tab_manager.tabs) == tabs_before + 1
    assert len(window.canvas.strands) == len(expected["strands"])
    names = {s.layer_name for s in window.canvas.strands}
    assert {s["layer_name"] for s in expected["strands"]} <= names
    assert set(expected["groups"]) <= set(window.group_layer_manager.get_group_data())
    assert window.tab_manager.get_active().title == "turks_head_3x5"

    # What Claude would start from is exactly what is now on the canvas.
    snapshot = window.claude_canvas_snapshot()
    assert len(snapshot["strands"]) == len(expected["strands"])


def test_the_claude_button_shows_and_hides_claude_over_the_canvas(window, monkeypatch, tmp_path):
    import claude_settings
    from PyQt5.QtCore import Qt
    from PyQt5.QtTest import QTest
    from PyQt5.QtWidgets import QApplication
    monkeypatch.setenv("APPDATA", str(tmp_path))
    panel, button = window.claude_panel, window.claude_button
    panel.set_open(False)
    assert button.isVisible() and not button.isChecked() and not panel.isVisible()
    # It sits with State and Settings at the end of the toolbar, as a twin of Settings.
    row = window.toolbar_button_layout if not window._toolbar_two_rows else window.toolbar_button_layout_2
    order = [row.itemAt(i).widget() for i in range(row.count()) if row.itemAt(i).widget()]
    assert order[-3:] == [window.layer_state_button, button, window.settings_button]
    assert button.size() == window.settings_button.size() and button.toolTip() == ""
    assert button.color().name() == "#f0f0f0" and button.RING.name() == "#ff5500"  # the logo's tile, at rest

    # Pressed, Claude floats over the bottom of the visible canvas; the canvas keeps its size.
    size = window.canvas.size()
    button.click()
    QApplication.processEvents()
    assert panel.isVisible() and button.isChecked() and window.canvas.size() == size
    assert panel.parentWidget() is window.canvas
    area = panel.visible_canvas()
    assert area.contains(panel.geometry()) and panel.geometry().bottom() == area.bottom() - panel.MARGIN
    assert "panel_open" not in claude_settings.load()  # not kept: Claude starts closed every time

    # Pressed again, nothing is left on screen; Ctrl+J does the same both ways.
    button.click()
    assert not panel.isVisible() and not button.isChecked()
    window.activateWindow()
    QTest.keyClick(window.windowHandle(), Qt.Key_J, Qt.ControlModifier)
    assert panel.isVisible() and button.isChecked()
    QTest.keyClick(window.windowHandle(), Qt.Key_J, Qt.ControlModifier)
    assert not panel.isVisible() and not button.isChecked()

    # Settings > Claude can hide it altogether: no button, and Ctrl+J does nothing.
    window.set_claude_available(False)
    assert not button.isVisible() and claude_settings.load()["show_button"] is True  # the page saves it
    QTest.keyClick(window.windowHandle(), Qt.Key_J, Qt.ControlModifier)
    assert not panel.isVisible()
    button.click()  # open when Settings hides it: shown again, it comes back closed
    window.set_claude_available(False)
    window.set_claude_available(True)
    assert button.isVisible() and not panel.isVisible() and not button.isChecked()

    # Each time the app starts Claude is closed, whatever was showing when it last closed.
    import json
    from claude_panel import ClaudePanel
    path = claude_settings.settings_path()
    claude_settings.save(show_button=True)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["panel_open"] = True  # what older versions kept
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    fresh = ClaudePanel(window, window.canvas)
    try:
        assert not fresh.isVisibleTo(window.canvas)
    finally:
        fresh.deleteLater()


def test_the_claude_button_shows_a_run_while_claude_is_hidden(window, monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    panel, button = window.claude_panel, window.claude_button
    panel.set_open(False)
    monkeypatch.setattr(panel, "running", lambda: True)
    panel.activity_changed.emit()
    assert button.spin.isActive()  # an arc turns around the button
    panel.set_open(True)
    assert not button.spin.isActive()  # Claude is in view, so the button stays still
    panel.set_open(False)
    monkeypatch.setattr(panel, "running", lambda: False)
    panel.design_waiting = True
    panel.activity_changed.emit()
    assert not button.spin.isActive() and button.grab().toImage().pixelColor(26, 6).green() > 150  # the dot
    panel.set_open(True)
    assert panel.design_waiting is False


def test_the_prompt_box_is_a_chat_box(window, monkeypatch):
    from PyQt5.QtCore import Qt
    from PyQt5.QtTest import QTest
    from PyQt5.QtWidgets import QApplication
    panel, manager = window.claude_panel, window.layer_panel.undo_redo_manager
    clicks, pans, sent = [], [], []
    for name in ("undo_button", "redo_button"):
        button = getattr(manager, name)
        monkeypatch.setattr(button, "click", lambda name=name: clicks.append(name))
        button.setEnabled(True)  # as if there were history to undo and redo
    monkeypatch.setattr(window.layer_panel, "toggle_pan_mode", lambda: pans.append(1))
    monkeypatch.setattr(panel, "send", lambda: sent.append(panel.prompt_edit.text()))
    panel.prompt_edit.submitted.disconnect()
    panel.prompt_edit.submitted.connect(panel.send)
    panel.set_open(True)
    window.activateWindow()
    panel.prompt_edit.clear()
    panel.prompt_edit.setFocus()
    QApplication.processEvents()

    for key in "a zx":  # through the window, the way real typing arrives
        QTest.keyClick(window.windowHandle(), Qt.Key_Space if key == " " else key)
    assert panel.prompt_edit.text() == "a zx"
    assert clicks == [] and pans == []

    # Shift+Enter starts a new line and the box grows to show it.
    one_line = panel.prompt_edit.height()
    QTest.keyClick(window.windowHandle(), Qt.Key_Return, Qt.ShiftModifier)
    QTest.keyClicks(panel.prompt_edit, "in teal")
    QApplication.processEvents()
    assert panel.prompt_edit.text() == "a zx\nin teal" and sent == []
    two_lines = panel.prompt_edit.height()
    assert two_lines > one_line

    # It stops growing after MAX_LINES and scrolls instead.
    for _ in range(20):
        QTest.keyClick(panel.prompt_edit, Qt.Key_Return, Qt.ShiftModifier)
    QApplication.processEvents()
    tallest = panel.prompt_edit.height()
    assert two_lines < tallest < 10 * panel.prompt_edit.line_height() + 30
    panel.prompt_edit.setText("a zx\nin teal")
    QApplication.processEvents()
    assert panel.prompt_edit.height() == two_lines

    # Enter (and the keypad Enter) sends.
    QTest.keyClick(window.windowHandle(), Qt.Key_Return)
    QTest.keyClick(panel.prompt_edit, Qt.Key_Enter, Qt.KeypadModifier)
    assert sent == ["a zx\nin teal"] * 2

    # Away from text boxes the shortcuts still work.
    window.canvas.setFocus()
    QApplication.processEvents()
    QTest.keyClick(window.windowHandle(), Qt.Key_Space)
    QTest.keyClick(window.windowHandle(), "z")
    assert pans == [1] and clicks == ["undo_button"]


def test_the_panel_turns_events_into_a_transcript_and_opens_the_result(window, tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))  # the run's cost is saved in the settings folder
    panel = window.claude_panel
    opened = []
    panel.design_ready.connect(opened.append)
    design = tmp_path / "design.json"
    design.write_text((ROOT / "knot_samples/links/json/hopf_link.json").read_text(), encoding="utf-8")
    panel.out_dir, panel.prompt = str(tmp_path), "two linked rings in teal"
    for event in [{"type": "tool_end", "name": "load_sample", "ok": True, "summary": "hopf_link"},
                  {"type": "tool_end", "name": "render", "ok": True, "summary": "picture"},
                  {"type": "text", "text": "Two linked rings."},
                  {"type": "done", "ok": True, "error": None, "project": str(design), "cost": 0.012,
                   "model": "claude-sonnet-5-5"}]:
        panel.handle_event(event)
    panel.finished()
    assert opened and opened[-1].endswith("two_linked_rings_in_teal.json")
    shown = unfolded(panel)
    assert "Two linked rings." in shown and "hopf_link" in shown
    assert panel.status_label.text().startswith("this request $0.012")


def test_sharing_with_the_developer_is_asked_once_and_only_a_yes_sends_it_sealed(window, monkeypatch, tmp_path):
    pytest.importorskip("cryptography.hazmat.primitives.hpke")
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from PyQt5.QtCore import QUrl
    from PyQt5.QtWidgets import QApplication
    import claude_settings
    import claude_sharing
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
    got = []

    class Worker(BaseHTTPRequestHandler):  # a stand-in for the developer's Cloudflare Worker
        def do_POST(self):
            got.append(self.rfile.read(int(self.headers["Content-Length"])))
            self.send_response(204)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *args):
            pass
    http = HTTPServer(("127.0.0.1", 0), Worker)
    threading.Thread(target=http.serve_forever, daemon=True).start()
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    private, public = claude_sharing.new_keys()
    panel = window.claude_panel
    panel.entries.clear()
    panel.share_asked, panel.stopping = False, False
    design = tmp_path / "made.json"
    design.write_text((ROOT / "knot_samples/links/json/hopf_link.json").read_text(), encoding="utf-8")

    def run():  # one request's events, as the agent sends them (new ones each time)
        return [{"type": "text", "text": "Two linked rings, in teal."},
                {"type": "done", "ok": True, "error": None, "project": str(design), "cost": 0.01,
                 "model": "claude-haiku-5-5"}]

    def received(count):
        for _ in range(200):
            if len(got) >= count:
                return True
            QApplication.processEvents()
            time.sleep(0.02)
        return False

    def cards():
        return [e for e in panel.entries if e["kind"] == "share"]
    try:
        # Until the developer sets sharing up, nothing asks and nothing goes.
        run_events(panel, run(), tmp_path, prompt="SECRET-PROMPT two rings")
        assert cards() == [] and got == []
        monkeypatch.setattr(claude_sharing, "SHARE_URL", f"http://127.0.0.1:{http.server_port}/v1/share")
        monkeypatch.setattr(claude_sharing, "SHARE_PUBLIC_KEY", public)
        run_events(panel, run(), tmp_path, prompt="SECRET-PROMPT two rings")
        (card,) = cards()
        assert card["state"] is None and got == [] and claude_settings.load()["share"] is None
        asked = panel.transcript.toPlainText()
        assert "Help make it better" in asked and "Yes, help improve it" in asked
        assert "From now on, send the developer what the model makes" in asked  # a yes holds from here on
        assert "Never sent: what you type, your pictures, your files, your API keys" in asked
        # What a short text could leave out is said too: the answer can quote, their design goes whole.
        assert "can repeat words from your request" in asked and "a design of yours that the model changed" in asked
        run_events(panel, run(), tmp_path, prompt="SECRET-PROMPT two rings")
        assert len(cards()) == 1  # left unanswered: not asked again while the app runs
        # Share: this request goes, sealed; the next ones go without asking.
        panel.follow_link(QUrl(f"os:share/{panel.entries.index(card)}"))
        assert card["state"] == "shared" and "record" not in card and claude_settings.load()["share"] is True
        assert received(1)
        shared = claude_sharing.unseal(got[0], private)
        assert shared["answer"] == ["Two linked rings, in teal."] and shared["model"] == "claude-haiku-5-5"
        assert shared["design"]["strands"] and shared["ok"] is True
        assert shared["version"] == claude_sharing.APP_VERSION and shared["gallery"] is False
        assert "SECRET-PROMPT" not in json.dumps(shared)  # what the person typed never goes
        assert [e for e in panel.entries if e["kind"] == "gallery"] == []  # no gallery set up: not asked
        run_events(panel, run(), tmp_path, prompt="SECRET-PROMPT again")
        assert received(2) and len(cards()) == 1
        panel.finished()  # the same request finishing twice is still shared once
        time.sleep(0.3)
        assert len(got) == 2
        # A design Claude opened in a tab itself (through the bridge) is shared with it too.
        tabbed = run()
        tabbed[-1]["opened_tabs"] = ["Two rings"]
        run_events(panel, tabbed, tmp_path, prompt="SECRET-PROMPT in a tab")
        assert received(3) and claude_sharing.unseal(got[2], private)["design"]["strands"]
        # A request that only looked at the person's canvas: their design is not Claude's to share.
        looked = run()
        looked[-1]["changed"] = False
        run_events(panel, looked, tmp_path, prompt="SECRET-PROMPT what is this")
        assert received(4)
        only_answer = claude_sharing.unseal(got[3], private)
        assert only_answer["design"] is None and only_answer["picture"] is None
        assert only_answer["answer"] == ["Two linked rings, in teal."]
        # An answer that repeats one of the person's keys (saved, of any shape): the key is cut out.
        claude_settings.save(provider_key=("openai", "an-odd-saved-key-0123456789"))
        keyed = run()
        keyed[0]["text"] = "Your key an-odd-saved-key-0123456789 works."
        run_events(panel, keyed, tmp_path, prompt="SECRET-PROMPT my key")
        assert received(5) and claude_sharing.unseal(got[4], private)["answer"] == ["Your key … works."]
        # The public gallery is a second question, asked only after a yes to sharing, and only
        # once the developer says where the gallery is. Until the person says yes, no share
        # says it may be shown, and never one made from a design of their own.
        monkeypatch.setattr(claude_sharing, "GALLERY_URL", "https://example.github.io/OpenStrandStudio/")
        fresh = lambda: run()[:1] + [dict(run()[1], new=True)]  # noqa: E731 (made from nothing of theirs)
        run_events(panel, fresh(), tmp_path, prompt="SECRET-PROMPT a new one")
        assert received(6) and claude_sharing.unseal(got[5], private)["gallery"] is False
        saved = json.loads(Path(claude_settings.settings_path()).read_text(encoding="utf-8"))
        saved.pop("share")  # as before the person was ever asked
        Path(claude_settings.settings_path()).write_text(json.dumps(saved), encoding="utf-8")
        panel.shared_event, panel.share_asked = None, False
        panel.entries.clear()
        run_events(panel, fresh(), tmp_path, prompt="SECRET-PROMPT asked again")
        (card,) = cards()
        panel.follow_link(QUrl(f"os:share/{panel.entries.index(card)}"))
        (asked,) = [e for e in panel.entries if e["kind"] == "gallery"]
        text = panel.transcript.toPlainText()
        assert "public gallery" in text and "https://example.github.io/OpenStrandStudio/" in text
        assert "Never the answer" in text and "cannot find yours later to take them down" in text
        assert received(7) and claude_sharing.unseal(got[6], private)["gallery"] is False  # not answered yet
        panel.follow_link(QUrl(f"os:gallery/{panel.entries.index(asked)}"))
        assert asked["state"] == "shared" and claude_settings.load()["gallery"] is True
        run_events(panel, fresh(), tmp_path, prompt="SECRET-PROMPT for the gallery")
        assert received(8)
        shown = claude_sharing.unseal(got[7], private)
        assert shown["gallery"] is True and shown["new"] is True
        run_events(panel, run(), tmp_path, prompt="SECRET-PROMPT from my canvas")  # not new: stays private
        assert received(9) and claude_sharing.unseal(got[8], private)["gallery"] is False
        assert len([e for e in panel.entries if e["kind"] == "gallery"]) == 1  # asked once
        # Turned off (Settings > Models): nothing goes, not even a share already on its way.
        claude_settings.save(share=False)
        run_events(panel, run(), tmp_path, prompt="SECRET-PROMPT once more")
        said = []
        monkeypatch.setattr(sys.modules[type(panel).__module__], "terminal_log", said.append)
        panel.send_share(claude_sharing.record(["Queued just before sharing was turned off."]))
        for _ in range(250):
            if "not shared: sharing was turned off" in said:
                break
            time.sleep(0.02)
        assert "not shared: sharing was turned off" in said
        assert not any(line.startswith("shared with the developer") for line in said)
        time.sleep(0.2)
        assert len(got) == 9 and len(cards()) == 1
    finally:
        http.shutdown()
        panel.entries.clear()


def test_settings_say_where_the_keys_are_and_offer_sharing_once_it_is_set_up(tmp_path, monkeypatch):
    pytest.importorskip("cryptography.hazmat.primitives.hpke")
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])  # noqa: F841 (kept alive for the page)
    import claude_settings
    import claude_sharing
    from claude_panel import ClaudeSettingsPage
    monkeypatch.setenv("APPDATA", str(tmp_path))
    page = ClaudeSettingsPage("en")
    assert page.share_check.isHidden() and page.share_hint.isHidden()  # the developer has not set it up
    assert "settings folder" in page.storage.text()
    _, public = claude_sharing.new_keys()
    monkeypatch.setattr(claude_sharing, "SHARE_URL", "https://openstrand-share.example.workers.dev/v1/share")
    monkeypatch.setattr(claude_sharing, "SHARE_PUBLIC_KEY", public)
    monkeypatch.setattr(claude_settings, "keychain", lambda: object())  # a password store on this computer
    page.retranslate("en")
    assert not page.share_check.isHidden() and not page.share_check.isChecked()  # off until they say yes
    assert "encrypted on this computer" in page.share_hint.text() and "password store" in page.storage.text()
    page.share_check.setChecked(True)
    assert claude_settings.load()["share"] is True
    page.retranslate("de")
    assert page.share_check.isChecked() and page.share_check.text().startswith("Was das Modell erstellt")
    # The gallery box: shown once the developer says where the gallery is, its own yes, and
    # only while sharing is on.
    assert page.gallery_check.isHidden() and page.gallery_hint.isHidden()
    monkeypatch.setattr(claude_sharing, "GALLERY_URL", "https://example.github.io/OpenStrandStudio/")
    page.retranslate("en")
    assert not page.gallery_check.isHidden() and not page.gallery_check.isChecked()
    assert "https://example.github.io/OpenStrandStudio/" in page.gallery_hint.text()
    page.gallery_check.setChecked(True)
    assert claude_settings.load()["gallery"] is True
    page.share_check.setChecked(False)  # sharing off: the gallery box goes with it
    assert not page.gallery_check.isEnabled() and not page.gallery_check.isChecked()
    assert claude_settings.load()["share"] is False


def test_with_models_off_the_panel_sends_nothing_and_a_running_request_stops(window, monkeypatch, tmp_path):
    from PyQt5.QtCore import QProcess, Qt
    from PyQt5.QtTest import QTest
    import claude_settings
    from claude_panel import ClaudeSettingsPage
    monkeypatch.setenv("APPDATA", str(tmp_path))
    claude_settings.save(api_key="sk-ant-test-1234567890")
    page = ClaudeSettingsPage("en")
    assert page.models_check.isChecked() and not page.china_check.isChecked() and page.refresh_button.isEnabled()
    labels = [page.model_combo.itemText(i) for i in range(page.model_combo.count())]
    assert labels and not any(name in label for label in labels for name in ("Kimi", "DeepSeek", "Qwen"))
    page.china_check.setChecked(True)  # allowed: their models are offered
    assert any("DeepSeek" in page.model_combo.itemText(i) for i in range(page.model_combo.count()))
    page.china_check.setChecked(False)
    assert claude_settings.load()["allow_china"] is False
    page.show_button_changed.connect(window.set_claude_available)  # as the Settings dialog does
    button, panel = window.claude_button, window.claude_panel
    panel.set_open(True)
    assert button.isVisible() and panel.isVisible() and page.show_check.isEnabled()
    page.models_check.setChecked(False)
    assert claude_settings.load()["models_on"] is False and not page.refresh_button.isEnabled()
    # Off is off everywhere: no Claude button in the main window, no panel, and Ctrl+J does nothing.
    assert not button.isVisible() and not panel.isVisible() and not claude_settings.claude_available()
    window.activateWindow()
    QTest.keyClick(window.windowHandle(), Qt.Key_J, Qt.ControlModifier)
    assert not panel.isVisible()
    assert not page.show_check.isEnabled() and claude_settings.load()["show_button"] is True  # kept for later
    assert "Claude button also leaves the main window" in page.models_hint.text()
    started, killed = [], []
    monkeypatch.setattr("claude_panel.QProcess.start", lambda self, program, args: started.append(args))
    panel.prompt_edit.setText("a heart")
    panel.send()
    assert started == [] and "AI models are turned off in Settings > Models" in panel.transcript.toPlainText()
    # Turned off while a request runs: it stops at once, as with Stop.
    page.models_check.setChecked(True)
    assert claude_settings.load()["models_on"] and page.refresh_button.isEnabled()
    assert button.isVisible() and not panel.isVisible() and page.show_check.isEnabled()  # back, and closed
    page.show_check.setChecked(False)  # hidden by its own box: turning models on does not bring it back
    page.models_check.setChecked(False)
    page.models_check.setChecked(True)
    assert not button.isVisible()
    page.show_check.setChecked(True)
    assert button.isVisible()
    panel.process = SimpleNamespace(state=lambda: QProcess.Running, kill=lambda: killed.append(1))
    try:
        panel.refresh_controls()
        assert killed == []  # on: it runs on
        page.models_check.setChecked(False)  # the dialog sends settings_changed to the panel
        panel.refresh_controls()
        assert killed == [1] and panel.stopping
    finally:
        panel.process, panel.stopping = None, False
        claude_settings.save(models_on=True)


def test_the_panel_asks_for_a_key_before_sending(window, monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    panel = window.claude_panel
    panel.prompt_edit.setText("a heart")
    panel.send()
    assert panel.process is None or not panel.running()
    assert "Settings > Models" in panel.transcript.toPlainText()


def test_spending_adds_up_across_requests_until_reset(tmp_path, monkeypatch):
    import datetime
    import claude_settings
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert claude_settings.add_spending(0.25) == 0.25
    assert claude_settings.add_spending(0.5) == 0.75
    for nothing in (0, -3, "x", float("nan"), None):
        assert claude_settings.add_spending(nothing) == 0.75
    claude_settings.save(api_key="sk-ant-test-1234567890", model="claude-haiku-5-5")  # keeps the total
    saved = claude_settings.load()
    assert saved["spent"] == 0.75 and saved["spent_since"] == datetime.date.today().isoformat()
    claude_settings.reset_spending()
    assert claude_settings.load()["spent"] == 0.0 and claude_settings.load()["api_key"]


def test_the_panel_total_keeps_counting_and_settings_show_it(window, monkeypatch, tmp_path):
    import claude_settings
    from claude_panel import ClaudeSettingsPage
    monkeypatch.setenv("APPDATA", str(tmp_path))
    claude_settings.add_spending(1.2)  # earlier requests
    panel = window.claude_panel
    panel.out_dir, panel.prompt = str(tmp_path), "a heart"

    # A first request: the total rises live from what was spent before.
    panel.run_cost, panel.total_before = 0.0, claude_settings.load()["spent"]
    panel.handle_event({"type": "usage", "cost": 0.04})
    assert panel.status_label.text().endswith("this request $0.040 · total $1.24")
    panel.handle_event({"type": "done", "ok": True, "error": None, "project": None, "cost": 0.06,
                        "model": "claude-haiku-5-5"})
    panel.finished()
    assert panel.status_label.text() == "this request $0.060 · total $1.26"
    assert claude_settings.load()["spent"] == pytest.approx(1.26)

    # A second request is stopped part way: what it spent still counts, once.
    panel.run_cost, panel.total_before = 0.0, claude_settings.load()["spent"]
    panel.done_event = None
    panel.handle_event({"type": "usage", "cost": 0.03})
    panel.finished()
    panel.finished()
    assert claude_settings.load()["spent"] == pytest.approx(1.29)

    page = ClaudeSettingsPage("en")
    assert page.spent_label.text().startswith("Spent with Claude: $1.29 since ")
    page.reset_spending()
    assert claude_settings.load()["spent"] == 0.0 and not page.reset_spent_button.isEnabled()
    assert page.spent_label.text().startswith("Spent with Claude: $0.000 since ")


def test_the_settings_page_saves_key_and_model(monkeypatch, tmp_path):
    from PyQt5.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    import claude_settings
    from claude_panel import ClaudeSettingsPage
    monkeypatch.setenv("APPDATA", str(tmp_path))
    page = ClaudeSettingsPage("en")
    from PyQt5.QtWidgets import QLineEdit, QPushButton
    # The eye in the key field shows what was typed and hides it again (no separate Show button).
    assert page.key_edit.echoMode() == QLineEdit.Password
    assert not any(b.text() in ("Show", "Hide") for b in page.findChildren(QPushButton))
    page.show_key_action.trigger()
    assert page.key_edit.echoMode() == QLineEdit.Normal and page.show_key_action.toolTip() == "Hide"
    page.show_key_action.trigger()
    assert page.key_edit.echoMode() == QLineEdit.Password and not page.show_key_action.icon().isNull()
    # The page never asks for more width than a dialog gives it: the model list sizes to a
    # short name, not to its longest entry.
    assert page.minimumSizeHint().width() < 520
    # The $ − / + controls are the same width, with room for the largest amount.
    page.fit_money_spins()
    assert page.limit_spin.width() == page.session_spin.width() >= page.limit_spin.fontMetrics().horizontalAdvance("$500.00") + 62
    page.key_edit.setText("sk-ant-api03-abcdefghijkl")
    page.save_key()
    assert claude_settings.load()["api_key"] == "sk-ant-api03-abcdefghijkl"
    assert "ijkl" in page.key_status.text() and page.key_edit.text() == ""
    page.model_combo.setCurrentIndex(page.model_combo.findData("claude-haiku-5-5"))
    assert claude_settings.load()["model"] == "claude-haiku-5-5"
    page.remove_key()
    assert claude_settings.load()["api_key"] == ""
    page.web_check.setChecked(False)
    page.limit_spin.setValue(4.5)
    assert claude_settings.load()["web"] is False and claude_settings.load()["max_cost"] == 4.5
    shown = []
    page.show_button_changed.connect(shown.append)
    assert page.show_check.isChecked()
    page.show_check.setChecked(False)
    assert shown == [False] and claude_settings.load()["show_button"] is False
    page.retranslate("he")
    assert page.model_combo.count() == len(claude_settings.models()) and not page.show_check.isChecked()
    assert not page.web_check.isChecked() and page.limit_spin.value() == 4.5


# ------------------------------------------------------- end to end, no key
FAKE_REPLIES = [
    {"content": [{"type": "thinking", "thinking": "A bracelet weave is an MxN stitch.", "signature": "sig-1"},
                 {"type": "server_tool_use", "id": "srvtoolu_1", "name": "web_search",
                  "input": {"query": "5x3 bracelet weave"}},
                 {"type": "web_search_tool_result", "tool_use_id": "srvtoolu_1",
                  "content": [{"type": "web_search_result", "url": "https://example.com/weave",
                               "title": "Bracelet weaves", "encrypted_content": "abc", "page_age": None}]},
                 {"type": "text", "text": "A 5x3 right-hand stitch."},
                 {"type": "tool_use", "id": "toolu_1", "name": "make_mxn", "input": {"m": 5, "n": 3, "hand": "rh"}}],
     "stop_reason": "tool_use"},
    {"content": [{"type": "tool_use", "id": "toolu_2", "name": "recolor", "input": {"sets": [4, 5, 6, 7, 8], "color": "teal"}},
                 {"type": "tool_use", "id": "toolu_3", "name": "recolor", "input": {"sets": [1, 2, 3], "color": "gold"}},
                 {"type": "tool_use", "id": "toolu_4", "name": "render", "input": {}}],
     "stop_reason": "tool_use"},
    {"content": [{"type": "text", "text": "Done: teal vertical ribbons, gold horizontal ones."}],
     "stop_reason": "end_turn"},
]

FAKE_DRAWING = [
    {"content": [{"type": "thinking", "thinking": "Two overlapping circles link like a chain.", "signature": "s"},
                 {"type": "tool_use", "id": "toolu_1", "name": "draw_design", "input": {
                     "name": "linked rings", "cords": [
                         {"shape": "circle", "center": [480, 400], "radius": 180, "color": "teal",
                          "label": "Left ring"},
                         {"shape": "circle", "center": [720, 400], "radius": 180, "color": "gold",
                          "label": "Right ring"}]}}],
     "stop_reason": "tool_use"},
    {"content": [{"type": "tool_use", "id": "toolu_2", "name": "render", "input": {}}], "stop_reason": "tool_use"},
    {"content": [{"type": "text", "text": "Two linked rings, teal and gold."}], "stop_reason": "end_turn"},
]


FIGURE_8 = {"name": "figure 8 knot", "cords": [{"label": "Figure 8", "color": "crimson", "width": 26, "points": [
    [200, 200], [380, 260], [560, 380], [620, 540], [520, 660], [400, 600], [420, 450], [560, 320],
    [600, 180], [480, 120], [400, 220], [480, 420], [640, 560], [820, 620]]}]}
STEP_TITLES = ["Step 1 · the tail", "Step 2 · first loop", "Step 3 · up and over",
               "Step 4 · through the top loop", "Step 5 · the figure 8"]
FAKE_STEPS = [
    {"content": [{"type": "tool_use", "id": "toolu_1", "name": "draw_design", "input": FIGURE_8}],
     "stop_reason": "tool_use"},
    {"content": [{"type": "tool_use", "id": "toolu_2", "name": "make_steps", "input": {"count": 5}}],
     "stop_reason": "tool_use"},
    {"content": [{"type": "tool_use", "id": "toolu_3", "name": "list_tabs", "input": {}}], "stop_reason": "tool_use"},
] + [
    {"content": [{"type": "tool_use", "id": f"toolu_{4 + n}", "name": "open_in_new_tab",
                  "input": {"design": f"step {n + 1}", "title": STEP_TITLES[n]}}], "stop_reason": "tool_use"}
    for n in range(5)
] + [
    {"content": [{"type": "text", "text": "Five tabs, one per step, from the tail to the finished figure 8."}],
     "stop_reason": "end_turn"},
]


FAKE_TALK = [{"content": [{"type": "text", "text": "A crimson figure 8 with open ends."}], "stop_reason": "end_turn"}]

TIE_TITLES = ["Step 1 · first loop", "Step 2 · round the standing part", "Step 3 · back across",
              "Step 4 · through the loop", "Step 5 · draw it up", "Step 6 · pull tight"]
FAKE_TIE = [
    {"content": [{"type": "tool_use", "id": "toolu_1", "name": "knot_library", "input": {}}], "stop_reason": "tool_use"},
    {"content": [{"type": "tool_use", "id": "toolu_2", "name": "tie_knot",
                  "input": {"knot": "figure 8", "color": "crimson"}}], "stop_reason": "tool_use"},
] + [
    {"content": [{"type": "tool_use", "id": f"toolu_{3 + n}", "name": "open_in_new_tab",
                  "input": {"design": f"step {n + 1}", "title": TIE_TITLES[n]}}], "stop_reason": "tool_use"}
    for n in range(6)
] + [
    {"content": [{"type": "tool_use", "id": "toolu_9", "name": "identify_knot", "input": {}}], "stop_reason": "tool_use"},
    {"content": [{"type": "text", "text": "Six tabs: a figure-eight tied step by step, then pulled tight."}],
     "stop_reason": "end_turn"},
]


@pytest.fixture
def fake_api(monkeypatch, request):
    """A local stand-in for the Messages API, reached through the real SDK."""
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            # The SDK sends the key as x-api-key or as a bearer token.
            key = self.headers.get("x-api-key") or (self.headers.get("authorization") or "").removeprefix("Bearer ")
            requests.append({"beta": self.headers.get("anthropic-beta"), "key": key, "body": body})
            replies = getattr(request, "param", FAKE_REPLIES)
            reply = replies[min(len(requests) - 1, len(replies) - 1)]
            searches = sum(1 for b in reply["content"] if b["type"] == "server_tool_use")
            out = json.dumps({"id": f"msg_{len(requests)}", "type": "message", "role": "assistant",
                              "model": body["model"], "stop_sequence": None,
                              "usage": {"input_tokens": 1200, "output_tokens": 300,
                                        "cache_creation_input_tokens": 0, "cache_read_input_tokens": 900,
                                        "server_tool_use": {"web_search_requests": searches}},
                              **reply}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    # The agent runs every model on the stand-in (ANTHROPIC_BASE_URL would be ignored: see
    # openstrand/providers.py, "Safe requests").
    monkeypatch.setenv("OPENSTRAND_TEST_API", f"http://127.0.0.1:{server.server_port}")
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    yield requests
    server.shutdown()


def test_the_panel_runs_the_agent_in_the_background_and_opens_its_design(window, fake_api, monkeypatch, tmp_path):
    import claude_settings
    from PyQt5.QtWidgets import QApplication
    monkeypatch.setenv("APPDATA", str(tmp_path))
    claude_settings.save(api_key="sk-ant-test-key", model="claude-sonnet-5-5")
    panel = window.claude_panel
    opened = []
    panel.design_ready.connect(opened.append)
    tabs_before = len(window.tab_manager.tabs)

    panel.prompt_edit.setText("5x3 right hand bracelet in teal and gold")
    panel.send()
    assert panel.running()
    deadline = time.time() + 240
    while panel.running() and time.time() < deadline:
        QApplication.processEvents()
        time.sleep(0.05)
    QApplication.processEvents()

    assert fake_api and fake_api[0]["key"] == "sk-ant-test-key"
    assert fake_api[0]["body"]["model"] == "claude-sonnet-5-5"
    assert opened, panel.transcript.toPlainText()
    # Opened in a new tab through Load: canvas, layer panel and color sets.
    assert len(window.tab_manager.tabs) == tabs_before + 1
    loaded = project.read(opened[-1])
    assert len(window.canvas.strands) == len(loaded["strands"])
    vertical = [s for s in window.canvas.strands if s.layer_name.split("_")[0] in {"4", "5", "6", "7", "8"}
                and type(s).__name__ != "MaskedStrand"]
    assert vertical and all(s.color.name() == "#257d98" for s in vertical)
    shown = unfolded(panel)
    assert "teal vertical ribbons" in shown
    # The search and the thinking show in the panel, and both went back to the API unchanged.
    assert "Searched the web: 5x3 bracelet weave" in shown and "A bracelet weave is an MxN stitch." in shown
    echoed = [b["type"] for b in fake_api[1]["body"]["messages"][1]["content"]]
    assert echoed[:3] == ["thinking", "server_tool_use", "web_search_tool_result"]
    # The search is priced in: 3 replies of tokens plus one $0.01 search.
    tokens = 3 * (1200 * 2 + 300 * 10 + 900 * 0.2) / 1e6
    assert f"${tokens + 0.01:.3f}" in panel.status_label.text()


@pytest.mark.parametrize("fake_api", [FAKE_DRAWING], indirect=True)
def test_a_drawing_by_claude_opens_with_its_groups_in_the_layer_panel(window, fake_api, monkeypatch, tmp_path):
    import claude_settings
    from PyQt5.QtWidgets import QApplication
    monkeypatch.setenv("APPDATA", str(tmp_path))
    claude_settings.save(api_key="sk-ant-test-key", model="claude-haiku-5-5", web=False, max_cost=0.5)
    panel = window.claude_panel
    opened = []
    panel.design_ready.connect(opened.append)
    panel.prompt_edit.setText("two linked rings")
    panel.send()
    deadline = time.time() + 300
    while panel.running() and time.time() < deadline:
        QApplication.processEvents()
        time.sleep(0.05)
    QApplication.processEvents()

    assert opened, panel.transcript.toPlainText()
    body = fake_api[0]["body"]
    assert body["model"] == "claude-haiku-5-5" and not [t for t in body["tools"] if "web" in t.get("name", "")]
    assert len(window.canvas.strands) == len(project.read(opened[-1])["strands"])
    assert {"Left ring", "Right ring"} <= set(window.group_layer_manager.get_group_data())
    shown = unfolded(panel)
    assert "New Strand" in shown and "Two linked rings" in shown


@pytest.mark.parametrize("package, expected", [
    ("raise ImportError('no anthropic here')\n", "not installed for this Python"),
    ("__version__ = '1.9.0'\n", "too old"),
])
def test_cli_agent_says_how_to_install_the_anthropic_package(tmp_path, package, expected):
    fake = tmp_path / "site" / "anthropic"
    fake.mkdir(parents=True)
    (fake / "__init__.py").write_text(package, encoding="utf-8")
    env = dict(os.environ, PYTHONPATH=str(tmp_path / "site"), ANTHROPIC_API_KEY="sk-ant-test")
    result = subprocess.run([sys.executable, "-m", "openstrand", "agent", "a heart"], cwd=ROOT, env=env,
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 1
    assert expected in result.stderr and "-m pip install" in result.stderr and "anthropic>=2.4" in result.stderr


# --------------------------------------------- Claude Code-style controls
def test_agent_command_carries_effort_and_plan():
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "src"))
    from claude_panel import agent_command
    _, args = agent_command("a heart", "claude-haiku-5-5", "out", effort="max", plan=True, max_cost=1.5)
    assert args[args.index("--effort") + 1] == "max" and "--plan" in args
    assert args[args.index("--max-cost") + 1] == "1.50"
    _, args = agent_command("a heart", "claude-haiku-5-5", "out")
    assert "--plan" not in args and "--effort" not in args


def test_plan_mode_offers_only_tools_that_look():
    from types import SimpleNamespace
    from openstrand import agent
    runner = agent.Agent(SimpleNamespace(), ROOT / "designs", plan=True, web=True)
    names = [t["name"] for t in runner.tools()]
    assert set(names) == {"search_samples", "describe", "knot_library", "identify_knot", "check_masks", "web_search", "web_fetch"}
    assert "Plan mode is on" in runner.system()[0]["text"]
    builder = agent.Agent(SimpleNamespace(), ROOT / "designs")
    assert "draw_design" in [t["name"] for t in builder.tools()]
    assert "Plan mode is on" not in builder.system()[0]["text"]


def test_the_status_line_switches_mode_model_and_effort(window, monkeypatch, tmp_path):
    import claude_settings
    from PyQt5.QtCore import Qt
    from PyQt5.QtTest import QTest
    monkeypatch.setenv("APPDATA", str(tmp_path))
    panel = window.claude_panel
    panel.set_open(True)
    panel.set_mode("ask")
    assert "ask before opening designs" in panel.mode_button.text()
    # Shift+Tab in the box cycles ask -> open automatically -> plan, like Claude Code.
    panel.prompt_edit.setFocus()
    QTest.keyClick(panel.prompt_edit, Qt.Key_Backtab, Qt.ShiftModifier)
    assert panel.mode == "auto" and claude_settings.load()["mode"] == "auto"
    assert panel.prompt_edit.hasFocus()  # Shift+Tab switched the mode, not the focus
    panel.mode_button.click()
    assert panel.mode == "plan" and "plan mode" in panel.mode_button.text()
    # The mode's symbol is a picture (images/mode_*.png), not a character that may be an emoji.
    assert not panel.mode_button.icon().isNull() and not any(ch in panel.mode_button.text() for ch in "⏵⏸")
    assert claude_settings.load()["mode"] == "auto"  # plan mode is never kept
    panel.cycle_mode()
    assert panel.mode == "ask"
    panel.set_mode("auto")
    # The model and effort menus save the choice and the status line shows it.
    # The company has its own drop-down; the model drop-down lists that company's models.
    providers = panel.provider_menu.actions()
    assert providers[0].text().startswith("Anthropic") and providers[0].isChecked()
    assert [a.isChecked() for a in providers].count(True) == 1
    assert panel.provider_button.text() == "Anthropic"
    assert [a.text() for a in panel.model_menu.actions()] == ["Claude Sonnet 5.5", "Claude Haiku 5.5"]
    assert ("QMenu::item:selected" in panel.model_menu.styleSheet()
            and panel.provider_menu.styleSheet() == panel.model_menu.styleSheet() == panel.effort_menu.styleSheet())
    openai = [a for a in providers if a.text().startswith("OpenAI")][0]
    openai.trigger()  # another company: its first model
    assert claude_settings.provider_of(claude_settings.load()["model"]) == "openai"
    assert panel.provider_button.text() == "OpenAI" and all("GPT" in a.text() for a in panel.model_menu.actions())
    [a for a in panel.provider_menu.actions() if a.text().startswith("Anthropic")][0].trigger()
    assert claude_settings.load()["model"] == "claude-sonnet-5-5"
    # The Image button's picture is a PNG in images/, white on the dark theme.
    assert panel.attach_button.text() == "Image" and not panel.attach_button.icon().isNull()
    # Pictures, not characters: the drop-downs' arrow, the toggle's check, the Shift key.
    for pick in (panel.provider_button, panel.model_button, panel.effort_button):
        assert "▾" not in pick.text()
    assert "menu_arrow_on_" in panel.styleSheet() and "::menu-indicator" in panel.styleSheet()
    assert panel.use_canvas_check.isChecked() and not panel.use_canvas_check.icon().isNull()
    assert "✓" not in panel.use_canvas_check.text()
    panel.use_canvas_check.setChecked(False)
    assert panel.use_canvas_check.icon().isNull()
    panel.use_canvas_check.setChecked(True)
    assert panel.mode_key.text() == "Tab" and not panel.mode_key.icon().isNull()
    import os
    for name in ("check.png", "cross.png", "menu_arrow_on_dark.png", "menu_arrow_on_light.png",
                 "shift_on_dark.png", "shift_on_light.png"):
        assert os.path.exists(os.path.join(os.path.dirname(claude_settings.__file__), "images", name))
    haiku = [a for a in panel.model_menu.actions() if "Haiku" in a.text()][0]
    haiku.trigger()
    assert claude_settings.load()["model"] == "claude-haiku-5-5" and panel.model_button.text().startswith("Claude Haiku 5.5")
    top = [a for a in panel.effort_menu.actions() if a.text() == "Max effort"][0]
    top.trigger()
    assert claude_settings.load()["effort"] == "max" and panel.effort_button.text().startswith("Max effort")
    assert re.fullmatch(r"session \$\d+\.\d+ of \$10\.00", panel.session_label.text())


def test_steps_fold_into_one_line_once_claude_answers(window, monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    panel = window.claude_panel
    panel.set_mode("auto")
    panel.entries.clear()
    panel.handle_event({"type": "thinking", "text": "Two rings that link like a chain."})
    panel.handle_event({"type": "search", "name": "web_search", "query": "hopf link"})
    panel.handle_event({"type": "tool_start", "name": "draw_design"})
    group = panel.entries[-1]
    assert group["kind"] == "group" and group["open"] and group["steps"][-1]["running"]
    panel.handle_event({"type": "tool_end", "name": "draw_design", "ok": True, "summary": "2 cords, 2 crossings"})
    assert [s["kind"] for s in group["steps"]] == ["thinking", "search", "tool"] and group["steps"][-1]["ok"]
    panel.handle_event({"type": "text", "text": "Two linked rings."})
    assert not group["open"] and group["end"] is not None  # folded: "3 steps · 1s ›"
    shown = panel.transcript.toPlainText()
    assert "3 steps" in shown and "hopf link" not in shown and "Two linked rings." in shown
    # A click opens the group, and another click opens the thought.
    from PyQt5.QtCore import QUrl
    index = panel.entries.index(group)
    panel.follow_link(QUrl(f"os:group/{index}"))
    shown = panel.transcript.toPlainText()
    assert "Searched the web: hopf link" in shown and "2 cords, 2 crossings" in shown
    assert "Two rings that link" not in shown
    panel.follow_link(QUrl(f"os:think/{index}/0"))
    assert "Two rings that link like a chain." in panel.transcript.toPlainText()


def test_a_long_tool_shows_its_progress_with_a_picture_and_time_left(window, monkeypatch, tmp_path):
    from PyQt5.QtCore import QUrl
    from openstrand.progress import picture
    monkeypatch.setenv("APPDATA", str(tmp_path))
    panel = window.claude_panel
    panel.set_mode("auto")
    panel.entries.clear()
    panel.handle_event({"type": "tool_start", "name": "tie_knot", "input": {"knot": "overhand"}})
    step = panel.running_step("tie_knot")
    assert step is not None and step["key"] and panel.tick.isActive()
    step["start"] -= 10  # it has run ten seconds
    cord = [(100 + 4 * k, 300 + 40 * ((k // 10) % 2), 5.0 if 20 < k < 30 else 0.0) for k in range(80)]
    panel.handle_event({"type": "tool_progress", "name": "tie_knot", "stage": "draw_step", "step": 3, "steps": 5,
                        "fraction": 0.5, "frame": picture([cord], 24, "#257d98")})
    assert step["fraction"] == 0.5 and step["frame"] and step["eta"] is not None
    shown = panel.transcript.toPlainText()
    assert "Tie knot" in shown and "drawing step 3 of 5" in shown
    assert re.search(r"50% · about \d+s left · 10s", shown)  # ten seconds for half: about ten more
    html_text = panel.transcript.toHtml()
    assert f'claude-frame:{step["key"]}' in html_text and f'claude-bar:{step["key"]}' in html_text
    picture_shown = panel.transcript.document().resource(3, QUrl(f'claude-frame:{step["key"]}'))
    assert picture_shown is not None and not picture_shown.isNull()  # 3: QTextDocument.ImageResource
    assert panel.working.progress[0] == 0.5 and "50%" in panel.working.progress[1]
    assert panel.working.label == "Tie knot · drawing step 3 of 5"
    assert panel.working.grab().width() > 0
    # A tool that cannot tell how far it is: a sliding bar, never a made-up percent.
    panel.handle_event({"type": "tool_progress", "name": "tie_knot", "stage": "draw_step", "step": 4,
                        "steps": 5, "fraction": None})
    assert step["fraction"] == 0.5  # the bar never goes back
    panel.handle_event({"type": "tool_end", "name": "tie_knot", "ok": True, "summary": "Overhand knot · 5 steps"})
    assert not step["running"] and step["seconds"] >= 10 and panel.working.progress is None
    assert "Overhand knot · 5 steps · 10s" in panel.transcript.toPlainText()  # what it took, once done
    gone = panel.transcript.document().resource(3, QUrl(f'claude-frame:{step["key"]}'))
    assert gone is None or gone.isNull()  # the picture is freed
    panel.refresh_running()
    assert not panel.tick.isActive()  # nothing runs: the second hand stops


def test_the_mouse_over_a_tool_s_picture_shows_it_larger_and_it_keeps_moving(window, monkeypatch, tmp_path):
    from PyQt5.QtCore import QEvent, QPoint, QPointF, Qt
    from PyQt5.QtGui import QMouseEvent
    from PyQt5.QtWidgets import QApplication
    from openstrand.progress import picture
    import claude_panel
    monkeypatch.setenv("APPDATA", str(tmp_path))
    panel = window.claude_panel
    panel.set_open(True)
    panel.entries.clear()
    panel.handle_event({"type": "tool_start", "name": "tie_knot", "input": {}})
    step = panel.running_step("tie_knot")
    frame = lambda k: picture([[(100 + 4 * n, 300 + k * (n % 9), 0.0) for n in range(60)]], 24, "#257d98")
    panel.handle_event({"type": "tool_progress", "name": "tie_knot", "stage": "lay_out", "fraction": 0.2,
                        "frame": frame(1)})
    assert 'href="os:frame/' in panel.transcript.toHtml()
    QApplication.processEvents()
    # Find the picture in the conversation and move the mouse over it.
    viewport = panel.transcript.viewport()
    spot = next((QPoint(x, y) for y in range(0, viewport.height(), 3) for x in range(0, viewport.width(), 3)
                 if panel.transcript.anchorAt(QPoint(x, y)).startswith("os:frame/")), None)
    assert spot is not None
    move = QMouseEvent(QEvent.MouseMove, QPointF(spot), QPointF(viewport.mapToGlobal(spot)),
                       Qt.NoButton, Qt.NoButton, Qt.NoModifier)
    panel.eventFilter(viewport, move)
    preview = panel.preview
    assert preview.isVisible() and preview.key == step["key"]
    size = preview.pixmap().deviceIndependentSize() if hasattr(preview.pixmap(), "deviceIndependentSize") \
        else preview.pixmap().size() / preview.pixmap().devicePixelRatio()
    assert (round(size.width()), round(size.height())) == claude_panel.PREVIEW_SIZE
    before = preview.pixmap().toImage()
    panel.handle_event({"type": "tool_progress", "name": "tie_knot", "stage": "tighten", "fraction": 0.6,
                        "frame": frame(4)})
    assert preview.isVisible() and preview.pixmap().toImage() != before  # the new frame, still large
    panel.eventFilter(viewport, QEvent(QEvent.Leave))
    assert not preview.isVisible()
    panel.eventFilter(viewport, move)
    assert preview.isVisible()
    panel.handle_event({"type": "tool_end", "name": "tie_knot", "ok": True, "summary": "done"})
    assert not preview.isVisible() and "frame_data" not in step  # the tool ended: no picture to show


def test_finished_tools_show_a_picture_where_one_says_something(tmp_path):
    """In the app, a tool that made, changed, checked or read a design ends with its
    picture, cut to the design; tools that answer with words get none."""
    from types import SimpleNamespace
    from PyQt5.QtGui import QImage
    from openstrand import agent, draw
    events = []
    runner = agent.Agent(SimpleNamespace(), tmp_path, app=SimpleNamespace(call=lambda name, args: {}),
                         on_event=events.append)
    data, _ = draw.build({"cords": [{"points": [[100, 300], [300, 200], [500, 300]], "color": "teal"}]})
    try:
        runner.workspace.store(data)
        path = runner.tool_image("recolor", {})
        assert path and Path(path).exists()
        image = QImage(path)
        assert 300 < image.width() < 700 and image.height() < image.width()  # the design, not the whole canvas
        assert runner.tool_image("identify_knot", {}) == path  # the same design: drawn once
        assert runner.tool_image("describe", {}) is None and runner.tool_image("list_tabs", {}) is None
        runner.app = None  # the command line: nobody shows pictures
        assert runner.tool_image("recolor", {}) is None
    finally:
        runner.workspace.close()


def test_a_finished_tool_keeps_its_picture_and_app_tools_picture_the_canvas(window, monkeypatch, tmp_path):
    from PyQt5.QtCore import QUrl
    from PyQt5.QtGui import QColor, QImage
    monkeypatch.setenv("APPDATA", str(tmp_path))
    panel = window.claude_panel
    panel.set_open(True)
    panel.entries.clear()
    panel.out_dir = str(tmp_path)
    # The agent's picture of the design it made.
    made = tmp_path / "made.png"
    picture = QImage(400, 200, QImage.Format_ARGB32)
    picture.fill(QColor("#257d98"))
    picture.save(str(made))
    panel.handle_event({"type": "tool_start", "name": "make_heart", "input": {}})
    step = panel.running_step("make_heart")
    panel.handle_event({"type": "tool_end", "name": "make_heart", "ok": True, "summary": "Heart", "image": str(made)})
    assert step["picture"] == str(made) and f'claude-frame:{step["key"]}' in panel.transcript.toHtml()
    shown = panel.transcript.document().resource(3, QUrl(f'claude-frame:{step["key"]}'))
    assert shown is not None and not shown.isNull()
    # An app tool: the canvas as the tool left it, without Claude floating over it.
    panel.handle_event({"type": "tool_start", "name": "app_window", "input": {"op": "zoom"}})
    step = panel.running_step("app_window")
    panel.handle_event({"type": "tool_end", "name": "app_window", "ok": True, "summary": "zoom 100 %"})
    grabbed = QImage(step["picture"])
    assert grabbed.size() == window.canvas.size()
    # Words only (a list), or a failed tool: no picture.
    for name, ok in (("list_tabs", True), ("app_window", False)):
        panel.handle_event({"type": "tool_start", "name": name, "input": {}})
        step = panel.running_step(name)
        panel.handle_event({"type": "tool_end", "name": name, "ok": ok, "summary": ""})
        assert "picture" not in step


def test_stop_folds_the_steps_says_stopped_once_and_claude_hears_of_it(window, monkeypatch, tmp_path):
    from types import SimpleNamespace
    from PyQt5.QtCore import QProcess
    monkeypatch.setenv("APPDATA", str(tmp_path))
    panel = window.claude_panel
    panel.set_mode("auto")
    panel.entries.clear()
    panel.history.clear()
    panel.out_dir, panel.prompt, panel.shown_prompt = str(tmp_path), "an overhand tutorial", "an overhand tutorial"
    panel.run_cost, panel.total_before, panel.run_texts, panel.done_event = 0.0, 0.0, [], None
    panel.stdout_buffer, panel.stderr_text, panel.stopping = b"", "", False
    panel.add_user("an overhand tutorial")
    panel.handle_event({"type": "tool_start", "name": "identify_knot", "input": {}})
    killed = []
    panel.process = SimpleNamespace(state=lambda: QProcess.Running, kill=lambda: killed.append(True),
                                    readAllStandardOutput=lambda: b"", readAllStandardError=lambda: b"",
                                    write=lambda data: None)
    panel.send_or_stop()
    panel.finished()
    panel.process = None
    assert killed
    group = [e for e in panel.entries if e["kind"] == "group"][-1]
    assert group["end"] is not None and not group["open"]  # folded, not left "running"
    assert group["steps"][-1]["stopped"] and not group["steps"][-1]["running"]
    shown = panel.transcript.toPlainText()
    assert shown.count("Stopped.") == 1 and "Claude stopped" not in shown
    assert panel.history[-1]["tools"] and "identify_knot (stopped by the person" in panel.history[-1]["tools"][0]


def test_claude_hears_which_tools_ran_and_how_they_ended():
    from openstrand.agent import with_history
    text = with_history("why so slow?", [{"user": "an overhand tutorial", "claude": "",
                                          "tools": ["tie_knot (stopped by the person, 339 s)"]}])
    assert "Tools you ran" in text and "tie_knot (stopped by the person, 339 s)" in text


def test_the_working_line_draws_the_knot_while_claude_works(window):
    import json as _json
    line = window.claude_panel.working
    info = _json.loads((ROOT / "src" / "claude_knot.json").read_text())
    count = len(info["durations_ms"])
    assert len(line.frames) == count > 1000 and line.sheet is not None
    assert line.loop_from == info["loop_from"] and 0 < line.loop_from < count - 1
    # every frame lies on the sheet: no picture wider than a few thousand pixels (Windows, macOS)
    assert line.sheet.width() <= 4096 and line.sheet.height() <= 4096
    assert all(line.sheet.rect().contains(r) for r in line.frames)
    # twice the size it had (28 px), and frames with the pixels for it on a 2x screen
    assert line.SIZE == 56 and line.height() >= line.SIZE and info["frame"] >= 2 * line.SIZE
    assert line.sheet.depth() == 8  # kept as the file has it, not as a 50 MB pixmap
    line.start("Thinking…")
    assert line.isVisibleTo(window.claude_panel) and line.timer.isActive() and line.frame == 0
    # the tying moves on in the animation's own time, frame after frame
    line.advance(info["durations_ms"][0])
    assert line.frame_at(line.at) == 1
    # after the last frame it goes on from the level the loop comes back to, not from the start
    line.at = line.starts[-1] - 1
    assert line.frame_at(line.at) == count - 1
    line.advance(1)
    assert line.frame_at(line.at) == info["loop_from"] + 1
    line.advance(line.starts[-1] - line.starts[info["loop_from"] + 1])  # once round the loop
    assert line.frame_at(line.at) == info["loop_from"] + 1
    picture = line.grab()
    assert picture.width() > 0
    line.frame = 300
    assert line.frame_picture().size().width() == info["frame"] and line.cut[0] == 300
    line.stop()
    assert not line.timer.isActive() and not line.isVisibleTo(window.claude_panel)


def test_the_working_line_keeps_claudes_tempo(window):
    """How fast the stitch is tied and how often the picture changes are two things, and both
    follow what Claude does: thinking, writing, a tool, a tool that draws, waiting."""
    from claude_panel import KICK, TEMPOS, step_mood
    line = window.claude_panel.working

    def run(mood, seconds, dt=0.005):
        """seconds at work in this mood (settled first): animation ms tied, picture changes."""
        line.start("…")
        line.timer.stop()  # the test is the clock
        line.set_mood(mood)
        line.pace = TEMPOS[mood][0]
        tied, changes, before, at = 0.0, 0, line.frame, line.at
        for _ in range(round(seconds / dt)):
            line.step(dt)
            tied += (line.at - at) % line.starts[-1]
            at = line.at
            changes, before = changes + (line.frame != before), line.frame
        return tied / (1000 * seconds), changes / seconds

    rate = 1000 / line.durations[0]  # the frames come 22 a second at speed 1
    speeds, changes = {}, {}
    for mood in TEMPOS:
        speeds[mood], changes[mood] = run(mood, 6.4)  # two whole swells
        speed, fps, _ = TEMPOS[mood]
        assert abs(speeds[mood] - speed) < 0.06 * speed, mood          # as fast as the mood says
        assert changes[mood] <= fps + 0.5, mood                         # never more pictures than its fps
        assert abs(changes[mood] - min(fps, speed * rate)) < 1.5, mood  # and no fewer than it can show
    assert speeds["waiting"] < speeds["thinking"] < speeds["working"] < speeds["tool"] < speeds["picture"]
    # a tool that draws: the fastest tying in the fewest pictures, so it jumps (stop motion);
    # thinking: slow, and every frame shows
    assert changes["picture"] < changes["thinking"] < changes["working"] < changes["tool"]
    assert speeds["picture"] * rate / changes["picture"] > 5      # frames of the animation a picture
    assert abs(speeds["thinking"] * rate / changes["thinking"] - 1) < 0.1

    # thinking breathes: the speed swells and falls around the mood's
    line.start("…")
    line.timer.stop()
    seen = []
    for _ in range(640):
        line.step(0.005)
        seen.append(line.speed())
    low, high, swell = min(seen), max(seen), TEMPOS["thinking"][2]
    assert abs(low - TEMPOS["thinking"][0] * (1 - swell)) < 0.02
    assert abs(high - TEMPOS["thinking"][0] * (1 + swell)) < 0.02

    # an event pushes it on for a moment, and a new mood glides in
    line.start("…")
    line.timer.stop()
    line.step(0.005)
    calm = line.speed()
    line.nudge()
    assert abs(line.speed() / calm - (1 + KICK)) < 0.01
    for _ in range(600):
        line.step(0.005)
    assert line.kick < 0.01
    line.set_label("Tying…", "tool")
    line.step(0.05)
    assert TEMPOS["thinking"][0] < line.pace < TEMPOS["tool"][0]
    for _ in range(600):
        line.step(0.005)
    assert abs(line.pace - TEMPOS["tool"][0]) < 0.01
    # a held-up app does not make the tying leap: a tick counts a quarter of a second at most
    line.ticked -= 30
    at = line.at
    line.tick()
    assert (line.at - at) % line.starts[-1] <= 250 * line.speed() * 1.01 + 1
    line.stop()

    # the panel sets the mood from the agent's events
    assert step_mood({"name": "tie_knot"}) == "picture" and step_mood({"name": "read_tab"}) == "tool"
    assert step_mood({"name": "edit_mask", "frame": True}) == "picture"  # it sends pictures
    assert step_mood({"name": "tie_knot", "waiting": True}) == "waiting"
    panel = window.claude_panel
    panel.add_user("a bowline")
    line.start("Thinking…")
    line.timer.stop()
    assert line.mood == "thinking"
    panel.handle_event({"type": "tool_start", "name": "read_tab", "input": {}})
    assert line.mood == "tool" and line.kick == 1.0
    panel.handle_event({"type": "tool_end", "name": "read_tab", "ok": True})
    assert line.mood == "working"
    panel.handle_event({"type": "thinking", "text": "a loop, then the rabbit"})
    assert line.mood == "thinking"
    panel.handle_event({"type": "tool_start", "name": "tie_knot", "input": {}})
    assert line.mood == "picture"
    line.kick = 0.0
    panel.handle_event({"type": "tool_progress", "name": "tie_knot", "stage": "relaxing", "fraction": 0.2})
    assert line.mood == "picture" and line.kick == 1.0  # a new stage
    line.kick = 0.0
    panel.handle_event({"type": "tool_progress", "name": "tie_knot", "stage": "relaxing", "fraction": 0.3})
    assert line.kick == 0.0  # the same stage, no picture: no push
    panel.handle_event({"type": "tool_end", "name": "tie_knot", "ok": True})
    panel.handle_event({"type": "text", "text": "Here is your bowline."})
    assert line.mood == "working"
    line.stop()


def test_the_assistant_button_is_the_openstrand_logo(window):
    from PyQt5.QtCore import QPoint, Qt
    from PyQt5.QtGui import QColor, QImage, QPainter
    from claude_panel import ClaudeButton, LOGO_BLUE, LOGO_ORANGE
    button = window.claude_button
    assert not ClaudeButton.pressed_picture().isNull()  # the stretched 1x1 starting stitch

    def picture():
        image = QImage(button.size() * 4, QImage.Format_ARGB32)
        image.setDevicePixelRatio(4)
        image.fill(Qt.white)
        painter = QPainter(image)
        button.render(painter, QPoint())
        painter.end()
        return image

    colors = {picture().pixelColor(x, y).name() for x in range(0, 128, 2) for y in range(0, 128, 2)}
    assert LOGO_ORANGE.name() in colors and LOGO_BLUE.name() in colors
    # working while hidden: the arc's colour drifts from the logo's orange to its blue and back
    button.tint = 0
    assert button.arc_color() == LOGO_ORANGE
    button.tint = ClaudeButton.TINT_TICKS // 2
    assert button.arc_color() == LOGO_BLUE
    button.tint = ClaudeButton.TINT_TICKS - 1
    button.turn()
    assert button.tint == 0 and button.arc_color() == LOGO_ORANGE
    # the arc runs in a ring of its own: clear of the frame (inner edge 15 px out) and of the logo
    assert ClaudeButton.ARC_RADIUS + ClaudeButton.ARC_WIDTH / 2 <= 14.0
    assert ClaudeButton.ARC_RADIUS - ClaudeButton.ARC_WIDTH / 2 >= 11.46 + 1.0
    assert button.spin.timerType() == Qt.PreciseTimer and window.claude_panel.working.timer.timerType() == Qt.PreciseTimer
    assert QColor(LOGO_ORANGE).name() == "#ff5500"


def test_ask_mode_waits_for_open_in_new_tab(window, monkeypatch, tmp_path):
    from PyQt5.QtCore import QUrl
    monkeypatch.setenv("APPDATA", str(tmp_path))
    panel = window.claude_panel
    panel.set_mode("ask")
    opened = []
    panel.design_ready.connect(opened.append)
    design = tmp_path / "design.json"
    design.write_text((ROOT / "knot_samples/links/json/hopf_link.json").read_text(), encoding="utf-8")
    run_events(panel, [{"type": "text", "text": "Two linked rings."},
                       {"type": "done", "ok": True, "error": None, "project": str(design), "cost": 0.01,
                        "model": "claude-sonnet-5-5"}], tmp_path)
    card = panel.entries[-1]
    assert card["kind"] == "design" and not opened
    assert "Design ready: two_linked_rings.json" in panel.transcript.toPlainText()
    panel.follow_link(QUrl(f"os:open/{panel.entries.index(card)}"))
    assert opened and opened[-1].endswith("two_linked_rings.json") and card["opened"]
    panel.set_mode("auto")


def test_plan_mode_ends_with_build_this_plan(window, monkeypatch, tmp_path):
    from PyQt5.QtCore import QUrl
    monkeypatch.setenv("APPDATA", str(tmp_path))
    panel = window.claude_panel
    panel.set_mode("ask")
    panel.set_mode("plan")
    run_events(panel, [{"type": "text", "text": "1. Two circles of 180 px, linked.\n2. Teal and gold."},
                       {"type": "done", "ok": True, "error": None, "project": None, "cost": 0.02,
                        "model": "claude-sonnet-5-5", "plan": True}], tmp_path)
    card = panel.entries[-1]
    assert card["kind"] == "plan" and "Build this plan" in panel.transcript.toPlainText()
    assert "<br>2. Teal and gold." in panel.transcript.toHtml().replace("\n", "") or \
        "2. Teal and gold." in panel.transcript.toPlainText().splitlines()[-2]
    sent = []
    monkeypatch.setattr(panel, "send", lambda prompt=None, shown=None: sent.append((prompt, shown)))
    panel.follow_link(QUrl(f"os:plan/{panel.entries.index(card)}"))
    prompt, shown = sent[-1]
    assert prompt.startswith("two linked rings") and "Two circles of 180 px" in prompt
    assert shown == "Build this plan" and card["built"]
    assert panel.mode == "ask"  # back to the mode used before planning
    panel.set_mode("auto")


def test_the_session_limit_stops_new_requests(window, monkeypatch, tmp_path):
    import claude_settings
    monkeypatch.setenv("APPDATA", str(tmp_path))
    claude_settings.save(api_key="sk-ant-test-key", session_limit=1.0)
    panel = window.claude_panel
    started = []
    monkeypatch.setattr("claude_panel.QProcess.start", lambda self, program, args: started.append(args))
    panel.session_spent = 0.75
    panel.prompt_edit.setText("a heart")
    panel.send()
    args = started[-1]
    assert args[args.index("--max-cost") + 1] == "0.25"  # never past what the session has left
    panel.process = None
    panel.working.stop()
    panel.session_spent = 1.0
    panel.prompt_edit.setText("another heart")
    panel.send()
    assert len(started) == 1
    assert "This session has spent its $1.00 limit" in panel.transcript.toPlainText()
    panel.session_spent = 0.0


def test_the_knot_spinner_is_a_real_closed_overhand_drawn_strand_by_strand():
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_knot_spinner as spinner
    from openstrand import check, draw
    full, report = draw.build(spinner.SPEC)
    assert "3 crossings in all" in report and "conflicts: 0" in report and check.problems(full) == []
    frames = spinner.frames_of(full)
    strands = [s for s in full["strands"] if s["type"] != "MaskedStrand"]
    assert len(frames) == 3 * len(strands)
    last = frames[-1]
    assert [s["layer_name"] for s in last["strands"]] == [s["layer_name"] for s in full["strands"]]
    for frame in frames:
        names = {s["layer_name"] for s in frame["strands"] if s["type"] != "MaskedStrand"}
        for mask in (s for s in frame["strands"] if s["type"] == "MaskedStrand"):
            assert all(part in names for part in spinner.mask_parts(mask["layer_name"], sorted(names)))
        assert [s["index"] for s in frame["strands"]] == list(range(len(frame["strands"])))
    # A crossing shows its finished over and under as soon as both its strands
    # appear: the mask is there while the second strand is still being drawn.
    for frame in frames + spinner.untie_frames(full):
        names = {s["layer_name"] for s in frame["strands"] if s["type"] != "MaskedStrand"}
        masks = {s["layer_name"] for s in frame["strands"] if s["type"] == "MaskedStrand"}
        for mask in (s for s in full["strands"] if s["type"] == "MaskedStrand"):
            parts = spinner.mask_parts(mask["layer_name"], [s["layer_name"] for s in strands])
            assert (mask["layer_name"] in masks) == all(p in names for p in parts)
    # Then it unties from its first end, strand after strand, down to nothing.
    untie = spinner.untie_frames(full)
    assert len(untie) == 3 * len(strands) and untie[-1]["strands"] == []
    for frame in untie[:-1]:
        cords = [s for s in frame["strands"] if s["type"] != "MaskedStrand"]
        assert cords[0]["type"] == "Strand" and "attached_to" not in cords[0]  # the new first strand
        names = {s["layer_name"] for s in cords}
        assert all(s.get("attached_to", names and next(iter(names))) in names for s in cords)
        assert [s["index"] for s in frame["strands"]] == list(range(len(frame["strands"])))
    assert untie[0]["strands"][0]["start"] != strands[0]["start"]  # its first end has moved along
    # A strand being drawn ends where its curve is cut, with no joint at its loose end.
    first = frames[0]["strands"][0]
    assert first["has_circles"][1] is False and first["end"] != strands[0]["end"]


# ------------------------------------------------- steps and the app bridge
@pytest.fixture(scope="module")
def figure8():
    from openstrand import draw
    data, report = draw.build(FIGURE_8)
    assert "4 crossings in all" in report and "conflicts: 0" in report
    return data


def test_steps_follow_the_cord_tail_to_tail(figure8):
    from openstrand import check, steps
    strands = [s for s in figure8["strands"] if s["type"] != "MaskedStrand"]
    path = steps.cord_path(strands)
    assert len(path) == len(strands) and len({s["layer_name"] for s, _ in path}) == len(strands)
    # Neighbours along the path share an end: it is one continuous cord.
    ends = lambda s, forward: ((s["start"], s["end"]) if forward else (s["end"], s["start"]))
    for (a, fa), (b, fb) in zip(path, path[1:]):
        assert ends(a, fa)[1] == ends(b, fb)[0]
    made = steps.make(figure8, count=5)
    assert [t for t, _ in made] == [f"Step {n} of 5" for n in range(1, 6)]
    assert made[-1][1] == figure8  # the whole design, groups and all
    sizes = [sum(s["type"] != "MaskedStrand" for s in d["strands"]) for _, d in made]
    assert sizes == sorted(sizes) and sizes[-1] == len(strands)
    for _, data in made[:-1]:
        assert check.problems(data) == []
        cords = [s for s in data["strands"] if s["type"] != "MaskedStrand"]
        names = {s["layer_name"] for s in cords}
        assert all(s.get("attached_to", next(iter(names))) in names for s in cords)  # nothing hangs off a missing strand
        arrows = [s for s in cords if s.get("end_arrow_visible") or s.get("start_arrow_visible")]
        assert len(arrows) == 1  # one working end
    with pytest.raises(steps.StepsError):
        steps.make(figure8, count=40)


def test_steps_of_two_cords_show_the_first_cord_first():
    """A knot joining two cords (a bend) gets its steps from make_steps: cord 1
    is drawn first, then cord 2, whichever lies lower in the layers."""
    from openstrand import draw, steps
    data, _ = draw.build({"name": "two yarns joined", "cords": [
        {"label": "Old yarn", "color": "teal", "width": 22,
         "points": [[80, 380], [260, 390], [350, 320], [430, 250], [500, 300], [450, 380], [390, 440],
                    [330, 420], [370, 340], [560, 300], [680, 340]]},
        {"label": "New yarn", "color": "gold", "width": 22,
         "points": [[920, 440], [760, 430], [640, 480], [540, 520], [440, 480], [400, 420], [470, 380],
                    [560, 420], [600, 500], [300, 470], [120, 450]]}]})
    strands = [s for s in data["strands"] if s["type"] != "MaskedStrand"]
    assert strands[0]["layer_name"].startswith("2_")  # the second cord is the lower layer here
    sets = [steps.set_of(s) for s, _ in steps.cord_path(strands)]
    assert sets == sorted(sets) and set(sets) == {1, 2}
    made = steps.make(data)
    shown = [{steps.set_of(s) for s in d["strands"] if s["type"] != "MaskedStrand"} for _, d in made]
    assert shown[0] == {1} and shown[-1] == {1, 2}


def test_a_tutorial_is_a_design_not_a_written_answer():
    """Asked for a magic knot tutorial, the agent wrote the steps out and
    offered to draw: the instructions told it to say a bend is not supported."""
    from openstrand.agent import INSTRUCTIONS, TOOLS
    from openstrand.app_tools import APP_INSTRUCTIONS
    assert "say it is not supported" not in INSTRUCTIONS
    assert "Never answer with written steps alone" in INSTRUCTIONS
    assert "never end by offering\n   to draw it" in INSTRUCTIONS
    bend = INSTRUCTIONS[INSTRUCTIONS.index("a knot that joins two cords"):]
    assert "draw_design" in bend[:400] and "make_steps" in bend[:400]
    assert "keep the closest one, make and open its\n  steps all the same" in bend  # no giving up before the steps
    tie = next(t for t in TOOLS if t["name"] == "tie_knot")["description"]
    assert "draw those with draw_design, then make_steps" in tie
    assert "a knot joining two cords" in APP_INSTRUCTIONS and "not a written list" in APP_INSTRUCTIONS


def test_the_app_client_waits_for_its_own_answer():
    import os as _os
    from openstrand.app_tools import AppClient, AppError
    read_end, write_end = _os.pipe()
    writer = _os.fdopen(write_end, "w")
    sent = []

    def emit(event):  # the app answers: a stray line, then the reply
        sent.append(event)
        writer.write(json.dumps({"id": 999, "ok": True}) + "\n")
        if event["name"] == "list_tabs":
            writer.write(json.dumps({"id": event["id"], "ok": True, "result": {"tabs": [{"id": "a"}]}}) + "\n")
        else:
            writer.write(json.dumps({"id": event["id"], "ok": False, "error": "plan mode is on"}) + "\n")
        writer.flush()
    client = AppClient(emit, stream=_os.fdopen(read_end), timeout=5)
    assert client.call("list_tabs", {}) == {"tabs": [{"id": "a"}]}
    assert sent[0] == {"type": "app_call", "id": 1, "name": "list_tabs", "args": {}}
    with pytest.raises(AppError, match="plan mode"):
        client.call("rename_tab", {"tab_id": "a", "title": "x"})
    writer.close()


def test_the_app_client_reads_stdin_only_while_a_call_waits():
    """No read may be left waiting on stdin while a tool runs: on Windows it
    holds the pipe, and loading numpy's DLLs (they check the standard handles)
    then waits for it, so the first knot tool hung for good."""
    import queue as _queue
    import threading as _threading
    import time as _time
    from openstrand.app_tools import AppClient

    class Stdin:
        def __init__(self):
            self.waiting, self.lines = _threading.Event(), _queue.Queue()

        def readline(self):
            self.waiting.set()
            line = self.lines.get()
            self.waiting.clear()
            return line

    stdin = Stdin()
    client = AppClient(lambda event: stdin.lines.put(json.dumps({"id": event["id"], "ok": True}) + "\n"),
                       stream=stdin, timeout=5)
    _time.sleep(0.2)
    assert not stdin.waiting.is_set()  # started: nothing read yet
    assert client.call("list_tabs", {}) == {}
    _time.sleep(0.2)
    assert not stdin.waiting.is_set()  # answered: nothing left waiting while tools run
    assert client.call("list_tabs", {}) == {}
    stdin.lines.put("")  # the app closes the pipe


def test_the_log_says_what_a_request_still_waits_for(tmp_path):
    from openstrand.app_tools import AppClient
    from openstrand.debuglog import Log
    log = Log(tmp_path / "agent.log")
    log("round 1: asking claude-sonnet-5-5")
    with log.waiting("Claude's answer (round 1)", every=0.05):
        time.sleep(0.2)
    read_end, write_end = os.pipe()
    writer = os.fdopen(write_end, "w")

    def emit(event):
        writer.write(json.dumps({"id": event["id"], "ok": True, "result": {}}) + "\n")
        writer.flush()
    AppClient(emit, stream=os.fdopen(read_end), timeout=5, log=log).call("list_tabs", {})
    lines = (tmp_path / "agent.log").read_text(encoding="utf-8").splitlines()
    assert all(line.startswith("log ") for line in lines)
    assert "round 1: asking claude-sonnet-5-5" in lines[0]
    assert any("still waiting for Claude's answer (round 1)" in line for line in lines)
    assert any("asking the app #1: list_tabs" in line for line in lines)
    assert any("the app answered #1 in" in line and line.endswith("ok") for line in lines)


def test_the_panel_prints_the_agent_log_in_the_terminal_and_keeps_errors_apart(window, monkeypatch, tmp_path):
    import io
    from types import SimpleNamespace
    from PyQt5.QtCore import QProcess
    import claude_panel
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert "--log" in claude_panel.agent_command("a heart", "claude-haiku-5-5", str(tmp_path))[1]
    terminal = io.StringIO()
    monkeypatch.setattr(sys, "__stderr__", terminal)
    panel = window.claude_panel
    panel.entries.clear()
    chunks = [b"log 10:00:01 +    0.2s  round 1: asking claude-sonnet-5-5\nlog 10:00:4", b"0 +   39.0s  ... still",
              b" waiting for Claude's answer (round 1): 30s\nerror: the Anthropic API returned 529: overloaded\n"]
    panel.process = SimpleNamespace(state=lambda: QProcess.NotRunning, readAllStandardError=lambda: chunks.pop(0) if chunks else b"",
                                    readAllStandardOutput=lambda: b"")
    panel.stderr_text, panel.stopping, panel.done_event = "", False, None
    panel.out_dir = str(tmp_path)
    for _ in range(3):
        panel.read_errors()
    shown = terminal.getvalue().splitlines()
    assert shown[0].startswith("[Claude] 10:00:01") and "round 1: asking" in shown[0]
    assert "still waiting for Claude's answer (round 1): 30s" in shown[1]  # a line split across reads, whole
    assert shown[2] == "[Claude] error: the Anthropic API returned 529: overloaded"
    panel._finish()
    panel.process = None
    assert "Claude stopped: the Anthropic API returned 529: overloaded" in panel.transcript.toPlainText()


def test_the_agent_offers_app_tools_only_from_the_app(tmp_path):
    from types import SimpleNamespace
    from openstrand import agent
    from openstrand.app_tools import APP_TOOL_NAMES
    names = lambda runner: {t["name"] for t in runner.tools()}
    assert not names(agent.Agent(SimpleNamespace(), tmp_path)) & APP_TOOL_NAMES
    app = SimpleNamespace(call=lambda name, args: {})
    assert APP_TOOL_NAMES <= names(agent.Agent(SimpleNamespace(), tmp_path, app=app))
    looking = names(agent.Agent(SimpleNamespace(), tmp_path, app=app, plan=True))
    assert looking & APP_TOOL_NAMES == {"list_tabs", "read_tab", "read_tab_step", "read_settings"}  # only looks
    assert "running inside the person's OpenStrand Studio" in agent.Agent(
        SimpleNamespace(), tmp_path, app=app).system()[0]["text"]


def test_open_in_new_tab_sends_the_step_file(tmp_path, figure8):
    from types import SimpleNamespace
    from openstrand import agent
    calls = []
    app = SimpleNamespace(call=lambda name, args: calls.append((name, args)) or {"opened": True})
    runner = agent.Agent(SimpleNamespace(), tmp_path, app=app)
    runner.workspace.store(figure8)
    runner.workspace.run("make_steps", {"count": 3})
    summary, _ = runner.app_tool("open_in_new_tab", {"design": "step 2", "title": "Step 2 · loop"})
    assert calls[-1] == ("open_in_new_tab", {"path": str(tmp_path / "step_2.json"), "title": "Step 2 · loop"})
    assert summary == "New tab · Step 2 · loop" and runner.opened_tabs == ["Step 2 · loop"]
    with pytest.raises(agent.ToolError, match="3 steps"):
        runner.app_tool("open_in_new_tab", {"design": "step 9", "title": "x"})


def test_the_bridge_runs_the_real_tab_code(window, monkeypatch, tmp_path, figure8):
    from openstrand import project as _project
    panel, tm = window.claude_panel, window.tab_manager
    bridge = panel.bridge
    monkeypatch.setenv("APPDATA", str(tmp_path))
    run = tmp_path / "run"
    run.mkdir()
    panel.out_dir = str(run)
    step = run / "step_1.json"
    _project.write(figure8, step)
    replies = []
    monkeypatch.setattr(panel, "answer", replies.append)

    panel.run_mode = "auto"
    before = len(tm.tabs)
    reply = bridge.handle({"id": 1, "name": "open_in_new_tab", "args": {"path": str(step), "title": "Step 1 · tail"}})
    assert reply["ok"] and reply["result"]["opened"] and len(tm.tabs) == before + 1
    active = tm.get_active()
    assert tm.title_for(active) == "Step 1 · tail" and len(window.canvas.strands) == len(figure8["strands"])
    listed = bridge.handle({"id": 2, "name": "list_tabs"})["result"]["tabs"]
    entry = next(t for t in listed if t["id"] == active.id)
    assert {k: entry[k] for k in ("id", "title", "active", "strands", "unsaved")} == {
        "id": active.id, "title": "Step 1 · tail", "active": True,
        "strands": len(figure8["strands"]), "unsaved": active.dirty}
    # Its version (changes whenever the person edits it) and where it is in its undo history.
    assert entry["version"] == bridge.version(active) and entry["at_step"] <= entry["undo_steps"]
    read = bridge.handle({"id": 3, "name": "read_tab", "args": {"tab_id": active.id}})["result"]
    assert len(_project.read(read["file"])["strands"]) == len(figure8["strands"])
    # Nothing from outside this request's folder opens.
    outside = tmp_path / "elsewhere.json"
    _project.write(figure8, outside)
    refused = bridge.handle({"id": 4, "name": "open_in_new_tab", "args": {"path": str(outside), "title": "x"}})
    assert not refused["ok"] and "only designs made in this request" in refused["error"]
    assert not bridge.handle({"id": 5, "name": "close_tab", "args": {}})["ok"]

    # Plan mode looks only.
    panel.run_mode = "plan"
    assert "plan mode" in bridge.handle({"id": 6, "name": "rename_tab",
                                         "args": {"tab_id": active.id, "title": "x"}})["error"]
    assert bridge.handle({"id": 7, "name": "list_tabs"})["ok"]

    # Ask mode: a design waits as a card; a rename waits for Allow or Deny.
    panel.run_mode = "ask"
    count = len(tm.tabs)
    card = bridge.handle({"id": 8, "name": "open_in_new_tab", "args": {"path": str(step), "title": "Step 1 · again"}})
    assert card["ok"] and not card["result"]["opened"] and len(tm.tabs) == count
    assert panel.entries[-1]["kind"] == "design" and panel.entries[-1]["title"] == "Step 1 · again"
    assert bridge.handle({"id": 9, "name": "rename_tab", "args": {"tab_id": active.id, "title": "Tail"}}) is None
    confirm = panel.entries[-1]
    assert confirm["kind"] == "confirm" and "rename the tab “Step 1 · tail” to “Tail”" in panel.transcript.toPlainText()
    from PyQt5.QtCore import QUrl
    panel.follow_link(QUrl(f"os:allow/{panel.entries.index(confirm)}"))
    assert replies[-1]["ok"] and tm.title_for(active) == "Tail" and confirm["state"] == "allowed"
    assert bridge.handle({"id": 10, "name": "switch_tab", "args": {"tab_id": tm.tabs[0].id}}) is None
    panel.follow_link(QUrl(f"os:deny/{panel.entries.index(panel.entries[-1])}"))
    assert not replies[-1]["ok"] and "declined" in replies[-1]["error"] and tm.active_tab_id == active.id
    panel.run_mode = "auto"


@pytest.mark.parametrize("fake_api", [FAKE_STEPS], indirect=True)
def test_claude_opens_a_figure_8_step_by_step_in_real_tabs(window, fake_api, monkeypatch, tmp_path):
    import claude_settings
    from PyQt5.QtWidgets import QApplication
    monkeypatch.setenv("APPDATA", str(tmp_path))
    claude_settings.save(api_key="sk-ant-test-key", model="claude-haiku-5-5", web=False)
    panel, tm = window.claude_panel, window.tab_manager
    panel.set_mode("auto")
    before = len(tm.tabs)
    panel.prompt_edit.setText("make a paracord figure 8 knot with open ends, and a tab for each step")
    panel.send()
    deadline = time.time() + 300
    while panel.running() and time.time() < deadline:
        QApplication.processEvents()
        time.sleep(0.05)
    QApplication.processEvents()
    shown = unfolded(panel)
    assert "Five tabs, one per step" in shown, shown
    # The tab tools went to Claude, and five real tabs opened with Claude's titles, in order.
    assert "open_in_new_tab" in {t["name"] for t in fake_api[0]["body"]["tools"]}
    assert [tm.title_for(s) for s in tm.tabs[before:]] == STEP_TITLES
    assert tm.title_for(tm.get_active()) == "Step 5 · the figure 8"
    figure_8_strands = len(window.canvas.strands)
    tm.switch_to_tab(tm.tabs[before].id)
    QApplication.processEvents()
    assert 0 < len(window.canvas.strands) < figure_8_strands  # step 1: the cord so far
    # list_tabs reached Claude with the real tabs, and the finished design did not open again.
    listed = json.loads(fake_api[3]["body"]["messages"][-1]["content"][0]["content"])
    assert len(listed) == before and any(t["active"] for t in listed)
    assert "New tab · Step 3 · up and over" in shown


@pytest.mark.parametrize("fake_api", [FAKE_TIE], indirect=True)
def test_claude_ties_a_figure_eight_into_real_tabs_checked_at_every_step(window, fake_api, monkeypatch, tmp_path):
    import claude_settings
    from PyQt5.QtWidgets import QApplication
    from openstrand import identify
    from save_load_manager import serialize_strand
    monkeypatch.setenv("APPDATA", str(tmp_path))
    claude_settings.save(api_key="sk-ant-test-key", model="claude-haiku-5-5", web=False)
    panel, tm = window.claude_panel, window.tab_manager
    panel.set_mode("auto")
    before = len(tm.tabs)
    panel.prompt_edit.setText("show me how to tie a figure 8 knot, a tab per step, and pull it tight at the end")
    panel.send()
    deadline = time.time() + 300
    while panel.running() and time.time() < deadline:
        QApplication.processEvents()
        time.sleep(0.05)
    QApplication.processEvents()
    shown = unfolded(panel)
    assert "Six tabs" in shown, shown
    # What tie_knot told Claude: every stage checked, also as the app draws it.
    result = fake_api[2]["body"]["messages"][-1]["content"][0]["content"]
    assert "Figure-eight knot: figure-eight, 4 crossings." in result
    assert "pulled tight: figure-eight" in result and "step 6 as drawn in the app: figure-eight" in result
    assert "WARNING" not in result
    # Behind the scenes: the request's log says each round, tool and app answer, and how long each took.
    log = (Path(panel.out_dir) / "agent.log").read_text(encoding="utf-8")
    assert "agent starts:" in log and "numpy loaded in" in log
    assert re.search(r"round 1: answered in [\d.]+s, stop tool_use", log)
    assert re.search(r"tool tie_knot done in [\d.]+s", log) and re.search(r"the app answered #\d+ in", log)
    assert "request ends: answered" in log
    # Six real tabs, in order, with Claude's titles; each holds its step as the app loaded it.
    assert [tm.title_for(t) for t in tm.tabs[before:]] == TIE_TITLES
    knots = []
    for tab in tm.tabs[before:]:
        tm.switch_to_tab(tab.id)
        QApplication.processEvents()
        data = {"strands": [serialize_strand(s, window.canvas) for s in window.canvas.strands],
                "project_settings": {"version": 1, "control_point_base_fraction": 1.0,
                                     "distance_multiplier": 2.0, "curve_response_exponent": 2.0}}
        knots.append(identify.cords(data)[0]["knot"])
    assert knots == ["unknot", "unknot", "unknot", "figure-eight", "figure-eight", "figure-eight"]
    # identify_knot on the current design (the tight knot) went back to Claude too.
    checked = fake_api[9]["body"]["messages"][-1]["content"][0]["content"]
    assert "4 crossings with itself: figure eight knot (4_1)" in checked


def test_the_tab_strip_floats_over_claude_and_claude_stays_put(window, monkeypatch, tmp_path):
    from PyQt5.QtCore import QPoint
    from PyQt5.QtWidgets import QApplication
    monkeypatch.setenv("APPDATA", str(tmp_path))
    panel, edge, canvas = window.claude_panel, window.tab_edge, window.canvas
    if window.tabs_button.isChecked():
        window.tabs_button.click()
    panel.set_open(False)
    panel.set_open(True)
    QApplication.processEvents()
    home = panel.geometry()
    assert home.bottom() == panel.visible_canvas().bottom() - panel.MARGIN

    def on_top():  # later siblings are drawn over earlier ones
        kids = [w for w in canvas.children() if w in (panel, edge)]
        return kids[-1] is edge
    # Showing the strip, dragging it over Claude, opening Claude again:
    # Claude never moves, and the strip is always drawn over it.
    window.tabs_button.click()
    QApplication.processEvents()
    assert edge.isVisible() and on_top() and panel.geometry() == home
    for spot in (home.center(), QPoint(home.left() + 40, home.bottom() - 10), QPoint(80, 80)):
        edge.move(spot - QPoint(edge.width() // 2, edge.height() // 2))
        QApplication.processEvents()
        assert panel.geometry() == home
    panel.set_open(False)
    panel.set_open(True)
    QApplication.processEvents()
    assert on_top() and panel.geometry() == home
    window.tabs_button.click()
    QApplication.processEvents()
    assert panel.geometry() == home


def test_new_session_starts_from_nothing(window, monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    panel = window.claude_panel
    panel.set_mode("auto")
    panel.new_session()
    run_events(panel, [{"type": "text", "text": "A crimson figure 8."},
                       {"type": "usage", "cost": 0.05},
                       {"type": "done", "ok": True, "error": None, "project": None, "cost": 0.05,
                        "model": "claude-haiku-5-5"}], tmp_path, prompt="a figure 8")
    assert panel.history[-1] == {"user": "a figure 8", "claude": "A crimson figure 8.", "design": None}
    assert panel.session_spent > 0 and "＋ New session" == panel.new_button.text()
    panel.new_button.click()
    assert panel.history == [] and panel.session_spent == 0
    assert [e["kind"] for e in panel.entries] == ["note"]
    assert "New session: Claude starts with no earlier messages." in panel.transcript.toPlainText()
    # /clear and /new in the box do the same, as in Claude Code.
    run_events(panel, [{"type": "text", "text": "Hi."}, {"type": "done", "ok": True, "error": None,
                        "project": None, "cost": 0.0, "model": "claude-haiku-5-5"}], tmp_path, prompt="hello")
    for command in ("/clear", "/new"):
        panel.history.append({"user": "x", "claude": "y", "design": None})
        panel.prompt_edit.setText(command)
        panel.send()
        assert panel.history == [] and panel.prompt_edit.text() == ""


@pytest.mark.parametrize("fake_api", [FAKE_TALK], indirect=True)
def test_claude_remembers_the_session_until_a_new_one(window, fake_api, monkeypatch, tmp_path):
    import claude_settings
    from PyQt5.QtWidgets import QApplication
    monkeypatch.setenv("APPDATA", str(tmp_path))
    claude_settings.save(api_key="sk-ant-test-key", model="claude-haiku-5-5", web=False)
    panel = window.claude_panel
    panel.set_mode("auto")
    panel.use_canvas_check.setChecked(False)
    panel.new_session()

    def ask(text):
        panel.prompt_edit.setText(text)
        panel.send()
        assert not panel.new_button.isEnabled()  # not while Claude works
        deadline = time.time() + 120
        while panel.running() and time.time() < deadline:
            QApplication.processEvents()
            time.sleep(0.05)
        QApplication.processEvents()
        return fake_api[-1]["body"]["messages"][0]["content"][-1]["text"]
    first = ask("make a paracord figure 8 knot with open ends")
    assert first == "make a paracord figure 8 knot with open ends"  # nothing earlier yet
    second = ask("now add a tab for each step")
    assert second.startswith("Earlier in this conversation")
    assert "make a paracord figure 8 knot with open ends" in second and "A crimson figure 8 with open ends." in second
    assert second.endswith("Now the person asks:\nnow add a tab for each step")
    panel.new_button.click()
    third = ask("a heart")
    assert third == "a heart"  # a new session: from nothing
    panel.use_canvas_check.setChecked(True)


# ------------------------------------------------- Claude waits for an Allow or Deny
def test_a_card_that_comes_while_its_tool_runs_does_not_break_the_tool_s_row(window, monkeypatch, tmp_path):
    """In ask mode a card (a design to open, an Allow/Deny) comes while its tool runs. The tool's
    end looked for its row only in the last group, which the card had closed off: it made a row
    with no picture name and raised KeyError: 'key', and the events after it were lost."""
    monkeypatch.setenv("APPDATA", str(tmp_path))
    panel = window.claude_panel
    panel.set_open(True)
    panel.entries.clear()
    panel.out_dir = str(tmp_path)
    panel.add_user("only up to the _4 strands")
    try:
        cards = {"open_in_new_tab": lambda: panel.add_design_card(str(tmp_path / "ring.json"), "Ring"),
                 "app_window": lambda: panel.add_confirm_card(5, ("window", "Ring", "delete 1_5, 2_5, 3_5"))}
        for name, card in cards.items():
            panel.handle_event({"type": "tool_start", "name": name, "input": {}})
            step = panel.running_step(name)
            card()
            panel.handle_event({"type": "tool_end", "name": name, "ok": True, "summary": "done"})
            assert not step["running"] and step["ok"] and step["summary"] == "done" and "waiting" not in step
            assert step["picture"]  # the canvas as the tool left it
            assert panel.running_step() is None
        rows = [s["name"] for e in panel.entries if e["kind"] == "group" for s in e["steps"]]
        assert rows == ["open_in_new_tab", "app_window"]  # no second row without a picture name
    finally:
        panel.entries.clear()
        panel.render_transcript()


def test_an_event_the_panel_cannot_show_does_not_lose_the_lines_after_it(window, monkeypatch, caplog):
    """An error in one event stopped the read: the lines after it were lost, an app_call among
    them, and Claude waited ten minutes for an answer that never came."""
    from types import SimpleNamespace
    from PyQt5.QtCore import QProcess
    panel = window.claude_panel
    real, answered = panel.handle_event, []

    def handle(event):
        if event.get("text") == "cannot show this":
            raise KeyError("key")
        real(event)
    monkeypatch.setattr(panel, "handle_event", handle)
    monkeypatch.setattr(panel, "answer", answered.append)
    lines = [{"type": "note", "text": "cannot show this"}, {"type": "app_call", "id": 9, "name": "list_tabs", "args": {}}]
    out = b"".join(json.dumps(e).encode() + b"\n" for e in lines)
    panel.stdout_buffer = b""
    panel.process = SimpleNamespace(state=lambda: QProcess.Running, readAllStandardOutput=lambda: out)
    try:
        panel.read_events()
    finally:
        panel.process = None
    assert [(r["id"], r["ok"]) for r in answered] == [(9, True)]
    assert "could not show a note event" in caplog.text and "KeyError" in caplog.text


def test_an_allow_card_stays_in_view_at_the_end_of_a_long_conversation(window, monkeypatch, tmp_path):
    """Qt lays a long conversation out a little at a time, so the scroll bar's range grew after
    the panel had scrolled to the end: the view stopped short, and the Allow/Deny card at the end
    went unseen while Claude waited for it. Scrolled up by the person, the view stays put."""
    from PyQt5.QtGui import QTextDocument
    from PyQt5.QtWidgets import QApplication
    monkeypatch.setenv("APPDATA", str(tmp_path))
    panel = window.claude_panel
    panel.set_open(True)
    panel.entries.clear()
    panel.out_dir = str(tmp_path)
    transcript, bar = panel.transcript, panel.transcript.verticalScrollBar()

    def settle():
        end = time.monotonic() + 0.3
        while time.monotonic() < end:
            QApplication.processEvents()
            time.sleep(0.01)
    try:
        for r in range(20):
            panel.add_user(f"request {r}: a hexagon stitch, a box stitch with one more strand")
            for _ in range(14):
                panel.handle_event({"type": "tool_start", "name": "draw_design", "input": {}})
                panel.handle_event({"type": "tool_end", "name": "draw_design", "ok": True,
                                    "summary": "cord 1 (Ribbon 1): 7 strands, 17 crossings, open"})
            panel.add_claude("the three ribbons cross at 60 degrees " * 8)
        settle()
        panel.add_user("only up to the _4 strands")
        panel.handle_event({"type": "tool_start", "name": "app_window", "input": {"op": "delete"}})
        panel.add_confirm_card(3, ("window", "Ring", "delete 1_5, 2_5, 3_5"))
        settle()
        assert bar.value() == bar.maximum() > 0
        doc = transcript.document()
        allow = doc.find("Allow", doc.characterCount(), QTextDocument.FindBackward | QTextDocument.FindCaseSensitively)
        shown = transcript.cursorRect(allow)
        assert 0 <= shown.top() and shown.bottom() <= transcript.viewport().height()
        # The person scrolls up to read: new lines leave the view where they put it...
        bar.setValue(bar.maximum() // 2)
        place = bar.value()
        panel.handle_event({"type": "thinking", "text": "the _5 strands are the start lines"})
        settle()
        assert bar.value() == place
        # ...until they send a request.
        panel.add_user("thanks")
        settle()
        assert bar.value() == bar.maximum()
    finally:
        panel.entries.clear()
        panel.render_transcript()


def test_while_a_card_waits_the_panel_and_the_terminal_say_claude_waits_for_the_person(window, monkeypatch,
                                                                                         tmp_path):
    """Claude's tool waits for the person's Allow or Deny. Its row showed a moving bar and a clock,
    as if Claude were busy, and the terminal only said the agent waited for the app."""
    import io
    from PyQt5.QtCore import QUrl
    monkeypatch.setenv("APPDATA", str(tmp_path))
    terminal = io.StringIO()
    monkeypatch.setattr(sys, "__stderr__", terminal)
    panel = window.claude_panel
    panel.set_open(True)
    panel.entries.clear()
    panel.out_dir = str(tmp_path)
    decided = []
    monkeypatch.setattr(panel.bridge, "decide", lambda call_id, allowed: decided.append((call_id, allowed)))
    try:
        panel.add_user("only up to the _4 strands")
        panel.handle_event({"type": "tool_start", "name": "app_window", "input": {"op": "delete"}})
        step = panel.running_step("app_window")
        step["start"] -= 10  # it has waited a while: a busy tool shows its bar and time by now
        panel.add_confirm_card(3, ("window", "Ring", "delete 1_5, 2_5, 3_5"))
        panel.refresh_running()
        shown = panel.transcript.toPlainText()
        assert "App · Waiting for you: Allow or Deny" in shown
        assert "Claude wants to delete 1_5, 2_5, 3_5 (tab “Ring”)." in shown
        assert "claude-bar:" not in panel.transcript.toHtml()  # no bar, no clock: nothing is moving
        assert panel.working.label == "Waiting for you: Allow or Deny"
        assert ("[Claude] waiting for the person to click Allow or Deny in the panel: "
                "Claude wants to delete 1_5, 2_5, 3_5 (tab “Ring”).") in terminal.getvalue()
        card = panel.entries[-1]
        panel.follow_link(QUrl(f"os:allow/{panel.entries.index(card)}"))
        assert decided == [(3, True)] and card["state"] == "allowed"
        assert "waiting" not in step and panel.working.label == "App…"  # the tool runs on
        assert "[Claude] allowed by the person: Claude wants to delete 1_5" in terminal.getvalue()
        # Other languages say it with the card's own words.
        panel.retranslate("fr")
        assert panel.waiting_text() == "En attente de votre choix : Autoriser ou Refuser"
    finally:
        panel.retranslate("en")
        panel.entries.clear()
        panel.render_transcript()


def test_a_card_no_one_answered_does_nothing_once_claude_stops_waiting_for_it(window, monkeypatch, tmp_path):
    """The agent waits ten minutes for the app's answer, then its tool fails. The card it waited
    for then does nothing: a late Allow would make a change Claude no longer knows of."""
    from PyQt5.QtCore import QUrl
    monkeypatch.setenv("APPDATA", str(tmp_path))
    panel = window.claude_panel
    panel.set_open(True)
    panel.entries.clear()
    panel.out_dir = str(tmp_path)
    try:
        panel.add_user("only up to the _4 strands")
        panel.handle_event({"type": "tool_start", "name": "app_window", "input": {"op": "delete"}})
        panel.bridge.pending[11] = {"id": 11, "name": "window", "args": {"op": "delete"}}
        panel.add_confirm_card(11, ("window", "Ring", "delete 1_5, 2_5, 3_5"))
        card = panel.entries[-1]
        panel.handle_event({"type": "tool_end", "name": "app_window", "ok": False,
                            "summary": "the app did not answer window in time"})
        assert card["state"] == "expired" and 11 not in panel.bridge.pending
        assert "Allow" not in panel.transcript.toPlainText().split("(tab “Ring”).")[-1]
        decided = []
        monkeypatch.setattr(panel.bridge, "decide", lambda *args: decided.append(args))
        panel.follow_link(QUrl(f"os:allow/{panel.entries.index(card)}"))
        assert decided == []
    finally:
        panel.bridge.pending.pop(11, None)
        panel.entries.clear()
        panel.render_transcript()
