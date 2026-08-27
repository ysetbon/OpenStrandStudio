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

## Translated toolbar labels

The toolbar holds 16 buttons with an Expanding size policy, so they never
overflow the row geometrically — they shrink and the label gets cut on both
sides (centered text). At 1280px the German, Spanish, Portuguese, Italian and
French labels were being truncated to nonsense ("Verbinden" rendered as
"rbind"). English and Hebrew were never affected.

Two levers fixed it, in this order:

1. **Shorter labels that are still complete words** — no truncation-style
   abbreviations. e.g. de `Auswählen`->`Wählen`, `Ansicht`->`Sicht`,
   `Verbinden`->`Binden`, `Speiche.`->`Sichern`; es `Seleccionar`->`Elegir`,
   `Cuadrícula`->`Rejilla`, `Cargar`->`Abrir`; pt `Rotacionar`->`Girar`
   (which its settings description already used), `Carregar`->`Abrir`;
   it `Seleziona`->`Scegli`, `Sposta`->`Muovi`, `Collega`->`Unisci`;
   fr `Ombres`->`Ombre`, `Onglets`->`Onglet`. The matching `*_desc` strings
   in the settings dialog were updated so the button name shown there stays
   consistent.
2. **Width, not words, for the rest** — the gap between toolbar buttons is
   derived from the space the labels do not need (`_apply_toolbar_spacing`),
   sliding between 10px and 2px. With 15 gaps that is up to ~120px returned
   to the labels: far more than the layer panel can give, where each pixel is
   shared across all 16 buttons. The compact panel floor is 286px
   (`COMPACT_LAYER_PANEL_FLOOR`), set by the group panel's "Create Group"
   button rather than by the layer list.

   Spacing is deliberately *not* keyed to a window-width threshold. Doing that
   left the 1440x900 and 1470x956 screens tighter than the 1280 ones — they
   sat above the compact cutoff, so they kept the roomy panel and wide gaps
   while carrying the same labels. German at 1440x900 had only 1.7% of growth
   headroom as a result. Measuring the real surplus fixes that, and it also
   covers macOS: the same string renders wider there, so the spacing tightens
   on its own rather than the labels being cut.

## macOS headroom

Every measurement here is taken with Windows font metrics, but the app targets
MacBooks and macOS renders the same string wider. `audit_toolbar_macos_margin.py`
reports, per language and ratio, how much the text could grow before labels
start being cut — computed at the spacing floor, since the adaptive spacing
gives its room back first.

Nothing is cut at current metrics. The tightest cases are German `Bewegen`
(+6.4%), Italian `Immagine` (+9.1%) and Spanish `Máscara` (+9.6%), all on the
1280-wide screens. Since macOS typically runs ~5-10% wider, those three are
worth confirming on a real Mac. Everything else has >10% headroom.

`automation_tests/audit_toolbar_languages.py` checks all languages x all
ratios (it compares each button's width against its sizeHint) and
`capture_language_toolbars.py` captures `screenshots/language_audit/`.

## Right-to-left (Hebrew)

Verified, not a regression: in RTL the left panel already overlaps the
group panel (see the comment in `group_layers.py`, `_update_tree_column_width`,
which clips the group text column to the left panel's edge). Compact mode
slightly *reduces* that overlap (95px wide -> 84px compact), so visible group
names go from ~175px to ~136px on narrow screens — the intended consequence of
a narrower group panel. Create Group fits inside the panel in all four
combinations (en/he x wide/compact).

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
