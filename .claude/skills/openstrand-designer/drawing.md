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
- **tool**: what the cord is worked with, a straight stick from its handle
  (`from`) to its tip (`to`): `hook` (a crochet hook, round head with a barb),
  `needle` (a knitting needle, pointed) or `stick` (a rod, a peg, a finger).
  Grey and 34 px wide unless you say otherwise. It is woven like a cord:
  `{"tool": "hook", "from": [880, 160], "to": [530, 112], "height": 20}`

Every cord may add `color` (name or hex), `width`, `label` (its group name in
the layer panel), `second_color` (the cord changes color under a crossing; it
needs a crossing it passes under besides the one hiding a closed cord's ends,
or the report says it stayed one color) and `tucked: true` (it passes under
everything).

`weave` is `alternate` (default: every cord goes over, under, over… along
its length) or `alternate_under_first`.

**Heights** say what really lies on top, instead of alternating: where two
parts that both have a height cross, the higher one goes over. A points cord
takes `heights`, one number per point (the cord rises and dips between them);
any cord takes `height`, one number for all of it; a tool takes `height` or
`heights` of two numbers (handle, tip). Use them whenever over and under
matter: a loop lying on the table is 0, the end laid over it 20, a part that
passes behind it -20; a hook at 10 goes into a loop whose near side is 20 and
far side 0. Give heights to every cord of such a picture.

**Arrows** show a move: `"arrows": [{"points": [[700, 520], [760, 420], [860,
380]]}]` beside `"cords"`, from tail to head, 2 to 12 points, red unless
`color` says otherwise, at most 8. An arrow is not a cord: it is drawn on top
of everything, crosses nothing and gets no mask (in the app it is a hidden
strand showing its full arrow, so the person can move or delete it). Never
draw an arrow as a cord.

## Over and under by hand: `pattern`

Many knots do not alternate. In a square knot both ends of each cord go over
the other cord's turn; in a sheet bend the working cord passes under both
legs of the bight. Woven over, under, over they come out as other knots (a
square knot becomes a granny). For these, say which part is on top: give a
cord a `pattern`, one letter for each crossing it passes, in order from its
first point: `O` where it goes over, `U` where it goes under.

`{"points": [...], "pattern": "OUOOUO"}`

- A crossing of two cords is in both cords' patterns; a pattern on one of
  them is enough. If both speak, they must agree (one `O`, one `U`). `-`
  leaves a crossing to the other cord, or to the weave.
- A cord that crosses itself passes that crossing twice: two letters, one
  `O` and one `U`.
- Crossings no pattern speaks of alternate as before.
- The report lists every cord's crossings in the order it passes them, with
  the place of each, and the pattern as drawn. To turn one crossing the other
  way, copy that pattern, change its letter and draw again. A pattern with
  the wrong number of letters is refused with the same list.
- A design with a pattern ends its report with the mask check: every
  crossing shows the cord on top all over, or the places that do not.

