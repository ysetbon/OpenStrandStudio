"""Sharing what Claude makes with the developer (src/claude_sharing.py): what a share
holds and never holds, sealed so only the developer's private key opens it, and sent over
HTTPS (here: a local stand-in for the Worker) without following a redirect."""
import base64
import json
import os
import sys
import threading
import urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT, ROOT / "src"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

pytest.importorskip("cryptography.hazmat.primitives.hpke")  # cryptography 47 or newer
import claude_sharing  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n-a-picture-"
HOPF = json.loads((ROOT / "knot_samples/links/json/hopf_link.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def keys():
    return claude_sharing.new_keys()


@pytest.fixture
def worker(monkeypatch):
    """A local stand-in for the Worker: keeps what each POST sent; .redirect makes it answer
    302 to another host instead."""
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    got = []

    class Handler(BaseHTTPRequestHandler):
        redirect = None

        def do_POST(self):
            body = self.rfile.read(int(self.headers["Content-Length"]))
            got.append({"path": self.path, "type": self.headers["Content-Type"], "body": body,
                        "host": self.headers["Host"]})
            if Handler.redirect:
                self.send_response(302)
                self.send_header("Location", Handler.redirect)
            else:
                self.send_response(204)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *args):
            pass
    http = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=http.serve_forever, daemon=True).start()
    yield type("Worker", (), {"url": f"http://127.0.0.1:{http.server_port}/v1/share", "got": got,
                              "port": http.server_port, "handler": Handler})
    http.shutdown()


def test_a_share_opens_with_the_private_key_only_and_holds_nothing_readable(keys):
    private, public = keys
    record = claude_sharing.record(["Two linked rings, in teal."], HOPF, PNG, model="claude-sonnet-5-5",
                                   language="fr")
    sealed = claude_sharing.seal(record, public)
    assert sealed.startswith(b"OSS1")
    for plain in (b"linked rings", b"strands", b"claude-sonnet", PNG, base64.b64encode(PNG)):
        assert plain not in sealed
    opened = claude_sharing.unseal(sealed, private)
    assert opened == json.loads(json.dumps(record))
    assert opened["design"] == HOPF and base64.b64decode(opened["picture"]) == PNG
    assert opened["answer"] == ["Two linked rings, in teal."] and opened["language"] == "fr"
    # Another key, a changed byte, or a share sealed twice for the same record: never the same.
    other, _ = claude_sharing.new_keys()
    with pytest.raises(Exception):
        claude_sharing.unseal(sealed, other)
    changed = bytearray(sealed)
    changed[-20] ^= 1
    with pytest.raises(Exception):
        claude_sharing.unseal(bytes(changed), private)
    assert claude_sharing.seal(record, public) != sealed  # a fresh key exchange every time
    with pytest.raises(ValueError, match="not an OpenStrand Studio share"):
        claude_sharing.unseal(b"PK\x03\x04" + sealed[4:], private)


def test_a_share_never_holds_a_folder_or_the_person_s_name_in_one():
    home = os.path.expanduser("~")
    texts = [f"Saved it as {home}{os.sep}AppData{os.sep}OpenStrandStudio{os.sep}claude_designs{os.sep}ring.json.",
             r"The file C:\Users\Jane Doe\Documents\knot.json is open.",
             "Also /home/jane/designs/knot.json and ~/Desktop/k.json and \\\\server\\share\\k.json.",
             "From https://www.animatedknots.com/home/figure-8 and http://example.org/Users/x, as is."]
    groups = {r"C:\Users\Jane Doe\private": {}, r"D:\work\jane\a": {}, "Rings": {}}  # a key is a text too
    record = claude_sharing.record(texts + [r"cannot open D:\work\jane\a.json"],
                                   {"strands": [], "note": "/Users/jane/x.png", "groups": groups}, None, ok=False)
    said = json.dumps(record)
    for private in (home, "Jane Doe", "Documents", "/home/jane", "/Users/jane", "Desktop", "server\\\\share",
                    "D:\\\\work"):
        assert private not in said, private
    assert "https://www.animatedknots.com/home/figure-8" in said and "http://example.org/Users/x" in said
    assert record["design"]["note"] == "…" and record["picture"] is None
    assert record["design"]["groups"] == {"…": {}, "… (2)": {}, "Rings": {}}  # cut out, and none merged
    assert set(record) == {"format", "model", "language", "ok", "answer", "design", "picture",
                           "version", "new", "gallery"}
    # The app's version goes with each share: the one its installers say.
    spec = (ROOT / "src" / "OpenStrandStudio_mac.spec").read_text(encoding="utf-8")
    assert record["version"] == claude_sharing.APP_VERSION
    assert f"'CFBundleShortVersionString': '{claude_sharing.APP_VERSION}'" in spec
    # Nothing else: not the request, an error's text, the time, the computer or the person.


