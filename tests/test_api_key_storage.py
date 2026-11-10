"""Where the API keys are kept: the system's password store when there is one (macOS
Keychain, Windows Credential Manager, the Secret Service), else claude.json, readable by
its owner only and written whole or not at all. A store in memory stands in for the real
one, which the tests never touch (tests/conftest.py)."""
import json
import os
import stat
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT, ROOT / "src"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

import agent_settings  # noqa: E402


class Store:
    """A password store in memory, answering as keyring's backends do."""
    priority = 5

    def __init__(self, refuse=()):
        self.items, self.refuse = {}, set(refuse)

    def get_password(self, service, name):
        return self.items.get((service, name))

    def set_password(self, service, name, value):
        if name in self.refuse:
            raise RuntimeError("the store refused it")
        self.items[(service, name)] = value

    def delete_password(self, service, name):
        if (service, name) not in self.items:
            raise KeyError(name)
        del self.items[(service, name)]


@pytest.fixture
def settings(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(agent_settings, "_cache", {})
    return Path(agent_settings.settings_path())


def use_store(monkeypatch, store):
    monkeypatch.setattr(agent_settings, "keychain", lambda: store)
    monkeypatch.setattr(agent_settings, "_cache", {})  # as a new start of the app: nothing read yet
    monkeypatch.setattr(agent_settings, "_unreadable", set())


def test_keys_an_earlier_version_kept_in_the_file_move_into_the_password_store(settings, monkeypatch):
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(json.dumps({"api_key": "sk-ant-old-1234567890", "api_keys": {"xai": "xai-old-1234567890"},
                                    "model": "grok-4.7"}), encoding="utf-8")
    store = Store()
    use_store(monkeypatch, store)
    saved = agent_settings.load()
    assert saved["keys"] == {"anthropic": "sk-ant-old-1234567890", "xai": "xai-old-1234567890"}
    text = settings.read_text(encoding="utf-8")
    assert "sk-ant-old" not in text and "xai-old" not in text
    assert json.loads(text)["keychain"] == ["anthropic", "xai"] and json.loads(text)["model"] == "grok-4.7"
    assert store.items == {("OpenStrandStudio", "anthropic"): "sk-ant-old-1234567890",
                           ("OpenStrandStudio", "xai"): "xai-old-1234567890"}
    use_store(monkeypatch, store)  # the next start reads them back from the store
    assert agent_settings.load()["keys"] == saved["keys"] and agent_settings.key_storage() == "keychain"


def test_a_removed_key_leaves_the_store_and_other_settings_never_write_it_again(settings, monkeypatch):
    store = Store()
    use_store(monkeypatch, store)
    agent_settings.save(provider_key=("openai", "sk-openai-1234567890"))
    writes = []
    original = store.set_password
    store.set_password = lambda *args: writes.append(args) or original(*args)
    agent_settings.add_spending(0.5)
    agent_settings.save(model="claude-haiku-5-5", share=False)
    assert writes == []  # the key is there already: the store is not asked again
    agent_settings.save(provider_key=("openai", ""))
    assert store.items == {} and "keychain" not in json.loads(settings.read_text(encoding="utf-8"))
    assert agent_settings.load()["keys"] == {} and agent_settings.load()["share"] is False


def test_a_key_the_store_refuses_stays_in_the_private_file(settings, monkeypatch):
    use_store(monkeypatch, Store(refuse={"xai"}))
    agent_settings.save(provider_key=("xai", "xai-test-1234567890"))
    agent_settings.save(provider_key=("anthropic", "sk-ant-test-1234567890"))
    on_disk = json.loads(settings.read_text(encoding="utf-8"))
    assert on_disk["api_keys"] == {"xai": "xai-test-1234567890"} and on_disk["keychain"] == ["anthropic"]
    assert "api_key" not in on_disk
    assert agent_settings.load()["keys"] == {"anthropic": "sk-ant-test-1234567890", "xai": "xai-test-1234567890"}
    if os.name == "posix":
        assert stat.S_IMODE(os.stat(settings).st_mode) == 0o600


def test_without_a_store_keys_stay_in_a_file_only_its_owner_can_read(settings, monkeypatch):
    use_store(monkeypatch, None)
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text("{}", encoding="utf-8")
    if os.name == "posix":
        os.chmod(settings, 0o644)  # readable by others: made by an earlier version, or by hand
    agent_settings.save(provider_key=("deepseek", "sk-ds-1234567890"))
    assert json.loads(settings.read_text(encoding="utf-8"))["api_keys"] == {"deepseek": "sk-ds-1234567890"}
    assert agent_settings.key_storage() == "file"
    if os.name == "posix":
        assert stat.S_IMODE(os.stat(settings).st_mode) == 0o600
    assert [p.name for p in settings.parent.iterdir()] == ["claude.json"]  # no temporary file left behind


def test_only_a_secure_store_is_used(monkeypatch):
    keyring = pytest.importorskip("keyring")
    from keyring.backends import fail
    monkeypatch.delenv("OPENSTRAND_KEYCHAIN", raising=False)
    secure = Store()
    monkeypatch.setattr(keyring, "get_keyring", lambda: secure)
    assert agent_settings._find_keychain() is secure
    monkeypatch.setattr(keyring, "get_keyring", lambda: fail.Keyring())  # no store on this computer
    assert agent_settings._find_keychain() is None
    plain = type("PlaintextKeyring", (Store,), {"__module__": "keyrings.alt.file"})()  # its own plain files
    monkeypatch.setattr(keyring, "get_keyring", lambda: plain)
    assert agent_settings._find_keychain() is None
    monkeypatch.setenv("OPENSTRAND_KEYCHAIN", "off")
    assert agent_settings.keychain() is None


def test_a_key_the_store_cannot_give_for_now_is_never_deleted(settings, monkeypatch):
    store = Store()
    use_store(monkeypatch, store)
    agent_settings.save(provider_key=("anthropic", "sk-ant-test-1234567890"))
    agent_settings.save(provider_key=("xai", "xai-test-1234567890"))

    class Locked(Store):  # the same entries, but every read refused (locked, or access denied)
        def get_password(self, service, name):
            raise RuntimeError("locked")
    locked = Locked()
    locked.items = store.items
    use_store(monkeypatch, locked)  # the app starts with the store locked
    assert agent_settings.load()["keys"] == {}
    agent_settings.add_spending(0.25)  # every request's cost is saved: the keys must survive it
    agent_settings.save(model="claude-haiku-5-5", share=False)
    assert len(store.items) == 2 and json.loads(settings.read_text(encoding="utf-8"))["keychain"] == ["anthropic", "xai"]
    agent_settings.save(provider_key=("xai", ""))  # removed by the person: gone, even while locked
    assert list(store.items) == [("OpenStrandStudio", "anthropic")]
    assert json.loads(settings.read_text(encoding="utf-8"))["keychain"] == ["anthropic"]
    use_store(monkeypatch, None)  # no store at all now (keyring uninstalled): still listed, not lost
    agent_settings.add_spending(0.25)
    assert json.loads(settings.read_text(encoding="utf-8"))["keychain"] == ["anthropic"]
    use_store(monkeypatch, store)  # the store is back
    assert agent_settings.load()["keys"] == {"anthropic": "sk-ant-test-1234567890"}


def test_a_settings_file_held_open_elsewhere_is_still_written_whole(settings, monkeypatch):
    use_store(monkeypatch, None)
    agent_settings.save(model="claude-haiku-5-5")
    real, refused = os.replace, []

    def busy(source, target):  # Windows: another process has it open for a moment
        if len(refused) < 2:
            refused.append(target)
            raise PermissionError("in use")
        return real(source, target)
    monkeypatch.setattr(os, "replace", busy)
    monkeypatch.setattr(agent_settings.time, "sleep", lambda seconds: None)
    agent_settings.save(model="gpt-6.1-terra")
    assert len(refused) == 2 and agent_settings.load()["model"] == "gpt-6.1-terra"

    def always_busy(source, target):
        raise PermissionError("in use")
    monkeypatch.setattr(os, "replace", always_busy)  # held open all along: written in place, whole
    agent_settings.save(model="grok-4.7")
    assert agent_settings.load()["model"] == "grok-4.7" and json.loads(settings.read_text(encoding="utf-8"))
    assert [p.name for p in settings.parent.iterdir()] == ["claude.json"]  # no temporary file left behind
