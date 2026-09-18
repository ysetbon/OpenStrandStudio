# OpenStrand Studio - Version 1.111

An advanced diagramming tool for creating tutorials involving strand manipulation (knots, hitches, etc.)
with dynamic masking that automatically adjusts the over-under effects between strands,
making complex patterns clear and easy to understand.

## What's New in Version 1.111

### ✨ New Features

- **Stylize End Side**: Right-click a layer with a free end and pick Stylize End Side, just under Close the Knot. A dialog lets you choose how the strand ends: Straight, Angled, Rounded, Pointed, Notched or Concave. You can also set the tilt and depth, extend or trim the end, and add a side line with its own thickness and color. The preview is live on the canvas. The shadow, side line and masks all follow the new shape. End styles are saved with your project and work with undo and redo.
- **Right Size on Scaled Screens**: On high-resolution screens with display scaling turned on, the buttons and text used to look too small. The app now follows your display scale. Toolbar labels no longer get cut off, and the toolbar moves onto two rows when the window is narrow. The layer panel can be dragged narrower than before. The OpenStrand Studio logo now appears on every window and in the taskbar.
- **Dialogs Fit Small Screens**: The Settings dialog can now be made smaller, so its Apply and OK buttons always stay on screen. The same goes for Edit Shadow, the group shadow editor, Create Mask Grid, Edit Strand Angles, Change Width and the video player. A dialog never opens larger than your screen, and it keeps the size you give it.
- **Smoother Dragging**: The canvas stays sharp while you drag, even on scaled displays or with supersampling on. Move mode shows a closed hand while dragging a point. View mode can now pan with the left mouse button too. The Refresh button's tooltip now says what it does: reload layers and reset the view.

## Features

- Layer-based design with masking capability that automatically updates when strands are reordered or repositioned.
- Interactive strand manipulation 
- Group transformation tools
- Precise angle/length controls
- Grid snapping
- Multilingual (EN/FR/IT/ES/PT/HE/DE)

## Screenshots

<img width="1920" height="1030" alt="OpenStrand Studio 1.110 main window: the box stitch sample on the canvas, the layer panel and group column on the right, with the group column's collapse chevron at the bottom-right corner" src="docs/readme/main_window.png" />



## Usage

1. Clone the repository, best to use:
```bash
git clone --filter=blob:limit=5m https://github.com/ysetbon/OpenStrandStudio <your-desired-folder>
cd <your-desired-folder>
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python src/main.py
```

For installer builds see `src/INSTALL_GUIDE_Windows.md` and
`src/INSTALL_GUIDE_mac.md` (macOS: one command — `bash src/build_mac_1_111.sh`).

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

© 2026 OpenStrand Studio - Version 1.111
