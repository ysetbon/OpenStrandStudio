# Writing a knot recipe

A recipe is one JSON file that holds a knot and its tutorial: every cord as
the points it passes through, the reference (O or U at every crossing each
cord passes, in order), and the tying steps. `openstrand/recipes.py` describes
the format; `craft_library/macrame/recipes/larks_head_knot.json` is a short
example to copy from.

## Where to work

A new recipe is a candidate until it has been judged. Write it to
`designs/candidates/<name>/<name>.json` (that folder is ignored by git) and
nowhere else. `<name>` is the recipe's `"name"`: lower case, underscores.

## Trying it

```
export QT_QPA_PLATFORM=offscreen
python -m openstrand recipe designs/candidates/<name>/<name>.json
```

It prints, for every cord, the crossings it passes in order from its first
point, each with its place. Then it checks the drawing against `"patterns"`,
builds every step, reads each one back as the app draws it, and renders them:
`<name>_steps.png` shows all steps side by side. It ends with `PASS` or with
an error that says what to change.

- The number of letters in a cord's pattern is the number of crossings it
  passes. A cord that crosses itself passes that crossing twice: one O, one U.
- Where two cords cross, one says O and the other U.
- `python -m openstrand recipe FILE --alternate` only lists the crossings and
  prints the patterns that go over, under, over along every cord. Use it for
  a braid or a weave; it says so when the drawing cannot alternate.
- When the patterns come from a brief, they are the definition of the knot.
  If the drawing does not pass them, move the points. Never change the
  letters to make an error go away.

## Laying out the cords

- Canvas about x 150 to 1050, y 80 to 720; y grows downward. A tall design
  may go further down.
- Cord width 22 to 24.
- Crossings at least 70 px apart. Cords cross at 45 degrees or more, best
  near 90.
- A rounded turn has at least four points. A straight cord is two points and
  `"smooth": false`.
- Every end runs on at least 80 px past its last crossing.
- Points may be written by hand or made by a small script kept in the same
  candidate folder. A symmetric knot is best made from a formula.

## The steps

- Three to six steps. The first shows what is laid down first; each next step
  adds one move; the last shows every cord `"all"`.
- `"shown"` has one entry per cord: `null` (not yet), `"all"`, or
  `{"after": n}`: the cord drawn past its n-th crossing, half way to the
  next. Read n from the list of crossings the command prints.
- `"arrow"` is the number (from 0) of the cord that moves in this step; the
  picture gets an arrow on its end. Leave it out of the last step.
- A caption is one or two plain sentences that say what to do, and say over
  and under exactly as the patterns do (O: over, in front; U: under, behind).
  It ends with a full stop.

## Before reporting

Look at `<name>_steps.png` and at the last step's picture. Check that each
caption says what its picture shows, that nothing is cramped or lopsided, and
that the knot looks like the real one. Say plainly what does not match.
