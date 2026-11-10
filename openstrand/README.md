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
| `make heart` | A ribbon heart from one cord (fitted, a few seconds). |
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

- Runs on the model you pick with `--model` (an id or an alias), with your own
  key for its provider, from the provider's environment variable or the key
  saved in the app under Settings > Models. You pay the provider for what it
  uses; each run prints its cost and stops at `--max-cost` (default $2.00).

  | `--model` | model | provider, API | key |
  |---|---|---|---|
  | `sonnet` (default), `haiku` | Claude Sonnet 5.5, Claude Haiku 5.5 | Anthropic, Messages API | `ANTHROPIC_API_KEY` |
  | `gpt`, `gpt-6.1-sol`, `gpt-6-astra` | GPT-6.1 Terra, GPT-6.1 Sol, GPT-6 Astra | OpenAI, Responses API | `OPENAI_API_KEY` |
  | `grok` | Grok 4.7 | xAI, Responses API | `XAI_API_KEY` |
  | `kimi` | Kimi K3.1 Pro | Moonshot AI, Anthropic-compatible | `MOONSHOT_API_KEY` |
  | `deepseek` | DeepSeek V4.1 Flash (`deepseek-flash`) | DeepSeek, Anthropic-compatible | `DEEPSEEK_API_KEY` |
  | `qwen` | Qwen3.8 Max | Alibaba Cloud Model Studio, Anthropic-compatible | `DASHSCOPE_API_KEY` |

  `openstrand/providers.py` has the endpoints and prices, and a client for
  each that answers like the anthropic SDK, so the agent loop is the same for
  every model. The Responses API client uses Python's own urllib: nothing more
  to install.
- **Refresh models** (a button in Settings > Models, and on its own once a day,
  silently: 15 seconds after the app starts, then checked hourly; no window or
  note, only the lists change and the terminal log says what changed) asks each
  provider you have a key for which models it offers now (`providers.list_models`:
  Anthropic and OpenAI `/v1/models`, xAI `/v1/language-models`, Kimi
  `/v1/models`, DeepSeek `/models`; Qwen's list is not documented, so its
  built-in model stays unless the call works). It keeps only chat models (no
  embedding, speech, image or dated snapshot ids). It adds new ones, tagged "new",
  and marks the ones a provider is retiring with their date. Models a provider
  retired or no longer lists are hidden. A model without a published price
  (only xAI publishes them) gets the price of its provider's dearest built-in
  model (an Opus 2.5 times Sonnet), tagged "price estimated", so a spending limit
  is never run past. The answer is kept in `claude.json`; the agent uses the
  same list (`providers.use_catalog`). A provider that fails keeps what it
  offered last time. If the saved model is no longer offered, it moves to that
  provider's first model (the button's status says so).
- Web search and fetch (Claude models only: they are Anthropic's server
  tools) are on (`--no-web` turns them off); each search costs about $0.01.
  The model thinks at `--effort high` by default (a thinking budget on the
  Anthropic-compatible endpoints, reasoning effort on the Responses API).
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

Settings > Models holds the API keys (on this computer only, never in
projects: in the system's password store, macOS Keychain, Windows Credential
Manager or the Secret Service, when the `keyring` package finds one, else in
`claude.json` in the OpenStrand settings folder, readable by the user alone),
the model, web search, the spending limit per request, and what Claude has
cost in all with a Reset button. Its first switch hides the Claude button
altogether. For now Claude works when the app runs from source; the installed
app needs the openstrand package bundled first.

A key only ever goes to its own provider (`providers.py`, "Safe requests"):
each request is checked as it leaves (HTTPS, to the host its endpoint names,
certificate checked), no redirect is followed, and environment variables can
neither move a client (`ANTHROPIC_BASE_URL`, which Claude Code users of
DeepSeek or Kimi often have set) nor add another credential to its requests.
The one exception is for the tests: `OPENSTRAND_TEST_API` points the agent at
a local stand-in API, and only on this computer itself (`127.0.0.1`,
`localhost` or `::1`; any other host is refused).

Sharing with the developer (`src/claude_sharing.py`) is offered only once the
developer has set `SHARE_URL` and `SHARE_PUBLIC_KEY` there (the Worker's
README says how), and then off until the person says yes, on a card under
Claude's first answer or in Settings > Models; a yes holds for each request
after it, until they turn it off. For each request, whichever model answered,
the design Claude made (all of it, the person's canvas too when Claude changed
it; never a canvas, tab or past step that Claude only read: the agent's
`changed` says which), its picture and Claude's answer, with the model, the
app's version and language and whether the request worked, are encrypted on this computer
with the developer's public key and sent to the developer's Cloudflare Worker
(`cloudflare/share-worker`). The setting is read again just before a share
leaves, so one turned off meanwhile stays here. The request itself, the
person's pictures, keys and files, every folder path, an error's text and the
time are never sent, though Claude's answer may repeat words or bare file
names from the request or the canvas. An API key an answer repeats is cut out
(`claude_settings.own_keys`: the person's own keys, whatever their shape, and
any `sk-...` or `xai-...` key).

The public gallery (`gallery/`, on GitHub Pages) is a second, separate yes,
asked only after the first and only once the developer has set `GALLERY_URL`.
A share then says the developer may show its design there, and only when the
model made that design from nothing of the person's (the agent's `new`: False
once the request read their canvas, a tab or a past step). Nothing becomes
public by itself: the developer looks at each one and publishes a cleaned copy
by hand (`scripts/share_inbox.py publish`), with a picture drawn again from
that copy, the model and the app's version, and never the answer.

