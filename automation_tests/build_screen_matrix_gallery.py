"""Turn capture_screen_matrix.py output into a browsable gallery folder.

Reads every ``results_<scale>.json`` under the input directory (one per
display scale, as written by ``capture_screen_matrix.py``), converts each
screenshot to a WebP no wider than ``--max-width`` and writes
``<out>/shots.json`` plus ``<out>/img/*.webp``, next to a copy of the
gallery page ``screen_matrix_gallery.html`` (kept beside this script). The
page reads ``shots.json`` and offers dropdowns for screen, language and
layer-panel mode, a faults-only filter, and the checks and measured
geometry of the selected shot. Serve the folder over HTTP (or publish it)
so the page can fetch ``shots.json``.

Run:
    python automation_tests/build_screen_matrix_gallery.py --in DIR --out DIR/gallery
"""
import argparse
import glob
import json
import os
import shutil

from PIL import Image

GALLERY_PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screen_matrix_gallery.html")


def build(in_dir, out_dir, max_width=1400, quality=68):
    img_dir = os.path.join(out_dir, "img")
    os.makedirs(img_dir, exist_ok=True)
    shots = []
    fonts = set()
    for results_path in sorted(glob.glob(os.path.join(in_dir, "**", "results_*.json"), recursive=True)):
        with open(results_path, encoding="utf-8") as fh:
            results = json.load(fh)
        fonts.add(results.get("font", ""))
        src_dir = os.path.dirname(results_path)
        for shot in results["shots"]:
            src = os.path.join(src_dir, shot["file"])
            name = os.path.splitext(shot["file"])[0] + ".webp"
            dst = os.path.join(img_dir, name)
            with Image.open(src) as im:
                w, h = im.size
                if w > max_width:
                    im = im.resize((max_width, int(h * max_width / w)), Image.LANCZOS)
                im.convert("RGB").save(dst, "WEBP", quality=quality, method=6)
            shots.append({
                "preset": shot["preset"], "title": shot["title"],
                "physical": shot["physical"], "scale": shot["scale"],
                "logical": shot["logical"], "language": shot["language"],
                "mode": shot["mode"], "image": "img/" + name,
                "image_size": shot["image"], "metrics": shot["metrics"],
                "failures": shot["failures"],
            })
    shots.sort(key=lambda s: (s["physical"][0] * s["physical"][1], s["scale"], s["language"], s["mode"]))
    with open(os.path.join(out_dir, "shots.json"), "w", encoding="utf-8") as fh:
        json.dump({"font": ", ".join(sorted(f for f in fonts if f)), "shots": shots}, fh, ensure_ascii=False)
    shutil.copyfile(GALLERY_PAGE, os.path.join(out_dir, "screen_matrix_gallery.html"))
    total = sum(os.path.getsize(os.path.join(img_dir, f)) for f in os.listdir(img_dir))
    print(f"{len(shots)} shots, {total / 1e6:.1f} MB of images -> {out_dir}")
    return shots


def bundle(out_dir, bundle_path):
    """Write one self-contained HTML page with every image inlined as a
    data URI, so it can be opened from disk or published as a single file."""
    import base64

    with open(os.path.join(out_dir, "shots.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    for shot in data["shots"]:
        with open(os.path.join(out_dir, shot["image"]), "rb") as fh:
            shot["image"] = "data:image/webp;base64," + base64.b64encode(fh.read()).decode("ascii")
    with open(GALLERY_PAGE, encoding="utf-8") as fh:
        page = fh.read()
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    marker = "<script>"
    assert marker in page
    page = page.replace(marker, f'<script id="shots-data" type="application/json">{payload}</script>\n{marker}', 1)
    with open(bundle_path, "w", encoding="utf-8") as fh:
        fh.write(page)
    print(f"bundle {os.path.getsize(bundle_path) / 1e6:.1f} MB -> {bundle_path}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--in", dest="in_dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-width", type=int, default=1400)
    parser.add_argument("--quality", type=int, default=68)
    parser.add_argument("--bundle", default="",
                        help="also write a single self-contained HTML file here")
    args = parser.parse_args(argv)
    build(os.path.abspath(args.in_dir), os.path.abspath(args.out), args.max_width, args.quality)
    if args.bundle:
        bundle(os.path.abspath(args.out), os.path.abspath(args.bundle))


if __name__ == "__main__":
    main()
