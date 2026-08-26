# Review set — current state after all fixes

Every image here was regenerated from the code as it stands on
`fix-screen-ratio-layout`. If something still looks wrong, note the file
number and what you see.

## 00–10 · Screen ratios (English)

The full window at ten real Mac/PC screen sizes, with the menu bar and
dock/taskbar drawn around it. **00 is the contact sheet** — start there for
an overview, then open individual ones.

Each has a footer line with the measurements and a status word. Look for:

- Status reads **OK** in green (red would mean clipped buttons or an
  oversized panel).
- All toolbar buttons present, from View through State plus the gear.
- Layer panel at **286px** on the two 1280-wide screens (01 and 03), 350px
  on everything wider.

## 11–12 · Vertical scrollbar with 30 layers

Added enough layers to force the layer list to scroll.

- **11** is the compact 1280 case, **12** is the wide 1440 case.
- The scrollbar should sit in its own strip **beside** the layer buttons,
  never over their right edge. It is deliberately subtle in the dark theme.
- Layer buttons keep their full width and rounded corners.
- "Create Group" fully visible.

## 13–19 · Languages at the worst ratio (1280x705)

The MacBook 13" size, which is where translated labels used to break.

- Every toolbar label should be a **complete word, not cut** at either end.
  Previously German showed "rbind" for `Verbinden` and Spanish showed
  "eleccion" for `Seleccionar`.
- The Create Group button (top right) fully readable in each language.
- Hebrew (19) is right-to-left; the layout mirrors.

Expected labels per language:

| # | Language | Sample of what should read cleanly |
|---|---|---|
| 13 | English | View, Mask, Select, Attach, Move, Rotate |
| 14 | French | Voir, Masque, Choisir, Lier, **Ombre**, **Onglet** |
| 15 | German | **Sicht**, **Wählen**, **Binden**, **Sichern**, Schatten |
| 16 | Italian | Vista, **Scegli**, **Unisci**, **Muovi**, Immagine |
| 17 | Spanish | Ver, **Elegir**, **Rejilla**, **Abrir**, Pestaña |
| 18 | Portuguese | Ver, **Girar**, **Unir**, **Abrir**, Selecionar |
| 19 | Hebrew | (RTL layout) |

Bold entries are the labels that were changed to shorter complete words.

## Regenerating

```
python automation_tests/capture_screen_ratio_mocks.py      # 00-10
python automation_tests/capture_many_layers_scrollbar.py   # 11-12
python automation_tests/capture_language_toolbars.py       # 13-19
```

To see any of these live and interactive instead of as an image:

```
python automation_tests/preview_screen_ratio.py macbook13
python automation_tests/preview_screen_ratio.py air13_more_space
```
