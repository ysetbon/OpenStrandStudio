"""
Automatic per-pair shadow-visibility overrides for masked weaves.

Why this exists
---------------
A MaskedStrand X_Y flips the visual over/under at ONE crossing for ONE pair
(X over Y), but the regular shadow pass still runs on plain z-order for every
other pair. When strands are welded into chains (attached strands doubling
back over their parents), the chain members buried under the woven fabric
(typically the x_1 parents) still RECEIVE shadows from the under-chain there.
Those shadows have almost no exposed landing area — nearly all of their
region is eaten by the renderer's own subtractions (mask blocking +
intermediate layers) — so what remains on screen is residue: thin slivers at
the crossing edges plus the blur fringe, which is NOT clipped by those
subtractions (see draw_strand_shadow: only explicit subtracted_layers reduce
clip_path). The residue lands on pixels that visually belong to the strand
woven on top, contradicting the weave.

The fix: whenever masks change, evaluate each casting->receiving pair the
way the renderer drew it when this was tuned (_surviving_shadow; the
renderer has since stopped cutting mask blockers), and if the surviving
shadow is only a small fraction of the raw caster/receiver overlap, the pair
can only contribute
residue -> write shadow_overrides[casting][receiving] = {'visibility': False,
'auto': True}. This is plain shadow_overrides data, so rendering stays
byte-identical everywhere overrides are honored (including OpenStrandJS),
and the Shadow Editor dialog shows the pair unchecked like any manual edit.

Bookkeeping keys (stored inside the override dict, survive save/undo
verbatim — layer_state_manager stores override dicts as-is):
  'auto':   True  -> written by this module; wiped and recomputed each run.
  'pinned': True  -> user re-enabled an auto-hidden pair in the Shadow Editor;
                     recompute must never touch the pair again.
Entries without 'auto' (any user-authored override) are never modified.
"""

import logging

from PyQt5.QtGui import QPainterPath, QTransform


# A candidate pair is auto-hidden when (surviving area / raw overlap area)
# falls below this ratio: most of the shadow is covered by masks/intermediate
# layers, so what reaches the screen is edge slivers + unclipped blur fringe.
# Candidates are ONLY mask second-components casting into their mask's fabric
# (see compute_auto_hidden_pairs); measured on the reference weave scene those
# split at <=0.374 (residue, user hides) vs >=0.598 (real exposed crossings,
# user keeps), so 0.45 sits mid-gap.
AUTO_HIDE_SURVIVAL_RATIO = 0.45

# Ignore grazing overlaps (world-units^2). A real strand crossing at default
# width (46+2*4 = 54 px wide bodies) is tens of thousands of px^2.
AUTO_MIN_RAW_AREA = 150.0


def _path_area(path):
    """Net filled area of a QPainterPath (shoelace over toFillPolygons; holes
    carry opposite winding, so the signed sum is the net area)."""
    if path is None or path.isEmpty():
        return 0.0
    total = 0.0
    for poly in path.toFillPolygons(QTransform()):
        n = poly.count()
        s = 0.0
        for i in range(n):
            p1 = poly.at(i)
            p2 = poly.at((i + 1) % n)
            s += p1.x() * p2.y() - p2.x() * p1.y()
        total += s / 2.0
    return abs(total)


def _weld_chain_ids(canvas):
    """layer_name -> chain id for every non-mask strand, unioning attached
    children with their parents and knot-connected partners. The 'fabric' a
    mask asserts over/under for is the whole welded chain, not just the two
    component strands."""
    from masked_strand import MaskedStrand

    parent = {}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    strands = [s for s in canvas.strands if not isinstance(s, MaskedStrand)]
    for s in strands:
        parent.setdefault(s.layer_name, s.layer_name)
    for s in strands:
        p = getattr(s, 'parent', None)
        p_name = getattr(p, 'layer_name', None)
        if p_name in parent:
            union(s.layer_name, p_name)
        for info in (getattr(s, 'knot_connections', None) or {}).values():
            other = (info or {}).get('connected_strand')
            o_name = getattr(other, 'layer_name', None)
            if o_name in parent:
                union(s.layer_name, o_name)
    return {name: find(name) for name in parent}


