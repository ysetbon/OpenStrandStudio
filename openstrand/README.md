# openstrand command

Make, check, recolor and render OpenStrand Studio projects from a terminal.
It runs the app's own code (`src/`) and the sample generators (`scripts/`), so
a project made here opens in the app exactly as it was built. It is also the
tool the Claude Code skill in `.claude/skills/openstrand-designer/` uses.

Run it from the repository root (needs the packages in `requirements.txt`):

```
python -m openstrand make turks_head --leads 3 --bights 5 --color gold --out designs/mat.json
python -m openstrand make mxn --m 4 --n 3 --hand lh --stretch --out designs/bracelet.json
python -m openstrand make heart --color crimson --out designs/heart.json
python -m openstrand make sample hopf_link --out designs/rings.json
python -m openstrand draw my_design.json --out designs/mine.json
python -m openstrand tie figure-eight --color crimson --out-dir designs/figure8
python -m openstrand identify designs/figure8/figure_eight_knot_step_6.json
python -m openstrand masks designs/figure8/figure_eight_knot_step_6.json
python -m openstrand edit-mask designs/knot.json erase --mask 1_1_2_1 --covers 3_1
python -m openstrand samples turks
python -m openstrand info designs/bracelet.json
python -m openstrand recolor designs/bracelet.json --set 4,5,6,7 --color red
python -m openstrand validate designs/bracelet.json
python -m openstrand render designs/bracelet.json --out designs/bracelet.png
```

| Command | Does |
| --- | --- |
| `make turks_head` | A Turk's head ring knot, woven over and under. Published sizes are copied; others are fitted (a minute or two). |
| `make mxn` | An MxN stitch from `mxn_samples/` (m, n from 1 to 8, lh or rh, `--stretch`). |
| `make heart` | A ribbon heart from one cord (fitted, about a minute). |
| `make sample NAME` | A ready-made design from `knot_samples/` or `mxn_samples/`. |
| `draw SPEC` | Your own design from cords given as points, x(t)/y(t) curves or shapes; woven over and under, with a report of every crossing. See `.claude/skills/openstrand-designer/drawing.md`. |
| `tie KNOT` | Tying steps for a knot, one project per step: the cord laid move by move with an arrow on the working end, drawn up, then pulled tight. Worked out by simulating a real cord (`simulate.py`), every stage checked to be that knot (`invariants.py`, `identify.py`). `--list` for the library; `--path FILE` for any other knot. |
| `identify FILE` | Which knot each cord of a project makes, read from its strands, masks and layers the way the app draws them (erase boxes included). |
| `masks FILE` | Every mask (its two strands, which is on top, centre, erase boxes) and every place one is drawn wrong, with coordinates and the edit that fixes it. `--repair` does the safe fixes; `--json` for machines. See "Masks" below. |
| `edit-mask FILE OP` | One mask edit with the app's own code: `erase` (`--at x,y`, `--covers STRAND`, `--around x,y` or `--box ...`), `reset`, `swap`, `delete`, `create --first A --second B`. Checks again after it; `--preview` writes nothing. |
| `samples [TEXT]` | Lists the ready-made designs. |
| `info FILE` | Sets, colors, which way each set runs, strands, masks, size. `--json` for machines. |
| `validate FILE` | Loads the project with the app's loader and lists problems. |
| `recolor FILE` | `--colors red,gold` (set 1, set 2, ...) or `--set 1,2 --color red`. |
| `render FILE` | Draws the project with the app's real canvas to PNG, shadows included. |

Results are one short line; failures print `error: ...` with what to change and
exit with status 1. `--verbose` shows the app's own console output.

Rendering opens a hidden window with fresh settings, so your own OpenStrand
settings are never read or changed. Without a display it draws offscreen.

## Masks

A mask (a `MaskedStrand`) paints a piece of its first strand over its second
where they cross. In a tight knot, a stretched stitch or any design whose cords
touch, that piece can land on a strand beside the crossing, and a joint inside
a crossing can leave part of it drawn the other way. `masks.py` finds and
fixes these from the app's own drawing:

1. The project is loaded with the app's loader and painted, in the app's
   order, with the app's own paths and clipping, into a paint map: which
   strand or mask shows at each pixel (2 per canvas unit). Around each mask it
   is painted again without that mask.
2. Every crossing of the cords' centre lines says which side goes over: from
   the design (`draw` keeps its crossings as `design_crossings` in the
   project), else the crossing's own mask, else what most of it shows. Every
   pixel both sides cover, within the crossing's reach along each cord, must
   show the side on top; where the same cords cross several times close
   together, each pixel belongs to the crossing nearest it along both cords.
3. Where the map disagrees is a problem, with its place in canvas
   coordinates: a mask hiding a strand that should show (`covers_strand`),
   part of a crossing showing the strand that should be under (`wrong_way`),
   a mask over two crossings of its strands with one the other way
   (`two_crossings`), a crossing drawn the other way round from the design
   (`wrong_crossing`). Strips thinner than 4 px, where two strands of one cord
   barely differ, are left out. Where only the drawing says which strand goes
   over, the place is reported without an edit: a mask made from that guess
   would become the crossing's own mask and approve itself.
