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
same way the renderer will, and if the surviving shadow is only a small
fraction of the raw caster/receiver overlap, the pair can only contribute
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
            # geometry, exactly as calculate_shadow_for_layer_pair builds it
            # before any gating/subtraction (shader_utils.py:1950-1969).
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

            # SURVIVOR: the final per-pair path after the renderer's own
            # visibility gate + subtracted_layers + mask blocking +
            # intermediate subtraction (the shadow-editor preview primitive).
            survivor = shader_utils.calculate_shadow_for_layer_pair(
                canvas, cs, rs, casting, receiving)
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
