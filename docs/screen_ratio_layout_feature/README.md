# Screen ratio layout fix (compact layer panel)

Branch: `fix-screen-ratio-layout`

Makes the main window lay out correctly on narrow screens — the 1280-wide
logical MacBook resolutions (MacBook 13" smallest-scaled 1280x800, MacBook
Air 13" M2 "More Space" 1280x832) — where the toolbar buttons were cramped
and the layer list had scrollbar problems.

## What the fix does

All numbers are logical pixels. The trigger is **window width < 1350px**
(`MainWindow.COMPACT_WINDOW_WIDTH`); wide screens keep the stock layout,
verified pixel-identical.

1. **Compact panel width** (`main_window.py`,
   `_apply_layer_panel_compact_width`): the layer panel minimum drops
   350 -> 294 (reduction 56, split evenly between the group panel and the
   layer list), so the canvas pane / toolbar gains 56px.
2. **No horizontal scrollbar** (`layer_panel.py`): the layer-list scroll
   area sets `ScrollBarAlwaysOff` horizontally — layer buttons are fixed
   width (146) and centered, so horizontal scrolling could only ever cover
   a ~2px overflow.
3. **7px gap** under the lowest layer button: explicit layout spacing 5
   (was platform default ~9) + bottom panel top margin 2 (was 5).
4. **Vertical scrollbar gutter** (`layer_panel.py`,
   `set_compact_reduction`): on compact screens the list column slot
   becomes `146 (button) + scrollbar extent (~10) + 2 = ~158`, and the
   group panel genuinely shortens to the remainder (~135, with the
   Create Group button's fixed width capped to fit). Without this the
   scrollbar that appears with many layers was painted *under* the group
   panel and clipped the buttons' right edge. Wide screens already have
   ~28px spare in their natural 174px column and are untouched.

## Porting notes (e.g. for the JS version / ossjs)

The essence, independent of Qt:

- Layer buttons have a fixed width; the list column must be at least
  `button width + vertical scrollbar width + margin` **whenever the panel
  is slimmed**, otherwise the scrollbar overlaps the buttons.
- Take the compact slimming from both sub-panels, but take the scrollbar
  gutter from the group-panel side only, and shrink the group panel's
  content (Create Group button) to match so nothing overflows.
- Disable horizontal scrolling of the layer list entirely.
- Threshold: apply compact mode below ~1350px viewport width.

## Files

- `src/main_window.py` — compact trigger + constants.
- `src/layer_panel.py` — panel widths, gutter, gap, scrollbar policies.
- `automation_tests/capture_screen_ratio_mocks.py` — renders
  `screenshots/00..10` (full window at ten real screen ratios, with
  pass/fail footer).
- `automation_tests/capture_many_layers_scrollbar.py` — renders
  `screenshots/11/12` (30 layers, scrollbar visible, compact vs full).
- `automation_tests/preview_screen_ratio.py` — opens the live app at a
  simulated screen size for manual QA.
