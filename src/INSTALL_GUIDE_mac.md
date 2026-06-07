# OpenStrand Studio - macOS Installation Guide

## Version 1.108 - June 8, 2026

This guide explains how to build and package OpenStrand Studio for macOS.

## Prerequisites

Before starting, ensure you have the following installed:

- Python 3.9+ (recommended: 3.13)
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
bash src/build_mac_1_108.sh
```

No `chmod` and no `cd` needed — running it through `bash` doesn't require
the executable bit, and the script switches into `src` on its own.

When it finishes, the installer is created in the `installer_output`
directory as `OpenStrandStudio_1.108.pkg`, and that folder is opened
automatically.

Options:

```bash
PYTHON=python3.13 bash src/build_mac_1_108.sh   # use a specific Python interpreter
bash src/build_mac_1_108.sh --dmg               # build a .dmg instead of the .pkg
```

> The one-command script simply chains the two manual steps below
> (`OpenStrandStudio_mac.spec` → `build_installer_1_108.sh`). Use the manual
> steps if you need to run them individually.

## Manual Build (step by step)

### Step 1: Build the Application

From the `src` directory, create the application bundle:

```bash
cd src
python3 -m PyInstaller OpenStrandStudio_mac.spec
```

This creates `dist/OpenStrandStudio.app` using the macOS-specific spec file,
which includes the proper app-bundle configuration, flag images, and SVG
resources.

### Step 2: Create the Installer Package

Make the 1.108 installer script executable and run it:

```bash
chmod +x build_installer_1_108.sh
./build_installer_1_108.sh
```

This creates `OpenStrandStudio_1.108.pkg` in the `installer_output` directory.

> To build a disk image instead, use `build_dmg_1_108.sh` the same way.

## Step 3: Distribute the Application

Distribute `installer_output/OpenStrandStudio_1.108.pkg`. When users run it, it will:

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

## Optional: Updating the Application (next version)

When creating the next version:

1. Copy `build_installer_1_108.sh` to `build_installer_1_XXX.sh` (and
   `build_dmg_1_108.sh` / `build_mac_1_108.sh` likewise)
2. Update the `VERSION` and `APP_DATE` variables at the top of each script
3. Search for `#todo` markers to update the "What's New" header and feature
   descriptions for each language
4. Follow the Quick Build (or manual steps) to rebuild and package

## Notes for Developers

- The installer package includes scripts that handle setup and configuration
- PyInstaller bundles all dependencies into the application
- The final application runs on macOS 10.13 or later
- The build scripts assume the repository lives at
  `/Users/yonatan/Documents/GitHub/OpenStrandStudio` (the paths inside
  `build_installer_1_108.sh` are absolute); adjust those paths if your clone
  is elsewhere
