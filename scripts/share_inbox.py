"""Read what people chose to share with you from OpenStrand Studio (src/claude_sharing.py).

  python scripts/share_inbox.py keygen [--key FILE]
      Make your key pair. The private key goes in FILE (default ~/.openstrand-share.key),
      readable by you alone: keep it off line and backed up, never in the repository or
      anywhere online. The public key is printed, for SHARE_PUBLIC_KEY in
      src/claude_sharing.py.

  python scripts/share_inbox.py fetch --url https://openstrand-share.<account>.workers.dev
      Download the sealed shares your Worker keeps, open each with your private key, and
      save it in a folder of its own under --out (default shared/): design.json (opens in
      OpenStrand Studio), design.png, answer.md and about.json. The inbox token is read
      from OPENSTRAND_INBOX_TOKEN, else asked for (never on the command line, where the
      shell would keep it). --delete removes each share from the Worker once it is saved.

  python scripts/share_inbox.py open FILE.oss [FILE.oss ...]
      Open shares downloaded some other way (from the Cloudflare dashboard).

  python scripts/share_inbox.py publish shared/2026-11-10_1a2b3c4d [...]
      Put a share's design in the public gallery (gallery/, shown on GitHub Pages), once you
      have looked at it. Only a share whose sender allowed the gallery, and whose design the
      model made from nothing of theirs. What goes in is a cleaned copy, never the share
      itself: the design with its groups renamed and nothing in it but numbers, layer names
      and the format's own words, a picture drawn again from that copy, the model and the
      app's version. Never the answer. Commit and push gallery/ to show it.

  python scripts/share_inbox.py unpublish ID [...]
      Take a design out of the gallery again (its id is its file's name there).

Anyone can send a share (the public key is in the app), so read one as you would a file
from a stranger: it is sealed, not signed.
"""
import argparse
import base64
import getpass
import hashlib
import json
import os
import re
import secrets
import shutil
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import claude_sharing  # noqa: E402

DEFAULT_KEY = Path.home() / '.openstrand-share.key'
PNG = b'\x89PNG\r\n\x1a\n'
# A share's name in the Worker's bucket (cloudflare/share-worker/src/index.js): its day, its id.
NAME = re.compile(r'^shares/(\d{4}-\d{2}-\d{2})/([0-9a-f]{8})-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.oss$')
# A share is a stranger's: these bound what one can make this tool do.
MAX_NESTING = 32  # a real design is under 10 deep; written indented, a deeper one grows without end
MAX_GALLERY_BYTES = 5 * 1024 * 1024  # a design.json larger than this is not read for the gallery
MAX_STRANDS = 5000
# What a design in the gallery may hold besides numbers, true and false: layer names (1_2,
# 1_2_3_1; a set number alone, as a key) and the words of the format itself.
LAYER = re.compile(r'^\d{1,4}(_\d{1,4}){0,7}$')
FIELD = re.compile(r'^[a-z][a-z0-9_]{0,39}$')
WORDS = {'Strand', 'AttachedStrand', 'MaskedStrand', 'none', 'solid', 'stripes', 'dots', 'crosshatch', 'tiles'}
MODEL = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$')
VERSION = re.compile(r'^[0-9][0-9A-Za-z._-]{0,15}$')
GALLERY_ID = re.compile(r'^[0-9a-f]{12}$')
HEADER = ('# OpenStrand Studio share key: PRIVATE. It opens every share sent to you.\n'
          '# Keep it off line and backed up; never commit it, upload it or send it.\n')


def read_key(path):
    try:
        lines = Path(path).expanduser().read_text(encoding='ascii').splitlines()
    except OSError as e:
        raise SystemExit(f'cannot read the private key: {e}')
    return ''.join(line.strip() for line in lines if line.strip() and not line.startswith('#'))


def keygen(args):
    path = Path(args.key).expanduser()
    private, public = claude_sharing.new_keys()
    try:  # created for its owner alone, and never over a key that exists
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise SystemExit(f'{path} exists already: a new key would make every share sent to the old one '
                         'unreadable. Use --key for another file.')
    with os.fdopen(fd, 'w', encoding='ascii') as f:
        f.write(HEADER + private + '\n')
    print(f'Private key: {path} (only you can read it: keep it off line and backed up).\n')
    print('Public key, for SHARE_PUBLIC_KEY in src/claude_sharing.py:\n')
    print(public)


def plain(text, limit=None):
    """text as it is safe to print or keep: no control characters (a stranger's text could
    otherwise drive the terminal it is shown in), cut to limit characters."""
    keep = lambda c: c in '\n\t' or '\ud800' <= c <= '\udfff' or (c.isprintable() and c not in '\u2028\u2029')  # noqa: E731
    text = ''.join(c if keep(c) else '\ufffd' for c in str(text))  # (a lone surrogate is written as ?)
    return text if limit is None or len(text) <= limit else text[:limit] + '…'


