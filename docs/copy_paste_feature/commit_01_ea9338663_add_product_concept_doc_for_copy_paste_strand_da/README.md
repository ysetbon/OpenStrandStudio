# Commit 01 — Add product concept doc for Copy/Paste Strand Data feature

- **Hash**: `ea9338663fdaf6c3f3ce98ac13445db262da584d`
- **Date**: 2026-07-17 06:50
- **Author**: Claude
- **Branch**: `claude/strand-copy-paste-feature-j73h0n`

## Description

Documentation only — no application code changes. Includes:
- Full spec: copyable property toggles (Select All), layer-button copy
  dropdown, right-click paste with angle-from-start/end anchor semantics
- Five generated mockup PNGs (anatomy, copy menu, paste menu, anchor
  geometry, workflow)
- Helper scripts (matplotlib) to regenerate the mockups

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01CfuNTzzHDJZ4p594YL95mR

## Files changed

```
docs/copy_paste_strand_data/README.md                           | 255 ++++++++++++++++++
 docs/copy_paste_strand_data/mockups/01_strand_anatomy.png       | Bin 0 -> 145602 bytes
 docs/copy_paste_strand_data/mockups/02_copy_menu_toggles.png    | Bin 0 -> 193108 bytes
 docs/copy_paste_strand_data/mockups/03_paste_context_menu.png   | Bin 0 -> 115321 bytes
 .../mockups/04_paste_anchor_semantics.png                       | Bin 0 -> 108740 bytes
 docs/copy_paste_strand_data/mockups/05_workflow.png             | Bin 0 -> 66439 bytes
 docs/copy_paste_strand_data/tools/generate_mockups.py           | 386 ++++++++++++++++++++++++++++
 docs/copy_paste_strand_data/tools/mockup_common.py              | 252 ++++++++++++++++++
 8 files changed, 893 insertions(+)
```
