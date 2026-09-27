# Example 5: mask `2_2_1_3` (2_2 over 1_3), and 1_3's shadow on 2_1 beside it

**Status: fixed.** Two things drew this, one in each of `src/auto_shadow.py` and `src/shader_utils.py` (see
[the fix](../README.md#the-fix)). The app now draws [`expected.png`](expected.png) once it refreshes its
automatic shadow overrides, which it does on the next edit of the weave. A project saved before the fix keeps
1_3's shadow on 2_1 hidden until then, and no longer draws the bump. The images below show the app before the fix.

Two chains cross: 1_1 with 1_2 and 1_3 attached at its ends, and 2_1 with 2_2 and 2_3 attached at its ends. The
mask lifts 2_2 over 1_3. Everywhere else the layer order holds, so 1_3, near the top of it, lies over 2_1 where
they cross, just left of the mask.

Reported layer state:

| | |
|---|---|
| Order | `1_1, 2_1, 2_2, 2_3, 1_2, 1_3, 2_2_1_3` |
| Connections | 1_1 start ↔ 1_3 start, 1_1 end ↔ 1_2 start; 2_1 start ↔ 2_3 start, 2_1 end ↔ 2_2 start |
| Masked layers | `2_2_1_3` (first strand 2_2 on top, second strand 1_3 below) |
| Positions | 1_1 (224,140)→(504,280) · 2_1 (280,364)→(448,84) · 2_2 (448,84)→(364,392) · 2_3 (280,364)→(336,56) · 1_2 (504,280)→(196,252) · 1_3 (224,140)→(532,168) |
| Shadow settings | Shadow on, NumSteps 2, MaxBlurRadius 30, color 0,0,0,150; width 46, stroke 4 |

[`scene.json`](scene.json) rebuilds this state as the app saved it, including the override it added by itself
when the mask was made: `{"1_3": {"2_1": {"visibility": false, "auto": true}}}`. The reported screenshot,
[`user_screenshot.png`](user_screenshot.png), shows the canvas zoomed to 1.8×; the bump is at canvas (356–374,
183–196).

![Clean render: current vs expected](compare_clean.png)

## Observations

| # | Where | Current | Expected |
|---|---|---|---|
| 1 | On **2_1**, just under 1_3's lower edge, left of 2_2 | A grey half-disc hangs under 1_3's edge, and 1_3's shadow band on 2_1 is missing | 1_3's shadow band along its lower edge, as on 2_3 a little further left: 1_3 lies over 2_1 there, and the mask only swaps 2_2 and 1_3 |

## Why

1. **The app hid 1_3's shadow on 2_1 by itself.** `auto_shadow.py` hides the shadows a mask's second strand
   (1_3) casts on its fabric (here the chain 2_1, 2_2, 2_3) when most of the area they would land on is
   covered. It measured 30% of the area left (43% without the mask blockers the renderer no longer cuts),
   under its threshold of 45%. But much of that area is covered by 2_2, which is drawn over 2_1 anyway, and the
   rest is a full, visible band: shown, the shadow puts 771 px on 2_1.
2. **The half-disc is 1_3's shadow on 1_1, not on 2_1.** A strand's shadow pass strokes the faded edge of each
   of its shadows along the outline of the shadow, and clips it to the receiving strand's outline. The shadow
   on 1_1 ends at 2_1's edge, since 2_1 lies over 1_1 there, but 1_1's outline also covers the part under 2_1,
   so the rounded end of the faded edge landed on 2_1. With 1_3's own shadow on 2_1 shown, its band covers
   that; hidden, the half-disc was all that was left. The same happened with any hidden shadow, masks or not:
   in this scene, hiding any one of 7 of its 15 shadows still left 124–262 px of it behind.

## The fix

- `shader_utils._clip_off_hidden_rows`: a receiver's clip leaves out the strands between it and the caster whose
  own shadow from the caster is hidden, so hiding a shadow hides all of it.
- `auto_shadow.compute_auto_hidden_pairs`: a pair is hidden only if the canvas would also show next to nothing of
  it (`_visible_shadow_px`, less than a quarter of one crossing's band, about 200 px). This one shows 771 px and
  stays; example 4's automatically hidden shadows show 26–52 px and the plait's 0 px, and stay hidden.