The common knots that join cords or make a loop are ready-made and checked:
`openstrand tie "square knot"` (the agent's `tie_knot`), also sheet bend,
bowline, fisherman's knot (magic knot), double fisherman's knot, macrame
square knot. Draw one by hand only when it is not in that list
(`openstrand tie --list`), and check it with `openstrand identify`.

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
  passes through, crossing itself where the knot does. A knot of two cords:
  one cord per rope, each its own color, and a `pattern` wherever it does not
  alternate.
- **Unknown structure**: decide how many cords, where each runs, where they
  cross and which goes over; sketch it as points first, then refine.

## Steps drawn one by one

A tutorial whose pictures differ from step to step (a crochet or knitting
stitch, a slip knot, a hitch, a loop knot: the cord moves, a loop is pulled
through, a hook goes in) is one `draw_steps` design: every step is its own
drawing, and all of them are drawn in one call.

```
python -m openstrand draw-steps steps.json --out-dir designs/slip_knot
```

writes `step_1.json`, `step_2.json`, ... and `steps.png`, one picture of all
the steps side by side, numbered and titled (the agent's `draw_steps` returns
that picture).

```text
{"name": "what it shows",
 "steps": [ {"title": "...", "keep": [...], "cords": [...], "arrows": [...]}, ... ]}
```

- `title`: what the step does, as an instruction: "Pull the yarn through".
- `cords`: as in a design. Label every cord: labels tie the steps together.
- `keep`: the labels of the cords that stay exactly as in the step before
  (or `"all"`). A cord in `cords` with a label of the step before is that
  cord redrawn: it moved. Anything neither kept nor redrawn is gone.
- `arrows`: the move that leads to the next step. They belong to their step
  only.
- Up to 12 steps. Each step's masks are checked and the safe fixes made; the
  report says what is left.
- To change steps after a first call, the agent sends only those in
  `"replace": [{"step": 3, "title": ..., "cords": ...}]`; the number after the
  last adds a step.

How to plan them:

1. One move per step, three to six steps, the last one the finished thing.
2. Keep the same place and size from step to step: the part that does not
   move keeps its points, so the eye follows the part that does.
3. Copy the points of the cord from the step before and change only the
   stretch that moved; add points where it now goes.
4. Heights on every cord that crosses another (see Heights above).
5. Leave room: crossings two cord widths apart, loops at least four wide.
6. Look at the picture of all steps; in a slip knot's last steps `identify`
   must still find no knot in the yarn ("no knot: the cord would slip free",
   or "not knotted on its own" with the hook there): an overhand knot is not
   one.

**Slip knot on a crochet hook** (the start of crochet and knitting): a loop,
the working yarn laid behind it, caught by the hook and pulled up through as
a new loop, then drawn tight. One yarn, redrawn as it moves; the hook dips
from 20 at its handle to -40 at its tip to go into the loop and under the
yarn behind it:

```json
{"name": "Slip knot on a hook", "steps": [
  {"title": "Make a loop, working yarn on top",
   "cords": [{"label": "Yarn", "color": "teal", "width": 22,
     "points": [[320, 620], [470, 515], [640, 485], [760, 380], [720, 240], [600, 190], [480, 260],
                [465, 400], [560, 510], [680, 590], [830, 620]],
     "heights": [0, 0, 0, 0, 0, 0, 0, 0, 20, 20, 20]}],
   "arrows": [{"points": [[850, 560], [880, 420], [800, 320]]}]},
  {"title": "Lay the working yarn behind the loop",
   "cords": [{"label": "Yarn", "color": "teal", "width": 22,
     "points": [[320, 620], [470, 515], [640, 485], [760, 380], [720, 240], [600, 190], [480, 260],
                [465, 400], [560, 510], [680, 590], [810, 530], [810, 400], [650, 345], [420, 340], [290, 335]],
     "heights": [0, 0, 0, 0, 0, 0, 0, 0, 20, 20, 0, -20, -20, -20, -20]}]},
  {"title": "Hook into the loop and under the working yarn",
   "keep": ["Yarn"],
   "cords": [{"tool": "hook", "from": [900, 110], "to": [560, 400], "heights": [20, -40]}],
   "arrows": [{"points": [[590, 300], [600, 200], [640, 110]]}]},
  {"title": "Pull a loop of the working yarn up through",
   "cords": [{"label": "Yarn", "color": "teal", "width": 22,
     "points": [[320, 620], [470, 515], [640, 485], [760, 380], [720, 240], [600, 190], [480, 260],
                [465, 400], [560, 510], [680, 590], [810, 530], [800, 420], [720, 360], [655, 320],
                [640, 240], [640, 120], [610, 75], [580, 120], [580, 240], [560, 320], [500, 345],
                [420, 340], [290, 335]],
     "heights": [0, 0, 0, 0, 0, 0, 0, 0, 20, 20, 0, -20, -20, 0, 15, 10, 20, 30, 25, 0, -20, -20, -20]},
    {"tool": "hook", "from": [880, 160], "to": [530, 112], "height": 20}]},
  {"title": "Pull both ends: the knot closes on the hook",
   "cords": [{"label": "Yarn", "color": "teal", "width": 22,
     "points": [[330, 640], [450, 575], [600, 545], [662, 480], [600, 418], [538, 480], [560, 560],
                [640, 600], [720, 560], [715, 490], [640, 478], [628, 450], [625, 380], [625, 300],
                [600, 205], [575, 300], [575, 380], [572, 450], [555, 478], [440, 500], [320, 520]],
     "heights": [0, 0, 0, 0, 0, 0, 20, 20, 0, -20, -20, 10, 10, 10, 20, 30, 30, 30, -20, -20, -20]},
    {"tool": "hook", "from": [880, 275], "to": [430, 240], "height": 20}],
   "arrows": [{"points": [[470, 645], [380, 705]]}, {"points": [[440, 455], [325, 470]]}]}
]}
```

In step 4 the new loop's two legs are at 10 and 30 and the hook at 20: the
hook passes over one leg and under the other, so it is through the loop.

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

**Square knot** (reef knot), with a `pattern`: two bights hooked through
each other. Both legs of the teal cord go over the gold cord's turn, its own
turn goes over both gold legs, and the gold cord is on top where the legs
cross in the middle. One pattern says it all, since the teal cord passes
every crossing; without it the weave would alternate and make a granny knot.
(`openstrand tie "square knot"` makes this one, with its tying steps.)

```json
{"name": "square knot", "cords": [
  {"label": "First cord", "color": "teal", "width": 24, "pattern": "OUOOUO", "points": [
    [120, 435], [296, 435], [500, 435], [560, 448], [600, 473], [640, 497], [700, 510], [800, 510],
    [878, 478], [910, 400], [878, 322], [800, 290], [700, 290], [640, 303], [600, 327], [560, 352],
    [500, 365], [296, 365], [120, 365]]},
  {"label": "Second cord", "color": "gold", "width": 24, "points": [
    [1080, 365], [904, 365], [700, 365], [640, 352], [600, 327], [560, 303], [500, 290], [400, 290],
    [322, 322], [290, 400], [322, 478], [400, 510], [500, 510], [560, 497], [600, 473], [640, 448],
    [700, 435], [904, 435], [1080, 435]]}]}
```

**Lissajous knot** (7 crossings):

```json
{"cords": [{"x": "600 + 320*sin(3*t + pi/2)", "y": "400 + 230*sin(2*t)", "t1": "2*pi",
            "closed": true, "color": "violet", "width": 20, "steps": 6000}]}
```
