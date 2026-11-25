"""Links to pictures in a request (openstrand/links.py): downloaded before the model is
asked, so a picture pasted as its address reaches any model that sees pictures, not only
Claude, which alone has web tools."""
import http.server
import os
import sys
import tempfile
import threading
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("APPDATA", tempfile.mkdtemp(prefix="oss_links_test_"))
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from openstrand import agent, links  # noqa: E402
from test_agent import ScriptedClient, picture, reply, text  # noqa: E402


@pytest.fixture
def site(tmp_path, monkeypatch):
    """A local web server: /knot.png a picture, /knot.jpg? a JPEG with a query, /page an HTML
    page, /fake.png a page served as a PNG, /missing a 404. Yields its address."""
    for name in ("no_proxy", "NO_PROXY"):  # never through a proxy the machine is set up with
        monkeypatch.setenv(name, "127.0.0.1,localhost")
    png = Path(picture(tmp_path / "served.png")).read_bytes()
    jpg = Path(picture(tmp_path / "served.jpg")).read_bytes()
    files = {
        "/knot.png": ("image/png", png),
        "/knot.jpg": ("image/jpeg", jpg),
        "/page": ("text/html; charset=utf-8", b"<html><body>a prusik hitch</body></html>"),
        "/fake.png": ("image/png", b"<html>not really</html>"),
    }

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            kind, body = files.get(self.path.split("?")[0], (None, None))
            if body is None:
                self.send_error(404, "Not Found")
                return
            self.send_response(200)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


def test_links_are_found_in_the_words_without_the_sentence_around_them():
    url = ("https://media.istockphoto.com/id/2162114412/vector/prusik-hitch.jpg"
           "?s=1024x1024&w=is&k=20&c=-soMgYSw9dqGvpxdBystGEhjyxnHsJ485A13R-5XDas=")
    assert links.find_links(f" {url} can you draw me this in a new tab? ") == [url]
    assert links.find_links("see (https://a.example/x.png), and https://a.example/x.png.") == \
        ["https://a.example/x.png"]
    assert links.find_links("no link here, nor ftp://a.example/x.png") == []
    many = " ".join(f"https://a.example/{n}.png" for n in range(9))
    assert len(links.find_links(many)) == links.MAX_LINKS


def test_a_picture_is_told_by_its_first_bytes():
    assert links.picture_kind(b"\x89PNG\r\n\x1a\n....") == "png"
    assert links.picture_kind(b"\xff\xd8\xff\xe0") == "jpg"
    assert links.picture_kind(b"GIF89a") == "gif"
    assert links.picture_kind(b"RIFF\x00\x00\x00\x00WEBPVP8 ") == "webp"
    assert links.picture_kind(b"<!doctype html>") is None


def test_only_pictures_are_downloaded(site, tmp_path, monkeypatch):
    got = links.fetch_picture(f"{site}/knot.png", tmp_path / "out", "link_1")
    assert got == tmp_path / "out" / "link_1.png" and got.read_bytes()[:4] == b"\x89PNG"
    got = links.fetch_picture(f"{site}/knot.jpg?s=1024x1024&k=20", tmp_path / "out", "link_2")
    assert got.name == "link_2.jpg"  # its kind from its bytes, not from the address
    with pytest.raises(links.LinkError, match="a web page, not a PNG"):
        links.fetch_picture(f"{site}/page", tmp_path / "out", "x")
    with pytest.raises(links.LinkError, match="not a PNG"):  # what the server says is not enough
        links.fetch_picture(f"{site}/fake.png", tmp_path / "out", "x")
    with pytest.raises(links.LinkError, match="answered 404"):
        links.fetch_picture(f"{site}/missing", tmp_path / "out", "x")
    with pytest.raises(links.LinkError, match="only http and https"):
        links.fetch_picture("file:///etc/passwd", tmp_path / "out", "x")
    monkeypatch.setattr(links, "MAX_BYTES", 10)
    with pytest.raises(links.LinkError, match="larger than"):
        links.fetch_picture(f"{site}/knot.png", tmp_path / "out", "x")
    assert sorted(p.name for p in (tmp_path / "out").iterdir()) == ["link_1.png", "link_2.jpg"]


