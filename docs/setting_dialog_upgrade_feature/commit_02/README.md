# Commit 02 — Tighten Segmented Spin Box Value Gap by 50%

**Commit:** `406b24b90` — follow-up to the Option B segmented stepper
(see [`../commit_01/README.md`](../commit_01/README.md)).

## What changed (`src/segmented_spin_box.py`)

User feedback after trying the first build: the whitespace between the number
and the −/+ buttons was too wide, and the buttons did not cover the control's
full height. Both fixed:

| | Before | After |
|---|---|---|
| Value field width | 66px | **48px** (whitespace halved) |
| Total control width | 128px | **110px** |
| Button height | natural ~22px (gap above/below) | **fills full inner height** (26px) |

- `_FIXED_WIDTH` 128 → 110; side padding recalculated to `_BUTTON_WIDTH + 1`.
- Buttons get `QSizePolicy(Fixed, Expanding)` so they stretch to the full
  inner height of the 28px control — separators now run edge to edge.

## Verification

- 3× zoomed render (`screenshots/seg_zoom_narrow.png`): 110×28 control,
  "29.99" fits comfortably with the halved gap, buttons flush with the
  border on all sides.
- Full `SettingsDialog` offscreen check re-run after the change: 15/15
  spin boxes segmented, theme cycling + Hebrew RTL fine, +/− stepping works.