def test_a_share_never_holds_an_api_key_even_when_the_answer_repeats_one(tmp_path, monkeypatch):
    import claude_settings
    monkeypatch.setenv("APPDATA", str(tmp_path))
    claude_settings.save(provider_key=("moonshot", "an-odd-saved-key-0123456789"))
    monkeypatch.setenv("OPENAI_API_KEY", "an-odd-env-key-9876543210")
    keys = claude_settings.own_keys()  # the person's own, saved or in the environment, any shape
    assert {"an-odd-saved-key-0123456789", "an-odd-env-key-9876543210"} <= set(keys)
    record = claude_sharing.record(
        ["Your keys an-odd-saved-key-0123456789 and an-odd-env-key-9876543210 both work.",
         "So would sk-ant-api03-AbCdEf0123456789_xyz-QQ, sk-proj-ABCDEFGHIJKLMNOPQRSTUVWX or "
         "xai-0123456789abcdefghijKLMNOP.",
         "A risk-free-of-charge-for-everyone knot, task-based, from xai-org/grok-1."],
        {"strands": [], "note": "sk-0123456789abcdef0123", "name": "an-odd-saved-key-0123456789"}, None,
        secrets=keys + ["", "short"])
    said = json.dumps(record)
    for secret in ("an-odd-saved-key", "an-odd-env-key", "sk-ant-", "sk-proj-", "xai-0123", "sk-0123"):
        assert secret not in said, secret
    assert record["answer"] == ["Your keys … and … both work.", "So would …, … or ….",
                                "A risk-free-of-charge-for-everyone knot, task-based, from xai-org/grok-1."]
    assert record["design"] == {"strands": [], "note": "…", "name": "…"}


def test_sharing_is_off_until_the_developer_sets_it_up(keys, monkeypatch):
    _, public = keys
    monkeypatch.setattr(claude_sharing, "SHARE_URL", "")
    monkeypatch.setattr(claude_sharing, "SHARE_PUBLIC_KEY", "")
    assert not claude_sharing.available()
    assert claude_sharing.available("https://openstrand-share.example.workers.dev/v1/share", public)
    assert not claude_sharing.available("http://openstrand-share.example.workers.dev/v1/share", public)  # not HTTPS
    assert not claude_sharing.available("https://openstrand-share.example.workers.dev/v1/share", public[:-8])
    with pytest.raises(ValueError, match="bytes"):
        claude_sharing.public_key(base64.b64encode(b"short").decode())


def test_a_share_goes_to_the_worker_sealed_and_never_follows_a_redirect(keys, worker):
    private, public = keys
    sealed = claude_sharing.seal(claude_sharing.record(["A heart."], HOPF, PNG), public)
    assert claude_sharing.send(sealed, worker.url) == 204
    (sent,) = worker.got
    assert sent["path"] == "/v1/share" and sent["type"] == "application/octet-stream" and sent["body"] == sealed
    assert claude_sharing.unseal(sent["body"], private)["answer"] == ["A heart."]
    worker.handler.redirect = f"http://localhost:{worker.port}/elsewhere"
    with pytest.raises(urllib.error.HTTPError) as answer:
        claude_sharing.send(sealed, worker.url)
    assert answer.value.code == 302 and [g["path"] for g in worker.got] == ["/v1/share", "/v1/share"]
    with pytest.raises(ValueError, match="https://"):  # never in the clear to another computer
        claude_sharing.send(sealed, "http://openstrand-share.example.workers.dev/v1/share")
    huge = claude_sharing.record(["x"], None, os.urandom(claude_sharing.MAX_BYTES))
    with pytest.raises(ValueError, match="too large"):
        claude_sharing.seal(huge, public)


