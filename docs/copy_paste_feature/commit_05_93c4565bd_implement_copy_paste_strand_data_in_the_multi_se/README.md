# Commit 05 — Implement copy/paste strand data in the multi-select layer panel

- **Hash**: `93c4565bdbaedab5b918cf553f1c07ef4a8a2baa`
- **Date**: 2026-07-18 12:15
- **Author**: Your Name
- **Branch**: `claude/strand-copy-paste-feature-j73h0n`

## Description

Copy Strand Data / Paste Copied Data dropdowns in the multi-select batch
menu (Paste above Copy, same chrome as the normal layer dropdown in all
themes, RTL-aware, auto-repositions when the expanded panel would run off
screen). Paste uses the delta-preserving rule: every copied point keeps
its angle and length from the copied strand's anchor and is re-planted at
the target's start or end - no rotation, no scaling.

Layer-panel indicators: supersampled circular copy badge (PNG icon) on
the source layer, hover triangle/square paste chips on eligible targets,
click-to-clear popup, right-click explanations instead of hover tooltips.

Also: undo/redo now preserves the current selection when the strand still
exists in the restored state; badge popup deferred out of the mouse-press
grab so Clear always fires; removed unsupported box-shadow CSS warnings;
translations for the new strings in all 7 languages; unit tests for the
clipboard math and panel logic.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>

## Files changed

```
docs/copy_paste_strand_data/README.md                           |  59 +++--
 docs/copy_paste_strand_data/copy_paste_strand_data.html         |  52 ++---
 docs/copy_paste_strand_data/mockups/qt/indicator_copy_badge.png | Bin 0 -> 5140 bytes
 .../copy_paste_strand_data/mockups/qt/indicator_paste_chips.png | Bin 0 -> 6110 bytes
 src/layer_panel.py                                              | 104 ++-------
 src/layer_panel_icons/chip_end.png                              | Bin 0 -> 393 bytes
 src/layer_panel_icons/chip_start.png                            | Bin 0 -> 1103 bytes
 src/layer_panel_icons/copy_badge.png                            | Bin 0 -> 2086 bytes
 src/numbered_layer_button.py                                    | 351 ++++++++++++++++++++++++----
 src/strand_data_clipboard.py                                    |  55 ++---
 src/strand_data_menu.py                                         | 278 +++++++++++++++++-----
 src/translations.py                                             |  14 ++
 src/undo_redo_manager.py                                        |  14 +-
 tests/copy_paste/test_strand_data_clipboard.py                  |  48 +++-
 tests/copy_paste/test_strand_data_mixin.py                      | 124 ++++++++++
 15 files changed, 809 insertions(+), 290 deletions(-)
```
