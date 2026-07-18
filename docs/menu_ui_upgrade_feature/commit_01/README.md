# Layer Context Menu — Themed Dropdowns & Larger Checkboxes

## What changed (`src/numbered_layer_button.py`)

The Arrow customization section of the layer-button context menu previously
used native (unthemed) Qt widgets — tiny Windows comboboxes and 13px
checkboxes that ignored the app theme.

New module-level helpers, applied to Arrow Head Texture / Arrow Shaft Style
combos and Show Arrow Head / Arrow Casts Shadow checkboxes:

- `style_menu_combobox(combo, theme, is_rtl)` — rounded 4px border, themed
  field and popup list (light/default: white + `#AAAAAA`; dark: `#3D3D3D` +
  `#666666`; blue selection accents), and a proper triangle drop-down arrow.
  Qt stylesheets cannot draw CSS border-triangles (they render as a filled
  box), so the arrow uses packaged PNGs: `src/layer_panel_icons/
  combo_arrow_dark.png` (light themes) and `combo_arrow_light.png` (dark).
  The drop-down side, padding and arrow margin mirror for RTL (Hebrew).
- `style_menu_checkbox(checkbox, theme)` — 20px indicator (50% larger than
  the native ~13px), rounded, with the same blue-accent palette as the Edit
  Shadow dialog checkboxes.
- `setup_menu_checkmark(checkbox)` — paints the white V over the styled
  indicator (stylesheet-styled indicators lose Qt's native checkmark).

## Verification (live GUI)

Launched the real MainWindow, enabled Full Arrow on a strand, opened the
actual context menu in both default and dark themes, and captured the open
menu. Screenshots in `screenshots/` (full menu + zoomed crops of the
combo/checkbox rows).