def _surviving_shadow(canvas, casting_strand, receiving_strand, casting_layer, receiving_layer):
    """What is left of *casting_layer*'s shadow on *receiving_layer* once the
    masks' shadow blockers and the strands in between are cut out: the caster
    grown by the blur, intersected with the receiver.

    This is the measure AUTO_HIDE_SURVIVAL_RATIO was tuned on (it is how the
    renderer treated masks before the mask shadow fix, and how the Shadow
    Editor previewed shadows until then), so the pairs this module hides stay
    the same. The renderer no longer cuts blockers; the preview now shows the
    renderer's own shadow (shader_utils.shadow_preview).
    """
    from masked_strand import MaskedStrand
    import shader_utils

    layer_order = canvas.layer_state_manager.getOrder()
    if casting_layer not in layer_order or receiving_layer not in layer_order:
        return QPainterPath()

    casting_index = layer_order.index(casting_layer)
    receiving_index = layer_order.index(receiving_layer)

    # Shadow only casts downward (onto layers with lower index)
    if receiving_index >= casting_index:
        return QPainterPath()

    # Build shadow path from casting strand
    max_blur_radius = 30.0
    shadow_path = shader_utils.build_shadow_geometry(casting_strand, max_blur_radius, include_circles=False)

    # Build receiving strand stroke path
    receiving_stroke_path = shader_utils.build_rendered_geometry(receiving_strand)

    # Special handling for masked strands
    if hasattr(receiving_strand, 'get_mask_path'):
        try:
            receiving_stroke_path = shader_utils.get_proper_masked_strand_path(receiving_strand)
        except Exception:
            pass

    # Calculate intersection
    intersection = QPainterPath(shadow_path)
    if not (getattr(casting_strand, 'full_arrow_visible', False) and getattr(casting_strand, 'arrow_casts_shadow', False)):
        circle_shadow_path = shader_utils.build_shadow_circle_geometry(casting_strand, max_blur_radius+2)
        intersection.addPath(circle_shadow_path)
    intersection = QPainterPath(intersection).intersected(receiving_stroke_path)

    if intersection.isEmpty():
        return QPainterPath()

    # Check shadow override visibility
    shadow_override = canvas.layer_state_manager.get_shadow_override(casting_layer, receiving_layer)
    if not canvas.layer_state_manager.get_shadow_visibility(casting_layer, receiving_layer):
        return QPainterPath()

    # Check if we should allow complete shadow (skip mask blocking)
    allow_full_shadow = shadow_override and shadow_override.get('allow_full_shadow', False)

    # Apply configured layer subtraction.
    subtracted_layers = canvas.layer_state_manager.get_subtracted_layers(casting_layer, receiving_layer)
    intersection, _ = shader_utils._subtract_named_layer_paths(intersection, canvas, subtracted_layers)
    if intersection.isEmpty():
        return QPainterPath()

    # Apply mask blocking (unless allow_full_shadow is enabled)
    current_shadow = QPainterPath(intersection)

    masked_strands_map = {}
    for s in canvas.strands:
        if isinstance(s, MaskedStrand):
            masked_strands_map[s.layer_name] = {
                'masked_strand': s,
                'components': [s.first_selected_strand.layer_name, s.second_selected_strand.layer_name]
            }

    if not allow_full_shadow:

        # Apply blocking from each mask above the casting strand
        for mask_name, mask_info in masked_strands_map.items():
            mask_strand = mask_info['masked_strand']
            is_mask_hidden = getattr(mask_strand, 'is_hidden', False)

            if not is_mask_hidden and mask_name in layer_order:
                mask_index = layer_order.index(mask_name)

                # Only masks above the casting strand can block
                if mask_index <= casting_index:
                    continue

                # Don't block if casting onto the mask itself
                if mask_name == receiving_layer:
                    continue

                # Get blocker path
                blocker_path = shader_utils.get_shadow_blocker_path(mask_strand, max_blur_radius)
                if not blocker_path.isEmpty():
                    current_shadow = QPainterPath(current_shadow).subtracted(blocker_path)

        current_shadow = shader_utils._subtract_visible_component_mask_coverage(
            current_shadow,
            masked_strands_map,
            layer_order,
            receiving_layer,
            receiving_stroke_path,
            max_blur_radius,
        )

        intermediate_layers = shader_utils._get_intermediate_layer_names(layer_order, casting_layer, receiving_layer)
        current_shadow, _ = shader_utils._subtract_named_layer_paths(current_shadow, canvas, intermediate_layers)

    return current_shadow


