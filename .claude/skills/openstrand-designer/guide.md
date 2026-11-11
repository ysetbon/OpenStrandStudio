# OpenStrand guide

What a designer needs to know to turn a request into `openstrand` commands.

## Projects

- A project is a list of **strands**. Each is a curved band from a start to an
  end point, with control points that shape the curve.
- A **set** is one cord: a main strand (`1_1`) and the strands attached to it in
  a chain (`1_2`, `1_3`, ...). Set 2 is `2_1`, `2_2`, ... One set has one color.
- **Masks** make over and under: where two strands cross, a mask hides the one
  underneath. A well woven design alternates over, under, over along every cord.
  A mask is named by its two strands, the one on top first (`1_1_2_1`: 1_1
  over 2_1), and can have erase boxes (Edit Mask) that take part of it away.
  Where cords touch (a knot pulled tight, a stretched stitch, a Turk's head
  with a small inner radius) a mask can cover a strand beside its crossing:
  check_masks finds such places and edit_mask fixes them.
- **Groups** name parts of a design ("Turk's head", "Gold lacing") in the app's
  layer panel.
- Files: the app saves plain projects and history files (with undo states).
  The command reads both and writes plain projects.

## Turk's heads (`make turks_head`)

A ring knot woven in a round, as on a sailor's mat or a bracelet.

- **Leads**: how many times the cord goes around the ring.
- **Bights**: the loops on the rim, counted around the outside.
- Crossings = bights x (leads - 1).
- Leads and bights must share no factor, or the design falls apart into
  separate cords: 3 and 5 works, 3 and 6 does not.
- Known names: trefoil = 2 leads x 3 bights; figure-eight = 3 x 2;
  cinquefoil = 2 x 5; Carrick mat = 3 x 4.
- Published sizes copy instantly: 2x3, 3x2, 2x5, 2x7, 3x4, 3x5, 4x3, 4x5.
  Other sizes are fitted from scratch (a minute or two).
- `--width` (cord width, px) and `--inner` (inner radius, px; outer is 290)
  change the look. Thin cords suit many bights.

## MxN stitches (`make mxn`)

A woven patch of ribbons, the base of many bracelets and braids.

- **m** vertical ribbons, **n** horizontal ribbons, each 1 to 8.
- **Hand**: `lh` (left) or `rh` (right), mirror images of each other.
- **Stretched** (`--stretch`): ribbons packed closer, no sideways offset.
- Each ribbon is its own set. `openstrand info` says which sets run vertical
  and which horizontal, so a two-color weave is two recolor commands.

## Hearts (`make heart`)

A ribbon heart from one cord whose two ends cross below the tip. `--color`
and `--width` change it.

## Samples (`make sample NAME`)

Ready-made designs from `knot_samples/` (knots, Turk's heads, links such as
hopf_link, borromean_rings, solomons_knot, five_ring_chain) and `mxn_samples/`.
`openstrand samples <word>` searches them.

## The craft library (`samples <any name>`, the agent's `search_samples`)

Designs by craft, found by any name people use for them. Each match says
what it is and ends with the exact command or tool call that makes it: run
that one. Search before you draw anything.

- **Boondoggle** (scoubidou, gimp, lanyard, plastic lace): every stitch is an
  MxN stitch. Box or square stitch = 1x1 (two strings); brick stitch = 2x1
  (three strings); any other size is `make mxn`.
- **Macrame**: the square knot (cobra knot, Solomon bar), with tying steps;
  the lark's head knot (cow hitch, mounting knot) and its reverse, shown loose.
- **Chinese knotting**: double coin, cloverleaf, good luck, Pan Chang (mystic
  or endless knot), shown finished and flat.
- **Knitting**: the magic knot that joins two yarns, with tying steps.
- **Crochet**: nothing ready-made yet: say so, then draw it.
- **Knots**: every knot `tie` makes, by all its names.

## Knots by name (`tie`)

`openstrand tie NAME` (the agent's `tie_knot`) makes a knot with its tying
steps, every step checked to be that knot, crossing by crossing.

- Stopper knots tied in one cord: overhand, figure-eight, double overhand,
  stevedore, triple overhand. Simulated with a real cord: laid out, drawn up,
  pulled tight.
- Knots that join two cords (bends): square knot (reef knot), sheet bend
  (weaver's knot), fisherman's knot (the knitters' magic knot), double
  fisherman's knot (grapevine), and the granny knot, shown so it can be told
  from a square knot. A loop knot: bowline. Macrame: the square knot round
  two filler cords. From a checked drawing, shown loose.
- These do not alternate over and under, so a freehand drawing of one comes
  out as another knot: use `tie`.

## Words people use

| They say | Build |
| --- | --- |
| mat, round mat, ring, coaster, sailor's knot | `make turks_head` |
| trefoil, three-lobed knot | `make turks_head --leads 2 --bights 3` |
| Carrick mat | `make turks_head --leads 3 --bights 4` |
| stitch, weave, bracelet weave, braid, basket weave | `make mxn` |
| boondoggle, scoubidou, gimp, lanyard, plastic lace | `samples boondoggle`, then `make mxn` |
| box stitch, square stitch | `make mxn --m 1 --n 1` |
| brick stitch | `make mxn --m 2 --n 1` |
| Chinese knot, mystic knot, Pan Chang, double coin, good luck knot | `samples "chinese knot"`, then `make sample NAME` |
| macrame, crochet, knitting, any knot or stitch by name | `samples <the name>` first |
| "4 by 3", "4x3" | `--m 4 --n 3` |
| left-handed / right-handed | `--hand lh` / `--hand rh` |
| tight, packed, close together | `--stretch` |
| heart, love knot (simple) | `make heart` |
| linked rings, chain | `make sample` with a link sample |
| how to tie, tutorial, steps for a knot | `tie NAME`, then its steps |
| square knot, reef knot | `tie "square knot"` |
| magic knot, fisherman's knot, joining two yarns | `tie "fisherman's knot"` |
| sheet bend, weaver's knot | `tie "sheet bend"` |
| bowline, a loop that does not slip | `tie bowline` |
| macrame square knot, cobra knot | `tie "macrame square knot"` |

## Colors

Names: teal, gold, rose, violet, jade, copper, ink, crimson, sky, red, yellow,
orange, green, blue, purple, pink, brown, black, white, grey; or hex like
`#c83e4d`. "Red and gold" on a stitch usually means one color for the
vertical ribbons and the other for the horizontal ones.

## Checking a picture

- Count what the request names: bights around the rim, ribbons each way.
- Every crossing shows one cord clearly on top.
- Colors match, set by set.
- Nothing is cut off at the edge of the picture.
