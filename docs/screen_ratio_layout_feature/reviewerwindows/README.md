# Review set — complete coverage

Every supported language at every screen ratio: **7 languages x 10 ratios =
70 screens**, plus 7 contact sheets and the 2 scrollbar cases. All rendered
from the code as it stands on `fix-screen-ratio-layout`.

If something looks wrong, note the folder and file name.

```
contact_sheets/   one sheet per language — all 10 ratios at a glance
by_language/      the 70 individual full-size screens
scrollbar/        the 30-layer vertical scrollbar cases
```

## Where to start

Open **`contact_sheets/`** first — 7 images, each showing that language at
all ten ratios. That covers the whole matrix in seven glances. Drop into
`by_language/<language>/` only when a thumbnail looks off.

## Every image checks itself

Each screen has a footer line in green or red:

```
app 1280x705 · canvas pane 967px · layer panel 286px (target min 286, group 127px) · compact · OK
```

The last word is the verdict:

| Footer | Meaning |
|---|---|
| **OK** (green) | Nothing wrong on this screen |
| **LABELS CUT** (red) | A toolbar label is wider than its button, so the text is cut at both ends — lists which labels and by how many px |
| **BUTTONS CLIPPED** (red) | A toolbar button falls outside the canvas pane |
| **LAYER PANEL NOT MINIMIZED** (red) | The panel failed to shrink to its target |

All 70 currently read **OK**. "compact" in the footer just notes the screen
is under 1350px wide, so the narrow-screen layout is active — that is
expected, not a warning.

## The ten ratios

| # | Screen | Size |
|---|---|---|
| 01 | MacBook 13" smallest scaled | 1280x800 |
| 02 | MacBook Air 13" Intel | 1440x900 |
| 03 | MacBook Air 13" M2 "More Space" | 1280x832 |
| 04 | MacBook Air 13" M2 default | 1470x956 |
| 05 | MacBook Pro 14" | 1512x982 |
| 06 | MacBook Pro 16" | 1728x1117 |
| 07 | iMac 24" | 2240x1260 |
| 08 | External 1080p | 1920x1080 |
| 09 | External 1440p | 2560x1440 |
| 10 | Ultrawide 21:9 | 2560x1080 |

**01 and 03 are the ones that used to break** — they are the 1280-wide
screens where the compact layout kicks in (panel 286px instead of 350px).
Everything 1440 and wider was always fine.

## What to look for per language

Toolbar labels should be complete words, never cut at either end. Bold
entries below are the ones shortened during this work:

| Language | Labels worth checking |
|---|---|
| English | View, Mask, Select, Attach, Move, Rotate |
| French | Voir, Masque, Choisir, Lier, **Ombre**, **Onglet** |
| German | **Sicht**, **Wählen**, **Binden**, **Sichern**, Schatten, Bewegen |
| Italian | Vista, **Scegli**, **Unisci**, **Muovi**, Immagine, Maschera |
| Spanish | Ver, **Elegir**, **Rejilla**, **Abrir**, Pestaña, Máscara |
| Portuguese | Ver, **Girar**, **Unir**, **Abrir**, Selecionar, Máscara |
| Hebrew | right-to-left layout, mirrored |

Also check the **Create Group** button top-right is fully readable — it sets
the floor on how narrow the panel can go (it needs 104-117px depending on
language, and gets 123px).

## The scrollbar cases

`scrollbar/` has 30 layers loaded so the layer list must scroll. The
scrollbar should sit in its own strip **beside** the layer buttons, never
over their right edge. It is deliberately subtle in the dark theme.

## Regenerating

```
python automation_tests/capture_review_matrix.py            # everything here
python automation_tests/capture_many_layers_scrollbar.py    # scrollbar cases first
```

`capture_review_matrix.py` exits non-zero and lists the offenders if any
screen is not clean, so it doubles as a regression check.

To open a case live and interactive instead of as an image:

```
python automation_tests/preview_screen_ratio.py macbook13
python automation_tests/preview_screen_ratio.py air13_more_space
```
