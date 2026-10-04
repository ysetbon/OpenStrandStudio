# OpenStrand Studio - Version 2.0

An advanced diagramming tool for creating tutorials involving strand manipulation (knots, hitches, etc.)
with dynamic masking that automatically adjusts the over-under effects between strands,
making complex patterns clear and easy to understand.

## What's New in Version 2.0

Why 2.0? Masks now feel much more natural to use. Weaving is key to tying knots, and masks are a big part of weaving, so this is a major step for OpenStrand Studio.

### ✨ New Features and Fixes

- **Strands and Masks Tabs**: The layer list is now split into two tabs, Strands and Masks, with a switch just above Draw Names. The Masks tab has its own New Mask, Delete Mask, Deselect All and Delete All buttons, and New Mask replaces the Mask button in the toolbar. Delete All on this tab removes only the masks, after a confirmation, in one undo step. Masks are now always kept above all strands, so where a mask sits in the list no longer matters, and selecting a layer from the other tab opens that tab for you.
- **Fixed Shadow Issues**: Fixed shadow issues from older versions. Shadows for masks now behave more naturally.
- **Seven New Samples**: In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.

## Features

- Layer-based design with masking capability that automatically updates when strands are reordered or repositioned.
- Interactive strand manipulation 
- Group transformation tools
- Precise angle/length controls
- Grid snapping
- Multilingual (EN/FR/IT/ES/PT/HE/DE)

## Screenshots

<img width="1920" height="1030" alt="OpenStrand Studio 2.0 main window: the Kagome Weave sample on the canvas, the Strands/Masks layer panel and group column on the right" src="docs/readme/main_window.png" />

*The Kagome Weave sample (Settings → Samples), open in OpenStrand Studio 2.0.*

## Install

### Easiest: download the installer (no Python needed)

Grab the latest installer from the [Releases page](https://github.com/ysetbon/OpenStrandStudio/releases/latest) and run it.
To update, just run the newer installer — it installs over the old version. Your saved `.oss` projects are ordinary files and are untouched.

| | Download | Then |
|---|---|---|
| **Windows** | `OpenStrandStudioSetup_<date>_<version>.exe` | Double-click it and follow the wizard (Start Menu shortcut, optional desktop icon, `.oss` file association). |
| **macOS** | `OpenStrandStudio_<version>.pkg` (or `.dmg`) | Double-click it and follow the wizard; the app lands in Applications. If macOS blocks it, right-click → **Open**. |

### Run from source (any platform, always the newest code)

Needs **Python 3.9–3.13** (not 3.14 — PyQt5 crashes on it).

**macOS** (Terminal):
```bash
git clone --filter=blob:limit=5m https://github.com/ysetbon/OpenStrandStudio
cd OpenStrandStudio
pip3 install -r requirements.txt && python3 src/main.py
```

**Windows** (PowerShell — a virtual environment avoids PyQt/Anaconda DLL conflicts):
```powershell
git clone --filter=blob:limit=5m https://github.com/ysetbon/OpenStrandStudio
cd OpenStrandStudio
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python src\main.py
```

To update later: `git pull`, then run it again.

### Build the installer for a new version

| | Command (from the repository root) | Output |
|---|---|---|
| **macOS** | `bash src/build_mac_2_0.sh` (add `--dmg` for a disk image; `PYTHON=python3.13 bash ...` to pick an interpreter) | `src/installer_output/OpenStrandStudio_2_0.pkg` |
| **Windows** | `cd src` then `.\build_with_venv.bat`, then open `src\inno setup\OpenStrand Studio2_0.iss` in [Inno Setup](https://jrsoftware.org/isdl.php) and click **Compile** | `src\dist\OpenStrandStudioSetup_<date>_2_0.exe` |

The version-specific scripts are generated, not hand-edited: for a new release, edit the CONFIG section of `scripts/make_release_files.py`
and run it (see `src/RELEASE_HOWTO.md`). More detail and troubleshooting: `src/INSTALL_GUIDE_Windows.md` and `src/INSTALL_GUIDE_mac.md`.

## Video Tutorials

Find usage tutorials on the [LanYarD YouTube channel](https://www.youtube.com/@1anya7d).

## Development

- Python 3.9+
- PyQt5

## License

GNU General Public License v3.0

## Contact

Created by Yonatan Setbon
- [LinkedIn](https://www.linkedin.com/in/yonatan-setbon-4a980986/)
- [Instagram](https://www.instagram.com/ysetbon/)
- [YouTube - LanYarD](https://www.youtube.com/@1anya7d)
- Email: [ysetbon@gmail.com](mailto:ysetbon@gmail.com)

---

© 2026 OpenStrand Studio - Version 2.0
