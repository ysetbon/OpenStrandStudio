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
| `identify FILE` | Which knot each cord of a project makes, read from its strands, masks and layers the way the app draws them. |
| `samples [TEXT]` | Lists the ready-made designs. |
| `info FILE` | Sets, colors, which way each set runs, strands, masks, size. `--json` for machines. |
| `validate FILE` | Loads the project with the app's loader and lists problems. |
| `recolor FILE` | `--colors red,gold` (set 1, set 2, ...) or `--set 1,2 --color red`. |
| `render FILE` | Draws the project with the app's real canvas to PNG, shadows included. |

Results are one short line; failures print `error: ...` with what to change and
exit with status 1. `--verbose` shows the app's own console output.

Rendering opens a hidden window with fresh settings, so your own OpenStrand
settings are never read or changed. Without a display it draws offscreen.

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
app: `list_tabs`, `read_tab`, `open_in_new_tab`, `rename_tab` and
`switch_tab`. Each call goes out as a JSON line (`{"type": "app_call", ...}`);
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

Tests: `python -m pytest tests/test_openstrand_cli.py tests/test_claude_agent.py`
