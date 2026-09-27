"""Check that hiding a shadow hides all of it.

For every shadow row the Shadow Editor offers for a strand (the strand onto
each layer below it), this hides the row, as unticking it in the Shadow
Editor does, and finds what the caster's shadow pass still paints where the
receiver shows (the pixels that change when the receiver is drawn in another
colour), both measured without the other shadows, as check_shadow_preview.py
does. It must paint nothing there: before, the faded edge of the caster's
shadow on a strand below the receiver still landed on the receiver where it
lies over that strand (a round bump under the caster's edge). A mask's piece
is drawn in its first strand's colour but is a layer of its own, with its
own row: the receiver's pieces are not counted as the receiver.

Run offscreen from the repo root:

    QT_QPA_PLATFORM=offscreen python automation_tests/check_hidden_shadow_rows.py [scene.json ...]

Without arguments it checks the examples in docs/mask_shadow_observations/.
Exits non-zero if a hidden row still gets more than MAX_LEAK_PX of shadow.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_shadow_preview as preview

MAX_LEAK_PX = 3  # anti-aliased pixels along the receiver's edges


def check_scene(check, scene_path, window_size, background):
    check.renderer.configure(window_size, background)
    check.renderer.render(scene_path, preview.SHADOW)
    check.passes = set(check.renderer.calls)
    check.bare = check.render_skipping(check.passes)
    canvas = check.canvas
    manager = canvas.layer_state_manager
    by_name = {s.layer_name: s for s in canvas.strands}
    shows, results = {}, []
    for caster, receiver in check.rows():
        cs, rs = by_name[caster], by_name[receiver]
        if hasattr(cs, "get_mask_path") or not check.may_touch(cs, rs):
            continue
        overrides = manager.layer_state.setdefault("shadow_overrides", {})
        saved = (overrides.get(caster) or {}).get(receiver)
        overrides.setdefault(caster, {})[receiver] = dict(saved or {}, visibility=False)
        try:
            painted = check.painted_by("%s: draw_strand_shadow" % caster)
        finally:
            if saved is None:
                del overrides[caster][receiver]
                if not overrides[caster]:
                    del overrides[caster]
            else:
                overrides[caster][receiver] = saved
        if receiver not in shows:
            pieces = [check.shader_utils._piece_of(m, {}) for m in canvas.strands
                      if hasattr(m, "get_mask_path") and not getattr(m, "is_hidden", False)
                      and getattr(m.first_selected_strand, "layer_name", None) == receiver]
            shows[receiver] = check.shows(rs)
            if pieces:
                shows[receiver] = preview.ImageChops.subtract(
                    shows[receiver], preview.grown(check.raster(pieces), 1))
        leak = preview.count(preview.solid(preview.both(painted, shows[receiver])))
        results.append((caster, receiver, leak))
    return results


def main(argv):
    scenes = [(path, (1600, 1200), "#ECECEC") for path in argv[1:]] or preview.example_scenes()
    check = preview.PreviewCheck()
    failed = []
    for scene_path, window_size, background in scenes:
        results = check_scene(check, scene_path, window_size, background)
        name = os.path.basename(os.path.dirname(scene_path)) if scene_path.endswith("scene.json") \
            else os.path.basename(scene_path)
        leaks = [(c, r, n) for c, r, n in results if n > MAX_LEAK_PX]
        print("%s: %d rows hidden one at a time, %d still get shadow" % (name, len(results), len(leaks)))
        for caster, receiver, leak in leaks:
            print("  FAIL %s -> %s: %d px of %s's shadow where %s shows" % (caster, receiver, leak, caster, receiver))
            failed.append((name, caster, receiver))
        sys.stdout.flush()
    print("OK: a hidden shadow is hidden everywhere" if not failed else "%d hidden rows still get shadow" % len(failed))
    # Tear-down of the offscreen window hangs in QApplication shutdown.
    os._exit(1 if failed else 0)


if __name__ == "__main__":
    main(sys.argv)