def test_a_model_without_web_tools_sees_the_picture_a_link_points_to(site, tmp_path):
    """Gemini has no web tools: the picture at the link is downloaded and sent as a reference
    image, after the attached ones, and the request says which link it came from. The panel
    hears of it as a Reading step with the picture."""
    events = []
    client = ScriptedClient([reply(text("A prusik hitch."), stop="end_turn")])
    attached = picture(tmp_path / "mine.png")
    runner = agent.Agent(client, tmp_path / "run", model="gemini-4-neon", on_event=events.append)
    assert runner.web is False
    runner.run(f"{site}/knot.png can you draw me this in a new tab?", images=[attached])
    content = client.calls[0][1]["messages"][0]["content"]
    assert [b["type"] for b in content] == ["image", "image", "text"]
    assert f"- {site}/knot.png: the app downloaded this picture; it is reference image 2" in content[-1]["text"]
    assert (tmp_path / "run" / "link_1.png").is_file()
    fetch = [e for e in events if e.get("name") == "web_fetch"]
    assert [e["type"] for e in fetch] == ["search", "search_result"]
    assert fetch[0]["query"] == f"{site}/knot.png"
    assert fetch[1]["ok"] and fetch[1]["image"] == str(tmp_path / "run" / "link_1.png")
    assert fetch[1]["pages"][0]["url"] == f"{site}/knot.png"


def test_a_link_that_gives_no_picture_is_said_to_the_model_and_the_person(site, tmp_path):
    """Without web tools a page link cannot be read: the model is told not to pretend it saw
    it, and a note tells the person to attach the picture. With web tools (Claude) the page
    is left to web_fetch and nothing is added."""
    events = []
    client = ScriptedClient([reply(text("Which knot?"), stop="end_turn")])
    agent.Agent(client, tmp_path / "a", model="gemini-4-neon", on_event=events.append).run(f"draw {site}/page")
    content = client.calls[0][1]["messages"][0]["content"]
    assert [b["type"] for b in content] == ["text"]
    assert "could not be used (it is a web page" in content[0]["text"] and "Image button" in content[0]["text"]
    assert any(e["type"] == "note" and "attach it with the Image button" in e["text"] for e in events)

    events = []
    client = ScriptedClient([reply(text("Reading it."), stop="end_turn")])
    agent.Agent(client, tmp_path / "b", model="claude-sonnet-5-5", on_event=events.append).run(f"draw {site}/page")
    content = client.calls[0][1]["messages"][0]["content"]
    assert content[-1]["text"] == f"draw {site}/page"  # web_fetch reads it
    assert not any(e["type"] == "note" for e in events)

    # A request with no link is sent as it was.
    client = ScriptedClient([reply(text("A knot."), stop="end_turn")])
    agent.Agent(client, tmp_path / "c", model="gemini-4-neon").run("an overhand knot")
    assert client.calls[0][1]["messages"][0]["content"] == [{"type": "text", "text": "an overhand knot"}]


def test_links_never_push_past_the_models_number_of_pictures(site, tmp_path):
    from openstrand import providers
    limit = providers.image_limit("claude-haiku-5-5")
    attached = [picture(tmp_path / f"v{n}.png") for n in range(limit)]
    client = ScriptedClient([reply(text("A knot."), stop="end_turn")])
    agent.Agent(client, tmp_path / "run", model="claude-haiku-5-5").run(f"like {site}/knot.png", images=attached)
    content = client.calls[0][1]["messages"][0]["content"]
    assert sum(b["type"] == "image" for b in content) == limit
    assert not (tmp_path / "run" / "link_1.png").exists()
