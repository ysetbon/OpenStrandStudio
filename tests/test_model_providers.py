"""The models of every provider: the requests each client sends (endpoint, key,
payload) and how their answers come back to the agent, against a local stand-in
for the providers' APIs (a real HTTP server on this computer, no network)."""
import dataclasses
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT, ROOT / "src", ROOT / "scripts"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from openstrand import agent, providers  # noqa: E402


@pytest.fixture(autouse=True)
def nothing_forbidden(monkeypatch):
    """These tests are about the clients themselves. What Settings > Models forbids
    (providers.POLICY, set once claude_settings is imported) has tests of its own."""
    monkeypatch.setattr(providers, "POLICY", None)


@pytest.fixture
def server(monkeypatch):
    """A local API: answers queued in .answers ((status, body)), requests kept in .seen."""
    seen, answers = [], []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            seen.append({"path": self.path, "headers": {k.lower(): v for k, v in self.headers.items()},
                         "body": body})
            status, reply = answers.pop(0)
            out = json.dumps(reply).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

        def do_GET(self):  # a model list
            seen.append({"path": self.path, "headers": {k.lower(): v for k, v in self.headers.items()}, "body": None})
            status, reply = answers.pop(0)
            out = json.dumps(reply).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, *args):
            pass
    http = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=http.serve_forever, daemon=True).start()
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    yield type("Server", (), {"url": f"http://127.0.0.1:{http.server_port}", "seen": seen, "answers": answers})
    http.shutdown()


def local(provider, server, path=""):
    """The provider, its API on the local server."""
    return dataclasses.replace(providers.PROVIDERS[provider], base_url=server.url + path)


def test_every_model_has_a_provider_a_price_and_an_alias_that_resolves():
    assert providers.resolve("sonnet") == "claude-sonnet-5-5" and providers.resolve("grok") == "grok-4.7"
    assert providers.resolve("kimi") == "kimi-k3.1-pro" and providers.resolve("deepseek") == "deepseek-flash"
    assert providers.resolve("qwen") == "qwen3.8-max" and providers.resolve("gpt") == "gpt-6.1-terra"
    for model in providers.MODELS.values():
        assert model.provider in providers.PROVIDERS and len(model.prices) == 4 and model.id in agent.PRICES
    with pytest.raises(ValueError, match="unknown model"):
        providers.resolve("gpt-9")
    endpoints = {p.key: (p.api, p.base_url, p.env) for p in providers.PROVIDERS.values()}
    assert endpoints["openai"] == ("responses", "https://api.openai.com/v1", "OPENAI_API_KEY")
    assert endpoints["xai"] == ("responses", "https://api.x.ai/v1", "XAI_API_KEY")
    assert endpoints["moonshot"] == ("anthropic-compatible", "https://api.moonshot.ai/anthropic", "MOONSHOT_API_KEY")
    assert endpoints["deepseek"] == ("anthropic-compatible", "https://api.deepseek.com/anthropic", "DEEPSEEK_API_KEY")
    assert endpoints["qwen"] == ("anthropic-compatible", "https://dashscope-intl.aliyuncs.com/apps/anthropic",
                                 "DASHSCOPE_API_KEY")


def test_the_key_comes_from_the_environment_then_the_settings(monkeypatch):
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="set XAI_API_KEY, or add it in OpenStrand Studio under Settings > Models"):
        providers.api_key("xai", {})
    assert providers.api_key("xai", {"xai": "xai-saved"}) == "xai-saved"
    monkeypatch.setenv("XAI_API_KEY", "xai-env")
    assert providers.api_key("xai", {"xai": "xai-saved"}) == "xai-env"