def nesting(value, limit=MAX_NESTING):
    """How deep value's lists and dictionaries go, counted no further than limit + 1."""
    deepest, stack = 0, [(value, 1)]
    while stack:
        item, depth = stack.pop()
        if isinstance(item, (dict, list)):
            deepest = max(deepest, depth)
            if depth > limit:
                break
            stack.extend((child, depth + 1) for child in (item.values() if isinstance(item, dict) else item))
    return deepest


def save(record, folder):
    """A share's parts as files you can open: the design, its picture, Claude's answer. Anyone
    can make a share, so each part is written only when it has the shape it should, and text
    that is not valid Unicode is written with a replacement character. The files go in a new
    folder beside folder first, which then takes its place whole: a share that cannot be
    written leaves nothing behind, and never damages a folder an earlier run made."""
    answer = record.get('answer')
    answer = [plain(t) for t in answer] if isinstance(answer, list) else []
    design = record.get('design') if isinstance(record.get('design'), dict) else None
    if design is not None and nesting(design) > MAX_NESTING:
        raise ValueError(f'its design is nested more than {MAX_NESTING} deep: not a design')
    try:
        picture = base64.b64decode(record['picture'], validate=True) if isinstance(record.get('picture'), str) else b''
    except ValueError:
        picture = b''
    about = {k: plain(record[k], 200) if isinstance(record[k], str) else record[k]
             for k in ('model', 'language', 'version', 'ok', 'new', 'gallery', 'received')
             if isinstance(record.get(k), (str, bool))}
    folder = Path(folder)
    folder.parent.mkdir(parents=True, exist_ok=True)
    new = Path(tempfile.mkdtemp(prefix=f'.{folder.name}-', dir=folder.parent))
    old = None
    try:
        text = {'encoding': 'utf-8', 'errors': 'replace'}  # a lone surrogate is valid JSON, not UTF-8
        (new / 'about.json').write_text(json.dumps(about, indent=2, ensure_ascii=False), **text)
        (new / 'answer.md').write_text('\n\n'.join(answer) + '\n', **text)
        if design is not None:
            (new / 'design.json').write_text(json.dumps(design, indent=2, ensure_ascii=False), **text)
        if picture.startswith(PNG):  # only a real PNG is written as one
            (new / 'design.png').write_bytes(picture)
        if folder.exists():  # an earlier extract of the same name: set aside until this one is in place
            old = folder.with_name(f'.{folder.name}-old-{secrets.token_hex(4)}')
            os.replace(folder, old)
        os.replace(new, folder)
    except BaseException:  # anything at all, Ctrl+C included: the earlier extract goes back in its place
        if old is not None and old.exists() and not folder.exists():
            try:
                os.replace(old, folder)
            except OSError:
                pass  # left where it is, under its dotted name: never removed
        shutil.rmtree(new, ignore_errors=True)
        raise
    if old is not None:
        shutil.rmtree(old, ignore_errors=True)


def call(url, token, method='GET'):
    request = urllib.request.Request(url, method=method, headers={'Authorization': f'Bearer {token}',
                                                                  'User-Agent': 'OpenStrandStudio-inbox/1'})
    providers = claude_sharing.claude_settings.providers
    try:
        with providers.open_url(request, providers.host_of(url), 60.0) as answer:
            return answer.read()
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise SystemExit('the Worker refused the inbox token: check OPENSTRAND_INBOX_TOKEN') from None
        if e.code == 404 and urllib.parse.urlsplit(url).path == '/v1/inbox':
            raise SystemExit('the Worker has no inbox: set its INBOX_TOKEN (cloudflare/share-worker/README.md)') from None
        raise


