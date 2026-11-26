"""Links to pictures in a request: downloaded before the model is asked, so a
picture pasted as its address (a browser's "Copy image address") reaches the
model as a reference image, whatever the model. Only Claude has web tools
(agent.WEB_TOOLS); for any other model a link was just words.

Only http and https, only PNG, JPEG, GIF and WebP (told by the file's first
bytes, not by what the server says), at most MAX_BYTES, within TIMEOUT.
"""
import re
import urllib.error
import urllib.request
from pathlib import Path

MAX_BYTES = 20 * 1024 * 1024  # a 1024 px stock picture is under 1 MB; a phone's photo under 15
TIMEOUT = 20  # seconds, for the connection and for each read
MAX_LINKS = 4  # links tried from one request: a pasted list of pages is not read one by one
# Some picture hosts refuse Python's own name for itself.
USER_AGENT = 'Mozilla/5.0 (compatible; OpenStrandStudio)'

# A link runs to the first space, quote or bracket; a full stop or comma after it is the sentence's.
LINK = re.compile(r'https?://[^\s<>"\'\[\]{}|\\^`]+', re.IGNORECASE)


class LinkError(Exception):
    """Why a link gave no picture, in words for the person."""


def find_links(text, most=MAX_LINKS):
    """The http(s) links in text, in order, each once, at most most of them."""
    found = []
    for match in LINK.finditer(text or ''):
        url = match.group(0).rstrip('.,;:!?)')
        if url not in found:
            found.append(url)
    return found[:most]


def picture_kind(head):
    """'png', 'jpg', 'gif' or 'webp' from a file's first bytes; None for anything else."""
    if head.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    if head.startswith(b'\xff\xd8\xff'):
        return 'jpg'
    if head[:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'
    if head[:4] == b'RIFF' and head[8:12] == b'WEBP':
        return 'webp'
    return None


def fetch_picture(url, folder, name, opener=None):
    """Download the picture at url into folder as name.<png|jpg|gif|webp>; its Path.
    Raises LinkError when it is not reachable, too large, or not a picture (a web page)."""
    if not re.match(r'https?://', url, re.IGNORECASE):
        raise LinkError('only http and https links can be downloaded')
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'image/*,*/*;q=0.5'})
    open_ = opener or urllib.request.urlopen
    try:
        with open_(request, timeout=TIMEOUT) as response:
            length = response.headers.get('Content-Length')
            if length and length.isdigit() and int(length) > MAX_BYTES:
                raise LinkError(f'the file is larger than {MAX_BYTES // (1024 * 1024)} MB')
            data = response.read(MAX_BYTES + 1)
            served = (response.headers.get('Content-Type') or '').split(';')[0].strip()
    except LinkError:
        raise
    except urllib.error.HTTPError as e:
        raise LinkError(f'the site answered {e.code} {e.reason}') from None
    except urllib.error.URLError as e:
        raise LinkError(f'cannot reach it ({e.reason})') from None
    except (OSError, ValueError) as e:  # a timeout, a reset connection, a malformed link
        raise LinkError(f'cannot download it ({e})') from None
    if len(data) > MAX_BYTES:
        raise LinkError(f'the file is larger than {MAX_BYTES // (1024 * 1024)} MB')
    kind = picture_kind(data[:16])
    if kind is None:
        what = 'a web page' if served.startswith('text/html') else (served or 'not a picture')
        raise LinkError(f'it is {what}, not a PNG, JPEG, GIF or WebP picture')
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f'{name}.{kind}'
    path.write_bytes(data)
    return path