# ------------------------------------------------------------ Responses API
def test_grok_runs_the_agent_loop_on_the_responses_api(tmp_path, server):
    server.answers[:] = [
        (200, {"id": "resp_1", "status": "completed", "model": "grok-4.7", "output": [
            {"type": "reasoning", "id": "rs_1", "summary": [{"type": "summary_text", "text": "Look at the knots."}],
             "encrypted_content": "gAAAA-secret"},
            {"type": "function_call", "id": "fc_1", "call_id": "call_1", "name": "knot_library", "arguments": "{}"}],
            "usage": {"input_tokens": 1200, "output_tokens": 80, "input_tokens_details": {"cached_tokens": 200}}}),
        (200, {"id": "resp_2", "status": "completed", "model": "grok-4.7", "output": [
            {"type": "message", "id": "msg_2", "role": "assistant", "status": "completed",
             "content": [{"type": "output_text", "text": "I know five knots.", "annotations": []}]}],
            "usage": {"input_tokens": 1500, "output_tokens": 20, "input_tokens_details": {"cached_tokens": 1000}}}),
    ]
    client = providers.ResponsesClient(local("xai", server, "/v1"), "xai-test")
    seen = server.seen
    events = []
    runner = agent.Agent(client, tmp_path, model="grok-4.7", on_event=events.append, effort="max")
    done = runner.run("which knots can you tie?")
    assert done["ok"] and done["text"] == "I know five knots." and len(seen) == 2
    first, second = seen[0], seen[1]
    assert first["path"] == "/v1/responses" and first["headers"]["authorization"] == "Bearer xai-test"
    body = first["body"]
    assert body["model"] == "grok-4.7" and body["store"] is False and body["include"] == ["reasoning.encrypted_content"]
    assert body["reasoning"]["effort"] == "xhigh" and "OpenStrand Studio" in body["instructions"]
    assert body["input"] == [{"role": "user", "content": [{"type": "input_text", "text": "which knots can you tie?"}]}]
    names = {t["name"] for t in body["tools"]}
    assert "knot_library" in names and "web_search" not in names  # Anthropic's server tools: Claude only
    assert all(t["type"] == "function" and "parameters" in t for t in body["tools"])
    # The second request: the reasoning and the call sent back as they came, then the tool's output.
    items = second["body"]["input"]
    assert items[1]["type"] == "reasoning" and items[1]["encrypted_content"] == "gAAAA-secret"
    assert items[2] == {"type": "function_call", "id": "fc_1", "call_id": "call_1", "name": "knot_library",
                        "arguments": "{}"}
    assert items[3]["type"] == "function_call_output" and items[3]["call_id"] == "call_1"
    assert "Overhand" in items[3]["output"]
    assert any(e["type"] == "thinking" and e["text"] == "Look at the knots." for e in events)
    # Cost at Grok's prices: input less what was cached, cached, output.
    expected = ((1000 + 500) * 2.00 + (200 + 1000) * 0.50 + (80 + 20) * 6.00) / 1_000_000
    assert abs(done["cost"] - round(expected, 4)) < 1e-6 and done["model"] == "grok-4.7"


