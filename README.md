# OpenStrand Studio - Version 1.105

An advanced diagramming tool for creating tutorials involving strand manipulation (knots, hitches, etc.)
with dynamic masking that automatically adjusts the over-under effects between strands,
making complex patterns clear and easy to understand.

## What's New in Version 1.105

### ✨ New Features

- **Mask Grid**: Quickly create multiple strand masks using a visual N×N grid interface in group functionalities.

- **Keyboard Shortcuts**: New shortcuts for faster workflow:
  - **Space**: Hold to quickly pan/unpan the canvas
  - **Z**: Undo your last action
  - **X**: Redo what you just undid
  - **N**: New Strand
  - **1**: Draw Names
  - **L**: Lock Layers
  - **D**: Delete Strand
  - **A**: Deselect All

### 🐛 Bug Fixes & Improvements

- **Fixed Selection & Zoom**: Selection in move, select, and attach modes now remains accurate at all zoom levels.
- **Smoother Knot Connections**: Fixed a rendering issue where "closed knots" (loops) would sometimes show visible seams or gaps at the connection point. Strands now merge seamlessly for a cleaner look.

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

© 2025 OpenStrand Studio - Version 1.105
