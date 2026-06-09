# OpenStrand Studio - Version 1.108

An advanced diagramming tool for creating tutorials involving strand manipulation (knots, hitches, etc.)
with dynamic masking that automatically adjusts the over-under effects between strands,
making complex patterns clear and easy to understand.

## What's New in Version 1.108

### ✨ New Features

- **Multi-Tab Workspace**: A new Tabs button opens a draggable tab edge that magnet-snaps to the side of the canvas. Each tab is an independent session with its own strands, groups, and undo/redo history, and you are warned before quitting when a tab still has unsaved changes.

- **View Mode Toggles in Settings**: New settings let you hide the selection highlight and hide control points while in View mode, giving you a clean, capture-ready canvas without changing your actual selection.

- **Unfolded Start Edge by Default**: A new Layer Panel setting makes every newly attached strand begin with an unfolded (transparent) start edge automatically, so you no longer have to set it strand by strand from the layer button menu.

- **Per-Layer Width Control**: A new "Change Width (This Layer Only)" option in the layer button menu resizes a single strand independently of its set, sets the stroke thickness directly in pixels, supports fractional grid sizes, and offers a match-connected-strand elliptical end-cap.

### 🐛 Bug Fixes & Improvements

- **Elliptical End-Cap Rendering**: Fixed the closed-knot and attached-strand end caps so a widened strand with the elliptical option renders a flat ellipse instead of a protruding semicircle, including inside masked strands and shadows.

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
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

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

© 2026 OpenStrand Studio - Version 1.108
