"""OpenStrand Studio from the command line: make, check, recolor and render projects.

The commands reuse the application's own code (src/) and the sample
generators (scripts/), so a project made here opens in the app exactly as it
was built. Run them with: python -m openstrand --help
"""
import sys
from pathlib import Path

__version__ = '0.1.0'

ROOT = Path(__file__).resolve().parents[1]

for _folder in (ROOT / 'scripts', ROOT / 'src'):
    if str(_folder) not in sys.path:
        sys.path.insert(0, str(_folder))