def test_gpt_sends_tool_pictures_as_the_next_message_and_retries_an_effort_it_lacks(server):
    messages = [{"role": "user", "content": "make a heart"},
                {"role": "assistant", "content": [{"type": "text", "text": "Rendering."},
                                                  {"type": "tool_use", "id": "call_9", "name": "render", "input": {}}]},
                {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "call_9", "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "iVBOR"}},
                    {"type": "text", "text": "rendered"}]}]}]
    items = providers.responses_input(messages)
    assert items[1] == {"role": "assistant", "content": "Rendering."}
    assert items[2]["type"] == "function_call" and items[2]["call_id"] == "call_9"
    assert items[3]["type"] == "function_call_output" and "rendered" in items[3]["output"]
    assert items[4]["role"] == "user" and items[4]["content"][1] == {
        "type": "input_image", "image_url": "data:image/png;base64,iVBOR"}
    # An effort the model does not take: asked again at high.
    seen = server.seen
    server.answers[:] = [(400, {"error": {"message": "Unsupported value: 'xhigh' for reasoning effort"}}),
                         (200, {"status": "completed", "output": [{"type": "message", "content": [
                             {"type": "output_text", "text": "ok"}]}], "usage": {"input_tokens": 10,
                                                                                  "output_tokens": 2}})]
    client = providers.ResponsesClient(local("openai", server, "/v1"), "sk-test")
    message = client.messages.create(model="gpt-6.1-terra", max_tokens=1000, system=[{"type": "text", "text": "hi"}],
                                     tools=[], messages=[{"role": "user", "content": "hi"}],
                                     output_config={"effort": "xhigh"})
    assert [s["body"]["reasoning"]["effort"] for s in seen] == ["xhigh", "high"]
    assert seen[0]["path"] == "/v1/responses" and message.stop_reason == "end_turn"
    # A refused key: the provider's own message, with its status.
    server.answers[:] = [(401, {"error": {"message": "Incorrect API key provided"}})]
    client = providers.ResponsesClient(local("openai", server, "/v1"), "sk-bad")
    with pytest.raises(providers.ProviderError, match="401: Incorrect API key"):
        client.messages.create(model="gpt-6.1-terra", messages=[{"role": "user", "content": "hi"}])


# ------------------------------------------------ Anthropic-compatible APIs
@pytest.mark.parametrize("model, path", [
    ("kimi-k3.1-pro", "/anthropic"), ("deepseek-flash", "/anthropic"), ("qwen3.8-max", "/apps/anthropic")])
def test_kimi_deepseek_and_qwen_use_their_anthropic_compatible_endpoints(model, path, server, tmp_path):
    anthropic = pytest.importorskip("anthropic")
    real = providers.client_for(model, "sk-test-key")  # the provider's own endpoint
    assert str(real._client.base_url).rstrip("/") == providers.provider_of(model).base_url
    server.answers[:] = [(200, {"id": "msg_1", "type": "message", "role": "assistant", "model": model,
                                "stop_reason": "end_turn", "stop_sequence": None,
                                "content": [{"type": "text", "text": "done"}],
                                "usage": {"input_tokens": 10, "output_tokens": 3}})]
    client = providers.CompatClient(providers.compatible_sdk(anthropic, "sk-test-key", server.url + path))
    runner = agent.Agent(client, tmp_path, model=model)
    params = dict(model=model, max_tokens=20000, system=runner.system(), tools=runner.tools(),
                  messages=[{"role": "user", "content": "hi"}], thinking={"type": "adaptive", "display": "summarized"},
                  output_config={"effort": "medium"})
    answer = client.messages.create(**params)
    assert answer.content[0].text == "done" and len(server.seen) == 1
    sent = server.seen[0]
    assert sent["path"] == path + "/v1/messages"
    assert sent["headers"]["x-api-key"] == "sk-test-key" and sent["headers"]["authorization"] == "Bearer sk-test-key"
    body = sent["body"]
    assert body["model"] == model and "output_config" not in body
    assert body["thinking"] == {"type": "enabled", "budget_tokens": 8000}
    assert body["tools"] and all("input_schema" in t for t in body["tools"])  # no Anthropic server tools
    assert runner.web is False


def test_claude_still_uses_anthropic_itself():
    anthropic = pytest.importorskip("anthropic")
    client = providers.client_for("claude-sonnet-5-5", "sk-ant-test")
    assert type(client) is anthropic.Anthropic and "api.anthropic.com" in str(client.base_url)
    assert isinstance(providers.client_for("gpt-6-astra", "sk"), providers.ResponsesClient)
    assert isinstance(providers.client_for("kimi", "sk"), providers.CompatClient)


# ------------------------------------------------------------ safe requests
MESSAGE = {"id": "msg_1", "type": "message", "role": "assistant", "model": "m", "stop_reason": "end_turn",
           "stop_sequence": None, "content": [{"type": "text", "text": "done"}],
           "usage": {"input_tokens": 1, "output_tokens": 1}}