def test_the_developer_s_tool_makes_a_private_key_and_opens_shares_into_files(tmp_path, capsys):
    sys.path.insert(0, str(ROOT / "scripts"))
    import share_inbox
    key = tmp_path / "share.key"
    assert share_inbox.main(["keygen", "--key", str(key)]) == 0
    public = capsys.readouterr().out.strip().splitlines()[-1]
    if os.name == "posix":
        assert oct(key.stat().st_mode & 0o777) == "0o600"  # readable by its owner alone
    with pytest.raises(SystemExit, match="exists already"):  # never over a key in use
        share_inbox.main(["keygen", "--key", str(key)])
    sealed = tmp_path / "one.oss"
    sealed.write_bytes(claude_sharing.seal(claude_sharing.record(["A trefoil."], HOPF, PNG, model="kimi-k3.1-pro"),
                                           public))
    assert share_inbox.main(["open", str(sealed), "--key", str(key), "--out", str(tmp_path / "shared")]) == 0
    folder = tmp_path / "shared" / "one"
    assert sorted(p.name for p in folder.iterdir()) == ["about.json", "answer.md", "design.json", "design.png"]
    assert (folder / "answer.md").read_text(encoding="utf-8") == "A trefoil.\n"
    assert json.loads((folder / "design.json").read_text(encoding="utf-8")) == HOPF
    assert (folder / "design.png").read_bytes() == PNG
    assert json.loads((folder / "about.json").read_text(encoding="utf-8"))["model"] == "kimi-k3.1-pro"


def test_a_share_anyone_could_make_cannot_flood_or_trip_the_developer_s_tool(keys, tmp_path, capsys):
    import zlib
    private, public = keys
    from cryptography.hazmat.primitives import hpke  # noqa: F401
    seal_raw = lambda data: claude_sharing.MAGIC + claude_sharing.suite().encrypt(  # noqa: E731
        data, claude_sharing.public_key(public), info=claude_sharing.INFO)
    bomb = zlib.compress(b"[" + b" " * (claude_sharing.MAX_OPENED_BYTES + 10) + b"]", 9)  # a few hundred kB
    assert len(bomb) < claude_sharing.MAX_BYTES
    with pytest.raises(ValueError, match="opens to more than"):
        claude_sharing.unseal(seal_raw(bomb), private)
    with pytest.raises(ValueError, match="not an OpenStrand Studio share record"):
        claude_sharing.unseal(seal_raw(zlib.compress(b'["a list"]')), private)
    # A record of the wrong shape: the developer's tool writes what it can, never trips on it.
    sys.path.insert(0, str(ROOT / "scripts"))
    import share_inbox
    odd = {"answer": "not a list", "design": ["not", "a", "dict"], "picture": "%%% not base64", "model": 7}
    share_inbox.save(odd, tmp_path / "odd")
    assert sorted(p.name for p in (tmp_path / "odd").iterdir()) == ["about.json", "answer.md"]
    key = tmp_path / "share.key"
    key.write_text(private + "\n", encoding="ascii")
    good, bad = tmp_path / "good.oss", tmp_path / "bad.oss"
    good.write_bytes(claude_sharing.seal(claude_sharing.record(["A ring."], HOPF, PNG), public))
    bad.write_bytes(seal_raw(bomb))
    assert share_inbox.main(["open", str(bad), str(good), "--key", str(key), "--out", str(tmp_path / "out")]) == 1
    assert not (tmp_path / "out" / "bad").exists() and (tmp_path / "out" / "good" / "design.json").exists()
    # A damaged file of the same name as one opened before: the earlier copy is left as it was.
    good.write_bytes(seal_raw(bomb))
    assert share_inbox.main(["open", str(good), "--key", str(key), "--out", str(tmp_path / "out")]) == 1
    assert json.loads((tmp_path / "out" / "good" / "design.json").read_text(encoding="utf-8")) == HOPF


