# Commit 02 — Rebuild concept doc mockups from the app's real UI

- **Hash**: `afa15f1d3f3ffd36b4e4df0bede60fc0bdeeccb4`
- **Date**: 2026-07-17 07:35
- **Author**: Claude
- **Branch**: `claude/strand-copy-paste-feature-j73h0n`

## Description

The menus in the mockups are now rendered from the actual widgets:
render_ui_qt.py runs NumberedLayerButton.show_context_menu offscreen
with real Strand/MaskedStrand objects and screenshots the result; the
proposed Copy Strand Data entry and options panel are built with the
app's own HoverLabel class, exact menu stylesheet, and the Arrow
Customization embedded-widget pattern. README updated with the exact
menu item order/labels and corrected toggle names.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01CfuNTzzHDJZ4p594YL95mR

## Files changed

```
docs/copy_paste_strand_data/README.md                           |  83 +++++--
 docs/copy_paste_strand_data/mockups/02_copy_menu_toggles.png    | Bin 193108 -> 542523 bytes
 docs/copy_paste_strand_data/mockups/03_paste_context_menu.png   | Bin 115321 -> 192105 bytes
 docs/copy_paste_strand_data/mockups/qt/copy_menu_with_panel.png | Bin 0 -> 246211 bytes
 docs/copy_paste_strand_data/mockups/qt/current_context_menu.png | Bin 0 -> 99431 bytes
 docs/copy_paste_strand_data/mockups/qt/layer_buttons.png        | Bin 0 -> 9817 bytes
 docs/copy_paste_strand_data/mockups/qt/masked_context_menu.png  | Bin 0 -> 30602 bytes
 docs/copy_paste_strand_data/mockups/qt/paste_angle_submenu.png  | Bin 0 -> 15748 bytes
 docs/copy_paste_strand_data/mockups/qt/paste_menu.png           | Bin 0 -> 14537 bytes
 docs/copy_paste_strand_data/tools/generate_mockups.py           | 145 ++++++-----
 docs/copy_paste_strand_data/tools/render_ui_qt.py               | 372 ++++++++++++++++++++++++++++
 11 files changed, 519 insertions(+), 81 deletions(-)
```
