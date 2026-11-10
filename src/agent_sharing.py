"""Sharing what the model makes with the OpenStrand Studio developer, only when the person
says yes. They are asked once, on a card under the model's first answer; Settings > Models
changes it at any time.

What goes, for each request once the person said yes (until they turn it off), whichever
model answered: the design it made, whole (the person's canvas too, when the model changed
it; never their canvas, a tab or a past step of one that it only read), its picture, the
model's answer, the model, the app's version and language, whether the request worked, and
whether the design was made from nothing of the person's (new). What never
goes: the request the person typed, pictures they gave the agent, their API keys, their files,
folders (every path and every API key in an answer or a design is cut out: the person's own
keys whatever their shape, and any sk-... or xai-... key), an error's text, the time,
anything about the computer or the person. The agent's answer can still repeat words or bare
file names (knot.json) from the request or the canvas: the consent text says so.

How it goes: sealed on this computer with the developer's public key before it leaves
(HPKE, RFC 9180: ML-KEM-768 with X25519, which holds against quantum computers too,
HKDF-SHA256 and ChaCha20-Poly1305), then sent over HTTPS (the certificate checked, TLS
1.2 or newer, no redirect followed) to the developer's Cloudflare Worker
(cloudflare/share-worker), which keeps it as it came. Only the developer's private key,
kept off line, opens it (scripts/share_inbox.py): neither Cloudflare nor anyone who gets
into the Worker or its storage can read it.

Off until the developer sets SHARE_URL and SHARE_PUBLIC_KEY below
(cloudflare/share-worker/README.md says how): the panel and Settings then show nothing.

The public gallery (gallery/, on GitHub Pages) is a second, separate yes, asked only after
the first: a share then says the developer may show its design there (gallery). Only a
design made from nothing of the person's can say so, and the developer still looks at each
one and publishes a cleaned copy by hand (scripts/share_inbox.py publish): the design and
its picture, with the model and the app's version, never the answer. What is in the inbox
stays private either way. Off until the developer sets GALLERY_URL below.
"""
import base64
import json
import os
import re
import urllib.request
import zlib

import agent_settings

# The Worker that receives shares, and the developer's public key (scripts/share_inbox.py keygen).
SHARE_URL = ''  # 'https://openstrand-share.<your-account>.workers.dev/v1/share'
SHARE_PUBLIC_KEY = ''
# Where the public gallery is shown, once it is on GitHub Pages (gallery/README.md).
GALLERY_URL = ''  # 'https://<your-account>.github.io/OpenStrandStudio/'
# This app's version, as its installers say it (src/OpenStrandStudio_mac.spec, src/inno setup):
# change it with them. It goes with each share, so a result can be set against the version.
APP_VERSION = '2.1'

MAGIC = b'OSS1'  # what every sealed share starts with: the format and its version
INFO = b'OpenStrand Studio share v1'  # bound into the encryption: a share opens as nothing else
FORMAT = 1
MAX_BYTES = 8 * 1024 * 1024  # a larger share is not sent (the Worker refuses it too)
# What a share may open up to: anyone can seal one (the public key is in the app), so one
# made to inflate without end (a zip bomb) stops here instead of filling the memory.
MAX_OPENED_BYTES = 64 * 1024 * 1024
MLKEM_PUBLIC, MLKEM_SEED, X25519_SIZE = 1184, 64, 32
TIMEOUT = 20.0

# A folder in a text, never a web address (http:// has a letter before its colon, and /home/
# in one follows a letter). On Windows, C:\... or \\server\share\..., whose folders may have
# spaces (C:\Users\Jane Doe\...; the last part ends at one); elsewhere /Users/..., /home/...
# or ~/..., up to a space.
PATHS = (re.compile(r'(?:(?<!\w)[A-Za-z]:[\\/](?![\\/])|\\\\(?=\w))(?:[^\\/\r\n"\'<>|:*?]+[\\/])*'
                    r'[^\s\\/"\'<>|:*?]*'),
         re.compile(r'(?:(?<![\w.])/(?:Users|home|private|var|tmp|mnt|Volumes)/|(?<!\w)~[\\/])[^\s"\'<>|]*'))
