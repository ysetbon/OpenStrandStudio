# OpenStrand Studio - Version 1.109

An advanced diagramming tool for creating tutorials involving strand manipulation (knots, hitches, etc.)
with dynamic masking that automatically adjusts the over-under effects between strands,
making complex patterns clear and easy to understand.

## What's New in Version 1.109

### ✨ New Features

- **Lock Mode Redesigned**: Each layer button now shows a small padlock in lock mode. Click the padlock to lock/unlock; clicking the layer simply selects it. Locked strands can be selected but not moved or attached to, and New Strand / Delete Strand remain available (delete is blocked only for locked layers). The lock state is also remembered through undo/redo, save/load, and tab switching.

- **Per-Layer Hide Shadow Option**: Right-click a layer to stop it from casting shadow onto other strands. The setting is saved with your project and survives undo/redo and group operations.

- **Arrow Customization in the Layer Menu**: Right-click a layer to style its arrows in place: start/end arrows, full arrow with color, transparency, texture, shaft style, arrow head and shadow, plus a new Arrow Sizes dropdown for all numeric arrow dimensions.

- **Copy & Paste Strand Data**: In multi-select mode, copy selected properties of a strand (start/end points, control points, width, strand and stroke colors) and paste them onto several layers at once, anchored from the start or end point — with a copy badge and one-click paste chips right on the layer buttons.

- **Mask Shadows in the Shadow Editor**: Shadows cast through a mask now appear in the over-strand's Shadow Editor, so you can turn them on or off like any other shadow.

### 🐛 Bug Fixes & Improvements

- **Automatic Shadow Correction for Woven Masks**: Incorrect shadow marks at mask crossings are now hidden automatically; your manual Shadow Editor settings are always respected.

- **More Accurate Strand Selection**: Clicking now selects exactly what you see: strand edges, end caps, and mask outlines are all clickable, the topmost strand is always picked, and the hover highlight always matches what a click will select.

- **Control Point Visibility Fix**: "Show control points only for the selected strand" now hides only control points; other strands keep their endpoint squares and remain movable. Dragging an endpoint no longer makes an untouched control point appear.

- **Shadow Settings Preserved**: A layer's hidden-shadow state is no longer reset by group move or duplicate operations.

- **Improved Drawing Stability**: Fixed internal painting issues that could corrupt the canvas after a drawing error.

## Features

- Layer-based design with masking capability that automatically updates when strands are reordered or repositioned.
- Interactive strand manipulation 
- Group transformation tools
- Precise angle/length controls
- Grid snapping
- Multilingual (EN/FR/IT/ES/PT/HE/DE)

## Screenshots

<img width="1917" height="1028" alt="image" src="https://github.com/user-attachments/assets/339bdcc0-ca8f-494b-9081-c0d97387fe97" />



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
`src/INSTALL_GUIDE_mac.md` (macOS: one command — `bash src/build_mac_1_109.sh`).

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

© 2026 OpenStrand Studio - Version 1.109
