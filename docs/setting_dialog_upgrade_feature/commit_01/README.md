# Settings Dialog Upgrade — Segmented +/− Spin Boxes (v1.109)

## What changed

All 15 `QSpinBox` / `QDoubleSpinBox` controls in the settings dialog (shadow blur
steps/radius, control point influence, distance boost, curve response, extension
line, arrow head/shaft settings) plus the thickness spin box in
`DefaultWidthConfigDialog` were upgraded from native Qt arrow spinners to a
segmented stepper:

```
[ − | value | + ]
```

Design chosen from mockup **Option B** (see `../mockups/spinbox_button_mockup.html`):
one rounded container (5px radius) with hairline separators, flat −/+ buttons,
press-and-hold auto-repeat (400ms delay, 60ms interval) — the same interaction
language as the Edit Strand Angles dialog buttons.

Geometry matches the approved HTML mock: 30px buttons, ~66px centered value
field, 28px tall, 128px total.

## Files

- `src/segmented_spin_box.py` (new) — `upgrade_spinbox()` embeds two `QToolButton`s
  inside the spin box itself (native buttons hidden via `NoButtons`), so all
  existing references/layouts keep working. `style_segmented_spinbox()` applies
  theme + direction styling. `upgrade_and_style_all()` sweeps a widget tree.
- `src/settings_dialog.py` — hooks:
  - end of `apply_dialog_theme()` → upgrade + restyle on every theme change
  - end of `update_layout_direction()` → remirror buttons on language change
  - `apply_numeric_input_alignment()` skips segmented boxes (they stay centered)
  - `DefaultWidthConfigDialog` upgrades its thickness spin box with the
    inherited theme

## Theme & direction support

- **default / light / dark** — colors match the existing dialog stylesheets
  (dark: `#3D3D3D`/`#505050`, light: white/`#CCCCCC`, default: white/`#ADADAD`),
  including hover, pressed and disabled states.
- **RTL (Hebrew)** — the internal button row flips (`+` on the left, `−` on the
  right) and outer corner radii/separators swap sides; the numeric field itself
  stays LTR per the dialog convention.

## Verification

- Offscreen instantiation of `SettingsDialog`: 15/15 spin boxes segmented; theme
  cycling (dark → light → default) and Hebrew RTL relayout exercised; `+`/`−`
  clicks step values correctly.
- Rendered screenshots in `screenshots/` for all 3 themes × LTR/RTL, including
  a disabled control; zoomed check confirms buttons fill the full inner height.
