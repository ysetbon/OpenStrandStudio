# Arrow Sizes Dropdown in the Layer Context Menu

## What changed

New "Arrow Sizes" row at the bottom of the Arrow customization section of the
layer-button context menu (`src/numbered_layer_button.py`). It looks like the
other dropdowns in that section (combo-style chrome via the new
`style_menu_dropdown_button()` helper — a `QToolButton` with `InstantPopup`
and the packaged triangle arrow PNG).

Opening it shows a popup panel with all six numeric arrow settings from the
settings dialog, each edited with the same segmented `[ - | value | + ]`
spin box (`segmented_spin_box.py`):

| Setting | Range |
|---|---|
| Arrow Head Length | 0–500 |
| Arrow Head Width | 0–500 |
| Arrow Head Stroke Width | 1–30 (int) |
| Arrow Gap Length | 0–1000 |
| Arrow Line Length | 0–1000 |
| Arrow Line Width | 0.1–100 |

Ranges/defaults mirror `settings_dialog.py` exactly.

## Behavior

- Value changes apply to the canvas immediately (`canvas.<attr>` +
  `canvas.update()`), so the arrow redraws live while stepping.
- Changes are mirrored into the settings dialog instance (attribute +
  spin box value, signals blocked) and persisted once via
  `dialog.save_settings_to_file()` when the popup closes — same effect as
  changing the value in the settings dialog and applying.
- Theme-aware (default/light/dark) and RTL-aware (labels/spin boxes mirror,
  dropdown arrow flips) like the rest of the section.
- New translation keys `arrow_sizes` / `adjust` added for en, fr, de, it, es,
  pt, he in `translations.py`.

## Verification (live GUI)

Real MainWindow + 24-layer sample: opened the context menu, clicked the
Arrow Sizes dropdown, stepped Arrow Head Length with the + / − buttons —
spin box and `canvas.arrow_head_length` moved 20.00 → 21.00 → 20.00 together.
Screenshots in `screenshots/` (menu with the new row, and the open panel).
