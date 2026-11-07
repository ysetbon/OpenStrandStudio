"""Work out the library knots' shapes once: laid out, drawn up and tight.

    python scripts/build_knot_shapes.py

Writes openstrand/knot_shapes.json (positions in cord widths), which
openstrand.tying scales to any width, so tying a library knot does not wait
for the simulation. Every stage is checked to be the knot it should be.
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))

from openstrand import tying  # noqa: E402


def main():
    started = time.monotonic()
    shapes = tying.make_library_shapes()
    for key, value in shapes.items():
        print(key, [(c['stage'], c['crossings'], c['knot']) for c in value.pop('checks')])
    tying.SHAPES.write_text(json.dumps(shapes, separators=(',', ':')), encoding='utf-8')
    print(f'wrote {tying.SHAPES} in {time.monotonic() - started:.0f} s')


if __name__ == '__main__':
    main()
