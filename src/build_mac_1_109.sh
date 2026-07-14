#!/bin/bash
################################################################################
# OpenStrand Studio - One-command macOS build (v1.109)
#
# Does EVERYTHING in a single run:
#   1. Builds the .app bundle with PyInstaller (OpenStrandStudio_mac.spec)
#   2. Packages the .pkg installer (build_installer_1_109.sh)
#
# Usage:
#   cd src
#   ./build_mac_1_109.sh
#
# Optional:
#   PYTHON=python3.13 ./build_mac_1_109.sh   # choose a specific interpreter
#   ./build_mac_1_109.sh --dmg               # also build the .dmg
#
# Prerequisites (install once):
#   pip3 install PyQt5==5.15.4 Pillow pyinstaller
################################################################################

set -euo pipefail

# Always run from this script's own directory (the src folder), so the
# relative spec path and the dist/ output line up regardless of where it's
# invoked from.
cd "$(dirname "$0")"

VERSION="1.109"
PY="${PYTHON:-python3}"
BUILD_DMG="no"
[ "${1:-}" = "--dmg" ] && BUILD_DMG="yes"

echo "=================================================="
echo " OpenStrand Studio - macOS build  (v${VERSION})"
echo " Interpreter: $("$PY" --version 2>&1)"
echo "=================================================="

# --- Step 1: build the .app bundle -------------------------------------------
echo ""
echo "[1/2] Building app bundle with PyInstaller (clean)..."
"$PY" -m PyInstaller OpenStrandStudio_mac.spec --noconfirm --clean

if [ ! -d "dist/OpenStrandStudio.app" ]; then
    echo "ERROR: dist/OpenStrandStudio.app was not produced. Aborting." >&2
    exit 1
fi

# --- Step 2: package the installer -------------------------------------------
echo ""
echo "[2/2] Packaging installer..."
if [ "$BUILD_DMG" = "yes" ]; then
    chmod +x build_dmg_1_109.sh
    ./build_dmg_1_109.sh
else
    chmod +x build_installer_1_109.sh
    ./build_installer_1_109.sh
fi

echo ""
echo "=================================================="
echo " Done. Output is in: installer_output/"
echo "=================================================="