def test_the_developer_s_tool_writes_a_share_whole_or_not_at_all(keys, tmp_path, monkeypatch):
    """A share that opens but cannot be written (here the disk refuses its picture) leaves no
    half folder, and an earlier folder of the same name exactly as it was; text that is not
    valid Unicode (a lone surrogate: valid JSON, not UTF-8) is written, not tripped on."""
    private, public = keys
    sys.path.insert(0, str(ROOT / "scripts"))
    import share_inbox
    key, out = tmp_path / "share.key", tmp_path / "out"
    key.write_text(private + "\n", encoding="ascii")
    first, second = tmp_path / "first" / "ring.oss", tmp_path / "second" / "ring.oss"  # the same name
    for path, answer in ((first, "A ring."), (second, "Another ring.")):
        path.parent.mkdir()
        path.write_bytes(claude_sharing.seal(claude_sharing.record([answer], HOPF, PNG), public))
    assert share_inbox.main(["open", str(first), "--key", str(key), "--out", str(out)]) == 0
    before = {p.name: p.read_bytes() for p in (out / "ring").iterdir()}
    real = share_inbox.Path.write_bytes

    def full_disk(self, data):
        if self.name == "design.png":
            raise OSError(28, "No space left on device")
        return real(self, data)
    monkeypatch.setattr(share_inbox.Path, "write_bytes", full_disk)
    assert share_inbox.main(["open", str(second), "--key", str(key), "--out", str(out)]) == 1
    monkeypatch.setattr(share_inbox.Path, "write_bytes", real)
    assert {p.name: p.read_bytes() for p in (out / "ring").iterdir()} == before
    assert [p.name for p in out.iterdir()] == ["ring"]  # nothing half written left beside it
    # Stopped (Ctrl+C) just as the new one would take its place: the earlier one is put back.
    real_replace = share_inbox.os.replace

    def interrupted(src, dst):
        if Path(dst) == out / "ring" and "-old-" not in Path(src).name:
            raise KeyboardInterrupt
        return real_replace(src, dst)
    monkeypatch.setattr(share_inbox.os, "replace", interrupted)
    with pytest.raises(KeyboardInterrupt):
        share_inbox.save(claude_sharing.record(["Another ring."], HOPF, PNG), out / "ring")
    monkeypatch.setattr(share_inbox.os, "replace", real_replace)
    assert {p.name: p.read_bytes() for p in (out / "ring").iterdir()} == before
    assert [p.name for p in out.iterdir()] == ["ring"]
    # Once it can be written, it takes the earlier one's place whole.
    assert share_inbox.main(["open", str(second), "--key", str(key), "--out", str(out)]) == 0
    assert (out / "ring" / "answer.md").read_text(encoding="utf-8") == "Another ring.\n"
    assert [p.name for p in out.iterdir()] == ["ring"]
    share_inbox.save({"answer": ["bad \ud800 text"], "design": {"name": "\udfff"}}, out / "odd")
    assert (out / "odd" / "answer.md").read_text(encoding="utf-8") == "bad ? text\n"
    assert json.loads((out / "odd" / "design.json").read_text(encoding="utf-8")) == {"name": "?"}


def test_a_share_says_gallery_only_for_a_new_design_the_person_allowed():
    """The gallery is a second yes, and only for a design made from nothing of the person's,
    in a request that worked."""
    share = lambda **given: claude_sharing.record(["Done."], given.pop("design", HOPF), PNG, **given)  # noqa: E731
    assert share()["gallery"] is False and share()["new"] is False  # nothing said: private
    assert share(new=True)["gallery"] is False  # new, but the person did not allow the gallery
    assert share(gallery=True)["gallery"] is False  # allowed, but made from their own design
    assert share(new=True, gallery=True, ok=False)["gallery"] is False  # the request failed
    assert share(new=True, gallery=True, design=None)["gallery"] is False  # no design at all
    allowed = share(new=True, gallery=True)
    assert allowed["gallery"] is True and allowed["new"] is True


