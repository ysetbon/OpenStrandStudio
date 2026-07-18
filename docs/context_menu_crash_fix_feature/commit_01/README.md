# Fix: Access Violation from Leaked Layer-Button Context Menus

## Symptom

After a long session (Edit Strand Angles dialog + several right-clicks on layer
buttons), the app died with `Windows fatal exception: access violation` at
`numbered_layer_button.py:373` — the `QMenu(self)` constructor in
`NumberedLayerButton.show_context_menu`.

(The repeated `Timeout (0:02:00)!` stack dumps in the same log are *not* part
of the bug — they are the faulthandler watchdog armed in `main.py`
(`dump_traceback_later(120, repeat=True)`) printing stacks while modal
dialogs/menus keep the event loop busy.)

## Root cause

Every right-click built a fresh `QMenu(self)` plus up to 21
`QWidgetAction(self)` entries with embedded `HoverLabel` widgets — all
parented to the **button**, and never cleaned up after `exec_()`. Stale menu
graphs accumulated as children of the button for its whole lifetime; combined
with layer-panel rebuilds (`setParent(None)` + `deleteLater()` on buttons),
Qt eventually walked a dangling child/ownership pointer when registering the
next menu into the button's child list → native crash.

## Fix (`src/numbered_layer_button.py`)

1. `QWidgetAction(self)` → `QWidgetAction(context_menu)` (21 call sites) —
   actions now belong to the menu, not the button.
2. `context_menu.deleteLater()` after `context_menu.exec_()` — the whole menu
   graph (menu, actions, embedded widgets) dies when the menu closes.

## Verification (live GUI, not headless)

Stress test launched the real `MainWindow`, loaded the 24-layer sample
project, opened/closed layer-button context menus 40 times across different
buttons with layer-panel rebuilds interleaved every 7 iterations:

- **Fixed:** 40/40 opens, 0 stale `QMenu` / 0 stale `QWidgetAction` children
  left on buttons, clean exit.
- **Unfixed baseline (main checkout):** same run leaves stale menu graphs
  parked on the surviving buttons (1 menu + 15 actions), confirming the leak.
