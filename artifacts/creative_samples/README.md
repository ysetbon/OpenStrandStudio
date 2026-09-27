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
strands whose native two-handle curves stay within 0.8 px of the design, with
the design's own tangents at every join. A span may also turn through at most
45 degrees, because a longer native curve bends unevenly and shows flat spots
on round shapes. The fitting uses the live canvas curvature defaults (1, 2, 2).

Over/under is solved for all cords at once: consecutive crossings along every
cord must alternate, which gives parity constraints between crossings. Hidden
ends pass under, and closing joins are placed where their cord passes under.
Every stroke overlap is then assigned to its crossing and realised with a
MaskedStrand. The whole overlap is covered, joins are kept out of crossings
(farther at shallow crossings), and a mask is erased only where the same pair
crosses the other way. Two things would otherwise show, so they are hidden
under a covering crossing:

- a colour change, whose attachment circle draws a round notch;
- the join of a closed design, built as a chain whose flat, line-free ends meet
  there.

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
