# OpenStrand Studio - macOS Installation Guide

## Version 1.109 - July 21, 2026

This guide covers running OpenStrand Studio from source (fastest) and building
the macOS installer package.

## Fastest: run from source after cloning

No packaging needed — three commands from a fresh clone:

```bash
git clone --filter=blob:limit=5m https://github.com/ysetbon/OpenStrandStudio
cd OpenStrandStudio
pip3 install -r requirements.txt && python3 src/main.py
```

That's it. `requirements.txt` pins PyQt5 5.15.4 and Pillow, which is all the
app needs at runtime.

> **Python version matters: use 3.9–3.13, NOT 3.14+.** PyQt5 has no working
> support for Python 3.14 — the app segfaults immediately (both from source
> and packaged). If `python3 --version` says 3.14, install a supported one
> (`brew install python@3.13`), install the deps for it
> (`python3.13 -m pip install "PyQt5>=5.15.10" pillow pyinstaller`) and run
> everything through `python3.13` / `PYTHON=python3.13`.

## Prerequisites for building the installer

- Python 3.9–3.13 (recommended: 3.13; **3.14 is not supported by PyQt5**)
- pip (Python package manager)
- Xcode Command Line Tools

Install the required Python packages once:

```bash
pip3 install PyQt5==5.15.4 Pillow pyinstaller
```

## Quick Build (one command)

From the repository root, run this single line. It builds the app bundle
with PyInstaller **and** packages the `.pkg` installer in one step:

```bash
bash src/build_mac_1_109.sh
```

No `chmod` and no `cd` needed — running it through `bash` doesn't require
the executable bit, and the script switches into `src` on its own. All build
paths are relative to the script, so any clone location works.

When it finishes, the installer is created in `src/installer_output/` as
`OpenStrandStudio_1_109.pkg`, and that folder is opened automatically.

Options:

```bash
PYTHON=python3.13 bash src/build_mac_1_109.sh   # use a specific Python interpreter
bash src/build_mac_1_109.sh --dmg               # build a .dmg instead of the .pkg
```

> The one-command script simply chains the two manual steps below
> (`OpenStrandStudio_mac.spec` → `build_installer_1_109.sh`). Use the manual
> steps if you need to run them individually.

## Manual Build (step by step)

### Step 1: Build the Application

From the `src` directory, create the application bundle:

```bash
cd src
python3 -m PyInstaller OpenStrandStudio_mac.spec
```

This creates `dist/OpenStrandStudio.app` using the macOS-specific spec file,
which includes the proper app-bundle configuration, flag images, layer-panel
icons, and SVG resources.

### Step 2: Create the Installer Package

Make the 1.109 installer script executable and run it:

```bash
chmod +x build_installer_1_109.sh
./build_installer_1_109.sh
```

This creates `OpenStrandStudio_1_109.pkg` in the `installer_output` directory.

> To build a disk image instead, use `build_dmg_1_109.sh` the same way.

## Step 3: Distribute the Application

Distribute `installer_output/OpenStrandStudio_1_109.pkg`. When users run it, it will:

1. Install the application to their Applications folder (including SVG resources)
2. Create a desktop icon
3. Offer to launch the application after installation

## Troubleshooting

If you encounter issues with missing dependencies:

1. Ensure all required packages are installed
2. Check the application log for errors
3. For PyQt5 issues, run the application from Terminal to see detailed error output:
   ```bash
   /Applications/OpenStrand\ Studio.app/Contents/MacOS/OpenStrandStudio
   ```

### Missing Flag Images

If language selection doesn't show flag images, ensure the `flags` directory with country flag PNG files (us.png, fr.png, it.png, es.png, pt.png, il.png, de.png) is in the src directory before building.

### Missing SVG Shapes

If shapes don't appear correctly, ensure the `images` directory with SVG files (circle.svg, square.svg, triangle.svg, bias_circle.svg, bias_triangle.svg) is in the src directory before building.

### Missing layer-panel icons

If the layer-panel toolbar buttons or the copy/paste indicators show blank,
ensure the `layer_panel_icons` directory (PNG files) is in the src directory
before building — the spec files package it automatically.

## Creating the next version

Do not edit the build scripts by hand — generate them. See
`src/RELEASE_HOWTO.md`: edit the CONFIG section of
`scripts/make_release_files.py` (new version, dates, what's-new bullets in 7
languages) and run it. It produces the new `.iss`, `build_installer_X_XXX.sh`,
`build_dmg_X_XXX.sh`, `build_mac_X_XXX.sh` and updates `translations.py` and
`OpenStrandStudio_mac.spec`.

## Notes for Developers

- The installer package includes scripts that handle setup and configuration
- PyInstaller bundles all dependencies into the application
- The final application runs on macOS 10.13 or later
- All paths inside the build scripts are relative to the script location, so
  the repository can live anywhere