# An API key in a text, as every provider's keys start: sk- (Anthropic sk-ant-, OpenAI sk- and
# sk-proj-, DeepSeek, Kimi, Qwen) or xai- (Grok). Never part of a word (risk-free, ask-me-...).
KEYS = re.compile(r'(?<![\w-])(?:sk|xai)-[A-Za-z0-9_\-]{16,}')
MIN_SECRET = 12  # a saved key shorter than this is cut out by its shape only (never a common word)


def suite():
    from cryptography.hazmat.primitives import hpke
    return hpke.Suite(hpke.KEM.MLKEM768_X25519, hpke.KDF.HKDF_SHA256, hpke.AEAD.CHACHA20_POLY1305)


def available(url=None, key=None):
    """Whether sharing can work here: the developer set the Worker and the key, and this
    Python has what seals a share (the cryptography package, 47 or newer)."""
    url = SHARE_URL if url is None else url
    key = SHARE_PUBLIC_KEY if key is None else key
    if not url or not key or agent_settings.providers is None:
        return False
    try:
        agent_settings.providers.check_url(url, agent_settings.providers.host_of(url))
        public_key(key)
        suite()
    except Exception:  # noqa: BLE001 - not set up, or no cryptography: no sharing
        return False
    return True


def gallery_available(url=None):
    """Whether the gallery can be offered: sharing works here, and the developer said where
    the gallery is (an https address)."""
    url = GALLERY_URL if url is None else url
    return str(url).startswith('https://') and available()


# ---------------------------------------------------------------------- keys
def _decode(text, size, what):
    try:
        raw = base64.b64decode(''.join(str(text).split()), validate=True)
    except ValueError:
        raise ValueError(f'the {what} is not base64') from None
    if len(raw) != size:
        raise ValueError(f'the {what} has {len(raw)} bytes, not {size}')
    return raw


def public_key(text):
    """The developer's public key from its base64 (ML-KEM-768's, then X25519's)."""
    from cryptography.hazmat.primitives import hpke
    from cryptography.hazmat.primitives.asymmetric import mlkem, x25519
    raw = _decode(text, MLKEM_PUBLIC + X25519_SIZE, 'public key')
    return hpke.MLKEM768X25519PublicKey(mlkem.MLKEM768PublicKey.from_public_bytes(raw[:MLKEM_PUBLIC]),
                                        x25519.X25519PublicKey.from_public_bytes(raw[MLKEM_PUBLIC:]))


def private_key(text):
    """The developer's private key from its base64 (ML-KEM-768's seed, then X25519's)."""
    from cryptography.hazmat.primitives import hpke
    from cryptography.hazmat.primitives.asymmetric import mlkem, x25519
    raw = _decode(text, MLKEM_SEED + X25519_SIZE, 'private key')
    return hpke.MLKEM768X25519PrivateKey(mlkem.MLKEM768PrivateKey.from_seed_bytes(raw[:MLKEM_SEED]),
                                         x25519.X25519PrivateKey.from_private_bytes(raw[MLKEM_SEED:]))