def compute_auto_hidden_pairs(canvas):
    """Find casting->receiving pairs whose shadow contradicts a masked weave.

    A mask X_Y forces X visually OVER Y at their crossing: Y is the strand
    being woven under, and the mask machinery itself takes over the shading
    of that crossing. So the CANDIDATE casters are exactly the second
    components (Y) of visible masks, and the candidate receivers are the
    lower-z strands welded into that mask's fabric (the weld chains of both
    components). For each candidate the survival ratio decides: if the pair's
    shadow, after the renderer's own mask-blocking + intermediate
    subtractions, keeps less than AUTO_HIDE_SURVIVAL_RATIO of its raw
    caster∩receiver overlap, everything it can still paint is residue
    (slivers + blur fringe) on top of the woven fabric -> hide it. Y's
    shadows onto EXPOSED fabric members at other, unmasked crossings survive
    with high ratios and are kept.

    Returns a list of dicts: {'casting', 'receiving', 'ratio', 'raw_area'}.
    Pairs that already carry a user-authored override (no 'auto' key) are
    skipped — the user's decision always wins.
    """
    from masked_strand import MaskedStrand
    import shader_utils

    manager = getattr(canvas, 'layer_state_manager', None)
    if manager is None:
        return []
    layer_order = manager.getOrder()
    by_name = {s.layer_name: s for s in canvas.strands}

    masks = [s for s in canvas.strands
             if isinstance(s, MaskedStrand) and not getattr(s, 'is_hidden', False)]
    if not masks:
        return []

    chain_of = _weld_chain_ids(canvas)

    # caster layer_name -> set of receiver layer_names in that mask's fabric.
    candidate_receivers = {}
    mask_component_pairs = set()
    for m in masks:
        first = getattr(m.first_selected_strand, 'layer_name', None)
        second = getattr(m.second_selected_strand, 'layer_name', None)
        if not first or not second:
            continue
        # Component pairs of a visible mask never shadow each other in the
        # renderer (the mask owns that crossing) — mirror the skip.
        mask_component_pairs.add((first, second))
        mask_component_pairs.add((second, first))
        fabric_chains = {chain_of.get(first), chain_of.get(second)} - {None}
        recvs = candidate_receivers.setdefault(second, set())
        for name, cid in chain_of.items():
            if cid in fabric_chains:
                recvs.add(name)

    overrides = manager.get_shadow_overrides()
    max_blur_radius = 30.0
    results = []

    for casting, fabric in candidate_receivers.items():
        cs = by_name.get(casting)
        if cs is None or isinstance(cs, MaskedStrand) or getattr(cs, 'is_hidden', False):
            continue
        if casting not in layer_order:
            continue
        ci = layer_order.index(casting)

        raw_caster = None  # built lazily, reused across receivers
        for ri in range(ci):
            receiving = layer_order[ri]
            rs = by_name.get(receiving)
            if rs is None or isinstance(rs, MaskedStrand) or getattr(rs, 'is_hidden', False):
                continue
            if receiving == casting or receiving not in fabric:
                continue
            if (casting, receiving) in mask_component_pairs:
                continue
            existing = (overrides.get(casting) or {}).get(receiving)
            if existing and not existing.get('auto'):
                continue  # user-authored (incl. 'pinned') — hands off

            # RAW overlap: caster shadow footprint ∩ receiver rendered
            # geometry, exactly as _surviving_shadow builds it before any
            # gating/subtraction.
            if raw_caster is None:
                raw_caster = QPainterPath(
                    shader_utils.build_shadow_geometry(cs, max_blur_radius, include_circles=False))
                if not (getattr(cs, 'full_arrow_visible', False)
                        and getattr(cs, 'arrow_casts_shadow', False)):
                    raw_caster.addPath(
                        shader_utils.build_shadow_circle_geometry(cs, max_blur_radius + 2))
            recv_geom = shader_utils.build_rendered_geometry(rs)
            raw = QPainterPath(raw_caster).intersected(recv_geom)
            if raw.isEmpty():
                continue
            raw_area = _path_area(raw)
            if raw_area < AUTO_MIN_RAW_AREA:
                continue

            # SURVIVOR: the per-pair path after the visibility gate +
            # subtracted_layers + mask blocking + intermediate subtraction,
            # measured as AUTO_HIDE_SURVIVAL_RATIO was tuned (_surviving_shadow).
            survivor = _surviving_shadow(canvas, cs, rs, casting, receiving)
            ratio = _path_area(survivor) / raw_area
            if ratio < AUTO_HIDE_SURVIVAL_RATIO:
                results.append({
                    'casting': casting,
                    'receiving': receiving,
                    'ratio': ratio,
                    'raw_area': raw_area,
                })
    return results


def recompute_auto_shadow_overrides(canvas):
    """Refresh the auto-managed shadow_overrides entries from the current
    scene: wipe previous 'auto' entries (and entries referencing deleted
    layers), then re-add {'visibility': False, 'auto': True} for every pair
    compute_auto_hidden_pairs flags. User-authored entries are untouched.

    Safe to call from any edit path — never raises. Returns True if the
    overrides changed."""
    manager = getattr(canvas, 'layer_state_manager', None)
    if manager is None:
        return False
    try:
        overrides = manager.get_shadow_overrides()
        names = {s.layer_name for s in canvas.strands}
        changed = False

        for c in list(overrides.keys()):
            recv_map = overrides[c]
            for r in list(recv_map.keys()):
                entry = recv_map[r] or {}
                if entry.get('auto') or c not in names or r not in names:
                    del recv_map[r]
                    changed = True
            if not recv_map:
                del overrides[c]

        for pair in compute_auto_hidden_pairs(canvas):
            c, r = pair['casting'], pair['receiving']
            if (overrides.get(c) or {}).get(r):
                continue  # user-authored survives
            overrides.setdefault(c, {})[r] = {'visibility': False, 'auto': True}
            changed = True

        if changed:
            manager.save_current_state()
        return changed
    except Exception:
        logging.exception("auto_shadow: recompute failed; overrides left as-is")
        return False
