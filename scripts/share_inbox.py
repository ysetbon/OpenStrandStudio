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

Anyone can send a share (the public key is in the app), so read one as you would a file
from a stranger: it is sealed, not signed.
"""
import argparse
import base64
import getpass
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


def save(record, folder):
    """A share's parts as files you can open: the design, its picture, Claude's answer. Anyone
    can make a share, so each part is written only when it has the shape it should, and text
    that is not valid Unicode is written with a replacement character. The files go in a new
    folder beside folder first, which then takes its place whole: a share that cannot be
    written leaves nothing behind, and never damages a folder an earlier run made."""
    answer = record.get('answer')
    answer = [str(t) for t in answer] if isinstance(answer, list) else []
    design = record.get('design') if isinstance(record.get('design'), dict) else None
    try:
        picture = base64.b64decode(record['picture'], validate=True) if isinstance(record.get('picture'), str) else b''
    except ValueError:
        picture = b''
    about = {k: record.get(k) for k in ('model', 'language', 'ok', 'received')
             if isinstance(record.get(k), (str, bool, type(None)))}
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
        try:
            os.replace(new, folder)
        except OSError:
            if old is not None:
                os.replace(old, folder)
                old = None
            raise
    except BaseException:
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
                print(f'{folder}: {record.get("model")}, {"worked" if record.get("ok") is True else "did not work"}')
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
        print(f'{folder}: {record.get("model")}')
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
    args = parser.parse_args(argv)
    return args.func(args) or 0


if __name__ == '__main__':
    sys.exit(main())
