# OpenStrand Studio - Version 1.112

An advanced diagramming tool for creating tutorials involving strand manipulation (knots, hitches, etc.)
with dynamic masking that automatically adjusts the over-under effects between strands,
making complex patterns clear and easy to understand.

## What's New in Version 1.112

### ✨ New Features and Fixes

- **Strands and Masks Tabs**: The layer list is now split into two tabs, Strands and Masks, with a switch just above Draw Names. The Masks tab has its own New Mask, Delete Mask, Deselect All and Delete All buttons, and New Mask replaces the Mask button in the toolbar. Delete All on this tab removes only the masks, after a confirmation, in one undo step. Masks are now always kept above all strands, so where a mask sits in the list no longer matters, and selecting a layer from the other tab opens that tab for you.
- **Better Shadows Around Masks**: Where a mask lifts one strand over another, the shadows now look just like a real crossing. The stray dark wedges, bumps and dents near masks are gone, and the lifted strand stays clean. The Shadow Path preview in the Shadow Editor now shows exactly what the canvas draws.
- **Hidden Shadows Stay Hidden**: When you untick a shadow in the Shadow Editor, all of it now goes away. Before, a small grey bump could stay behind next to another strand. Making a mask also no longer hides a shadow that should stay visible.
- **Seven New Samples**: In Settings, under Samples, you will find seven new projects to open and learn from: Straight Weave 12×12, Curved Weave 6×6, Plait, Thick and Thin, Bridge, Twisted Pairs and Kagome Weave. The sample buttons now sit two to a row, so the whole list fits on the page.

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
`src/INSTALL_GUIDE_mac.md` (macOS: one command — `bash src/build_mac_1_112.sh`).

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

© 2026 OpenStrand Studio - Version 1.112
