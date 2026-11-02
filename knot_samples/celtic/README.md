# Celtic and Norse knotwork samples

Three knotwork designs in the style of Celtic and Viking-age interlace, as editable OpenStrandStudio projects. Each one comes with a picture of the real canvas, shadows included. Every cord alternates over and under along its whole length, which is the rule all Celtic and Norse interlace follows.

| File | Design | Layers | Masks |
| --- | --- | --- | --- |
| `valknut` | Valknut: three interlaced triangles in gold, oxblood and iron | 23 | 5 |
| `celtic_knot_panel` | Celtic knot panel: a single cord, a 3 × 4 Lissajous figure woven alternately | 24 | 9 |
| `shield_knot` | Shield knot: a four-lobed Carrick mat threaded by a gold ring | 29 | 9 |
| `bridal_lotus_mandala` | Celtic interlace on an Indian lotus: eight gold petals (3 × 8 Turk's head), an emerald ring and a red Carrick mat heart | 64 | 20 |
| `bridal_paisley` | A paisley (buta) whose curled tip crosses itself, holding a gold triquetra and an emerald ring | 25 | 5 |

The two bridal designs use sindoor red, zari gold and emerald, the colours of Indian wedding embroidery. `images/bridal_concept_sheet.png` shows them side by side.

`images/contact_sheet.png` shows the three designs next to the box stitch sample (`src/samples/box_stitch.json`).

Regenerate the projects and pictures from the repository root with:

```sh
python scripts/generate_celtic_samples.py
```

The script uses the same fitting and weave solver as `scripts/generate_knot_samples.py`. The Valknut triangles are offset across their sides, not along them; offsetting along them would make their sides coincide. The mandala's ring has radius 260, between the petals' crossings at radius 230 and 300; a ring through those crossings would crowd them. The Lissajous panel uses phase 0, because a phase of π/8 makes the 3 × 4 figure retrace itself.