def test_the_gallery_is_offered_only_once_the_developer_says_where_it_is(keys, monkeypatch):
    monkeypatch.setattr(claude_sharing, "SHARE_URL", "https://openstrand-share.example.workers.dev/v1/share")
    monkeypatch.setattr(claude_sharing, "SHARE_PUBLIC_KEY", keys[1])
    assert claude_sharing.available() and not claude_sharing.gallery_available()
    monkeypatch.setattr(claude_sharing, "GALLERY_URL", "http://example.github.io/OpenStrandStudio/")
    assert not claude_sharing.gallery_available()  # https only
    monkeypatch.setattr(claude_sharing, "GALLERY_URL", "https://example.github.io/OpenStrandStudio/")
    assert claude_sharing.gallery_available()
    monkeypatch.setattr(claude_sharing, "SHARE_URL", "")
    assert not claude_sharing.gallery_available()  # no sharing, no gallery


@pytest.fixture
def inbox(tmp_path):
    """The developer's tool, a gallery folder, and extract(record): a share as fetch leaves it."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import share_inbox
    count = iter(range(1000))

    def extract(record):
        folder = tmp_path / "shared" / f"share{next(count)}"
        share_inbox.save(record, folder)
        return folder

    def draw(design, path):  # the app's canvas stands in: the test needs no window
        Path(path).write_bytes(PNG + json.dumps(sorted(design)).encode())
    return type("Inbox", (), {"tool": share_inbox, "gallery": tmp_path / "gallery", "extract": staticmethod(extract),
                              "draw": staticmethod(draw)})


def test_publish_puts_a_cleaned_copy_in_the_gallery_and_never_the_share_itself(inbox):
    tool, gallery = inbox.tool, inbox.gallery
    design = json.loads(json.dumps(HOPF))
    design["groups"] = {"Jane Doe's rings": {"layers": ["1_1"], "strands": ["1_1"], "main_strands": ["1_1"]}}
    record = claude_sharing.record(["Two rings for Jane Doe."], design, PNG, model="claude-haiku-5-5", new=True,
                                   gallery=True)
    name = tool.publish_one(inbox.extract(record), gallery, draw=inbox.draw)
    assert tool.GALLERY_ID.match(name)
    assert sorted(p.name for p in (gallery / "designs").iterdir()) == [f"{name}.json", f"{name}.png"]
    shown = (gallery / "designs" / f"{name}.json").read_text(encoding="utf-8")
    assert "Jane" not in shown and "rings" not in shown  # a group's name is the person's own text
    assert list(json.loads(shown)["groups"]) == ["Group 1"]
    assert json.loads(shown)["strands"] == HOPF["strands"]  # the design itself, as it was made
    assert (gallery / "designs" / f"{name}.png").read_bytes() != PNG  # drawn again, not the shared picture
    listed = json.loads((gallery / "designs.json").read_text(encoding="utf-8"))
    assert listed == {"designs": [{"id": name, "model": "claude-haiku-5-5", "version": claude_sharing.APP_VERSION}]}
    assert "Jane" not in json.dumps(listed)  # the answer goes nowhere near the gallery
    # The same design again is the same entry; taking it out leaves nothing behind.
    assert tool.publish_one(inbox.extract(record), gallery, draw=inbox.draw) == name
    assert len(json.loads((gallery / "designs.json").read_text(encoding="utf-8"))["designs"]) == 1
    assert tool.main(["unpublish", name, "--gallery", str(gallery)]) == 0
    assert list((gallery / "designs").iterdir()) == []
    assert json.loads((gallery / "designs.json").read_text(encoding="utf-8")) == {"designs": []}
    assert tool.main(["unpublish", "../../etc", "--gallery", str(gallery)]) == 1  # an id only, never a path


def test_publish_refuses_what_the_person_did_not_allow_and_what_a_stranger_could_hide(inbox):
    tool, gallery = inbox.tool, inbox.gallery
    share = lambda design=HOPF, **given: inbox.extract(dict(  # noqa: E731
        claude_sharing.record(["Done."], design, PNG, model="gpt-6.1-terra", new=True, gallery=True), **given))

    def why(folder):
        with pytest.raises(ValueError) as stopped:
            tool.publish_one(folder, gallery, draw=inbox.draw)
        return str(stopped.value)
    assert "did not allow the gallery" in why(share(gallery=False))
    assert "did not allow the gallery" in why(share(gallery="true"))  # a real yes only
    assert "from nothing of theirs" in why(share(new=False))
    assert "from nothing of theirs" in why(share(ok=False))
    assert "not a model name" in why(share(model="<img src=x onerror=alert(1)>"))
    assert "not a version" in why(share(version="2.1 <script>"))
    # Text hidden where a design has none: a strand's field, a field's name, a made-up field.
    hidden = json.loads(json.dumps(HOPF))
    hidden["strands"][0]["arrow_texture"] = "call Jane on 555 0100"
    assert "text that is not part of the format" in why(share(hidden))
    hidden = json.loads(json.dumps(HOPF))
    hidden["strands"][0]["Jane Doe"] = 1
    assert "name that is not part of the format" in why(share(hidden))
    hidden = json.loads(json.dumps(HOPF))
    hidden["note"] = "sk-not-a-layer-name"
    assert "text that is not part of the format" in why(share(hidden))
    # A design the app cannot draw is not shown either, and leaves nothing half made.
    def cannot(design, path):
        raise RuntimeError("no canvas")
    with pytest.raises(RuntimeError):
        tool.publish_one(share(), gallery, draw=cannot)
    assert not (gallery / "designs.json").exists()
    assert not (gallery / "designs").exists() or list((gallery / "designs").iterdir()) == []
    # The command goes on past a share it refuses, and says so.
    assert tool.main(["publish", str(share(gallery=False)), "--gallery", str(gallery)]) == 1


def test_a_stranger_s_share_cannot_swell_on_disk_or_drive_the_terminal(keys, tmp_path, capsys):
    """A design nested very deep would be written with a mile of indentation per number (a
    1 kB share became 100 MB): it is refused. Control characters never reach the terminal
    or the files."""
    import zlib
    sys.path.insert(0, str(ROOT / "scripts"))
    import share_inbox
    private, public = keys
    deep = ('{"format":1,"model":"m","ok":true,"answer":[],"picture":null,"design":{"strands":'
            + "[" * 900 + ",".join("0" * 1 for _ in range(20000)) + "]" * 900 + "}}").encode()
    sealed = claude_sharing.MAGIC + claude_sharing.suite().encrypt(
        zlib.compress(deep, 9), claude_sharing.public_key(public), info=claude_sharing.INFO)
    assert len(sealed) < 2000
    key, bomb = tmp_path / "share.key", tmp_path / "bomb.oss"
    key.write_text(private + "\n", encoding="ascii")
    bomb.write_bytes(sealed)
    assert share_inbox.main(["open", str(bomb), "--key", str(key), "--out", str(tmp_path / "out")]) == 1
    assert "nested more than" in capsys.readouterr().err and not (tmp_path / "out" / "bomb").exists()
    loud = tmp_path / "loud.oss"
    loud.write_bytes(claude_sharing.seal(dict(claude_sharing.record(["\x1b[31mred\x1b[0m\nline two"], HOPF, PNG),
                                              model="gpt\x1b]0;owned\x07" + "x" * 500), public))
    assert share_inbox.main(["open", str(loud), "--key", str(key), "--out", str(tmp_path / "out")]) == 0
    said = capsys.readouterr().out
    assert "\x1b" not in said and "\x07" not in said and len(said) < 400
    answer = (tmp_path / "out" / "loud" / "answer.md").read_bytes()
    assert b"\x1b" not in answer and b"line two" in answer
    assert "\\u001b" not in (tmp_path / "out" / "loud" / "about.json").read_text(encoding="utf-8")