@pytest.fixture
def start(monkeypatch):
    """start(answer=..., redirect_to=...): a local server that keeps every request it gets (its
    headers as sent, repeats included); it answers with a JSON body, or redirects elsewhere."""
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    servers = []

    def start_server(answer=None, redirect_to=None):
        seen = []

        class Handler(BaseHTTPRequestHandler):
            def reply(self):
                length = int(self.headers.get("Content-Length") or 0)
                if length:
                    self.rfile.read(length)
                seen.append({"path": self.path, "headers": [(k.lower(), v) for k, v in self.headers.items()]})
                out = json.dumps(answer or {}).encode()
                if redirect_to:  # 302: what a client following it would send on, key and all
                    self.send_response(302)
                    self.send_header("Location", redirect_to + self.path)
                else:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(out)))
                self.end_headers()
                self.wfile.write(out)

            do_GET = do_POST = reply

            def log_message(self, *args):
                pass
        http = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=http.serve_forever, daemon=True).start()
        servers.append(http)
        return f"http://127.0.0.1:{http.server_port}", http.server_port, seen
    yield start_server
    for http in servers:
        http.shutdown()


def credentials(request):
    return [(k, v) for k, v in request["headers"] if k in ("authorization", "x-api-key")]


def test_every_endpoint_is_https_and_lists_its_models_on_its_own_api_host():
    for p in providers.PROVIDERS.values():
        assert p.base_url.startswith("https://") and p.models_url.startswith("https://"), p.key
        assert providers.host_of(p.models_url) == providers.host_of(p.base_url), p.key
    context = providers.tls_context()
    import ssl
    assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
    assert context.minimum_version >= ssl.TLSVersion.TLSv1_2


def test_a_key_goes_over_https_to_its_own_host_only():
    providers.check_url("https://api.x.ai/v1/responses", "api.x.ai")
    providers.check_url("http://127.0.0.1:8123/v1", "127.0.0.1")  # this computer itself: the tests
    for url in ("http://api.x.ai/v1/responses", "https://api.x.ai.evil.example/v1", "https://evil.example/v1",
                "ftp://api.x.ai/v1"):
        with pytest.raises(providers.UnsafeRequest):
            providers.check_url(url, "api.x.ai")
    # Refused before anything is sent: no connection is even tried.
    plain = dataclasses.replace(providers.PROVIDERS["xai"], base_url="http://api.x.ai/v1")
    with pytest.raises(providers.UnsafeRequest, match="https://api.x.ai only"):
        providers.ResponsesClient(plain, "xai-secret").messages.create(
            model="grok-4.7", messages=[{"role": "user", "content": "hi"}])
    anthropic = pytest.importorskip("anthropic")
    client = providers.sdk_client(anthropic, "http://api.anthropic.com", "sk-ant-secret").with_options(max_retries=0)
    with pytest.raises(anthropic.APIConnectionError) as refused:
        client.messages.create(model="claude-sonnet-5-5", max_tokens=10, messages=[{"role": "user", "content": "hi"}])
    assert isinstance(refused.value.__cause__, providers.UnsafeRequest)


def test_a_redirect_never_carries_a_key_to_another_host(start, monkeypatch):
    elsewhere, port, taken = start()
    front, _, asked = start(redirect_to=f"http://localhost:{port}")  # another host name, as a redirect would be
    # The SDK (Claude, and Kimi, DeepSeek and Qwen's endpoints): the 302 is the answer, not followed.
    anthropic = pytest.importorskip("anthropic")
    client = providers.compatible_sdk(anthropic, "sk-secret", front + "/anthropic").with_options(max_retries=0)
    with pytest.raises(anthropic.APIStatusError) as answer:
        client.messages.create(model="kimi-k3.1-pro", max_tokens=10, messages=[{"role": "user", "content": "hi"}])
    assert answer.value.status_code == 302
    # The Responses API (GPT, Grok): a 302 would be followed as a GET, its Authorization header with it.
    responses = providers.ResponsesClient(dataclasses.replace(providers.PROVIDERS["openai"], base_url=front + "/v1"),
                                          "sk-secret")
    with pytest.raises(providers.ProviderError, match="returned 302"):
        responses.messages.create(model="gpt-6.1-terra", messages=[{"role": "user", "content": "hi"}])
    # Refresh models.
    monkeypatch.setitem(providers.PROVIDERS, "deepseek",
                        dataclasses.replace(providers.PROVIDERS["deepseek"], models_url=front + "/models"))
    with pytest.raises(providers.ProviderError, match="returned 302"):
        providers.list_models("deepseek", "sk-secret")
    assert len(asked) == 3 and taken == []  # the key reached the provider's own host only


