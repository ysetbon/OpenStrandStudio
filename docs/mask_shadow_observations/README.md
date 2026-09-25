# Mask shadow observations

A catalogue of how shadows looked **around masked crossings**, next to how they should look.
Each example has a scene you can open in the app, the drawing before the fix (`current.png`), the expected
drawing, and notes on what differs and why. The fix is described [below](#the-fix): the app now draws the
expected images, apart from anti-aliasing.

## What a mask should look like

A mask (`a_b_c_d`) is a local layer swap: at the crossing it covers, strand `a_b` must look **exactly**
as if it were genuinely above `c_d` in the layer order. For shadows that means:

1. **The top strand casts its normal shadow on the bottom strand.** Same soft band on both sides of the
   crossing as any regular crossing.
2. **Nothing from below lands on the top strand.** Near the crossing, neither the bottom strand's own
   shadow nor the blurred edge of shadows it casts on strands further down may darken the top strand. The
   mask does not shade the top strand either: its continuation just past the crossing (for example its
   rounded end) stays clean.
3. **Other strands are unaffected by the mask.** A third strand passing under the crossing gets the same
   shadows it would get without the mask: straight bands along each strand above it, meeting at clean
   corners, with no notches, bumps, or missing pieces. A third strand that lies *above* the top strand stays
   above it, even where it overlaps the masked crossing: the mask changes one pair of strands, not the
   whole stack. Its shadow falls across the lifted piece like across the rest of the top strand.
4. **Nothing depends on the view.** Selection, zoom, and pan don't change the shading.

## How "expected" is made

Expected images are rendered, not painted. The example's scene is drawn a second time with the masked
crossing expressed as a genuine layer order (the mask's first strand moved above its second strand, mask
removed). That is how the app already draws a normal crossing. Pixels that differ from the current
drawing near the masked crossing are transplanted into it. Places the reordering also changes but the
mask does not govern are declared as `keep_zones` (strand pairs) in the example's `example.json` and
stay as the app draws them today.

When the crossings form a loop (a under b, b under c, c under a), no layer order draws the whole scene.
The reference order is then chosen so that it is right everywhere near the mask, and the loop gives way
at a joint that is kept as drawn today (see example 2). With several masks, each mask's own piece is
always taken from its own reference (`own_piece_px`), even where another mask's keep zone reaches over it
(see example 4).

[`automation_tests/capture_mask_shadow_observations.py`](../../automation_tests/capture_mask_shadow_observations.py)
regenerates every image. It drives the real app offscreen, loads `scene.json` through the same history
import as **Load**, and also records which shadow pass paints each visible shadow pixel:

```
QT_QPA_PLATFORM=offscreen python automation_tests/capture_mask_shadow_observations.py
```

It draws with the code in `src/`. The committed images record the app before the fix; to regenerate them,
run the script from a checkout of the commit before the fix (for example `git worktree add`), since today's
code draws `current.png` the way `expected.png` looks.

## The fix

The renderer now draws every masked crossing as the genuine crossing it stands for
([`src/shader_utils.py`](../../src/shader_utils.py), [`src/masked_strand.py`](../../src/masked_strand.py)):

- **A mask no longer casts shadows of its own.** Everything around the lifted piece is the first strand's
  own shadow, computed in its own pass exactly as for a genuine crossing. The mask re-applies the part that
  falls on the second strand (`draw_mask_lift_shadow`), which is drawn after the first strand's pass.
- **No shadow blocker.** Shadows cast from below a mask are no longer cut by the mask grown by the blur,
  which notched the shadows of strands the mask does not cover (examples 1 and 4).
- **Local restacking.** Near a mask, the first strand and the strands crossing over it (its *upper side*)
  lie above the second strand and the strands it crosses over (its *lower side*), as if the first strand
  had been moved above the second in the layer order. Every shadow near the mask is computed with that
  order: which strands lie between a caster and its receiver, and where the blurred edge may land. When the
  mask covers the whole overlap of its two strands (nothing erased), the first strand lies above the second
  everywhere.
- **Strands above the piece stay above it.** A strand drawn between the first strand and the mask that
  crosses the piece is drawn again on top of it, with its shadows (example 2). When that strand is also
  below the second strand (a loop), it is lifted over the second strand across their connected overlap.
  Strands above the first strand whose shadows reach the piece put them back on it (example 4).
- **Pan and zoom draw the same** as the default view: both mask drawing paths share the same code.

[`automation_tests/check_mask_shadow_fix.py`](../../automation_tests/check_mask_shadow_fix.py) renders
every example with the code in `src/` and compares it with `expected.png`. It also checks that the
mask-free references are still drawn pixel for pixel as before:

```
QT_QPA_PLATFORM=offscreen python automation_tests/check_mask_shadow_fix.py [out_dir]
```

| Example | Pixels that differ from `expected.png` | What they are |
|---|---|---|
| 1 | 9 | Anti-aliasing (at most 27/255) at the corners of the lifted piece; 8 of them are drawn exactly as before the fix |
| 2 | 42 | 33 are a seam in `expected.png` at the 1_3/1_4 joint ring, where the render equals the genuine reference; 9 are anti-aliasing (at most 17/255): 5 at the corners of the lifted piece, drawn exactly as before the fix, and 4 on the joint ring |
| 4 | 0 | |

## Adding an example

1. Create `example_NN_<short_name>/` with the scene as `scene.json` (a saved history file). Optionally add
   the reported screenshot and its canvas offset.
2. Add `example.json`, copying example 1. The fields that matter:
   - `mask`: the mask layer.
   - `reference_order`: the layer order that makes the crossing genuine.
   - `keep_zones`: strand pairs whose stacking the reorder also flips.
   - `crop` and `insets`: canvas-space boxes for the figures.
   - `blocker_inset` (optional): which inset the blocker experiment zooms into.
   - `window_size`, `canvas_background` (optional): the reporter's window size and canvas colour, when
     they differ from example 1 (the "default" theme paints the canvas `#ECECEC`).
   - `workaround_order` (optional): a layer order, mask included, that gets close to the expected look
     with today's code. The script renders it and reports how far it is from the expected image.
   - `masks` (optional): for scenes with several masks whose crossings form a loop, a list of
     `{mask, reference_order, reference_note, near_mask_px, keep_zones, own_piece_px}`, one reference per
     mask. `own_piece_px` takes every changed pixel on the mask's own piece (grown by that many pixels)
     from the mask's reference, even inside a keep zone.
   - `screenshot_select` (optional): which layer was selected in the screenshot, if not the mask.
   - `screenshot_unreproduced` (optional): canvas boxes where the screenshot shows something the rebuilt
     scene does not draw; the expected screenshot takes the expected render there.
3. Run the script, then write the example's `README.md`: a table of what differs, and why.

## Examples

| # | Scene | Findings |
|---|---|---|
| [1](example_01_mask_2_1_over_2_3/README.md) | Mask `2_1_2_3` (2_1 over 2_3) beside an unrelated strand `1_1` | The mask's own shadow is right. A stray wedge of 2_3's shadow lands on top of 2_1 (it leaks through the blur clip). 1_1's shadow is notched by the mask's shadow blocker, and switching the blocker off exposes a second wedge. |
| [2](example_02_mask_1_1_over_1_4/README.md) | Mask `1_1_1_4` (1_1 over 1_4) right where 1_1 also passes under 1_3 | The mask's shading on 1_4 is right. The mask, sitting at the top of the stack, also paints a corner of 1_1 over 1_3 and casts a shadow onto it. Expected: 1_3 stays on top along its whole band and casts its usual shadow, which also puts 1_3 over 1_4 at their hairpin joint. Moving 1_3 above the mask in the layer panel already gets within 141 px of that. |
| [4](example_04_two_masks_weave/README.md) | Two masks weaving `2_2` and `2_3` through `1_2` and `1_3` (a 2×2 checkerboard) | Each mask's shading is right. Each mask also shades its own strand's rounded end just past the crossing, and dents the shadows at its corners. The reported screenshot also shows an L-shaped shadow on 1_3 that a fresh load of the layer state does not draw. |

![Example 1: screenshot vs expected](example_01_mask_2_1_over_2_3/compare_screenshot.png)

![Example 2: screenshot vs expected](example_02_mask_1_1_over_1_4/compare_screenshot.png)

![Example 4: screenshot vs expected](example_04_two_masks_weave/compare_screenshot.png)
