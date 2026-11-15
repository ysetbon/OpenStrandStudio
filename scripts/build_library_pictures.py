"""Make the craft library's pictures: one small picture of every entry, in craft_library/pictures/.

Run from any directory: python scripts/build_library_pictures.py [--only NAME ...]

A search for a design (the agent's search_samples) shows the designs it found side by
side. Most library entries are knots the agent ties when it loads them, so they have no
file to picture; this builds each one once, as load_sample or tie_knot would, and keeps
its picture: the finished knot, drawn by the app's own canvas, at most SIDE px.
Run it again after adding or changing an entry. If a run stops part way (a knot that
takes too long can stop it while the app's own code runs), --missing makes the rest.
"""
import argparse
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]

SIDE = 320  # px, the longer side: the search row shows it at 132 x 78, larger under the mouse
LIMIT = 90  # seconds for one entry: a knot whose tying runs longer is left without a picture


def build(workspace, entry):
    """The entry built in workspace, as the agent would build it."""
    kind, value = next(iter(entry['build'].items()))
    if kind == 'tie':
        workspace.run('tie_knot', {'knot': value})
    elif kind == 'make' and value == 'mxn':  # a stitch of any size: pictured as a 3 x 3
        workspace.run('make_mxn', {'m': 3, 'n': 3})
    else:
        workspace.run('load_sample', {'name': entry['name']})


class TooLong(BaseException):  # not an Exception: no "except Exception" in the tying swallows it
    pass


def time_limit(seconds):
    """Stop what runs after seconds (where the system can: not on Windows)."""
    import signal
    if not hasattr(signal, 'SIGALRM'):
        return
    def stop(*_):
        raise TooLong(f'took more than {seconds}s')
    signal.signal(signal.SIGALRM, stop)
    signal.alarm(seconds)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--only', nargs='*', help='entry names to make (default: all)')
    parser.add_argument('--missing', action='store_true', help='only the entries that have no picture yet')
    args = parser.parse_args(argv)
    import os
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])  # noqa: F841 - the canvas draws the pictures
    from PIL import Image
    from openstrand import agent, library
    library.PICTURES.mkdir(exist_ok=True)
    made, failed = 0, []
    for entry in library.entries():
        if args.only and entry['name'] not in args.only:
            continue
        if args.missing and library.picture_of(entry) is not None:
            continue
        workspace = agent.Workspace(Path(tempfile.mkdtemp()))
        try:
            time_limit(LIMIT)
            build(workspace, entry)
            shot = workspace.snapshot()
        except (Exception, TooLong) as e:  # noqa: BLE001 - say which, make the rest
            failed.append(f"{entry['name']}: {type(e).__name__}: {e}")
            continue
        finally:
            time_limit(0)
            workspace.close()
        print('made', entry['name'], flush=True)
        with Image.open(shot) as picture:
            picture = picture.convert('RGB')
            picture.thumbnail((SIDE, SIDE))
            # A few dozen colours are plenty for strands on white, and keep the files small.
            picture = picture.quantize(colors=64, method=Image.Quantize.MEDIANCUT)
            picture.save(library.PICTURES / library.picture_name(entry), optimize=True)
        made += 1
    print(f'{made} pictures in {library.PICTURES.relative_to(ROOT)}')
    for line in failed:
        print('not made:', line)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
