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
| `samples [TEXT]` | Lists the ready-made designs. |
| `info FILE` | Sets, colors, which way each set runs, strands, masks, size. `--json` for machines. |
| `validate FILE` | Loads the project with the app's loader and lists problems. |
| `recolor FILE` | `--colors red,gold` (set 1, set 2, ...) or `--set 1,2 --color red`. |
| `render FILE` | Draws the project with the app's real canvas to PNG, shadows included. |

Results are one short line; failures print `error: ...` with what to change and
exit with status 1. `--verbose` shows the app's own console output.

Rendering opens a hidden window with fresh settings, so your own OpenStrand
settings are never read or changed. Without a display it draws offscreen.

Tests: `python -m pytest tests/test_openstrand_cli.py`