def new_keys():
    """(private, public): a new key pair, each as base64."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import mlkem, x25519
    kem, dh = mlkem.MLKEM768PrivateKey.generate(), x25519.X25519PrivateKey.generate()
    raw = serialization.Encoding.Raw, serialization.PublicFormat.Raw
    private = kem.private_bytes_raw() + dh.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                                                         serialization.NoEncryption())
    public = kem.public_key().public_bytes_raw() + dh.public_key().public_bytes(*raw)
    return base64.b64encode(private).decode('ascii'), base64.b64encode(public).decode('ascii')


# ------------------------------------------------------------- what is shared
def _home():
    """This computer's home folder, in any slash and case: it holds the person's user name,
    which may have spaces, so it goes first, whole."""
    home = os.path.expanduser('~').rstrip('\\/')
    if len(home) < 4:
        return None
    parts = [re.escape(p) for p in re.split(r'[\\/]+', home) if p]
    prefix = '' if re.match(r'^[A-Za-z]:', home) else r'[\\/]'
    return re.compile(r'(?<![\w.])' + prefix + r'[\\/]+'.join(parts) + r'(?![\w.-])', re.IGNORECASE)


def scrub(value, secrets=()):
    """value with every folder path and API key cut out of its texts, its dictionaries' keys
    included, whatever its shape. secrets: the person's own keys (agent_settings.own_keys),
    cut out whatever their shape."""
    if isinstance(value, str):
        for secret in secrets:
            value = value.replace(secret, '…')
        value = KEYS.sub('…', value)
        home = _home()
        value = home.sub('~', value) if home else value
        for path in PATHS:
            value = path.sub('…', value)
        return value
    if isinstance(value, list):
        return [scrub(v, secrets) for v in value]
    if isinstance(value, dict):  # its keys too (a design's group names are keys): none merged
        out = {}
        for k, v in value.items():
            key = scrub(k, secrets) if isinstance(k, str) else k
            base, n = key, 2
            while key in out:  # two keys that differ only in what was cut out: both kept
                key, n = f'{base} ({n})', n + 1
            out[key] = scrub(v, secrets)
        return out
    return value


def record(answer, design=None, picture=None, model='', language='', ok=True, secrets=(), new=False,
           gallery=False):
    """One share: the model's answer (its texts, in order), the design it made (a project dict)
    and its picture (PNG bytes), the model, the app's version and language, whether the request
    worked (not why not: an error's text can hold the person's own settings, a spending limit).
    secrets: the person's API keys, cut out of the answer and the design like any key.
    new: the design was made from nothing of the person's. gallery: the person allows their new
    designs in the public gallery; a share only says so for a design that is new and worked."""
    secrets = sorted({str(s).strip() for s in secrets or () if len(str(s or '').strip()) >= MIN_SECRET},
                     key=len, reverse=True)  # a longer key first, should one hold another
    made = isinstance(design, dict)
    return {'format': FORMAT, 'model': str(model or ''), 'language': str(language or ''), 'ok': bool(ok),
            'version': APP_VERSION, 'new': bool(new) and made,
            'gallery': bool(gallery) and bool(new) and bool(ok) and made,
            'answer': scrub([str(t) for t in answer or [] if str(t).strip()], secrets),
            'design': scrub(design, secrets) if made else None,
            'picture': base64.b64encode(picture).decode('ascii') if picture else None}


def seal(rec, key=None):
    """The record, compressed, then encrypted to the developer's public key."""
    data = zlib.compress(json.dumps(rec, separators=(',', ':')).encode('utf-8'), 9)
    sealed = MAGIC + suite().encrypt(data, public_key(SHARE_PUBLIC_KEY if key is None else key), info=INFO)
    if len(sealed) > MAX_BYTES:
        raise ValueError(f'too large to share ({len(sealed)} bytes)')
    return sealed


def unseal(sealed, key):
    """The record a sealed share holds (key: the private key's base64). Anyone can seal a
    share, so what opens is checked: no more than MAX_OPENED_BYTES, and a record (a dict)."""
    if not sealed.startswith(MAGIC):
        raise ValueError('not an OpenStrand Studio share')
    data = suite().decrypt(sealed[len(MAGIC):], private_key(key), info=INFO)
    inflate = zlib.decompressobj()
    raw = inflate.decompress(data, MAX_OPENED_BYTES + 1)
    if len(raw) > MAX_OPENED_BYTES or inflate.unconsumed_tail:
        raise ValueError(f'the share opens to more than {MAX_OPENED_BYTES} bytes')
    opened = json.loads(raw.decode('utf-8'))
    if not isinstance(opened, dict):
        raise ValueError('not an OpenStrand Studio share record')
    return opened


def send(sealed, url=None, timeout=TIMEOUT):
    """POST a sealed share to the Worker over HTTPS; its HTTP status (2xx: kept)."""
    providers = agent_settings.providers
    providers.check_allowed(None)  # AI models turned off (Settings > Models): nothing is shared either
    url = SHARE_URL if url is None else url
    request = urllib.request.Request(url, data=sealed, method='POST',
                                     headers={'Content-Type': 'application/octet-stream',
                                              'User-Agent': 'OpenStrandStudio-share/1'})
    with providers.open_url(request, providers.host_of(url), timeout) as answer:
        return answer.status
