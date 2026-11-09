"""Settings > Models: the switch that keeps every AI model off the internet, and the one for
the providers based in China (off until the person allows them). providers.POLICY asks
claude_settings before every request leaves, so nothing they forbid is ever sent: not by
the app, not by the agent it starts, not by a share with the developer."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT, ROOT / "src"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from openstrand import providers  # noqa: E402
import claude_settings  # noqa: E402
import claude_sharing  # noqa: E402


# The app's own copy of providers.py, which claude_settings loads (the same module as
# openstrand.providers in the agent, but another copy when a test imported claude_settings first).
APP = claude_settings.providers


@pytest.fixture
def settings(tmp_path, monkeypatch):
    """This test's own settings, asked before every request as in the app and the agent."""
    monkeypatch.setenv("APPDATA", str(tmp_path))
    for copy in {id(providers): providers, id(APP): APP}.values():
        monkeypatch.setattr(copy, "POLICY", claude_settings.refusal)
    for spec in providers.PROVIDERS.values():
        monkeypatch.delenv(spec.env, raising=False)
    return Path(claude_settings.settings_path())


def test_the_providers_based_in_china_are_off_until_the_person_allows_them(settings):
    saved = claude_settings.load()
    assert saved["models_on"] is True and saved["allow_china"] is False
    offered = dict(claude_settings.models())
    assert "claude-sonnet-5-5" in offered and "gpt-6.1-terra" in offered and "grok-4.7" in offered
    assert not {"kimi-k3.1-pro", "deepseek-flash", "qwen3.8-max"} & set(offered)
    with pytest.raises(ValueError, match="unknown model"):
        claude_settings.save(model="deepseek-flash")
    with pytest.raises(providers.NotAllowed, match="DeepSeek is turned off"):
        providers.check_allowed("deepseek")
    providers.check_allowed("anthropic")
    claude_settings.save(allow_china=True, model="kimi-k3.1-pro")
    assert claude_settings.load()["model"] == "kimi-k3.1-pro" and "qwen3.8-max" in dict(claude_settings.models())
    providers.check_allowed("moonshot")
    claude_settings.save(allow_china=False)  # off again: the saved model moves off Kimi
    assert claude_settings.load()["model"] == "claude-sonnet-5-5"
    with pytest.raises(providers.NotAllowed, match=r"Moonshot AI \(Kimi\) is turned off"):
        providers.check_allowed("moonshot")
    # Someone who used DeepSeek with an earlier version: back on Claude until they allow it.
    settings.write_text(json.dumps({"model": "deepseek-flash", "api_keys": {"deepseek": "sk-ds-1234567890"}}),
                        encoding="utf-8")
    assert claude_settings.load()["model"] == "claude-sonnet-5-5"
    assert claude_settings.load()["keys"] == {"deepseek": "sk-ds-1234567890"}  # the key itself stays


def test_with_models_off_nothing_is_sent_anywhere(settings, monkeypatch):
    claude_settings.save(provider_key=("xai", "xai-test-1234567890"), models_on=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds-from-env")
    for provider in (*providers.PROVIDERS, None):  # None: a share with the developer
        with pytest.raises(providers.NotAllowed, match="AI models are turned off"):
            providers.check_allowed(provider)
    assert not claude_settings.refresh_due()  # no daily Refresh models
    asked = []
    monkeypatch.setattr(APP, "refresh", lambda keys, timeout=30.0: asked.append(dict(keys)) or {"providers": {}})
    claude_settings.fetch_catalog()
    with pytest.raises(APP.NotAllowed):
        claude_sharing.send(b"OSS1" + bytes(2000), "https://openstrand-share.example.workers.dev/v1/share")
    # On again: only the providers allowed are asked (not DeepSeek, whose key is in the environment).
    claude_settings.save(models_on=True)
    assert claude_settings.refresh_due()
    claude_settings.fetch_catalog()
    assert asked == [{}, {"xai": "xai-test-1234567890"}]
    claude_settings.save(allow_china=True)
    claude_settings.fetch_catalog()
    assert asked[-1] == {"xai": "xai-test-1234567890", "deepseek": "sk-ds-from-env"}


@pytest.mark.parametrize("saved, model, said", [
    ({"models_on": False}, "haiku", "AI models are turned off"),
    ({}, "deepseek", "DeepSeek is turned off"),
])
def test_the_agent_sends_nothing_the_settings_forbid(tmp_path, saved, model, said):
    pytest.importorskip("anthropic")
    # Where the agent looks: APPDATA's folder, or on macOS the home's Library (both this test's own).
    for folder in (tmp_path / "appdata" / "OpenStrandStudio",
                   tmp_path / "home" / "Library" / "Application Support" / "OpenStrandStudio"):
        folder.mkdir(parents=True)
        (folder / "claude.json").write_text(json.dumps(saved), encoding="utf-8")
    env = dict(os.environ, APPDATA=str(tmp_path / "appdata"), HOME=str(tmp_path / "home"),
               ANTHROPIC_API_KEY="sk-ant-test", DEEPSEEK_API_KEY="sk-ds-test", QT_QPA_PLATFORM="offscreen")
    env.pop("OPENSTRAND_TEST_API", None)
    run = subprocess.run([sys.executable, "-m", "openstrand", "agent", "a heart", "--model", model,
                          "--out-dir", str(tmp_path / "out")], cwd=ROOT, env=env, capture_output=True,
                         text=True, timeout=300)
    assert run.returncode == 1 and said in run.stderr, run.stderr[-2000:]