def test_environment_variables_neither_move_a_client_nor_add_a_credential(start, monkeypatch):
    anthropic = pytest.importorskip("anthropic")
    # Set for Claude Code by people who use DeepSeek's or Kimi's endpoint with it.
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://api.deepseek.com/anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-from-env")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "sk-other-from-env")
    monkeypatch.setenv("ANTHROPIC_CUSTOM_HEADERS",
                       "X-Api-Key: sk-ant-from-env\nAuthorization: Bearer sk-other-from-env\nX-Note: kept")
    claude = providers.client_for("claude-sonnet-5-5", "sk-ant-mine")
    assert str(claude.base_url).rstrip("/") == "https://api.anthropic.com"
    assert str(providers.client_for("deepseek", "sk-ds")._client.base_url).rstrip("/") == \
        "https://api.deepseek.com/anthropic"
    url, _, seen = start(answer=MESSAGE)
    for client, key in ((providers.sdk_client(anthropic, url, "sk-ant-mine"), "sk-ant-mine"),
                        (providers.compatible_sdk(anthropic, "sk-kimi-mine", url + "/anthropic"), "sk-kimi-mine")):
        client.messages.create(model="m", max_tokens=10, messages=[{"role": "user", "content": "hi"}])
        sent = credentials(seen[-1])
        assert sent and all(value in (key, f"Bearer {key}") for _, value in sent), sent
        assert len({name for name, _ in sent}) == len(sent)  # one value each, no repeats
        assert ("x-note", "kept") in seen[-1]["headers"]  # what is not a credential stays


def test_what_the_settings_forbid_is_never_sent(start, monkeypatch):
    anthropic = pytest.importorskip("anthropic")
    url, _, seen = start(answer=MESSAGE)
    forbidden = {"deepseek", "xai", None}  # None: a share with the developer
    monkeypatch.setattr(providers, "POLICY", lambda p: "turned off in Settings > Models" if p in forbidden else None)
    with pytest.raises(anthropic.APIConnectionError) as refused:
        providers.compatible_sdk(anthropic, "sk-ds", url + "/anthropic", provider="deepseek").with_options(
            max_retries=0).messages.create(model="m", max_tokens=10, messages=[{"role": "user", "content": "hi"}])
    assert isinstance(refused.value.__cause__, providers.NotAllowed)
    grok = providers.ResponsesClient(dataclasses.replace(providers.PROVIDERS["xai"], base_url=url + "/v1"), "xai-k")
    with pytest.raises(providers.NotAllowed, match="turned off"):
        grok.messages.create(model="grok-4.7", messages=[{"role": "user", "content": "hi"}])
    monkeypatch.setitem(providers.PROVIDERS, "deepseek",
                        dataclasses.replace(providers.PROVIDERS["deepseek"], models_url=url + "/models"))
    with pytest.raises(providers.NotAllowed):
        providers.list_models("deepseek", "sk-ds")
    assert providers.refresh({"deepseek": "sk-ds"})["providers"]["deepseek"] == {
        "error": "turned off in Settings > Models"}
    assert seen == []  # not one byte left
    providers.sdk_client(anthropic, url, "sk-ant", provider="anthropic").messages.create(
        model="m", max_tokens=10, messages=[{"role": "user", "content": "hi"}])
    assert len(seen) == 1  # what is allowed still goes


