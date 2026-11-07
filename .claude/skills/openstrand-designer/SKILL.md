---
name: openstrand-designer
description: Build OpenStrand Studio projects (.json) from a text request or a reference image, using the openstrand command in this repo. Use when asked to design, make or change a knot, mat, ring, Turk's head, stitch, weave, bracelet, heart or any strand pattern for OpenStrand Studio.
---

# OpenStrand designer

You make OpenStrand Studio projects by running the `openstrand` command from
the repository root. Never write project files or strand data by hand: give
the command a design (a sample, a generator, or your own cord centerlines for
`draw`) and it builds the strands with the app's own code, so they open
correctly.

Read `guide.md` (next to this file) before the first design in a session. It
explains sets, over and under, Turk's heads, MxN stitches and the words people
use for them. `drawing.md` explains how to draw any design yourself.

## Steps

1. **Understand the request.** Map the person's words to a design with the
   glossary in `guide.md`. With a reference image, describe what you see in
   those terms first: the kind of design, how many leads and bights or ribbons,
   the hand, the colors.
2. **Look for a starting point.** `python -m openstrand samples <word>` lists
   ready-made designs. Prefer a sample or a published size when one fits.
   When nothing fits, design it: search the web for what it is and how it is
   built (or reason it out when the web has nothing), plan the cords and
   crossings, write them as a JSON design (see `drawing.md`) and run
   `python -m openstrand draw design.json --out designs/x.json`.
3. **Build it.** Save every design under `designs/` (ignored by git):
   ```
   python -m openstrand make turks_head --leads 3 --bights 5 --color gold --out designs/mat.json
   python -m openstrand make mxn --m 4 --n 3 --hand lh --stretch --out designs/bracelet.json
   python -m openstrand make heart --color crimson --out designs/heart.json
   python -m openstrand make sample hopf_link --out designs/rings.json
   ```
   A Turk's head size that is not published, or a heart, is fitted from
   scratch and takes up to a minute or two. Wait for it.
4. **Set the colors.** `python -m openstrand info designs/x.json` lists the
   sets, their colors and which way each runs (vertical, horizontal). Then:
   ```
   python -m openstrand recolor designs/x.json --colors red,gold        # set 1, set 2, ...
   python -m openstrand recolor designs/x.json --set 4,5,6,7 --color teal
   ```
5. **Check it.**
   ```
   python -m openstrand validate designs/x.json
   python -m openstrand render designs/x.json --out designs/x.png
   ```
   Then open the PNG and look at it. Compare it with the request or the
   reference image: the count of loops, ribbons and crossings, the colors, and
   whether every cord goes over and under in turn.
6. **Fix and check again.** Change the arguments and repeat steps 3-5. Stop
   after 4 rounds and say what is still wrong.
7. **Report.** Give the project path, the picture, and the recipe: the exact
   commands that made it. Mention that the file opens in OpenStrand Studio.

## Knots tied in a cord

For how to tie a knot (overhand, figure-eight, double overhand, stevedore,
triple overhand), or a knot pulled tight, do not draw it: `tie` simulates a real
cord, tying it move by move and pulling it tight until it touches itself. It
checks every stage is the knot asked for, from its crossings and as drawn in
the app. Each step is its own project file:
```
python -m openstrand tie --list
python -m openstrand tie figure-eight --color crimson --out-dir designs/figure8
python -m openstrand tie --path designs/my_knot_path.json --out-dir designs/mine
python -m openstrand identify designs/x.json
```
A knot not in the library is given as its path: rough `[x, y]` points from
the standing end to the working end, crossing itself where the knot does, with
a few cord widths between parts, and `"pattern"` (O or U at each crossing along
the path; alternating by default). The checks name the knot the path makes; if
it is not the knot you meant, fix the path or the pattern. `identify` names the
knot any project shows; use it instead of judging over and under by eye.

## Masks in tight and crowded designs

A mask says which strand is on top where two cross. In a knot pulled tight
the parts of the cord touch and the joints between strands sit inside
crossings, so a mask can paint over a strand that lies beside its crossing, or
a crossing can show half one way and half the other. The same happens in any
crowded design: stretched MxN stitches, Turk's heads with a small inner radius,
cords drawn close together. `tie` already fixes what is safe in its finished
steps and prints `masks: fixed ...` and `masks: left ...`. For anything else,
or what is left:
```
python -m openstrand masks designs/x.json                     # every mask, every problem, with coordinates
python -m openstrand masks designs/x.json --repair            # fix what is safe
python -m openstrand edit-mask designs/x.json erase --mask 1_1_2_1 --covers 3_1 --preview
python -m openstrand edit-mask designs/x.json erase --mask 1_13_1_6 --at 497,386
python -m openstrand edit-mask designs/x.json create --first 1_3 --second 1_6
python -m openstrand edit-mask designs/x.json swap --mask 1_10_1_5 --preview
python -m openstrand edit-mask designs/x.json reset --mask 1_1_2_1
```
Each problem names the edit that fixes it; run that one, with `--preview`
first when unsure, and use the names and coordinates `masks` gives, never
guessed ones. `erase` takes `--at` (a place `masks` listed), `--covers` (a
strand to uncover), `--around` (a mask's whole piece at one crossing) or
`--box x0,y0,x1,y1`; the boxes are shaped along a strand's outline, and an
erase that would leave a cut is refused. `create` and `swap` trim the new
mask where it would paint the wrong way. After each edit the command checks
again and names the knot. Then render and look at each place you changed. A
place reported as "no single mask edit fixes it" stays as it is: say so.

## When the command cannot do it

Most shapes can be drawn with `openstrand draw`. If the request needs
something even drawing cannot do (an option the commands lack, editing one
strand of an existing design), build the closest thing, say plainly what is
missing, and add one line to `gaps.md` next to this file:

```
- <date> · <what was asked> · <what the command could not do>
```

Do not work around a missing command by editing the JSON yourself.

## Errors

The command prints `error: ...` and exits with status 1. The message says what
to change (for example a Turk's head whose leads and bights share a factor).
Follow it instead of guessing.
