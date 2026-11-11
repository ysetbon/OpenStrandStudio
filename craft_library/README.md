# Craft library

Ready-made designs by craft (boondoggle, macrame, Chinese knotting, knitting,
crochet, knots), found by any name people use for them. `catalog.json` is the
whole library: one entry per design.

**This is a backend library.** Only the `openstrand` command and the agent read
it (`openstrand/library.py`). Nothing here appears on the Samples page of the
app's settings, and the folder is not part of the app's installers, so the
library can grow without the Samples page growing with it.
`tests/test_craft_library.py` fails if either stops being true.

```
python -m openstrand samples boondoggle
python -m openstrand samples "mystic knot"
python -m openstrand make sample chinese_pan_chang --out designs/pan_chang.json
```

The agent uses the same lookup: `search_samples` with the person's words, then
the tool call the match ends with.

## An entry

```json
{
  "name": "box_stitch",
  "craft": "boondoggle",
  "title": "Box stitch",
  "also": ["square stitch", "scoubidou", "two-string stitch"],
  "about": "One or two sentences: what it is, how it is built, what is shown.",
  "build": {"mxn": {"m": 1, "n": 1}}
}
```

- `name`: unique, lower case with underscores; what `make sample` and
  `load_sample` take.
- `also`: every other name people use, any spelling. Search and `make sample`
  match these too.
- `patterns` (for a design drawn for the library): each cord's over and under
  in order, `O` or `U` at every crossing it passes, as the design must read
  back. The tests check the file against it, and that its masks are right.
- `build`, one of:
  - `{"file": "craft_library/<craft>/json/<name>.json"}`: a project file in
    this repository.
  - `{"sample": "hopf_link"}`: a published file in `knot_samples/` or
    `mxn_samples/`.
  - `{"mxn": {"m": 2, "n": 1}}` (also `hand`, `stretch`), or
    `{"turks_head": {"leads": 3, "bights": 4}}`: a generator with its sizes.
  - `{"tie": "bowline"}`: a knot `openstrand tie` makes, with its tying steps.
  - `{"make": "mxn"}`: a whole family; the size comes from the request.

The knots `tie` makes are listed from their own libraries
(`openstrand/tying.py`, `openstrand/bends.py`); they need no entry here unless
a craft has its own name for one (knitting's magic knot).

## A recipe: a knot with its tying steps

`<craft>/recipes/<name>.json` holds a knot as data: its cords, the reference
(O or U at every crossing each cord passes) and the tying steps with what to
do at each. A recipe needs no entry in `catalog.json`: it is listed from its
own file, and `openstrand tie "<its title>"` makes its steps, every one
checked. `AUTHORING.md` says how to write one and try it with
`openstrand recipe`.

## Adding a design

1. Build it with the `openstrand` command, never by hand: keep the drawing
   it was made from under `craft_library/<craft>/spec/` (`openstrand draw`
   makes the project from it again), the project under
   `craft_library/<craft>/json/`, its picture under
   `craft_library/<craft>/images/`.
2. Check it: `validate`, `masks`, `identify`, and look at the render beside a
   picture of the real thing.
3. Add its entry to `catalog.json`. A file with no entry is not in the library.
4. Do not add it to `SettingsDialog.SAMPLES` or `src/samples/`.
