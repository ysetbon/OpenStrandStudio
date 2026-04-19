# Shadow rendering performance — attempt from 1.107, deferred to 1.108

## Context

Looked into whether `src/shader_utils.py` could be made faster without changing
shadow logic or visual output. The hot path is almost entirely Qt path algebra
(156 calls to `QPainterPath.intersected / subtracted / united / addPath`,
`QPainterPathStroker.createStroke` etc.). NumPy was considered and ruled out:
it can't accelerate Qt's polygon/bezier boolean ops, and it would add
~30–50 MB to the installed footprint for near-zero gain.

Two logic-preserving optimizations were attempted:

1. **#2 — dict lookup**: replace `layer_order.index(name)` inside the O(N²)
   pair loop with a precomputed `{name: index}` map.
2. **#1 — paint-scoped cache**: memoize `build_rendered_geometry()` and
   `get_proper_masked_strand_path()` per-paint, keyed by `id(strand)`, so each
   underlying strand's geometry is built at most once per frame instead of
   up to N times.

## What went OK

- **#2 (dict lookup) works correctly.** Semantically identical to the original
  `list.index` calls, zero risk. Applied in three hot spots inside the main
  loop in `draw_strand_shadow`:
  - `shader_utils.py:637–639` — `self_index` / `other_index`
  - `shader_utils.py:810` — `mask_index_sub`
  - All guarded by `if ... in order_idx`.
- Measurable benefit: effectively <1% in realistic scenes. Not worth keeping
  for perf alone, but it is cleaner code. Either land it standalone or drop it.

## What went WRONG

**The paint-scoped cache broke shadow rendering specifically when a masked
strand was present.** Symptoms:

- `draw_strand_shadow` for a masked strand hung for 2 minutes.
- Python faulthandler stack pointed at
  `painter.strokePath(total_shadow_path, pen)` inside the `num_steps=3` fading
  loop (`shader_utils.py:1486` in the cached version).
- After the hang, painter was torn down and subsequent strands crashed with
  `'NoneType' object has no attribute 'size'` inside `masked_strand.py:404`
  (`painter.device().size()`), plus a cascade of "Painter not active" warnings.
- Disabling the cache via `_SHADER_FRAME_CACHE_ENABLED = False` restored
  normal behavior.

### Working hypothesis (unconfirmed)

`MaskedStrand.get_mask_path()` (`masked_strand.py:235`) returns a **fresh**
`QPainterPath` each call, so "shared internal reference" is not the problem.

The caller at `shader_utils.py:746` does
`other_stroke_path.addPath(oc_path_tmp)` — a pre-existing in-place mutation
of whatever path `build_rendered_geometry` / `get_proper_masked_strand_path`
returned.

The wrapper stored `QPainterPath(result)` in the cache and returned
`QPainterPath(cached)` on hit. This relies on Qt's **implicit sharing with
copy-on-write**: `QPainterPath(other)` shares a `d_ptr`, and `addPath()` is
supposed to detach before mutating. In C++ Qt this is reliable; in **PyQt5**
there are edge cases where detach does not fire cleanly.

If detach failed, the mutation at line 746 would leak back into the cached
path. Across the O(N²) pair loop, the same cached path would accumulate more
and more circles from each pair's mutation, exploding its element count.
That explains the hang happening inside `strokePath` on a massive
`total_shadow_path` — the path actually got that big.

This hypothesis is consistent with every symptom (only masks, only with
cache on, hang location on `strokePath`) but was never proven. Fix attempt
based on structural copying was proposed but not tested before the revert.

## Why #1 is harder than it looks

- `build_rendered_geometry` and `get_proper_masked_strand_path` call each
  other (line 1614 of the uncached impl delegates to the masked wrapper for
  `hasattr(strand, 'get_mask_path')`). Any cache design has to be coherent
  across both entry points.
- `build_shadow_geometry` at line 1920 also delegates to
  `get_proper_masked_strand_path` for masked strands — another cache entry
  point that would have needed the same treatment.
- The in-place `addPath` at line 746 (and the dead but identical pattern at
  line 1157) means the cache cannot hand out shared instances. Whether
  `QPainterPath(x)` is a safe copy in PyQt5 is not something to assume.
- The three paint entry points (`strand_drawing_canvas.py` `paintEvent`,
  `attach_mode.py` `optimized_paint_event`, `move_mode.py`
  `optimized_paint_event`) all need matching cache-clear calls. Missing any
  one produces stale-path rendering bugs.

## Recommended next steps (1.108)

**Do the measurement first.** Before any more surgery, profile a representative
scene (a file with masks, a dozen strands, a few moves):

```python
import cProfile, pstats
# wrap the paint cycle or draw_strand_shadow and dump to profiling_results.prof
```

That tells us where time actually goes. If `build_rendered_geometry` is not in
the top-3 hotspots on real scenes, caching it was never going to move the
needle anyway and we can stop chasing it.

**If caching is still worth pursuing**, the safer design is:

1. Confirm or disprove the PyQt5 COW hypothesis with a 10-line reproduction
   outside the app: build a path, `QPainterPath(x)` it, call `addPath` on the
   copy, check whether the original changed.
2. If COW is unsafe, use a `_copy_path(p)` helper that does
   `out = QPainterPath(); out.addPath(p); out.setFillRule(p.fillRule())` —
   that forces structural copying instead of relying on detach.
3. **Eliminate the in-place mutation at line 746 first** (move the circle
   addition into the uncached impl so callers never mutate), then cache.
   That removes the whole class of aliasing bugs.
4. Instrument cache hit rate and path element counts per-frame when
   re-enabling, so we can see corruption grow if it starts again.

**Bigger wins that do change shape, not logic**:

- Spatial prune before the O(N²) pair loop (bbox check exists, a grid or
  R-tree would help on canvases with >30 strands).
- Rasterize combined shadow to a `QImage` once per static frame; reuse while
  nothing moves.
- `QPainterPath.simplify()` on `combined_shadow_path` before `drawPath`.

## NumPy footprint (for the record, in case it comes up again)

- NumPy wheel on disk (Windows): ~35–45 MB unpacked (includes OpenBLAS DLLs).
- Added to a PyInstaller `--onefile` exe: ~15–25 MB compressed.
- Installed footprint increase: ~30–50 MB.
- **Gain for shadow rendering: effectively zero.** Qt path ops are the floor;
  NumPy operates on dense arrays and cannot replace them.

## Files touched during the attempt (all reverted)

- `src/shader_utils.py` — cache helper, wrappers around
  `build_rendered_geometry` / `get_proper_masked_strand_path`, dict lookup.
- `src/strand_drawing_canvas.py:1780–1782` — cache invalidation at paint
  entry.
- `src/attach_mode.py` — cache invalidation inside `optimized_paint_event`.
- `src/move_mode.py` — cache invalidation inside `optimized_paint_event`.