def test_each_provider_says_where_its_company_is_based():
    assert {p.key: p.country for p in providers.PROVIDERS.values()} == {
        "anthropic": "US", "openai": "US", "xai": "US", "moonshot": "CN", "deepseek": "CN", "qwen": "CN"}


def test_the_tests_own_stand_in_api_must_be_on_this_computer(monkeypatch):
    pytest.importorskip("anthropic")
    monkeypatch.setenv("OPENSTRAND_TEST_API", "http://127.0.0.1:8123")
    assert str(providers.client_for("claude-sonnet-5-5", "sk-ant-x").base_url).startswith("http://127.0.0.1:8123")
    assert providers.client_for("grok", "xai-x").provider.base_url == "http://127.0.0.1:8123"
    for elsewhere in ("https://api.deepseek.com/anthropic", "http://10.0.0.5:8123"):
        monkeypatch.setenv("OPENSTRAND_TEST_API", elsewhere)
        with pytest.raises(providers.UnsafeRequest, match="must be on this computer"):
            providers.client_for("claude-sonnet-5-5", "sk-ant-x")


# ------------------------------------------------------------ Refresh models
def listing(provider, server, monkeypatch, path="/models"):
    """The provider's model list on the local server."""
    monkeypatch.setitem(providers.PROVIDERS, provider,
                        dataclasses.replace(providers.PROVIDERS[provider], models_url=server.url + path))


def test_each_provider_lists_its_chat_models(server, monkeypatch):
    # Anthropic: two pages, its own names, a deprecated model.
    listing("anthropic", server, monkeypatch, "/v1/models")
    server.answers[:] = [
        (200, {"data": [{"id": "claude-opus-5-5", "display_name": "Claude Opus 5.5"},
                        {"id": "claude-sonnet-5-5", "display_name": "Claude Sonnet 5.5"}],
               "has_more": True, "last_id": "claude-sonnet-5-5"}),
        (200, {"data": [{"id": "claude-haiku-5-5", "display_name": "Claude Haiku 5.5",
                         "deprecated_at": "2026-12-01T00:00:00Z"}], "has_more": False})]
    rows = providers.list_models("anthropic", "sk-ant-test")
    assert [r["id"] for r in rows] == ["claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5"]
    assert rows[0]["label"] == "Claude Opus 5.5" and rows[2]["retiring"] == "2026-12-01"
    assert server.seen[0]["headers"]["x-api-key"] == "sk-ant-test" and "anthropic-version" in server.seen[0]["headers"]
    assert server.seen[1]["path"] == "/v1/models?limit=100&after_id=claude-sonnet-5-5"
    # OpenAI: only chat models, no snapshots, no image or speech ids; a shutdown date passed is retired.
    listing("openai", server, monkeypatch)
    server.answers[:] = [(200, {"data": [
        {"id": "gpt-6.1-terra"}, {"id": "gpt-6.1-terra-2026-10-26"}, {"id": "gpt-image-2"},
        {"id": "text-embedding-4"}, {"id": "gpt-realtime-2"}, {"id": "gpt-6.2-terra"},
        {"id": "gpt-6.1-sol", "shutdown_date": "2026-01-01"}]})]
    rows = providers.list_models("openai", "sk-test")
    assert [r["id"] for r in rows] == ["gpt-6.1-terra", "gpt-6.2-terra", "gpt-6.1-sol"]
    assert rows[1]["label"] == "GPT-6.2 Terra" and rows[2]["retired"] is True
    assert server.seen[-1]["headers"]["authorization"] == "Bearer sk-test"
    # xAI: its prices, in USD cents per 100 million tokens.
    listing("xai", server, monkeypatch, "/v1/language-models")
    server.answers[:] = [(200, {"models": [
        {"id": "grok-4.8", "input_modalities": ["text", "image"], "output_modalities": ["text"],
         "prompt_text_token_price": 25000, "cached_prompt_text_token_price": 5000,
         "completion_text_token_price": 80000},
        {"id": "grok-imagine-2", "output_modalities": ["image"]}]})]
    (grok,) = providers.list_models("xai", "xai-test")
    assert grok["id"] == "grok-4.8" and grok["prices"] == (2.5, 8.0, 2.5, 0.5) and grok["vision"] is True
    # A provider that refuses: its own message.
    listing("deepseek", server, monkeypatch)
    server.answers[:] = [(401, {"error": {"message": "Authentication Fails"}})]
    with pytest.raises(providers.ProviderError, match="Authentication Fails"):
        providers.list_models("deepseek", "sk-bad")


