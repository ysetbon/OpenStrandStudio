# Commit 06 — Remove the deletability hover tooltip from layer buttons

- **Hash**: `100e347bdce780b8522a3e26b3f8502bfe989ef4`
- **Date**: 2026-07-18 12:16
- **Author**: Your Name
- **Branch**: `claude/strand-copy-paste-feature-j73h0n`

## Description

"This layer cannot be deleted (both ends are attached)" popped up on
every hover; the green attachable strip already conveys the state.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>

## Files changed

```
src/layer_panel.py | 12 ++++--------
 1 file changed, 4 insertions(+), 8 deletions(-)
```
