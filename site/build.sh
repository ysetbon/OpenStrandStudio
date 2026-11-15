#!/usr/bin/env bash
# Puts the whole site in one folder (site/README.md): bash site/build.sh <folder>
# Run from the repository's root. The folder is emptied first.
set -euo pipefail
out="${1:?the folder to build the site in, such as _site}"
rm -rf "$out"
mkdir -p "$out/img"
cp -r site/. "$out/"
cp -r gallery "$out/gallery"
cp docs/readme/main_window.png "$out/img/main_window.png"   # the README's own screenshot
cp src/box_stitch.png "$out/img/icon.png"                   # the app's icon
rm -f "$out/build.sh" "$out/README.md" "$out/gallery/README.md"