4. Each problem comes with the edit that fixes it. An erase box is stored by
   its four corners, so it can lie at any angle: the tool tries short quads
   along a strand (the erased part then ends on that strand's outline), a box
   turned to split the place from what stays, and a plain box, measures each
   on the map (what it misses, what it takes of the piece that should stay,
   the cut edges it leaves) and keeps the best, or refuses when none is clean.
   A new mask (`create`, `swap`) is trimmed at once where it would paint the
   wrong way.

Everything is worked out in small windows of the map, so an 8x8 stretched
stitch (128 masks, 576 crossings) is checked in about ten seconds and a knot in
a fraction of one. `tie` runs the safe fixes on its finished steps.

## Claude agent

`openstrand agent` asks Claude to build or change a design with the commands
above. Claude reads the request (and any reference image), uses a sample or a
generator when one fits, and otherwise designs it: it searches the web for
what the thing is and how it is built (or reasons it out when nothing turns
up), plans the cords and crossings, draws them, looks at each render, fixes
what is off and stops when it is right. The loop is in `openstrand/agent.py`;
`guide.md` and `drawing.md` in `.claude/skills/openstrand-designer/` are its
built-in knowledge.

```
python -m openstrand agent "5x3 right hand bracelet in teal and gold"
python -m openstrand agent "make this" --image photo.jpg --model haiku
python -m openstrand agent "make the gold ribbons red" --start designs/bracelet.json
```

- Needs your own Anthropic API key: `ANTHROPIC_API_KEY`, or the key saved in
  the app under Settings > Claude. You pay Anthropic for what it uses; each
  run prints its cost and stops at `--max-cost` (default $2.00).
- Web search and fetch are on (`--no-web` turns them off); each search costs
  about $0.01. Claude thinks at `--effort high` by default.
- `--model sonnet` (Claude Sonnet 5.5, default) or `--model haiku`
  (Claude Haiku 5.5, faster and much cheaper).
- Results go to `--out-dir` (default `designs/`): `design.json` and `design.png`.
- `--json-events` prints one JSON line per step; the app's Claude panel reads
  these.

### In the app

The **Claude** button, next to Settings, shows and hides Claude (so does
Ctrl+J). Claude floats over the bottom of the canvas, so the drawing never
moves. Describe a design (Enter sends, Shift+Enter starts a new line; attach a
reference image if you have one). The agent runs in its own background
process, so the app stays responsive; each step shows with the color of the
matching app button, and while Claude is hidden an arc turns around its button.
The finished design opens in a new tab through the same loader as Load, so its
strands, masks, groups and layer panel are exactly as in a saved project. With
**Start from the canvas** on, the current canvas goes to Claude as the design
to change. The app remembers whether Claude was showing.

Settings > Claude holds the API key (on this computer only, in `claude.json`
in the OpenStrand settings folder, never in projects), the model, web search,
the spending limit per request, and what Claude has cost in all with a Reset
button. Its first switch hides the Claude button altogether. For now Claude
works when the app runs from source; the installed app needs the openstrand
package bundled first.

### Claude and the app's tabs (the bridge)

The agent runs in its own process, so it cannot touch the app's windows. When
the app starts it (`--app`), Claude also gets tools that act on the running
app: `list_tabs`, `read_tab`, `open_in_new_tab`, `rename_tab`, `switch_tab`
and `edit_mask_in_tab`. Each call goes out as a JSON line (`{"type": "app_call", ...}`);
the panel hands it to `AppBridge` (`src/claude_bridge.py`), which runs it on
the app's main thread with the app's own code (the real `TabManager`, the
same loader as Load) and answers on the agent's stdin
(`openstrand/app_tools.py`, `AppClient`). Only those actions exist, only
designs made in the request can open, and the panel's mode decides: plan
mode only looks, ask mode shows a card or an Allow / Deny for each change,
auto does it.

`make_steps` (`openstrand/steps.py`) turns a design into tying steps: the cord
drawn so far along its path, every crossing with its finished over and under,
and an arrow on the working end. With the bridge, Claude opens each step in a
tab of its own ("Step 1 · first loop", ...).

`check_masks` and `edit_mask` work on the current design. After `tie_knot`,
or on anything crowded, Claude checks the masks and fixes each problem with
the edit the check names (with `preview` first when unsure), then renders and
looks. When the person points at a mask in their own tab, Claude reads it
(`read_tab` carries the tab's curve settings, so its copy has the same paths),
checks it, and either opens a fixed copy in a new tab or, with
`edit_mask_in_tab`, changes the mask in that tab: worked out on Claude's copy,
done with the canvas's own mask code (Reset Mask, `create_masked_layer`,
`delete_masked_layer`, erase boxes by corners), one undo step, after Allow in
ask mode.

Tests: `python -m pytest tests/test_openstrand_cli.py tests/test_claude_agent.py tests/test_mask_tools.py`