def fetch(args):
    key = read_key(args.key)
    token = os.environ.get('OPENSTRAND_INBOX_TOKEN') or getpass.getpass('Inbox token: ')
    base = args.url.rstrip('/')
    out = Path(args.out)
    saved = skipped = failed = 0
    cursor = None
    while True:
        query = f'?cursor={urllib.parse.quote(cursor)}' if cursor else ''
        listed = json.loads(call(f'{base}/v1/inbox{query}', token))
        for share in listed.get('shares') or []:
            found = NAME.match(str(share.get('key') or ''))  # shares/2026-11-09/<uuid>.oss
            if not found:
                print(f'{share.get("key")!r}: not a share, left alone', file=sys.stderr)
                failed += 1
                continue
            name = found.group(0)
            folder = out / f'{found.group(1)}_{found.group(2)}'
            if folder.exists():
                skipped += 1
            else:
                address = f'{base}/v1/inbox/{urllib.parse.quote(name, safe="")}'
                try:  # one bad share (anyone can make one) does not stop the rest; save leaves no half one
                    record = claude_sharing.unseal(call(address, token), key)
                    save(dict(record, received=share.get('uploaded')), folder)
                except Exception as e:  # noqa: BLE001
                    print(f'{name}: cannot open it ({type(e).__name__}: {e})', file=sys.stderr)
                    failed += 1
                    continue
                saved += 1
                print(f'{folder}: {plain(record.get("model"), 80)}, '
                      f'{"worked" if record.get("ok") is True else "did not work"}'
                      f'{", allowed in the gallery" if record.get("gallery") is True else ""}')
            if args.delete:
                call(f'{base}/v1/inbox/{urllib.parse.quote(name, safe="")}', token, method='DELETE')
        cursor = listed.get('cursor')
        if not cursor:
            break
    print(f'{saved} new, {skipped} already here, {failed} could not be opened; in {out.resolve()}')
    return 1 if failed else 0


def open_files(args):
    key = read_key(args.key)
    failed = 0
    for path in args.files:
        folder = Path(args.out) / Path(path).stem
        try:  # a share that cannot be opened or written leaves an earlier folder of its name as it was
            record = claude_sharing.unseal(Path(path).read_bytes(), key)
            save(record, folder)
        except Exception as e:  # noqa: BLE001
            print(f'{path}: cannot open it ({type(e).__name__}: {e})', file=sys.stderr)
            failed += 1
            continue
        print(f'{folder}: {plain(record.get("model"), 80)}')
    return 1 if failed else 0


# ------------------------------------------------------------- the public gallery
def gallery_copy(design):
    """The copy of a shared design that may be shown in public: its groups renamed (a name is
    the one text a person types into a design), and nothing else in it but numbers, true,
    false, layer names and the format's own words. Anything else stops it (ValueError), and
    says what, so it is looked at instead of shown."""
    if not isinstance(design, dict) or not isinstance(design.get('strands'), list) or not design['strands']:
        raise ValueError('it holds no design')
    if len(design['strands']) > MAX_STRANDS or nesting(design) > MAX_NESTING:
        raise ValueError('it is too large or too deeply nested to be a design')

    def copy(value, where):
        if value is None or isinstance(value, (bool, int)):
            return value
        if isinstance(value, float):
            if value != value or value in (float('inf'), float('-inf')):
                raise ValueError(f'{where} is not a number')
            return value
        if isinstance(value, str):
            if not (LAYER.match(value) or value in WORDS):
                raise ValueError(f'{where} holds text that is not part of the format: {plain(value, 60)!r}')
            return value
        if isinstance(value, list):
            return [copy(v, f'{where}[{i}]') for i, v in enumerate(value)]
        if isinstance(value, dict):
            out = {}
            for key, v in value.items():
                if not isinstance(key, str) or not (LAYER.match(key) or FIELD.match(key)):
                    raise ValueError(f'{where} has a name that is not part of the format: {plain(key, 60)!r}')
                out[key] = copy(v, f'{where}.{key}')
            return out
        raise ValueError(f'{where} is not part of the format')

    groups = design.get('groups')
    if not isinstance(groups, (dict, type(None))):
        raise ValueError('its groups are not groups')
    cleaned = copy({k: v for k, v in design.items() if k != 'groups'}, 'the design')
    cleaned['groups'] = {f'Group {n}': copy(group, f'group {n}')
                         for n, group in enumerate((groups or {}).values(), start=1)}
    return cleaned


def draw(design, path):
    """The design's picture, drawn by the app's own canvas (openstrand.render)."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from openstrand import render
    render.render(design, path)


def read_gallery(gallery):
    """The gallery's list (gallery/designs.json): [{'id', 'model', 'version'}], oldest first."""
    try:
        listed = json.loads((gallery / 'designs.json').read_text(encoding='utf-8')).get('designs')
    except FileNotFoundError:
        return []
    return [d for d in listed or [] if isinstance(d, dict) and GALLERY_ID.match(str(d.get('id') or ''))]


def write_gallery(gallery, designs):
    gallery.mkdir(parents=True, exist_ok=True)
    new = gallery / '.designs.json.new'
    new.write_text(json.dumps({'designs': designs}, indent=1) + '\n', encoding='utf-8')
    os.replace(new, gallery / 'designs.json')


