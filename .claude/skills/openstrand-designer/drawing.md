# Drawing your own designs

When no ready design fits, draw one: describe each cord's centerline and
`openstrand draw` (the agent's `draw_design` tool) turns it into real
attached strands, with over and under at every crossing.

```
python -m openstrand draw design.json --out designs/x.json
python -m openstrand render designs/x.json --out designs/x.png
```

## The canvas

- Coordinates in px, y grows downward. The samples sit in about x 0-1200,
  y 0-800, centred near (600, 400). Every point must stay in -1000..4000.
- Cord width (`width`) 8-60 px; the samples use 18-30. Default 24.
- The picture is fitted to the design, so absolute size matters only
  relative to the cord width.

## A design

```text
{"name": "my design",
 "weave": "alternate",
 "cords": [ <cord>, <cord>, ... ]}
```

Up to 12 cords, together at most 30000 px long. Each cord is one of:

- **points** the cord passes through, smooth by default
  (`"smooth": false` for straight segments):
  `{"points": [[420, 640], [500, 420], [640, 300]], "closed": false}`
- **parametric** curve, any formula in t (numbers, + - * / % **, pi, tau,
  sin cos tan asin acos atan atan2 sqrt exp log abs floor ceil min max hypot
  sign pow radians):
  `{"x": "600 + 200*cos(t)", "y": "400 + 120*sin(2*t)", "t0": 0, "t1": "2*pi", "closed": true}`
  (`steps`, 100-20000, default 4000, is how finely t is sampled.)
- **shape**: `circle` (center, radius), `ellipse` (center, rx, ry,
  rotation), `polygon` (center, sides 3-12, radius, rounding, rotation),
  `heart` (center, size = width in px, rotation), `turks_head` (center,
  leads, bights, inner, outer). Shapes are closed.

Every cord may add `color` (name or hex), `width`, `label` (its group name in
the layer panel), `second_color` (the cord changes color under a crossing; it
needs a crossing it passes under besides the one hiding a closed cord's ends,
or the report says it stayed one color) and `tucked: true` (it passes under
everything).

`weave` is `alternate` (default: every cord goes over, under, over… along
its length) or `alternate_under_first`.

## Rules that make a good drawing

1. **A closed cord must cross something**, another cord or itself: its two
   ends meet hidden under a crossing. Otherwise make it open.
2. **Cross steeply**: 40 degrees or more. Nearly parallel cords overlap for a
   long way and their shading smears; the report warns below 25 degrees.
3. **Space crossings** at least two cord widths apart, and keep a third cord
   out of the spot where two cross: the report calls that a crowded crossing.
   A cord given heights (a tight knot) has one at every crossing, so for it
   the report ends with the mask check instead: the exact places where a mask
   or a crossing is drawn wrong, each with the edit that fixes it
   (`openstrand masks`, `openstrand edit-mask`, or `check_masks` and
   `edit_mask` for the agent).
4. **Read the report** after each draw: crossings per cord, which cord is on
   top at each crossing, over/under conflicts (places where alternation
   cannot hold), and warnings. Then render and look.
5. Change one thing at a time and draw again with the whole design.

## Strategies

- **Repeated loops along a line** (chains, sinnets, loop stitches): a looped
  curve, the prolate cycloid. Going up the page:
  `x = X - b*cos(t)`, `y = Y - (a*t - b*sin(t))`. It makes one loop per 2*pi of
  t when b > 1.3*a; a sets the spacing (2*pi*a px per loop), b the loop size.
  A mirrored copy (`x = X + b*cos(t)`) shifted up by a*pi interlocks with it.
- **Symmetric knots**: a parametric curve. The trefoil is
  `x = 600 + 95*(sin(t) + 2*sin(2*t))`, `y = 400 + 95*(cos(t) - 2*cos(2*t))`;
  rose and Lissajous curves (`sin(3*t)`, `sin(2*t)`) give many-crossing knots.
- **Rings and links**: shapes that overlap; two circles whose centres are
  less than the sum of their radii apart link like a chain.
- **Freehand knots** (pretzel, bends, loops with tails): 6-15 points the cord
  passes through, crossing itself where the knot does.
- **Unknown structure**: decide how many cords, where each runs, where they
  cross and which goes over; sketch it as points first, then refine.

## Worked examples

**Butterfly stitch** (also called rabbit ears): two strands, each forming a
loop that the other colour passes through, each colour on its own side, a
chain of interlocking loops. Two looped curves, columns 90 px apart, the
second shifted by half a loop; checked to keep crossings over 100 px apart
and steeper than 80 degrees:

```json
{"name": "butterfly stitch", "cords": [
  {"label": "Left loops", "color": "teal", "width": 22,
   "x": "555 - 125*cos(t)", "y": "900 - (48*t - 125*sin(t))", "t0": 0, "t1": "6*pi", "steps": 8000},
  {"label": "Right loops", "color": "gold", "width": 22,
   "x": "645 + 125*cos(t)", "y": "900 - 48*pi - (48*t - 125*sin(t))", "t0": 0, "t1": "6*pi", "steps": 8000}]}
```

**Trefoil knot**:

```json
{"cords": [{"x": "600 + 95*(sin(t) + 2*sin(2*t))", "y": "400 + 95*(cos(t) - 2*cos(2*t))",
            "t1": "2*pi", "closed": true, "color": "jade", "width": 28, "label": "Trefoil"}]}
```

**Two linked rings**:

```json
{"cords": [
  {"shape": "circle", "center": [480, 400], "radius": 180, "color": "teal", "label": "Left ring"},
  {"shape": "circle", "center": [720, 400], "radius": 180, "color": "gold", "label": "Right ring"}]}
```

**Pretzel (overhand) knot with tails**:

```json
{"cords": [{"label": "Pretzel", "color": "copper", "width": 26, "points": [
  [420, 640], [500, 420], [640, 300], [760, 360], [740, 480], [600, 520],
  [460, 480], [440, 360], [560, 300], [700, 420], [780, 640]]}]}
```

**Lissajous knot** (7 crossings):

```json
{"cords": [{"x": "600 + 320*sin(3*t + pi/2)", "y": "400 + 230*sin(2*t)", "t1": "2*pi",
            "closed": true, "color": "violet", "width": 20, "steps": 6000}]}
```
