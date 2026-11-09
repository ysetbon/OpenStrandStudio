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
    record = claude_sharing.record(texts, {"strands": [], "note": "/Users/jane/x.png"}, None,
                                   error=r"cannot open D:\work\jane\a.json")
    said = json.dumps(record)
    for private in (home, "Jane Doe", "Documents", "/home/jane", "/Users/jane", "Desktop", "server\\\\share",
                    "D:\\\\work"):
        assert private not in said, private
    assert "https://www.animatedknots.com/home/figure-8" in said and "http://example.org/Users/x" in said
    assert record["design"]["note"] == "…" and record["picture"] is None
    assert set(record) == {"format", "model", "language", "ok", "error", "answer", "design",
                           "picture"}  # nothing else: not the request, the time, the computer or the person


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
