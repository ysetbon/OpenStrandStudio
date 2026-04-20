# OpenStrand Studio - Version 1.107

An advanced diagramming tool for creating tutorials involving strand manipulation (knots, hitches, etc.)
with dynamic masking that automatically adjusts the over-under effects between strands,
making complex patterns clear and easy to understand.

## What's New in Version 1.107

### ✨ New Features

- **Group Shadow Editor**: Shadows can now be edited for entire groups, giving you full control over how group strands cast shadows on the canvas.

- **Selected Strand Settings**: A new "Selected Strand" category in Settings gathers options that apply only to the currently selected strand — move-only, control-points-only, shadow-only, and a customizable selection highlight color.

- **View Button**: New View button in the main window that hides all mode indicators (Move, Attach, etc.) so you can see your design clearly without any UI overlays.

- **Hebrew Right-to-Left Alignment**: The main window, settings dialog, group context menu, and group panel are now mirrored right-to-left in Hebrew for a natural reading order.

### 🐛 Bug Fixes & Improvements

- **Shadow Editor Fixes & Masked Strand Support**: Shadow subtraction logic is unified between the main renderer and the shadow preview, and masked strands can now be edited through the shadow editor dialog with smart defaults.
- **Group Creation Stability**: Fixed unexpected crashes caused by orphan hidden group dialogs when creating groups or exiting the application.

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

© 2026 OpenStrand Studio - Version 1.107
