# Knot and link samples

Fifteen classical knots and links as editable OpenStrandStudio projects, each with a picture of it on the real canvas (shadows included). They have nothing to do with the MxN stitches; each design is a smooth closed cord, or several, woven so that every cord alternates over and under along its whole length.

```
knot_samples/
├── knots/         single knots (5)
├── turks_heads/   ring knots (4)
└── links/         several linked rings (6)
```

Each folder has a `json/` folder with the projects and an `images/` folder with the pictures, same file names.

## Knots (`knots/`)

| File | Knot | Crossings |
| --- | --- | --- |
| `trefoil_3_1` | Trefoil, 3₁ | 3 |
| `figure_eight_4_1` | Figure-eight, 4₁ | 4 |
| `cinquefoil_5_1` | Cinquefoil, 5₁ | 5 |
| `septafoil_7_1` | Septafoil, 7₁ | 7 |
| `triquetra` | Celtic triquetra: a trefoil threaded by a ring | 9 |

## Turk's heads (`turks_heads/`)

Ring knots woven in a round. Leads are the turns a cord makes around the ring and bights are the loops on its rim. A knot with *L* leads and *B* bights has *B × (L − 1)* crossings, which gives the trefoil (2 × 3) and the figure-eight (3 × 2) above as well.

| File | Knot | Crossings |
| --- | --- | --- |
| `carrick_mat_3x4` | Carrick mat, 3 leads × 4 bights | 8 |
| `turks_head_3x5` | 3 leads × 5 bights | 10 |
| `turks_head_4x3` | 4 leads × 3 bights | 9 |
| `turks_head_4x5` | 4 leads × 5 bights | 15 |

## Links (`links/`)

| File | Link | Crossings |
| --- | --- | --- |
| `hopf_link` | Hopf link, two rings | 2 |
| `solomons_knot` | Solomon's knot, two loops linked twice | 4 |
| `borromean_rings` | Borromean rings: no two are linked, yet the three cannot be separated | 6 |
| `interlaced_triangles` | Two interlaced triangles (a hexagram) | 6 |
| `five_ring_chain` | A chain of five rings | 8 |
| `six_link_necklace` | Six rings closed into a necklace | 12 |

## How they are built

`scripts/generate_knot_samples.py` draws each design as a dense centerline and fits it into the fewest attached strands, using the same fitting and weave solver as `scripts/generate_creative_samples.py`. Each project is reloaded and validated, then captured in an offscreen MainWindow. Regenerate everything from the repository root with:

```sh
python scripts/generate_knot_samples.py
```

The rosette knots follow `r = mean + swing · cos(B·θ / L)` for `L` turns, which is why a single formula covers the trefoil, cinquefoil, septafoil, figure-eight and the Turk's heads. The weave solver reported no conflicts for any of the fifteen designs. The triquetra has one minor warning, a short overlap between its ring and a lobe that is not a crossing.