def publish_one(folder, gallery, draw=draw):
    """Put the share extracted in folder into the gallery; the id it has there."""
    folder = Path(folder)
    try:
        about = json.loads((folder / 'about.json').read_text(encoding='utf-8'))
        if (folder / 'design.json').stat().st_size > MAX_GALLERY_BYTES:
            raise ValueError('its design is too large for the gallery')
        design = json.loads((folder / 'design.json').read_text(encoding='utf-8'))
    except FileNotFoundError:
        raise ValueError('no share with a design here (about.json and design.json)') from None
    if not isinstance(about, dict) or about.get('gallery') is not True:
        raise ValueError('its sender did not allow the gallery: it stays private')
    if about.get('new') is not True or about.get('ok') is not True:
        raise ValueError('not a design the model made from nothing of theirs, in a request that worked')
    model, version = about.get('model'), about.get('version')
    if not isinstance(model, str) or not MODEL.match(model):
        raise ValueError('its model is not a model name')
    if not isinstance(version, str) or not VERSION.match(version):
        raise ValueError('its app version is not a version')
    cleaned = gallery_copy(design)
    text = json.dumps(cleaned, separators=(',', ':'), sort_keys=True)
    name = hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]
    designs = gallery / 'designs'
    designs.mkdir(parents=True, exist_ok=True)
    picture = designs / f'.{name}.new.png'  # (the canvas saves by the file's ending)
    try:  # the picture first: a design the app cannot draw is not shown at all
        draw(cleaned, picture)
        if not picture.read_bytes().startswith(PNG):
            raise ValueError('the app could not draw it')
        os.replace(picture, designs / f'{name}.png')
    finally:
        picture.unlink(missing_ok=True)
    (designs / f'{name}.json').write_text(text + '\n', encoding='utf-8')
    listed = [d for d in read_gallery(gallery) if d['id'] != name]
    write_gallery(gallery, listed + [{'id': name, 'model': model, 'version': version}])
    return name


def publish(args):
    gallery, failed = Path(args.gallery), 0
    for folder in args.folders:
        try:
            name = publish_one(folder, gallery)
        except Exception as e:  # noqa: BLE001 - a stranger's share: say why, go on with the rest
            print(f'{folder}: not published ({plain(e, 300) or type(e).__name__})', file=sys.stderr)
            failed += 1
            continue
        print(f'{folder}: in the gallery as {gallery / "designs" / (name + ".png")}')
    print(f'Look at each picture, then commit and push {gallery}/ to show them '
          f'(or take one out again: unpublish ID).')
    return 1 if failed else 0


def unpublish(args):
    gallery, failed = Path(args.gallery), 0
    for name in args.ids:
        if not GALLERY_ID.match(name):
            print(f'{plain(name, 40)!r}: not a gallery id (12 hex characters)', file=sys.stderr)
            failed += 1
            continue
        listed = read_gallery(gallery)
        write_gallery(gallery, [d for d in listed if d['id'] != name])
        for file in (gallery / 'designs' / f'{name}.json', gallery / 'designs' / f'{name}.png'):
            file.unlink(missing_ok=True)
        print(f'{name}: out of the gallery (commit and push {gallery}/)')
    return 1 if failed else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description='Read what people shared with you from OpenStrand Studio.')
    commands = parser.add_subparsers(dest='command', required=True)
    make = commands.add_parser('keygen', help='make your key pair')
    make.add_argument('--key', default=str(DEFAULT_KEY), help='where to write the private key')
    make.set_defaults(func=keygen)
    get = commands.add_parser('fetch', help="download and open what your Worker keeps")
    get.add_argument('--url', required=True, help='your Worker, e.g. https://openstrand-share.<account>.workers.dev')
    get.add_argument('--key', default=str(DEFAULT_KEY), help='your private key file')
    get.add_argument('--out', default='shared', help='where to save the shares (default: shared/)')
    get.add_argument('--delete', action='store_true', help='remove each share from the Worker once saved here')
    get.set_defaults(func=fetch)
    opener = commands.add_parser('open', help='open .oss files downloaded another way')
    opener.add_argument('files', nargs='+')
    opener.add_argument('--key', default=str(DEFAULT_KEY), help='your private key file')
    opener.add_argument('--out', default='shared', help='where to save them (default: shared/)')
    opener.set_defaults(func=open_files)
    show = commands.add_parser('publish', help='put shares you have looked at in the public gallery')
    show.add_argument('folders', nargs='+', help='folders that fetch or open made, e.g. shared/2026-11-10_1a2b3c4d')
    show.add_argument('--gallery', default=str(ROOT / 'gallery'), help='the gallery folder (default: gallery/)')
    show.set_defaults(func=publish)
    hide = commands.add_parser('unpublish', help='take designs out of the gallery again')
    hide.add_argument('ids', nargs='+', help="a design's id: its file's name in gallery/designs/")
    hide.add_argument('--gallery', default=str(ROOT / 'gallery'), help='the gallery folder (default: gallery/)')
    hide.set_defaults(func=unpublish)
    args = parser.parse_args(argv)
    return args.func(args) or 0


if __name__ == '__main__':
    sys.exit(main())
