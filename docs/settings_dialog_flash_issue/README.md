# Settings Dialog Position Flash

**Symptom:** opening the Settings dialog briefly shows it at the wrong position and
size; ~300 ms later it visibly shrinks and jumps to its centered position.

**Status:** investigated and reproduced with millisecond timestamps — **not fixed yet**.

Open [`report.html`](report.html) for the full report (measured event timeline, root
cause, and the proposed fix). Run `python repro.py` to reproduce the timeline yourself.

## TL;DR

The window appears on screen ~110 ms after the ⚙ click, but sits at stale geometry for
another ~280–350 ms before snapping into place. Three causes:

1. **`src/settings_dialog.py:6859` (`SettingsDialog.showEvent`)** — primary. It runs
   `update_translations()` + `update_layout_direction()` (~300 ms of full retranslation,
   button-guide HTML rebuild, etc.) *before* `super().showEvent(event)`. Qt centers a
   `QDialog` over its parent inside `QDialog::showEvent`, so the centering runs ~350 ms
   after the window is already visible → visible jump; the retranslation relayout is the
   visible size pop.
2. **`src/main_window.py:658` (`open_settings_dialog`)** — contributing. It calls
   `setWindowFlags(... & ~Qt.WindowContextHelpButtonHint)` on *every* open, which
   destroys/recreates the native window (`WinIdChange`) and discards placement.
3. Nothing moves the dialog before `show()`, so the first mapped frame is always wrong.

## Proposed fix (see report for details)

1. Strip the help-button flag once in the constructor; delete both per-open
   `setWindowFlags` calls (normal + `RuntimeError` recovery path).
2. In `showEvent`, retranslate only when `current_language` actually changed.
3. In `open_settings_dialog`, before `show()`: activate the layout and explicitly
   `move()` the dialog centered over the main window (sets `WA_Moved`, so Qt skips its
   own late repositioning).
4. Optional: guard remaining heavy refreshes with `setUpdatesEnabled(False)/(True)`.

**Verify:** rerun `repro.py`; the `Show` event should already report the final frame and
no `Move`/`Resize` should follow within 500 ms, on both first and second open.
