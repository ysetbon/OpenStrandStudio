"""Download Twemoji SVG files from GitHub and render as 512x512 PNGs using PyQt5."""
import os
import sys
import urllib.request

from PyQt5.QtCore import QByteArray, Qt
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QApplication

# Need a QApplication instance for Qt rendering
app = QApplication.instance() or QApplication(sys.argv)

# Twemoji SVG base URL (jdecked/twemoji fork, actively maintained)
SVG_BASE = "https://raw.githubusercontent.com/jdecked/twemoji/main/assets/svg/"

# Output directory
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "twemoji_512")
os.makedirs(OUT_DIR, exist_ok=True)

# Read codepoints from openmoji_72 as reference
REF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "openmoji_72")
codepoints = sorted(f.replace(".png", "") for f in os.listdir(REF_DIR) if f.endswith(".png"))

SIZE = 512

print(f"Downloading {len(codepoints)} Twemoji SVGs and rendering at {SIZE}x{SIZE}...")

success = 0
failed = []
for code in codepoints:
    out_path = os.path.join(OUT_DIR, f"{code}.png")
    if os.path.exists(out_path):
        print(f"  [skip] {code}.png already exists")
        success += 1
        continue

    url = f"{SVG_BASE}{code}.svg"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            svg_data = resp.read()

        renderer = QSvgRenderer(QByteArray(svg_data))
        if not renderer.isValid():
            raise ValueError("Invalid SVG data")

        img = QImage(SIZE, SIZE, QImage.Format_ARGB32_Premultiplied)
        img.fill(Qt.transparent)
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        renderer.render(painter)
        painter.end()

        if not img.save(out_path, "PNG"):
            raise IOError("Failed to save PNG")

        print(f"  [ok]   {code}.png")
        success += 1
    except Exception as e:
        print(f"  [FAIL] {code}: {e}")
        failed.append(code)

print(f"\nDone: {success}/{len(codepoints)} succeeded")
if failed:
    print(f"Failed: {', '.join(failed)}")
