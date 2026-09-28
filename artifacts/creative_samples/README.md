# Additional sample collection

Six extra application samples: Woven Heart, Tidal Waves, and four
Chinese-knot studies: Double Coin, Cloverleaf, Good Luck and Pan Chang. The
original twelve application samples are unchanged.

- **Woven Heart**: three exactly parallel heart ribbons (closed loops built from
  arcs and tangent lines) with three gold laces woven through them in a
  checkerboard.
- **Tidal Waves**: three rows of rolling, looping crests. Each row threads
  through the loops of the row above; a gold sun rises behind the top row.
- **Chinese Double Coin**: a mirror-symmetric single cord with eight
  alternating crossings and two tails.
- **Chinese Cloverleaf**: four heart-shaped leaves interlocking on one closed
  red cord, with a gold stem tucked under the centre.
- **Chinese Good Luck**: three large and four small ears around a star-woven
  centre, with two tails.
- **Chinese Pan Chang**: the first collection's geometry, now entirely red.

These are editable planar studies rather than step-by-step tying instructions.

## How the projects are built

`scripts/generate_creative_samples.py` draws each design as a smooth, dense
centerline, then `scripts/sample_geometry.py` fits it into the fewest attached
strands it can: each strand's two control points carry as long a stretch of
the design as they can. A span must stay within 2.5 px of the design and follow
its direction within 6 degrees (more on short, tight bends), so long spans
cannot hide flat spots on round shapes. Joins keep the design's tangent; a
cord's loose ends choose their own handles, so each Woven Heart lace is a
single strand. The fitting uses the live canvas curvature defaults (1, 2, 2).

Every join splits the shadows around it into pieces, so joins are kept out of
crossings and, as far as they can be, out of the reach of any shadow: a join
closer to another strand than a shadow's width costs up to four extra strands
in the fit.

Over/under is solved for all cords at once: consecutive crossings along every
cord must alternate, which gives parity constraints between crossings. Hidden
ends pass under, and closing joins are placed where their cord passes under.
Two strands never cross each other both ways: a join goes between two such
crossings, in the most open spot.

The layer order then draws the upper strand of each crossing later wherever it
can, so most crossings need no mask and are shaded from the strands' own
outlines. Each attached strand stays above the strand it attaches to (it
covers their join). An open cord's first strand may sit in the middle of the
cord, with strands attached outwards from both of its ends; it sits where the
fewest masks remain. Every remaining crossing whose upper strand is drawn
first is realised with a MaskedStrand that covers its whole overlap.

A colour change and the join of a closed design are hidden under a covering
crossing: the first would draw a round notch, the second is a chain whose
flat, line-free ends meet there.

The Cloverleaf stem tucks under every leaf; the Woven Heart laces alternate
along their length and start on alternate sides. Every other cord alternates
strictly along its whole length.

Regenerate the six projects and their previews from the repository root with:

```sh
python scripts/generate_creative_samples.py --preview artifacts/creative_samples
```

The generator reloads each JSON and checks strand counts, attachment endpoints,
attachment lengths, control points, group references and nonempty masks. The
previews and `contact_sheet.png` are captures of the real application canvas,
with shadows, in an isolated offscreen MainWindow.

`verify_ui.py` checks loading, group restoration, snapshot serialization,
translations, and access to all eighteen sample buttons in the real
application running offscreen. `review_in_app.py NAME --tag final` opens one
sample in an isolated real MainWindow. It checks that the loaded curves match
the validated geometry, captures the painted canvas with shadows, and checks
that control points and mask erasures survive serialization. The six final
canvas captures in `review/` come from this script.

Knot structure references: Carol Wang's
[Double Coin](https://chineseknotting.org/coin/howto2/),
[Good Luck](https://chineseknotting.org/luck/howto4/) and
[Pan Chang](https://chineseknotting.org/mystic/) guides. Reference photographs
are not distributed with these samples.