Two switches in Settings > Models decide what may be sent at all, and every
request asks them just before it leaves (`providers.POLICY`, which
`claude_settings.refusal` answers from the saved settings), in the app and in
the agent it starts alike. **Connect to AI models**, turned off, sends nothing
to any model: no request, no Refresh models, no share; a request already
running stops. Off is off everywhere: the Claude button leaves the main
window, Ctrl+J does nothing, the panel cannot be opened, and
`openstrand agent` refuses before it loads a package or reads a key (the
other `openstrand` commands never contact a model and still work). A
`claude.json` that is there and cannot be read counts as off, never as on,
and is not written over except by the person's own save
(`claude_settings._read`). **Allow Kimi, DeepSeek and Qwen (based in China)** is off until
the person ticks it: their models are hidden and anything for them is refused.
`openstrand agent` from a terminal follows the same settings.

### Claude and the app's tabs (the bridge)

The agent runs in its own process, so it cannot touch the app's windows. When
the app starts it (`--app`), Claude also gets tools that act on the running
app: `list_tabs`, `read_tab`, `read_tab_step`, `open_in_new_tab`, `rename_tab`,
`switch_tab`, `edit_mask_in_tab`, `edit_strand_in_tab`, `edit_layers_in_tab`,
`edit_groups_in_tab`, `show_group`, `app_window`, `read_settings` and
`app_settings`. Each call goes out as a JSON line (`{"type": "app_call", ...}`);
the panel hands it to `AppBridge` (`src/claude_bridge/`, one module per area: tabs,
strands, masks, layers, groups, window, settings), which runs it on
the app's main thread with the app's own code (the real `TabManager`, the
same loader as Load) and answers on the agent's stdin
(`openstrand/app/client.py`, `AppClient`; the tools Claude sees are in `openstrand/app/`,
by the same areas). Only those actions exist, only
designs made in the request can open, and the panel's mode decides: plan
mode only looks, ask mode shows a card or an Allow / Deny for each change,
auto does it.

`read_tab` gives the tab as it is at that moment: every strand with its start,
end and control points, every mask, the tab's undo history, and a version (a
fingerprint of its strands and groups). The person keeps working while Claude
does, so an edit in the tab names the version it was worked out on, and the
bridge refuses it when the tab changed since: Claude reads it again.
`read_tab_step` loads any step of the tab's undo history (before the person's
latest change, or a step they undid) as a copy. `edit_strand_in_tab` moves a
strand's ends and handles with Move mode's own code, as a drag does (strands
joined at a moved end follow, erase boxes follow their crossing), one undo step.

The other areas are the app's own panels and buttons, called the way a click
calls them:

- `edit_layers_in_tab`: the layer panel's right-click menu (hide, shadows,
  colors, widths, side lines, arrows, dashes, circles, full arrows, end styles,
  fold the start edge, close the knot, copy and paste strand data).
- `edit_groups_in_tab` and `show_group`: the group panel (create, rename,
  delete, move, snap, rotate, strand angles, shadows, mask grid, duplicate).
- `app_window`: the main window. View ops (zoom, center, grid, layer names,
  the tab edge, the Strands/Masks switch, modes, select) change only what the
  person sees and run in any mode; edit ops (undo, redo, control points,
  shadows, New Strand from a start to an end, delete, Delete All, New Level,
  locks, clearing the history) change the tab; `save` and `save_image` write
  a file to a path.
- `read_settings` and `app_settings`: the Settings dialog, set through its own
  widgets and the code its OK button runs, so the dialog shows what Claude set
  (dark mode is `{"theme": "dark"}`). Settings make no undo step; the reply
  gives the old values.

Where a button asks first (Delete All) or opens a dialog (Save, Image, a color,
the default width), the bridge answers that dialog with Claude's request
without showing it (`base.patched`), and the button's own code runs on.

The agent reads its stdin only while a call waits for the app's answer, and
loads numpy before it starts reading. On Windows a read left waiting holds the
pipe, and a DLL that looks at the standard handles as it loads (numpy's do)
waits for it: that is how the knot tools once hung in the app for good.

### Progress

A long tool says how far it has got (`openstrand/progress.py`): the fraction
done, what it is doing, and about once a second a small picture of the cord it
works on. `tie_knot` shows the cord laid out and pulled tight, then each step
as it is drawn; `draw_design` shows the design while it fits the strands (it
cannot know its total, so its bar slides). The panel draws the picture with a
bar, the time left and the tool's own time on its row, and the bar under the
conversation too; a finished tool's row says how long it took, and Stop marks
the tool stopped. The events go out on the agent's real stdout, kept aside,
since tools run with stdout pointed at nothing to hide the app's chatter. In a
terminal, `openstrand agent` prints a line per stage.

A finished tool keeps a picture on its row when one says something; the mouse
over it shows it larger. In the app, the tools that make, change, check or read
a design (`load_sample`, `make_*`, `draw_design`, `tie_knot`, `edit_mask`, a
preview included, `recolor`, `make_steps`, `render`, `identify_knot`,
`check_masks`, `read_tab`, `read_tab_step`) end with the design drawn by the
app's real canvas, cut to the design (`Workspace.snapshot`, once per version).
The panel pictures the app tools itself: the canvas as an edit, a tab switch or
a view change left it (without Claude floating over it), the group panel for
`show_group`, the window (or the Settings page shown) for `app_settings`. Tools
that answer with words (`search_samples`, `knot_library`, `describe`,
`validate`, `list_tabs`, `rename_tab`, `read_settings`) have none.

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
