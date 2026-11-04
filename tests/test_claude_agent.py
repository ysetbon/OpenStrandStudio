"""The Claude agent harness, its settings, and the app's Claude panel.

Claude itself is replaced by a scripted client: the tests check what the
harness sends, how it runs the tools, and that a finished design loads into
the real main window (canvas, layer panel, groups) through the Load path.
"""
import json
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

    assert result["ok"] and result["error"] is None
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


def test_sonnet_requests_use_fallback_cached_guide_and_medium_effort(tmp_path):
    client = ScriptedClient(bracelet_script())
    agent.Agent(client, tmp_path, model="claude-sonnet-5-5").run("bracelet")
    kind, params = client.calls[0]
    assert kind == "beta" and params["fallbacks"] == "default"
    assert params["betas"] == [agent.FALLBACK_BETA]
    assert params["model"] == "claude-sonnet-5-5"
    assert params["output_config"] == {"effort": "medium"}
    assert params["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert "Turk's heads" in params["system"][0]["text"]  # the guide is in the prompt
    assert "temperature" not in params and "tool_choice" not in params


def test_haiku_requests_have_no_fallback(tmp_path):
    client = ScriptedClient(bracelet_script())
    agent.Agent(client, tmp_path, model="claude-haiku-5-5").run("bracelet")
    kind, params = client.calls[0]
    assert kind == "messages" and "fallbacks" not in params and params["model"] == "claude-haiku-5-5"


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


# -------------------------------------------------------------- settings
def test_settings_keep_the_key_private_and_the_model_known(tmp_path, monkeypatch):
    import claude_settings
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert claude_settings.load() == {"api_key": "", "model": "claude-sonnet-5-5"}
    claude_settings.save(api_key="  sk-ant-test-1234567890  ", model="claude-haiku-5-5")
    assert claude_settings.load() == {"api_key": "sk-ant-test-1234567890", "model": "claude-haiku-5-5"}
    if os.name == "posix":
        assert stat.S_IMODE(os.stat(claude_settings.settings_path()).st_mode) == 0o600
    with pytest.raises(ValueError):
        claude_settings.save(model="claude-opus-1")
    claude_settings.save(api_key="")
    assert "api_key" not in json.loads(Path(claude_settings.settings_path()).read_text())
    assert claude_settings.masked("sk-ant-test-1234567890") == "sk-ant-…7890"


def test_cli_agent_without_a_key_says_where_to_add_it(tmp_path):
    env = dict(os.environ, APPDATA=str(tmp_path))
    env.pop("ANTHROPIC_API_KEY", None)
    result = subprocess.run([sys.executable, "-m", "openstrand", "agent", "a heart"], cwd=ROOT, env=env,
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 1 and "Settings > Claude" in result.stderr


# ------------------------------------------------------------------ app
@pytest.fixture(scope="module")
def window():
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
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


def test_the_panel_turns_events_into_a_transcript_and_opens_the_result(window, tmp_path, monkeypatch):
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
    shown = panel.transcript.toPlainText()
    assert "Two linked rings." in shown and "hopf_link" in shown
    assert "Sonnet 5.5" in panel.status_label.text()


def test_the_panel_asks_for_a_key_before_sending(window, monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    panel = window.claude_panel
    panel.prompt_edit.setText("a heart")
    panel.send()
    assert panel.process is None or not panel.running()
    assert "Settings > Claude" in panel.transcript.toPlainText()


def test_the_settings_page_saves_key_and_model(monkeypatch, tmp_path):
    from PyQt5.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    import claude_settings
    from claude_panel import ClaudeSettingsPage
    monkeypatch.setenv("APPDATA", str(tmp_path))
    page = ClaudeSettingsPage("en")
    page.key_edit.setText("sk-ant-api03-abcdefghijkl")
    page.save_key()
    assert claude_settings.load()["api_key"] == "sk-ant-api03-abcdefghijkl"
    assert "ijkl" in page.key_status.text() and page.key_edit.text() == ""
    page.model_combo.setCurrentIndex(page.model_combo.findData("claude-haiku-5-5"))
    assert claude_settings.load()["model"] == "claude-haiku-5-5"
    page.remove_key()
    assert claude_settings.load()["api_key"] == ""
    page.retranslate("he")
    assert page.model_combo.count() == 2


# ------------------------------------------------------- end to end, no key
FAKE_REPLIES = [
    {"content": [{"type": "thinking", "thinking": "", "signature": "sig-1"},
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


@pytest.fixture
def fake_api(monkeypatch):
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
            reply = FAKE_REPLIES[min(len(requests) - 1, len(FAKE_REPLIES) - 1)]
            out = json.dumps({"id": f"msg_{len(requests)}", "type": "message", "role": "assistant",
                              "model": body["model"], "stop_sequence": None,
                              "usage": {"input_tokens": 1200, "output_tokens": 300,
                                        "cache_creation_input_tokens": 0, "cache_read_input_tokens": 900},
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
    monkeypatch.setenv("ANTHROPIC_BASE_URL", f"http://127.0.0.1:{server.server_port}")
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
    shown = panel.transcript.toPlainText()
    assert "teal vertical ribbons" in shown and "Sonnet 5.5" in panel.status_label.text()