def test_a_refresh_adds_new_models_marks_retiring_ones_and_hides_what_is_gone():
    try:
        hidden = providers.use_catalog({"providers": {
            "anthropic": {"models": [
                {"id": "claude-opus-5-5", "label": "Claude Opus 5.5", "prices": None, "vision": True},
                {"id": "claude-sonnet-5-5", "label": "Claude Sonnet 5.5", "retiring": "2027-03-01"}]},
            "xai": {"models": [{"id": "grok-4.7"}, {"id": "grok-4.8", "label": "Grok 4.8",
                                                     "prices": [2.5, 8.0, 2.5, 0.5]}]},
            "openai": {"error": "cannot reach it"}}})
        assert hidden == ["claude-haiku-5-5"]  # Anthropic answered without it
        assert "claude-haiku-5-5" not in providers.MODELS and "claude-haiku-5-5" not in agent.PRICES
        opus = providers.MODELS["claude-opus-5-5"]
        assert opus.new and opus.estimated and opus.prices == tuple(v * 2.5 for v in providers.PRICES["claude-sonnet-5-5"])
        assert providers.MODELS["claude-sonnet-5-5"].retiring == "2027-03-01"
        grok = providers.MODELS["grok-4.8"]
        assert grok.new and not grok.estimated and agent.PRICES["grok-4.8"] == (2.5, 8.0, 2.5, 0.5)
        assert providers.resolve("grok-4.8") == "grok-4.8" and providers.provider_of("grok-4.8").key == "xai"
        assert "gpt-6.1-terra" in providers.MODELS  # OpenAI did not answer: its models stay
        assert providers.resolve("haiku") != "claude-haiku-5-5" if "haiku" in providers.ALIASES else True
    finally:
        providers.use_catalog({})
    assert "claude-haiku-5-5" in providers.MODELS and "grok-4.8" not in providers.MODELS


def test_the_saved_model_moves_on_when_its_provider_no_longer_offers_it(tmp_path, monkeypatch):
    import claude_settings
    monkeypatch.setenv("APPDATA", str(tmp_path))
    try:
        claude_settings.save(model="claude-haiku-5-5")
        result = claude_settings.apply_catalog({"refreshed": "2026-11-07 10:00", "providers": {
            "anthropic": {"models": [{"id": "claude-sonnet-5-5"}, {"id": "claude-opus-5-5", "label": "Claude Opus 5.5"}]}}})
        assert result["hidden"] == ["claude-haiku-5-5"] and result["new"] == ["claude-opus-5-5"]
        assert result["switched"] == "claude-sonnet-5-5"
        saved = claude_settings.load()
        assert saved["model"] == "claude-sonnet-5-5" and saved["catalog"]["refreshed"] == "2026-11-07 10:00"
        offered = dict(claude_settings.models())
        assert offered["claude-opus-5-5"] == "Claude Opus 5.5" and "claude-haiku-5-5" not in offered
        claude_settings.save(model="claude-opus-5-5")  # a refreshed model can be chosen and is kept
        assert claude_settings.load()["model"] == "claude-opus-5-5"
    finally:
        providers.use_catalog({})
