from PyQt5.QtGui import QPainterPath, QPainterPathStroker, QPen, QBrush, QColor, QPainter, QTransform
from PyQt5.QtCore import Qt, QRectF, QPointF
from typing import List
import math
from functools import lru_cache


def _union_paths(*paths: QPainterPath) -> QPainterPath:
    """
    Build a new QPainterPath that covers the union of the supplied paths.

    Using a fresh container avoids relying on implicit sharing, which can
    otherwise leave cached references pointing at stale geometry when callers
    expect an in-place update.
    """
    combined = QPainterPath()
    for path in paths:
        if not isinstance(path, QPainterPath) or path.isEmpty():
            continue
        combined.addPath(QPainterPath(path))
    if combined.isEmpty():
        return QPainterPath()
    combined.setFillRule(Qt.WindingFill)
    return QPainterPath(combined).simplified()


def _get_mask_visual_path(mask_strand) -> QPainterPath:
    """
    Return the combined visible geometry of a mask.

    Mask rendering uses both the fill path and the thicker stroke path. Shadow
    blocking must match that visible footprint or shadows can bleed through the
    mask's outline or translucent fill.
    """
    if mask_strand is None:
        return QPainterPath()

    fill_path = QPainterPath()
    stroke_path = QPainterPath()

    if hasattr(mask_strand, "get_mask_path"):
        try:
            fill_path = mask_strand.get_mask_path()
        except Exception:
            fill_path = QPainterPath()

    if hasattr(mask_strand, "get_mask_path_stroke"):
        try:
            stroke_path = mask_strand.get_mask_path_stroke()
        except Exception:
            stroke_path = QPainterPath()

    return _union_paths(fill_path, stroke_path)


def _mask_footprint(mask_strand) -> QPainterPath:
    """Everything the mask paints: its stroke and fill paths united.

    Unlike _get_mask_visual_path this is a proper union. Adding the two paths
    under the winding rule cancels them wherever they run in opposite
    directions, which drops whole parts of some masks (a crossing where one
    strand ends inside the other)."""
    try:
        fill_path = mask_strand.get_mask_path()
        stroke_path = mask_strand.get_mask_path_stroke()
    except Exception:
        return QPainterPath()
    if stroke_path.isEmpty():
        return QPainterPath(fill_path)
    if fill_path.isEmpty():
        return QPainterPath(stroke_path)
    return QPainterPath(stroke_path).united(fill_path)


def _grown(path: QPainterPath, radius: float) -> QPainterPath:
    """*path* grown by *radius* on every side, as a proper union (see
    _mask_footprint). The stroker's outline overlaps itself; it is
    simplified before the union, which otherwise drops pixels of *path* for
    small radii."""
    if path.isEmpty() or radius <= 0:
        return QPainterPath(path)
    stroker = QPainterPathStroker()
    stroker.setWidth(radius * 2.0)
    stroker.setJoinStyle(Qt.RoundJoin)
    stroker.setCapStyle(Qt.RoundCap)
    return QPainterPath(path).united(stroker.createStroke(path).simplified())


def _frame_cache(painter):
    """Scratch space for one paint of the canvas: mask geometry and shadow
    paths that every strand's pass would otherwise compute again. It lives on
    the painter, which the canvas creates anew for every paint, so nothing
    carries over once the scene changes."""
    if painter is None:
        return {}
    cache = getattr(painter, '_mask_shadow_cache', None)
    if cache is None:
        cache = {}
        try:
            painter._mask_shadow_cache = cache
        except Exception:
            pass
    return cache


def _piece_of(mask_strand, cache):
    """_mask_footprint(), once per paint."""
    key = ('footprint', id(mask_strand))
    if key not in cache:
        cache[key] = _mask_footprint(mask_strand)
    return cache[key]


def _erased_area(mask_strand):
    """The parts of a mask the user erased (its deletion rectangles, read as
    MaskedStrand.get_mask_path reads them), united."""
    area = QPainterPath()
    for rect in getattr(mask_strand, 'deletion_rectangles', None) or []:
        piece = QPainterPath()
        try:
            if 'top_left' in rect and 'bottom_right' in rect:
                piece.moveTo(QPointF(*rect['top_left']))
                piece.lineTo(QPointF(*rect.get('top_right', rect['bottom_right'])))
                piece.lineTo(QPointF(*rect['bottom_right']))
                piece.lineTo(QPointF(*rect.get('bottom_left', rect['top_left'])))
                piece.closeSubpath()
            elif all(k in rect for k in ('x', 'y', 'width', 'height')):
                piece.addRect(QRectF(rect['x'], rect['y'], rect['width'], rect['height']))
        except Exception:
            continue
        if not piece.isEmpty():
            area = piece if area.isEmpty() else area.united(piece)
    return area


def _zone_of(mask_strand, blur_px, cache):
    """The mask's footprint grown by the blur radius (where its shadows
    reach), minus the parts the user erased, where the second strand stays on
    top; once per paint.

    Growing a curved footprint is costly, so the last zone is also kept on
    the mask and reused while its footprint, erased parts and the blur are
    unchanged (for example while another strand is dragged). It is kept in
    the instance's own __dict__: MaskedStrand forwards unknown attributes to
    its strands."""
    key = ('zone', id(mask_strand), float(blur_px))
    if key not in cache:
        piece = _piece_of(mask_strand, cache)
        erased = _erased_area(mask_strand)
        own = getattr(mask_strand, '__dict__', {})
        memo = own.get('_mask_zone_memo')
        if memo is not None and memo[0] == float(blur_px) and memo[1] == piece and memo[2] == erased:
            zone = memo[3]
        else:
            zone = _grown(piece, blur_px)
            if not erased.isEmpty():
                zone = zone.subtracted(erased)
            own['_mask_zone_memo'] = (float(blur_px), QPainterPath(piece), QPainterPath(erased), zone)
        cache[key] = zone
    return cache[key]


def _may_touch(item, rect, cache=None):
    """Cheap and conservative: can *item*'s drawn geometry overlap *rect*?
    Qt's boolean operations leave a path untouched when the other one does
    not overlap it, so skipping such items changes nothing."""
    key = ('bounds', id(item))
    bounds = cache.get(key) if cache is not None else None
    if bounds is None:
        try:
            first = getattr(item, 'first_selected_strand', None)
            second = getattr(item, 'second_selected_strand', None)
            if hasattr(item, 'get_mask_path') and first is not None and second is not None:
                bounds = first.boundingRect().intersected(second.boundingRect())
                owner = first
            else:
                bounds = item.boundingRect()
                owner = item
            # Room for rounded ends, circles and the masks' widened outlines.
            margin = getattr(owner, 'width', 0) + 2 * getattr(owner, 'stroke_width', 0) + 4
            bounds = bounds.adjusted(-margin, -margin, margin, margin)
        except Exception:
            return True
        if cache is not None:
            cache[key] = bounds
    return bounds.intersects(rect)


def _subtract_visible_component_mask_coverage(
    shadow_path: QPainterPath,
    masked_strands_map: dict,
    layer_order: List[str],
    receiving_layer: str,
    receiving_path: QPainterPath,
    blur_px: float,
) -> QPainterPath:
    """
    Remove shadow segments that fall beneath a visible mask drawn above one of
    its component strands.

    This prevents unrelated shadows on a component strand from remaining
    visible through the mask.
    """
    if not isinstance(shadow_path, QPainterPath):
        return QPainterPath()
    if shadow_path.isEmpty():
        return QPainterPath(shadow_path)
    if not receiving_layer or receiving_layer not in layer_order:
        return QPainterPath(shadow_path)

    current_shadow = QPainterPath(shadow_path)
    receiving_index = layer_order.index(receiving_layer)

    for mask_name, mask_info in masked_strands_map.items():
        components = mask_info.get("components", [])
        if receiving_layer not in components:
            continue
        if mask_name not in layer_order:
            continue

        mask_strand = mask_info.get("masked_strand")
        if getattr(mask_strand, "is_hidden", False):
            continue

        mask_index = layer_order.index(mask_name)
        if mask_index <= receiving_index:
            continue

        blocker_path = get_shadow_blocker_path(mask_strand, blur_px)
        if blocker_path.isEmpty():
            blocker_path = _get_mask_visual_path(mask_strand)
        if blocker_path.isEmpty():
            continue

        if isinstance(receiving_path, QPainterPath) and not receiving_path.isEmpty():
            try:
                if not blocker_path.intersects(receiving_path):
                    continue
            except Exception:
                pass

        current_shadow = QPainterPath(current_shadow).subtracted(blocker_path)
        if current_shadow.isEmpty():
            break

    return current_shadow


def draw_mask_lift_shadow(painter, mask_strand, shadow_color=None, num_steps=3, max_blur_radius=29.99):
    """Paint the first strand's shadow on the second strand where the mask
    lifts it.

    The first strand's own pass computes this shadow together with all its
    other shadows, exactly as for a genuine crossing, but that pass runs
    before the second strand is drawn, which would cover it. The mask re-applies
    the same fill and soft edge on top, clipped to the part of the second
    strand that shows (only near the mask when part of it is erased).
    """
    first = getattr(mask_strand, 'first_selected_strand', None)
    second = getattr(mask_strand, 'second_selected_strand', None)
    canvas = getattr(mask_strand, 'canvas', None)
    if first is None or second is None or canvas is None:
        return
    if hasattr(canvas, 'shadow_enabled') and not canvas.shadow_enabled:
        return
    collected = draw_strand_shadow(painter, first, shadow_color, num_steps=num_steps,
                                   max_blur_radius=max_blur_radius, collect_only=True)
    if not collected or collected['lift_path'].isEmpty():
        return
    clip = _mask_lift_clip(mask_strand, max_blur_radius, _frame_cache(painter))
    if clip.isEmpty():
        return

    _paint_collected_shadow(painter, collected, clip, num_steps, max_blur_radius,
                            fill_path=collected['lift_path'])


def _mask_lift_clip(mask_strand, max_blur_radius, cache):
    """Where draw_mask_lift_shadow may paint: the part of the second strand
    that shows when the mask is drawn (only near the mask when part of it is
    erased)."""
    canvas = mask_strand.canvas
    second = mask_strand.second_selected_strand
    if _piece_of(mask_strand, cache).isEmpty():
        return QPainterPath()
    visible = build_rendered_geometry(second)
    if hasattr(canvas, 'layer_state_manager') and canvas.layer_state_manager:
        layer_order = canvas.layer_state_manager.getOrder()
        if second.layer_name in layer_order and mask_strand.layer_name in layer_order:
            # Whatever is drawn after the second strand but before the mask covers it.
            covering = _get_intermediate_layer_names(layer_order, second.layer_name, mask_strand.layer_name)
            by_name = {getattr(item, 'layer_name', None): item for item in canvas.strands}
            area = visible.boundingRect()
            covering = [name for name in covering if name in by_name and _may_touch(by_name[name], area, cache)]
            visible, _ = _subtract_named_layer_paths(visible, canvas, covering)
    clip = QPainterPath(visible)
    if not _whole_mask(mask_strand):
        # Only near the mask; elsewhere the second strand stays on top.
        clip = clip.intersected(_zone_of(mask_strand, max_blur_radius, cache))
    return clip


def _shadow_shown_for(strand, canvas):
    """Whether *strand*'s draw paints its shadow pass (not switched off for
    it, and not left out by "shadow for the selected strand only")."""
    if getattr(strand, 'hide_shadow', False) or not getattr(strand, 'should_draw_shadow', True):
        return False
    if getattr(canvas, 'shadow_selected_only', False):
        return strand is getattr(canvas, 'selected_strand', None) or \
            strand is getattr(canvas, 'selected_attached_strand', None)
    return True


def _footprint_of(strand, cache):
    """_drawn_footprint(), once per paint."""
    key = ('drawn', id(strand))
    if key not in cache:
        cache[key] = _drawn_footprint(strand)
    return cache[key]


def _runs_under(item, footprint, piece):
    """Whether the mask's piece covers *item* across (it crosses the piece),
    not only along an edge (it runs beside the piece, its outline overlapping).

    It crosses when the overlap is more than half the strand's drawn width
    thick somewhere: some point of it lies deeper than a quarter width inside,
    which the overlap shifted that far in eight directions still covers."""
    shared = QPainterPath(footprint).intersected(piece)
    if shared.isEmpty():
        return False
    reach = max(2.0, (getattr(item, 'width', 0) + 2 * getattr(item, 'stroke_width', 0)) / 4.0)
    diagonal = reach * 0.7071
    core = QPainterPath(shared)
    for dx, dy in ((reach, 0), (-reach, 0), (0, reach), (0, -reach),
                   (diagonal, diagonal), (diagonal, -diagonal), (-diagonal, diagonal), (-diagonal, -diagonal)):
        core = core.intersected(QTransform().translate(dx, dy).map(shared))
        if core.isEmpty():
            return False
    return _approx_path_area(core) > 0.5


def _cut_on_receiver(collected, receiver_layer, cut, cut_key, cache):
    """*collected* (a draw_strand_shadow(collect_only=True) result) with its
    outline on *receiver_layer* cut by *cut*, both for the fill and for the
    soft edge.

    Near a mask the caster's outline on the mask's second strand is not cut by
    the first strand (see _subtract_intermediates), so the soft edge along it
    would land on the piece the mask lifts over that strand. At a genuine
    crossing the first strand, lying above the second one, cuts it there.
    *cut_key* names *cut* in the frame cache."""
    key = ('cut_on', id(collected), receiver_layer, cut_key)
    if key in cache:
        return cache[key]
    outlines = collected.get('outlines')
    if outlines is None or all(name != receiver_layer for name, _outline in outlines):
        cache[key] = collected
        return collected
    fill_path = QPainterPath()
    for name, outline in outlines:
        if name == receiver_layer and outline.intersects(cut):
            outline = _closed_outline(_subtracted_checked(outline, cut))
        fill_path.addPath(outline)
    fill_path.setFillRule(Qt.WindingFill)
    stroke_path = QPainterPath(fill_path)
    stroke_path.addPath(collected['lift_path'])
    stroke_path.addPath(collected['circles'])
    stroke_path.setFillRule(Qt.WindingFill)
    result = dict(collected, stroke_path=stroke_path, fill_path=fill_path)
    result.pop('_subpaths', None)
    cache[key] = result
    return result


def _layer_positions(canvas, cache):
    """{layer name: index} in the canvas's layer order, once per paint."""
    positions = cache.get('layer_positions')
    if positions is None:
        manager = getattr(canvas, 'layer_state_manager', None)
        order = manager.getOrder() if manager else []
        positions = {name: index for index, name in enumerate(order)}
        cache['layer_positions'] = positions
    return positions


def _joined(item, strands):
    """Whether *item* has an end on an end of one of *strands*: it continues
    one of them at a joint (an attached strand, a closed knot)."""
    for strand in strands:
        for point in (getattr(strand, 'start', None), getattr(strand, 'end', None)):
            if point is not None and _ends_at(item, point):
                return True
    return False


def _opaque_cover(item, footprint):
    """What *item* paints solidly over whatever is below it, or None when it
    shows what is below. A strand paints its whole body in the outline
    colour, then its fill on top (Strand._paint_body_paths): with an opaque
    outline all of it is solid, whatever the fill; with a see-through outline
    only an opaque fill is, 1 outline width in from the edge. A strand drawn
    as a shadow only or as an arrow paints nothing solid there."""
    if getattr(item, 'shadow_only', False) or getattr(item, 'full_arrow_visible', False):
        return None
    stroke = getattr(item, 'stroke_color', None)
    stroke_width = float(getattr(item, 'stroke_width', 0) or 0)
    if stroke_width > 0 and (stroke is None or stroke.alpha() == 255):
        return footprint
    color = getattr(item, 'color', None)
    if color is not None and color.alpha() < 255:
        return None
    if stroke_width <= 0:
        return footprint
    solid = QPainterPath(footprint).simplified()
    band = QPainterPathStroker()
    band.setWidth(stroke_width * 2)
    band.setJoinStyle(Qt.RoundJoin)
    return solid.subtracted(band.createStroke(solid).simplified())


def _covering_strands(mask_strand, cache):
    """The strands the mask's piece must not cover, as [(strand, area)]:
    the area is what the strand paints solidly (_opaque_cover).

    The piece is drawn at the mask's place in the layer order, over every
    strand drawn before it. A strand above both of the mask's strands lies
    above their crossing, lifted or not, so where it overlaps the piece it
    stays on top: a wide neighbour running beside the crossing keeps its
    edge, and the first strand keeps its shadow there. Left out, and covered
    as before: a strand between the two (see _mask_sides: it would sit both
    above and below the crossing), one that shows what is below it (the
    piece is what should show through it), and one that continues either
    strand at a joint (the piece hides the joint)."""
    key = ('covering', id(mask_strand))
    if key in cache:
        return cache[key]
    covering = []
    first = getattr(mask_strand, 'first_selected_strand', None)
    second = getattr(mask_strand, 'second_selected_strand', None)
    canvas = getattr(mask_strand, 'canvas', None)
    piece = _piece_of(mask_strand, cache) if first is not None and second is not None else QPainterPath()
    if canvas is not None and not piece.isEmpty():
        positions = _layer_positions(canvas, cache)
        indexes = [positions.get(getattr(item, 'layer_name', None)) for item in (mask_strand, first, second)]
        if None not in indexes:
            mask_index, above = indexes[0], max(indexes[1], indexes[2])
            area = piece.boundingRect()
            for item in canvas.strands:
                index = positions.get(getattr(item, 'layer_name', None))
                if (index is None or not above < index < mask_index or hasattr(item, 'get_mask_path')
                        or getattr(item, 'is_hidden', False) or not _may_touch(item, area, cache)
                        or _joined(item, (first, second))):
                    continue
                solid = _opaque_cover(item, _footprint_of(item, cache))
                if solid is not None and _approx_path_area(QPainterPath(solid).intersected(piece)) > 1.0:
                    covering.append((item, solid))
    cache[key] = covering
    return covering


def _piece_keep(mask_strand, cache):
    """Where the mask's piece may paint: around it, without the strands it
    must not cover (_covering_strands); None when it covers them all. The
    piece and the shadows put back on it are both clipped to it, so they
    match exactly."""
    key = ('keep', id(mask_strand))
    if key not in cache:
        keep = None
        covering = _covering_strands(mask_strand, cache)
        if covering:
            try:
                bounds = mask_strand.get_mask_path_stroke().boundingRect().united(
                    _piece_of(mask_strand, cache).boundingRect()).adjusted(-4, -4, 4, 4)
            except Exception:
                bounds = None
            if bounds is not None:
                keep = QPainterPath()
                keep.addRect(bounds)
                for _item, solid in covering:
                    keep = keep.subtracted(solid)
        cache[key] = keep
    return cache[key]


def clip_mask_piece(painter, mask_strand):
    """Clip *painter* so the mask's piece (fill and outline) leaves the
    strands in _covering_strands uncovered. Call it inside a save/restore
    before painting the piece."""
    keep = _piece_keep(mask_strand, _frame_cache(painter))
    if keep is not None:
        painter.setClipPath(keep, Qt.IntersectClip)


def draw_mask_restored_shadows(painter, mask_strand, shadow_color=None, num_steps=3, max_blur_radius=29.99):
    """Paint again, on top of the mask's piece, the shadows that land on its
    first strand there and were painted before the mask.

    The mask fills its piece flat with the first strand's colour, reaching
    2 px past the second strand's outline to hide that edge. Shadows already on
    the first strand under the piece are painted over, and their soft edges
    end in a straight cut along the piece. They come from strands above the
    first strand in the layer order (their own passes) and from strands that
    masks earlier in the order lift over the first strand (those masks'
    draw_mask_lift_shadow). At a genuine crossing those strands would lie
    above the lifted piece as well, so their shadows go back on top of it.

    The piece is not drawn over a strand above both of the mask's strands
    (_covering_strands), so that strand's shadow always goes back. Any other
    strand is covered where it overlaps the piece:
    - one that continues either strand at a joint casts no shadow on it;
    - one the piece is drawn across (_runs_under) lies below the lifted
      strand there, so its shadow does not belong on the piece;
    - one whose edge only the piece covers (a neighbour running beside the
      crossing) keeps its shadow, reaching the piece's edge.
    """
    canvas = getattr(mask_strand, 'canvas', None)
    first = getattr(mask_strand, 'first_selected_strand', None)
    second = getattr(mask_strand, 'second_selected_strand', None)
    if canvas is None or first is None or second is None:
        return
    if hasattr(canvas, 'shadow_enabled') and not canvas.shadow_enabled:
        return
    manager = getattr(canvas, 'layer_state_manager', None)
    if not manager:
        return
    layer_order = manager.getOrder()
    if mask_strand.layer_name not in layer_order or first.layer_name not in layer_order:
        return
    mask_index = layer_order.index(mask_strand.layer_name)
    first_index = layer_order.index(first.layer_name)
    cache = _frame_cache(painter)
    piece = _piece_of(mask_strand, cache)
    if piece.isEmpty():
        return
    area = piece.boundingRect()
    reach = area.adjusted(-max_blur_radius, -max_blur_radius, max_blur_radius, max_blur_radius)
    uncovered = {id(item) for item, _solid in _covering_strands(mask_strand, cache)}
    keep = _piece_keep(mask_strand, cache)

    for item in canvas.strands:
        if item is mask_strand or item is first or item is second:
            continue
        name = getattr(item, 'layer_name', None)
        if name not in layer_order or layer_order.index(name) > mask_index:
            continue
        if hasattr(item, 'get_mask_path'):
            # A mask before this one that lifts its first strand over ours.
            if getattr(item, 'second_selected_strand', None) is not first or getattr(item, 'is_hidden', False):
                continue
            caster = getattr(item, 'first_selected_strand', None)
            if (caster is None or not _shadow_shown_for(item, canvas)
                    or not item._intersection_shadow_visible()
                    or not _may_touch(item, reach, cache)):
                continue
            collected = draw_strand_shadow(painter, caster, shadow_color, num_steps=num_steps,
                                           max_blur_radius=max_blur_radius, collect_only=True)
            fill_path = collected['lift_path'] if collected else None
            # As draw_mask_lift_shadow: only near that mask when part of it is erased.
            zone = None if _whole_mask(item) else _zone_of(item, max_blur_radius, cache)
        else:
            # A strand above ours in the layer order, which its own pass shades.
            if layer_order.index(name) < first_index:
                continue
            if not _shadow_shown_for(item, canvas) or not _may_touch(item, reach, cache):
                continue
            collected = draw_strand_shadow(painter, item, shadow_color, num_steps=num_steps,
                                           max_blur_radius=max_blur_radius, collect_only=True)
            # Only a strand that shades the first strand.
            if not collected or all(receiver != first.layer_name
                                    for receiver, _outline in collected.get('outlines', ())):
                continue
            zone = None
            if id(item) not in uncovered and _may_touch(item, area, cache):
                footprint = _footprint_of(item, cache)
                if _joined(item, (first, second)):
                    # It continues one of the two at a joint the piece hides:
                    # no shadow of it on the piece.
                    if footprint.intersects(piece):
                        continue
                elif _runs_under(item, footprint, piece):
                    # The piece is drawn across it, so it lies below the
                    # lifted strand there: no shadow on the piece. When the
                    # piece only covers its edge, the shadow goes back up to
                    # the piece's visible edge.
                    continue
            collected = _cut_on_receiver(collected, second.layer_name, piece,
                                         id(mask_strand), cache)
            fill_path = collected['fill_path']
        if not collected or fill_path is None:
            continue
        if (not fill_path.boundingRect().intersects(area)
                and _stroke_source_near(collected, area, max_blur_radius / 2.0 + 2.0).isEmpty()):
            continue  # nothing of it reaches the piece
        # The piece lies on the first strand, so it is the clip itself, less
        # the strands it leaves uncovered (keep) and, for a mask with erased
        # parts, only near that mask (zone).
        _paint_collected_shadow(painter, collected, piece, num_steps, max_blur_radius,
                                fill_path=fill_path, and_clip=[c for c in (zone, keep) if c is not None])


def draw_circle_shadow(painter, strand, shadow_color=None):
    """
    Draw shadow for a circle at the start or end of a strand.
    """
    pass


def _find_canvas_strand_by_layer_name(canvas, layer_name):
    """Return the strand whose ``layer_name`` exactly matches ``layer_name``."""
    if not canvas or not layer_name:
        return None

    for strand in getattr(canvas, 'strands', []):
        if getattr(strand, 'layer_name', None) == layer_name:
            return strand

    return None


def _get_intermediate_layer_names(layer_order, casting_layer, receiving_layer):
    """Return the ordered layer names strictly between casting and receiving."""
    if not layer_order or casting_layer not in layer_order or receiving_layer not in layer_order:
        return []

    casting_index = layer_order.index(casting_layer)
    receiving_index = layer_order.index(receiving_layer)
    start = min(casting_index, receiving_index) + 1
    end = max(casting_index, receiving_index)
    return list(layer_order[start:end])


def _subtract_named_layer_paths(source_path, canvas, layer_names):
    """
    Subtract the rendered geometry of the supplied layers from ``source_path``.

    Returns:
        tuple[QPainterPath, QPainterPath]: The updated path and the union of all
        subtraction geometries that were applied.
    """
    result_path = QPainterPath(source_path)
    blocker_path = QPainterPath()

    if result_path.isEmpty() or not canvas or not layer_names:
        return result_path, blocker_path

    for layer_name in layer_names:
        strand = _find_canvas_strand_by_layer_name(canvas, layer_name)
        if not strand or getattr(strand, 'is_hidden', False):
            continue

        try:
            subtraction_path = build_rendered_geometry(strand)
            if hasattr(strand, 'get_mask_path'):
                subtraction_path = get_proper_masked_strand_path(strand)
        except Exception:
            continue

        if subtraction_path.isEmpty():
            continue

        result_path = _subtracted(result_path, subtraction_path)
        if blocker_path.isEmpty():
            blocker_path = QPainterPath(subtraction_path)
        else:
            blocker_path.addPath(QPainterPath(subtraction_path))

        if result_path.isEmpty():
            break

    return result_path, blocker_path

def _approx_path_area(path: QPainterPath) -> float:
    """Area of *path* from its fill polygons, so overlap tests can ignore the
    hairline slivers Qt's boolean operations leave along shared edges."""
    area = 0.0
    for polygon in path.toFillPolygons():
        points = [polygon.at(i) for i in range(polygon.count())]
        twice = 0.0
        for a, b in zip(points, points[1:] + points[:1]):
            twice += a.x() * b.y() - b.x() * a.y()
        area += abs(twice) / 2.0
    return area


def _overlap_within(path_a: QPainterPath, path_b: QPainterPath, zone: QPainterPath) -> bool:
    """Whether two strand outlines genuinely overlap inside *zone*."""
    if not path_a.boundingRect().intersects(path_b.boundingRect()):
        return False
    shared = QPainterPath(path_a).intersected(path_b)
    if shared.isEmpty():
        return False
    return _approx_path_area(QPainterPath(shared).intersected(zone)) > 1.0


def _drawn_footprint(strand) -> QPainterPath:
    """What *strand* paints, rounded ends included. build_rendered_geometry
    leaves out an attached strand's own start cap even though draw() paints
    it (unless the cap is lowered, see lowered_start_cap)."""
    if lowered_start_cap(strand) is not None:
        return _build_rendered_geometry(strand)
    try:
        footprint = strand.get_selection_path()
        if not footprint.isEmpty():
            return footprint
    except Exception:
        pass
    return build_rendered_geometry(strand)


def _strand_key(strand):
    """The geometry a strand is drawn from, to tell when a memo is stale."""
    def xy(point):
        return (round(point.x(), 3), round(point.y(), 3)) if point is not None else None
    return (id(strand), xy(getattr(strand, 'start', None)), xy(getattr(strand, 'end', None)),
            xy(getattr(strand, 'control_point1', None)), xy(getattr(strand, 'control_point2', None)),
            xy(getattr(strand, 'control_point_center', None)),
            getattr(strand, 'width', None), getattr(strand, 'stroke_width', None),
            bool(getattr(strand, 'is_hidden', False)),
            getattr(strand, 'control_point_base_fraction', None), getattr(strand, 'distance_multiplier', None),
            getattr(strand, 'curve_response_exponent', None),
            bool(getattr(strand, 'control_point_center_locked', False)))


def lowered_start_cap(strand):
    """How an attached strand's unfolded start cap is drawn under the strands
    that cross its parent at the joint, or None when it is drawn as usual.

    An unfolded joint (start circle switched on with a transparent stroke) is
    hidden by a round cap of fill colour. The attached strand painted it at
    its own layer, so a strand between the parent and the attached strand in
    the layer order that crosses the parent at the joint ended up under the
    cap, its edge and the band it casts on the cord bitten off. Such a cap is
    lowered: the parent paints it right after itself (draw_lowered_caps), the
    strands crossing there are drawn over it and shade it (it counts as part
    of the parent in build_rendered_geometry), the attached strand hides the
    seam with a thin strip (``patch``), and the crossers' soft edges are
    painted again over the attached strand next to the joint (``shade_zone``),
    where the cord still runs under them until it comes out. Only a strand that crosses the parent at
    the joint and not the attached strand's own body there counts: one the
    attached strand lies over next to the joint (the cord passes over it
    there, as the layer order says) keeps lying under the cap too.

    Returns {'parent', 'cap', 'crossers', 'patch', 'shade_zone',
    'parent_geometry'}; memoised on the strand while the strands involved,
    the layer order and the blur are unchanged.
    """
    parent = getattr(strand, 'parent', None)
    canvas = getattr(strand, 'canvas', None)
    if (parent is None or canvas is None or not hasattr(strand, 'unfolded_start_cap')
            or getattr(strand, 'is_hidden', False) or getattr(parent, 'is_hidden', False)
            or not strand.has_circles or not strand.has_circles[0]
            or strand.start_circle_stroke_color.alpha() != 0
            or not getattr(strand, 'is_setting_staring_circle', False)):
        return None
    manager = getattr(canvas, 'layer_state_manager', None)
    if not manager:
        return None
    try:
        layer_order = manager.getOrder()
        low = layer_order.index(parent.layer_name)
        high = layer_order.index(strand.layer_name)
    except (ValueError, AttributeError):
        return None
    if high - low < 2:
        return None
    between = set(layer_order[low + 1:high])
    candidates = [item for item in canvas.strands
                  if getattr(item, 'layer_name', None) in between and not hasattr(item, 'get_mask_path')
                  and not getattr(item, 'is_hidden', False)]
    if not candidates:
        return None
    shading = bool(getattr(canvas, 'shadow_enabled', False))
    blur = float(getattr(canvas, 'max_blur_radius', 29.99) or 29.99)
    key = (tuple(layer_order), _strand_key(strand), _strand_key(parent),
           tuple(_strand_key(item) for item in candidates), shading, blur)
    own = strand.__dict__
    memo = own.get('_lowered_cap_memo')
    if memo is not None and memo[0] == key:
        return memo[1]
    info = _compute_lowered_start_cap(strand, parent, candidates, shading, blur)
    own['_lowered_cap_memo'] = (key, info)
    return info


def _compute_lowered_start_cap(strand, parent, candidates, shading, blur):
    try:
        cap = strand.unfolded_start_cap()
    except Exception:
        return None
    if cap.isEmpty():
        return None
    cap_rect = cap.boundingRect()
    try:
        parent_body = parent.get_body_selection_path()
    except Exception:
        parent_body = _build_rendered_geometry(parent)
    near_joint = QPainterPath(parent_body).intersected(_grown(cap, 2.0))
    # The attached strand's own body next to the joint (its cap left out): a
    # strand it lies over there stays under the cap too.
    own_near_joint = QPainterPath(_build_rendered_geometry(strand)).intersected(_grown(cap, 2.0))
    crossers = []
    for item in candidates:
        try:
            if not item.boundingRect().adjusted(-4, -4, 4, 4).intersects(cap_rect):
                continue
            footprint = item.get_selection_path()
        except Exception:
            continue
        if footprint.isEmpty() or not footprint.intersects(cap):
            continue
        if (_approx_path_area(QPainterPath(footprint).intersected(near_joint)) > 1.0
                and _approx_path_area(QPainterPath(footprint).intersected(own_near_joint)) <= 1.0):
            crossers.append((item, footprint))
    if not crossers:
        return None
    covered = QPainterPath()
    for _item, footprint in crossers:
        covered = QPainterPath(footprint) if covered.isEmpty() else covered.united(footprint)
    # A strip across the seam, where the attached strand's flat start meets
    # the parent's flat end, in fill colour so that no hairline shows there.
    angle = strand._unfolded_start_angle()
    strip = QPainterPath()
    strip.addRect(QRectF(-2.5, -strand.width / 2.0, 5.0, strand.width))
    strip = QTransform().translate(strand.start.x(), strand.start.y()).rotate(math.degrees(angle)).map(strip)
    patch = _subtracted(strip, covered)
    # Next to the joint the cord runs under the crossers until it comes out
    # beside them, so their soft edges land on the attached strand there too:
    # its body (and the strip) within a full width of the joint, off the
    # crossers, and away from anywhere it lies over one of them.
    own = QPainterPath(_build_rendered_geometry(strand)).united(strip)
    reach = QPainterPath()
    reach.addEllipse(QPointF(strand.start), strand.width + strand.stroke_width * 2,
                     strand.width + strand.stroke_width * 2)
    shade_zone = QPainterPath()
    if shading:
        shade_zone = _subtracted(QPainterPath(own).intersected(reach), covered)
        for _item, footprint in crossers:
            over = QPainterPath(footprint).intersected(own).intersected(reach)
            if _approx_path_area(over) > 1.0:
                shade_zone = _subtracted(shade_zone, _grown(over, blur / 2.0 + 2.0))
    parent_geometry = QPainterPath(_build_rendered_geometry(parent)).united(cap)
    return {'parent': parent, 'cap': cap, 'crossers': [item for item, _f in crossers],
            'patch': patch, 'shade_zone': shade_zone, 'parent_geometry': parent_geometry}


def lowered_caps_of(strand):
    """lowered_start_cap() of *strand*'s attached strands whose cap it paints."""
    lowered = []
    for child in getattr(strand, 'attached_strands', None) or []:
        info = lowered_start_cap(child)
        if info is not None and info['parent'] is strand:
            lowered.append((child, info))
    return lowered


def draw_lowered_caps(painter, strand):
    """Paint, at *strand*'s layer, the unfolded start caps of its attached
    strands that are lowered (see lowered_start_cap)."""
    lowered = lowered_caps_of(strand)
    if not lowered:
        return
    painter.save()
    try:
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        for child, info in lowered:
            painter.setBrush(QBrush(child.color))
            painter.drawPath(info['cap'])
    finally:
        painter.restore()


def _draw_crosser_edges(painter, strand, info):
    """Paint the soft edges of the crossers of *strand*'s lowered cap again
    over *strand* next to the joint (``shade_zone``), as each crosser's own
    pass strokes them."""
    canvas = strand.canvas
    zone = info['shade_zone']
    if zone.isEmpty() or not getattr(canvas, 'shadow_enabled', False):
        return
    manager = getattr(canvas, 'layer_state_manager', None)
    num_steps = int(getattr(canvas, 'num_steps', 3) or 3)
    blur = float(getattr(canvas, 'max_blur_radius', 29.99) or 29.99)
    parent_layer = info['parent'].layer_name
    for crosser in info['crossers']:
        if not _shadow_shown_for(crosser, canvas):
            continue
        if manager is not None and not manager.get_shadow_visibility(crosser.layer_name, parent_layer):
            continue
        _path, shadow_path, _joints = _caster_shadow_path(crosser)
        color = QColor(getattr(canvas, 'default_shadow_color', None) or getattr(crosser, 'shadow_color', None)
                       or QColor(0, 0, 0, 150))
        collected = {'color': color, 'stroke_path': _closed_outline(shadow_path)}
        _paint_collected_shadow(painter, collected, zone, num_steps, blur)


def draw_with_lowered_cap(painter, strand, draw_body):
    """Draw *strand* with *draw_body* (its own drawing), handling a lowered
    start cap: the body paints no cap of its own, a strip hides the seam, and
    the crossers' soft edges go back over it next to the joint. Then paint
    the lowered caps of the strands attached to it."""
    info = lowered_start_cap(strand)
    if info is None:
        draw_body()
    else:
        strand._start_cap_lowered = True
        try:
            draw_body()
        finally:
            strand._start_cap_lowered = False
        painter.save()
        try:
            if not info['patch'].isEmpty():
                painter.setRenderHint(QPainter.Antialiasing, True)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(strand.color))
                painter.drawPath(info['patch'])
            _draw_crosser_edges(painter, strand, info)
        finally:
            painter.restore()
    draw_lowered_caps(painter, strand)


def _mask_sides(mask_strand, canvas, layer_order, blur_px, lifted_pairs=frozenset(), cache=None):
    """How a visible mask restacks the strands around it, or None.

    A mask lifts its first strand F over its second strand S at their
    crossing, but only the crossing itself is redrawn. Near the mask (the
    ``zone``: its footprint grown by the blur radius) the picture must look
    like a genuine crossing: the ``upper`` side (F and the strands above F
    that cross F there) lies above the ``lower`` side (S and the strands below
    S that S crosses there), as if F had been moved above S in the layer
    order. Returns {'zone', 'upper', 'lower'} with sets of layer names, plus
    ``between``: strands above F and below S that cross both there, which
    keep their place in the layer order (moving one to either side would flip
    one of its crossings, and the mask swaps F and S only; the mask's piece is
    drawn at the mask's own place in the layer order and covers whatever is
    below it), ``first``/``second`` (layer names) and ``whole``: whether the
    mask covers all of F and S's overlap (no erased parts), which makes F lie
    above S everywhere, not only near the mask. *lifted_pairs* are the (first,
    second) layer names of every visible mask: a strand another mask lifts
    over S is not below S, and one F is lifted over is not above F.
    """
    key = ('sides', id(mask_strand), float(blur_px))
    if cache is not None and key in cache:
        return cache[key]
    sides = _compute_mask_sides(mask_strand, canvas, layer_order, blur_px, lifted_pairs,
                                {} if cache is None else cache)
    if cache is not None:
        cache[key] = sides
    return sides


def _compute_mask_sides(mask_strand, canvas, layer_order, blur_px, lifted_pairs, cache):
    first = getattr(mask_strand, 'first_selected_strand', None)
    second = getattr(mask_strand, 'second_selected_strand', None)
    if (first is None or second is None or getattr(mask_strand, 'is_hidden', False)
            or first.layer_name not in layer_order or second.layer_name not in layer_order):
        return None
    mask_path = _piece_of(mask_strand, cache)
    if mask_path.isEmpty():
        return None
    zone = _zone_of(mask_strand, blur_px, cache)
    zone_rect = zone.boundingRect()
    first_index = layer_order.index(first.layer_name)
    second_index = layer_order.index(second.layer_name)
    first_geometry = build_rendered_geometry(first)
    second_geometry = build_rendered_geometry(second)
    upper = {first.layer_name}
    lower = {second.layer_name}
    between = set()
    for other in canvas.strands:
        name = getattr(other, 'layer_name', None)
        if (other is first or other is second or name not in layer_order
                or hasattr(other, 'get_mask_path') or getattr(other, 'is_hidden', False)):
            continue
        index = layer_order.index(name)
        if (index <= first_index and index >= second_index) or not _may_touch(other, zone_rect, cache):
            continue
        geometry = build_rendered_geometry(other)
        over_first = (index > first_index and (first.layer_name, name) not in lifted_pairs
                      and _overlap_within(geometry, first_geometry, zone))
        under_second = (index < second_index and (name, second.layer_name) not in lifted_pairs
                        and _overlap_within(geometry, second_geometry, zone))
        if over_first and under_second:
            # Above F and below S, crossing both: moving it to either side
            # would flip its crossing with the other one, and the mask swaps
            # F and S only. It keeps its place in the layer order; where it
            # runs under the mask, the mask's piece covers it like any layer
            # below the mask.
            between.add(name)
        elif over_first:
            upper.add(name)
        elif under_second:
            lower.add(name)
    return {'zone': zone, 'zone_rect': zone_rect, 'upper': upper, 'lower': lower, 'between': between,
            'first': first.layer_name, 'second': second.layer_name, 'whole': _whole_mask(mask_strand)}


def _whole_mask(mask_strand):
    """Whether the mask lifts its first strand over the whole of its overlap
    with the second strand (no part erased), so that the first strand lies
    above the second strand everywhere."""
    return not getattr(mask_strand, 'deletion_rectangles', None)


def _frame_masks_map(canvas, layer_order, cache):
    """{layer name: {'masked_strand', 'components'}} for the canvas's masks."""
    masks_map = cache.get('masks_map')
    if masks_map is not None:
        return masks_map
    masks_map = {}
    for item in canvas.strands:
        if item.__class__.__name__ != 'MaskedStrand':
            continue
        first = getattr(item, 'first_selected_strand', None)
        second = getattr(item, 'second_selected_strand', None)
        first_layer = getattr(first, 'layer_name', None)
        second_layer = getattr(second, 'layer_name', None)
        if first_layer and second_layer:
            masks_map[getattr(item, 'layer_name', None) or '%s_%s' % (first_layer, second_layer)] = {
                'masked_strand': item, 'components': [first_layer, second_layer]}
    cache['masks_map'] = masks_map
    return masks_map


def _lifted_pairs(masked_strands_map):
    """(first, second) layer names of every visible mask."""
    return frozenset(tuple(info['components']) for info in masked_strands_map.values()
                     if not getattr(info['masked_strand'], 'is_hidden', False))


def _masks_near(strand, masked_strands_map, canvas, layer_order, blur_px, cache=None):
    """_mask_sides() of every visible mask whose zone *strand* can reach."""
    reach = QRectF(strand.boundingRect())
    reach.adjust(-blur_px, -blur_px, blur_px, blur_px)
    near = []
    lifted_pairs = _lifted_pairs(masked_strands_map)
    for masked_info in masked_strands_map.values():
        mask_strand = masked_info['masked_strand']
        if getattr(mask_strand, 'is_hidden', False):
            continue
        sides = _mask_sides(mask_strand, canvas, layer_order, blur_px, lifted_pairs, cache)
        if sides is not None and sides['zone_rect'].intersects(reach):
            near.append(sides)
    return near


def _lifted_near_masks(strand, near_masks):
    """Where masks put strands above *strand*, as [(area, layer names)];
    an area of None means everywhere.

    When *strand* is on a mask's lower side (see _mask_sides), its blurred
    shadow edge must not land on the upper side near the mask, although plain
    layer order would let it. For the mask's own second strand, the first
    strand is above it everywhere when the mask covers their whole overlap.
    """
    lifted = []
    for sides in near_masks:
        if strand.layer_name not in sides['lower']:
            continue
        upper = set(sides['upper'])
        if strand.layer_name == sides['second'] and sides['whole']:
            lifted.append((None, {sides['first']}))
            upper.discard(sides['first'])
        if upper:
            lifted.append((sides['zone'], upper))
    return lifted


def _sunk_near_masks(receiver_layer, near_masks):
    """Where masks put strands below the receiver, as [(area, layer names)];
    an area of None means everywhere.

    When the receiver is on a mask's upper side (see _mask_sides), the
    lower-side strands lie below it near the mask, so they are not between
    it and a caster there, although plain layer order may put them there.
    """
    sunk = []
    for sides in near_masks:
        if receiver_layer not in sides['upper']:
            continue
        lower = set(sides['lower'])
        if receiver_layer == sides['first'] and sides['whole']:
            sunk.append((None, {sides['second']}))
            lower.discard(sides['second'])
        if lower:
            sunk.append((sides['zone'], lower))
    return sunk


def _restacked_above(upper_layer, lower_layer, near_masks):
    """Whether a mask near by puts *upper_layer* above *lower_layer*."""
    return any(upper_layer in sides['upper'] and lower_layer in sides['lower'] for sides in near_masks)


def _raised_near_masks(receiver_layer, caster_layer, near_masks, layer_order, canvas):
    """Strands masks put between the receiver and the caster from below, as
    [(area, geometry)]; an area of None means everywhere.

    When the receiver is on a mask's lower side and the caster is not, the
    upper-side strands below the receiver in the layer order lie above it near
    the mask, so they are between it and the caster there, as at a genuine
    crossing. The mask's first strand lies above its second strand
    everywhere when the mask covers their whole overlap.
    """
    raised = []
    if not near_masks or receiver_layer not in layer_order or caster_layer not in layer_order:
        return raised
    receiver_index = layer_order.index(receiver_layer)
    caster_index = layer_order.index(caster_layer)
    for sides in near_masks:
        if receiver_layer not in sides['lower'] or caster_layer in sides['lower']:
            continue
        # In layer order: set order changes between runs, and the order of
        # the cuts changes the outline the soft edge follows.
        for name in sorted(sides['upper'], key=layer_order.index):
            index = layer_order.index(name)
            # Below the receiver in the layer order, but still below the caster
            # (which a mask may have lifted over the receiver).
            if (name == caster_layer or index >= receiver_index or index >= caster_index
                    or _restacked_above(name, caster_layer, near_masks)):
                continue
            everywhere = sides['whole'] and receiver_layer == sides['second'] and name == sides['first']
            raised.append((None if everywhere else sides['zone'],
                           build_rendered_geometry(_find_canvas_strand_by_layer_name(canvas, name))))
    return raised


def _lowered_near_masks(strand, near_masks, layer_order):
    """Where masks put strands below *strand*, as [(upper layer names,
    [(layer name, layer index, geometry, area)] of the lower-side strands
    above it)]; an area of None means everywhere.

    When *strand* is on a mask's upper side, the lower-side strands lie
    between it and whatever it shades below them near the mask, as at a
    genuine crossing, although plain layer order puts them above it. The
    mask's own second strand lies below its first strand everywhere when the
    mask covers their whole overlap.
    """
    lowered = []
    if not near_masks or strand.layer_name not in layer_order:
        return lowered
    this_index = layer_order.index(strand.layer_name)
    for sides in near_masks:
        if strand.layer_name not in sides['upper']:
            continue
        below = []
        for name in sorted(sides['lower'], key=layer_order.index):
            if layer_order.index(name) <= this_index:
                continue
            everywhere = sides['whole'] and strand.layer_name == sides['first'] and name == sides['second']
            below.append((name, layer_order.index(name),
                          build_rendered_geometry(_find_canvas_strand_by_layer_name(strand.canvas, name)),
                          None if everywhere else sides['zone']))
        if below:
            lowered.append((sides['upper'], below))
    return lowered


def _mask_lift_zone(masked_strands_map, first_layer, second_layer, blur_px, cache=None):
    """(zone, mask) when a visible mask lifts *first_layer* over
    *second_layer*: where the first strand's shadow on the second strand
    belongs, the mask's footprint grown by the blur radius, or None for
    everywhere (see _whole_mask). Else None."""
    cache = {} if cache is None else cache
    by_pair = cache.get(('masks_by_pair', id(masked_strands_map)))
    if by_pair is None:
        by_pair = {}
        for masked_info in masked_strands_map.values():
            if not getattr(masked_info['masked_strand'], 'is_hidden', False):
                by_pair.setdefault(tuple(masked_info['components']), masked_info['masked_strand'])
        cache[('masks_by_pair', id(masked_strands_map))] = by_pair
    mask_strand = by_pair.get((first_layer, second_layer))
    if mask_strand is None or _piece_of(mask_strand, cache).isEmpty():
        return None
    return (None if _whole_mask(mask_strand) else _zone_of(mask_strand, blur_px, cache)), mask_strand


def _subtract_intermediates(region, canvas, intermediate_layers, exemptions, cache=None):
    """Remove the strands between caster and receiver from a shadow area.

    Returns (outline, fill_area). *exemptions* are [(area, layer names)] of
    strands that lie between the two in the layer order but not near a mask
    (area None: nowhere): above the caster (see _lifted_near_masks) or below
    the receiver (see _sunk_near_masks). There they are not cut out of the
    outline: at a genuine crossing the soft edge is stroked along an area that
    runs on past them. They are still kept out of the filled area. With no
    mask involved the two paths are the same and match the plain subtraction
    exactly (fill_area is then None).
    """
    exempt = {}
    if exemptions:
        between = set(intermediate_layers)
        for zone, names in exemptions:
            for name in names & between:
                exempt.setdefault(name, []).append(zone)
    if not exempt:
        region, _ = _subtract_named_layer_paths(region, canvas, intermediate_layers)
        return region, None

    fill_cover = QPainterPath()
    region_rect = region.boundingRect()
    for layer_name in intermediate_layers:
        layer_strand = _find_canvas_strand_by_layer_name(canvas, layer_name)
        if (layer_strand is None or getattr(layer_strand, 'is_hidden', False)
                or not _may_touch(layer_strand, region_rect, cache)):
            continue
        if hasattr(layer_strand, 'get_mask_path'):
            geometry = get_proper_masked_strand_path(layer_strand)
        else:
            geometry = build_rendered_geometry(layer_strand)
        if geometry.isEmpty():
            continue
        for zone in exempt.get(layer_name, ()):
            if zone is None:
                geometry = QPainterPath()
                covered = QPainterPath(_drawn_footprint(layer_strand))
            else:
                geometry = QPainterPath(geometry).subtracted(zone)
                covered = QPainterPath(_drawn_footprint(layer_strand)).intersected(zone)
            fill_cover = covered if fill_cover.isEmpty() else fill_cover.united(covered)
            if geometry.isEmpty():
                break
        if not geometry.isEmpty():
            region = _subtracted(region, geometry)
    fill_area = QPainterPath(region)
    if not fill_cover.isEmpty():
        fill_area = QPainterPath(fill_area).subtracted(fill_cover)
    return region, fill_area


def _split_subpaths(path):
    """[(bounding rect, subpath)] of *path*, curves kept as they are."""
    pieces = []
    current = None
    index, count = 0, path.elementCount()
    while index < count:
        element = path.elementAt(index)
        if element.type == QPainterPath.MoveToElement:
            if current is not None:
                pieces.append(current)
            current = QPainterPath()
            current.moveTo(element.x, element.y)
            index += 1
        elif element.type == QPainterPath.LineToElement:
            current.lineTo(element.x, element.y)
            index += 1
        elif element.type == QPainterPath.CurveToElement and index + 2 < count:
            control, end = path.elementAt(index + 1), path.elementAt(index + 2)
            current.cubicTo(element.x, element.y, control.x, control.y, end.x, end.y)
            index += 3
        else:
            index += 1
    if current is not None:
        pieces.append(current)
    return [(piece.boundingRect(), piece) for piece in pieces]


def _subtraction_ok(path, cut, result, samples=12):
    """Whether *result* holds everything of *path* outside *cut*, checked on
    a grid of points over *path* (a point on the edge of *cut* may land
    either side, so a few may go)."""
    rect = path.boundingRect()
    if rect.isEmpty():
        return True
    kept = lost = 0
    for i in range(samples):
        for j in range(samples):
            point = QPointF(rect.left() + rect.width() * (i + 0.5) / samples,
                            rect.top() + rect.height() * (j + 0.5) / samples)
            if path.contains(point) and not cut.contains(point):
                if result.contains(point):
                    kept += 1
                else:
                    lost += 1
    return lost <= max(2, (kept + lost) // 20)


def _subtracted_checked(path, cut):
    """*path* minus *cut*, or *path* itself where Qt's boolean operation gets
    it wrong: subtracting a *cut* from a strand with an end circle can return
    an empty path, even where they barely touch (_subtraction_ok)."""
    result = QPainterPath(path).subtracted(cut)
    return result if _subtraction_ok(path, cut, result) else QPainterPath(path)


def _subtracted(path, cut):
    """*path* minus *cut*. Where *cut* meets *path* along a shared edge, as
    two strands do at a seamless joint, Qt's boolean operation can return
    nothing, or a path reaching past *path*: the cut moved by a hundredth of
    a pixel is subtracted then (and *path* kept whole if that fails too).
    Only an empty result is checked point by point, which is costly."""
    bounds = path.boundingRect().adjusted(-0.5, -0.5, 0.5, 0.5)
    result = QPainterPath(path).subtracted(cut)
    if result.isEmpty():
        if _subtraction_ok(path, cut, result):
            return result
    elif bounds.contains(result.boundingRect()):
        return result
    nudged = QTransform().translate(0.01, 0.01).map(cut)
    result = QPainterPath(path).subtracted(nudged)
    if (result.isEmpty() or bounds.contains(result.boundingRect())) and _subtraction_ok(path, nudged, result):
        return result
    return QPainterPath(path)


def _closed_outline(path):
    """*path* with every subpath closed, for stroking a shadow area's soft
    edge along it. Qt can return a boolean result open: intersected() with an
    axis-aligned rectangle clips each polygon without repeating its first
    point, and the stroke then misses that last side (a horizontal strand
    over one drawn from the bottom right up to the top left lost the soft
    edge below it). Filling closes subpaths anyway."""
    start = last = None
    is_open = False
    for index in range(path.elementCount()):
        element = path.elementAt(index)
        if element.type == QPainterPath.MoveToElement:
            if start is not None and (abs(last.x - start.x) > 1e-6 or abs(last.y - start.y) > 1e-6):
                is_open = True
                break
            start = element
        last = element
    if not is_open and (start is None or (abs(last.x - start.x) <= 1e-6 and abs(last.y - start.y) <= 1e-6)):
        return path
    closed = QPainterPath()
    closed.setFillRule(path.fillRule())
    for _bounds, piece in _split_subpaths(path):
        piece.closeSubpath()
        closed.addPath(piece)
    return closed


def _stroke_source_near(collected, rect, reach):
    """The parts of a collected soft-edge outline whose strokes can reach
    *rect*: each subpath is stroked on its own, so the rest cannot change a
    pixel there. A mask re-applies a whole strand's shadow for one small
    area, and stroking everything again would cost as much as the pass."""
    pieces = collected.get('_subpaths')
    if pieces is None:
        pieces = collected['_subpaths'] = _split_subpaths(collected['stroke_path'])
    area = QRectF(rect).adjusted(-reach, -reach, reach, reach)
    near = QPainterPath()
    near.setFillRule(collected['stroke_path'].fillRule())
    for bounds, piece in pieces:
        if bounds.intersects(area) or (bounds.isEmpty() and area.contains(bounds.topLeft())):
            near.addPath(piece)
    return near


def _paint_collected_shadow(painter, collected, clip, num_steps, max_blur_radius, fill_path=None,
                            and_clip=None):
    """Paint a shadow computed with draw_strand_shadow(collect_only=True):
    the fill, then the same faded edge, clipped to *clip* (and to *and_clip*
    too when given, a path or a list of paths: the painter intersects them,
    which is exact where a boolean operation on paths sharing edges is not)."""
    if and_clip is None:
        and_clip = []
    elif isinstance(and_clip, QPainterPath):
        and_clip = [and_clip]
    if clip.isEmpty() or any(extra.isEmpty() for extra in and_clip):
        return
    color = collected['color']
    stroke_source = _stroke_source_near(collected, clip.boundingRect(), max_blur_radius / 2.0 + 2.0)
    painter.save()
    try:
        painter.setClipPath(clip)
        for extra in and_clip:
            painter.setClipPath(extra, Qt.IntersectClip)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        if fill_path is not None and not fill_path.isEmpty():
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawPath(fill_path)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(Qt.NoBrush)
        base_alpha = color.alpha()
        for i in range(num_steps):
            progress = (float(num_steps - i) / num_steps)
            current_alpha = base_alpha * progress * (1.0 / num_steps) * 2.0
            current_width = max_blur_radius * (float(i + 1) / num_steps)
            pen_color = QColor(color.red(), color.green(), color.blue(), max(0, min(255, int(current_alpha))))
            pen = QPen(pen_color)
            pen.setWidthF(current_width)
            pen.setCapStyle(Qt.FlatCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.strokePath(stroke_source, pen)
    finally:
        painter.restore()


def _clip_off_lifted_strands(receiver_path, canvas, lifted_near_masks, layers_between, cache=None):
    """The receiver's clip for the blurred edge, minus the lifted strands
    drawn between the receiver and the caster (see _lifted_near_masks)."""
    clip = QPainterPath(receiver_path)
    if not lifted_near_masks or not layers_between:
        return clip
    keep_off = QPainterPath()
    clip_rect = clip.boundingRect()
    for zone, upper in lifted_near_masks:
        # In layer order, not set order: see _raised_near_masks.
        for name in [name for name in layers_between if name in upper]:
            lifted_strand = _find_canvas_strand_by_layer_name(canvas, name)
            if lifted_strand is None or not _may_touch(lifted_strand, clip_rect, cache):
                continue
            piece = QPainterPath(_drawn_footprint(lifted_strand))
            if zone is not None:
                piece = piece.intersected(zone)
            if not piece.isEmpty():
                keep_off = piece if keep_off.isEmpty() else keep_off.united(piece)
    if keep_off.isEmpty():
        return clip
    clip = QPainterPath(clip).subtracted(keep_off)
    # Boolean results come back odd-even; the other receivers are added to
    # the same clip afterwards and overlaps must not cancel out.
    clip.setFillRule(Qt.WindingFill)
    return clip


def _clip_off_hidden_rows(clip, canvas, caster_layer, layers_between, cache=None):
    """*clip* minus the strands between the receiver and the caster whose own
    shadow from the caster is hidden (in the Shadow Editor, or by
    auto_shadow.py). The faded edge of the caster's shadow on the receiver
    would otherwise land on them where they lie over the receiver: hiding a
    shadow hides all of the caster's shadow on that strand."""
    manager = getattr(canvas, 'layer_state_manager', None)
    if manager is None or not layers_between or clip.isEmpty():
        return clip
    clip_rect = clip.boundingRect()
    for name in layers_between:
        if manager.get_shadow_visibility(caster_layer, name):
            continue
        hidden_strand = _find_canvas_strand_by_layer_name(canvas, name)
        if (hidden_strand is None or getattr(hidden_strand, 'is_hidden', False)
                or not _may_touch(hidden_strand, clip_rect, cache)):
            continue
        footprint = (_piece_of(hidden_strand, cache if cache is not None else {})
                     if hasattr(hidden_strand, 'get_mask_path') else _drawn_footprint(hidden_strand))
        if footprint.isEmpty():
            continue
        clip = _subtracted_checked(clip, footprint)
        # As in _clip_off_lifted_strands: the other receivers are added to
        # the same clip afterwards.
        clip.setFillRule(Qt.WindingFill)
    return clip


def _pair_shadow(strand, other_strand, shadow_path, canvas, layer_order, masked_strands_map,
                 near_masks, lifted_near_masks, lowered_near_masks, max_blur_radius, cache, joints=()):
    """The shadow *strand* casts on *other_strand*, computed as
    draw_strand_shadow draws it, or None when it casts none there.

    *shadow_path* is where the caster's shadow starts and *joints* its joints
    hidden by a transparent circle (both from _caster_shadow_path); the other
    arguments are what draw_strand_shadow works out once per caster.
    Returns a dict:

    - ``outline``: the area whose outline the soft edge is stroked along;
    - ``fill``: the area filled, or None when it is the outline's area;
    - ``lift``: the mask that lifts the caster over the receiver, which paints
      this shadow (see draw_mask_lift_shadow), or None;
    - ``receiver_path``: the receiver's geometry;
    - ``clip``: where the soft edge may land on the receiver (None for a lift);
    - ``clip_blocker``: the layers the user subtracts from this shadow, which
      draw_strand_shadow also cuts out of the clip of the receivers before it.

    shadow_preview, the Shadow Editor's preview, uses the same function, so
    the preview shows what is drawn.
    """
    # Skip self or strands without layer names
    # Note: Arrow shadows should not cast on their own strand body
    if other_strand is strand:
        return None
    if not hasattr(other_strand, 'layer_name') or not other_strand.layer_name:
        return None
    # Skip hidden strands - hidden strands should not receive shadows
    # EXCEPT if they have a visible full arrow that should receive shadows
    if getattr(other_strand, 'is_hidden', False) and not getattr(other_strand, 'full_arrow_visible', False):
        return None
    this_layer = strand.layer_name
    other_layer = other_strand.layer_name
    if this_layer not in layer_order or other_layer not in layer_order:
        return None

    # Normal layer order rules apply
    self_index = layer_order.index(this_layer)
    other_index = layer_order.index(other_layer)
    should_be_above = self_index > other_index
    # Where a visible mask lifts this strand over the other one, cast onto it
    # near the mask even though it is higher in the layer order. A whole mask
    # whose first strand is already above its second changes nothing, and the
    # layer order casts; with erased parts it still bounds where that is so
    # (another mask may lift the second strand over the first elsewhere).
    mask_lift = _mask_lift_zone(masked_strands_map, this_layer, other_layer, max_blur_radius, cache)
    lift = mask_lift
    if mask_lift is not None and should_be_above and mask_lift[0] is None:
        lift = None

    # Only calculate shadow if this strand should be above the other
    if not should_be_above and lift is None:
        return None

    # Both strands are components of the same visible mask: the mask owns
    # their crossing.
    part_of_same_visible_mask = False
    for masked_info in masked_strands_map.values():
        components = masked_info['components']
        if this_layer in components and other_layer in components:
            if not getattr(masked_info['masked_strand'], 'is_hidden', False):
                part_of_same_visible_mask = True
                break
    if part_of_same_visible_mask and mask_lift is None:
        return None

    # Quick reject using bounding rectangles
    try:
        strand_rect = strand.boundingRect()
        other_strand_rect = other_strand.boundingRect()
        # --- EXTEND bounding rectangle to include circle geometry of the underlying strand ---
        if hasattr(other_strand, 'has_circles') and any(other_strand.has_circles):
            try:
                base_circle_radius_br = other_strand.width + other_strand.stroke_width * 2
                for oc_idx_br, oc_flag_br in enumerate(other_strand.has_circles):
                    if not oc_flag_br:
                        continue
                    if hasattr(other_strand, 'circle_stroke_color'):
                        oc_color_br = other_strand.circle_stroke_color
                        if oc_color_br and oc_color_br.alpha() == 0:
                            continue  # Transparent circle – no geometry
                    oc_center_br = other_strand.start if oc_idx_br == 0 else other_strand.end
                    # Create a QRectF for this circle and unite with other_strand_rect
                    circle_rect_br = QRectF(
                        oc_center_br.x() - (base_circle_radius_br / 2) - 1,
                        oc_center_br.y() - (base_circle_radius_br / 2) - 1,
                        base_circle_radius_br + 2,
                        base_circle_radius_br + 2,
                    )
                    other_strand_rect = other_strand_rect.united(circle_rect_br)
            except Exception:
                pass
        # Inflate the rectangles by half the rendered stroke width plus max blur so that
        # the quick bounding-box test does not miss near-tangent crossings.
        try:
            inflate_self = (strand.width + strand.stroke_width * 2 + max_blur_radius) / 2.0
            inflate_other = (other_strand.width + other_strand.stroke_width * 2 + max_blur_radius) / 2.0

            strand_rect.adjust(-inflate_self, -inflate_self, inflate_self, inflate_self)
            other_strand_rect.adjust(-inflate_other, -inflate_other, inflate_other, inflate_other)
        except Exception:
            # Should never happen, but be robust in case a strand misses width attributes.
            pass
        if not strand_rect.intersects(other_strand_rect):
            return None
    except Exception:
        pass

    try:
        # Build the full rendered geometry (body + visible circles) of the
        # underlying strand in a single call.  This guarantees that any
        # end-circles are already part of the path we test against, avoiding
        # later ad-hoc unions.
        other_stroke_path = build_rendered_geometry(other_strand)
        # A lowered cap only takes the shadows of the strands that cross the
        # joint (see lowered_start_cap); elsewhere the attached strand covers it.
        lowered = lowered_caps_of(other_strand)
        if lowered and any(strand not in info['crossers'] for _child, info in lowered):
            other_stroke_path = _build_rendered_geometry(other_strand)
            for _child, info in lowered:
                if strand in info['crossers']:
                    other_stroke_path = QPainterPath(other_stroke_path).united(info['cap'])

        # If the other strand is a MaskedStrand, use its actual mask path
        # instead of just the stroke path to get the correct intersection area
        if hasattr(other_strand, 'get_mask_path'):
            try:
                other_stroke_path = get_proper_masked_strand_path(other_strand)
            except Exception:
                pass

        # build_rendered_geometry() already includes the receiving
        # strand's visible end-cap geometry, including elliptical
        # match-connected caps. Re-adding circular caps here makes the
        # clip path larger than the drawn strand and lets shadows appear
        # over empty canvas at width-changed junctions.

        # Calculate intersection
        intersection = QPainterPath(shadow_path)
        # A strand that continues the caster at a hidden joint gets no halo
        # around the joint (see _caster_shadow_path).
        for centre, disc in joints:
            if _ends_at(other_strand, centre):
                intersection = QPainterPath(intersection).subtracted(disc)
        # Only add circle shadows if not using arrow shadow
        if not (getattr(strand, 'full_arrow_visible', False) and getattr(strand, 'arrow_casts_shadow', False)):
            circle_shadow_path = build_shadow_circle_geometry(strand, max_blur_radius+2)
            intersection.addPath(circle_shadow_path)
        intersection = QPainterPath(intersection).intersected(other_stroke_path)
        if lift is not None and lift[0] is not None and not lift[0].contains(intersection):
            # Only cut when needed: every boolean operation merges the
            # region's overlapping pieces, and the soft edge follows them.
            intersection = QPainterPath(intersection).intersected(lift[0])

        # Skip shadow if there's no actual intersection between the paths
        if intersection.isEmpty():
            return None

        # --- CHECK SHADOW OVERRIDE ---
        # Check if there's a shadow override for this specific shadow relationship
        shadow_override = None
        if lift is not None:
            # Keyed like the mask's own shading row in the shadow editor.
            if hasattr(lift[1], '_intersection_shadow_visible') and not lift[1]._intersection_shadow_visible():
                return None
        elif hasattr(canvas, 'layer_state_manager'):
            shadow_override = canvas.layer_state_manager.get_shadow_override(this_layer, other_layer)
            if not canvas.layer_state_manager.get_shadow_visibility(this_layer, other_layer):
                return None

        # Check if we should allow complete shadow (skip mask blocking)
        allow_full_shadow = shadow_override and shadow_override.get('allow_full_shadow', False)

        # --- LAYER PATH SUBTRACTION ---
        # Check if there are any layers whose paths should be subtracted from this shadow
        clip_blocker_path = QPainterPath()
        if hasattr(canvas, 'layer_state_manager'):
            subtracted_layers = canvas.layer_state_manager.get_subtracted_layers(this_layer, other_layer)
            intersection, clip_blocker_path = _subtract_named_layer_paths(
                intersection,
                canvas,
                subtracted_layers,
            )

        # Masks no longer cut a "blocker" (the mask grown by half the blur)
        # out of shadows cast from below them: anything under an opaque mask
        # is painted over by the mask anyway, and the grown ring notched the
        # shadows of strands the mask does not cover. The blurred edges that
        # the blocker used to hide are kept off the lifted strands by the
        # clip below instead.
        current_intersection_shadow = QPainterPath(intersection)

        # --- SUBTRACT INTERMEDIATE STRANDS ---
        # Any strands between the casting and receiving strands should block the shadow
        current_fill_shadow = None
        if not allow_full_shadow and not current_intersection_shadow.isEmpty():
            # Where a mask lifts this strand over the other one, nothing lies
            # between them: the strands drawn in between are below the other
            # one there, or above this one (and put back by the mask).
            intermediate_layers = [] if lift is not None else \
                _get_intermediate_layer_names(layer_order, this_layer, other_layer)
            current_intersection_shadow, current_fill_shadow = _subtract_intermediates(
                current_intersection_shadow,
                canvas,
                intermediate_layers,
                lifted_near_masks + _sunk_near_masks(other_layer, near_masks),
                cache,
            )
        # --- END INTERMEDIATE STRAND SUBTRACTION ---
        if not current_intersection_shadow.isEmpty():
            # Near a mask that puts this strand above others, those others
            # lie between it and the strands below them, as at a genuine crossing.
            cuts = []
            for upper, below in lowered_near_masks:
                if other_layer in upper:
                    continue
                for below_name, below_index, below_geometry, area in below:
                    # Unless another mask puts the receiver above it.
                    if other_index < below_index and not _restacked_above(
                            other_layer, below_name, near_masks):
                        cuts.append((area, below_geometry))
            # Likewise strands a mask lifts above the receiver.
            cuts += _raised_near_masks(other_layer, this_layer, near_masks, layer_order, canvas)
            for area, geometry in cuts:
                cut = QPainterPath(geometry)
                if area is not None:
                    cut = cut.intersected(area)
                current_intersection_shadow = QPainterPath(current_intersection_shadow).subtracted(cut)
                if current_fill_shadow is not None:
                    current_fill_shadow = QPainterPath(current_fill_shadow).subtracted(cut)

        # Apply side line exclusion for both casting and receiving strands
        if not current_intersection_shadow.isEmpty():
            try:
                # Exclusion for the casting strand (this strand) - auto-calculate multiplier
                casting_exclusion = get_side_line_exclusion_path(strand)
                if not casting_exclusion.isEmpty():
                    current_intersection_shadow = QPainterPath(current_intersection_shadow).subtracted(casting_exclusion)

                # Exclusion for the receiving strand (other strand) - auto-calculate multiplier
                receiving_exclusion = get_side_line_exclusion_path(other_strand)
                if not receiving_exclusion.isEmpty():
                    current_intersection_shadow = QPainterPath(current_intersection_shadow).subtracted(receiving_exclusion)
            except Exception:
                pass

        current_intersection_shadow = _closed_outline(current_intersection_shadow)
        if current_intersection_shadow.isEmpty():
            return None
        # The receiver's area, so the faded edge only lands where a strand is.
        receiver_clip = None
        if lift is None:
            layers_between = _get_intermediate_layer_names(layer_order, this_layer, other_layer)
            receiver_clip = _clip_off_lifted_strands(
                other_stroke_path, canvas, lifted_near_masks, layers_between, cache)
            receiver_clip = _clip_off_hidden_rows(receiver_clip, canvas, this_layer, layers_between, cache)
        return {'outline': current_intersection_shadow, 'fill': current_fill_shadow,
                'lift': lift[1] if lift is not None else None, 'receiver_path': other_stroke_path,
                'clip': receiver_clip, 'clip_blocker': clip_blocker_path}
    except Exception:
        return None


def _transparent_ends(strand):
    """[(end index, centre, disc)] of *strand*'s ends whose circle is switched
    on but fully transparent, with the area around the end that its shadow
    keeps off (see _caster_shadow_path): a disc whose radius is two thirds of
    the strand's full width."""
    ends = []
    try:
        if not (hasattr(strand, "has_circles") and any(strand.has_circles)):
            return ends
        radius = (strand.width + strand.stroke_width * 2) / 1.5
        for idx, enabled in enumerate(strand.has_circles):
            if not enabled:
                continue
            color = strand.start_circle_stroke_color if idx == 0 else strand.end_circle_stroke_color
            if color and color.alpha() == 0:
                centre = QPointF(strand.start if idx == 0 else strand.end)
                disc = QPainterPath()
                disc.addEllipse(centre, radius, radius)
                ends.append((idx, centre, disc))
    except Exception:
        pass
    return ends


def _seam_slab(strand, idx, depth=2.0):
    """A thin band across *strand*'s flat end *idx*, reaching *depth* px to
    either side of it and a little past both edges. At a seamless joint the
    neighbour's flat end is the very same segment, and Qt's boolean
    operations go wrong on shared edges: subtracting the neighbour from a
    shadow that ends there returned nothing, or a path larger than the
    shadow. With this band cut out, the shadow ends *depth* px short of the
    joint, which its soft edge covers. Oriented along the path the body is
    stroked from, as the stroker orients the flat end."""
    try:
        path = strand.get_shadow_path() if hasattr(strand, 'get_shadow_path') else strand.get_path()
        length = path.length()
        if length <= 0:
            return QPainterPath()
        step = min(1.0, length / 2.0)
        if idx == 0:
            end, inner = path.pointAtPercent(0.0), path.pointAtPercent(path.percentAtLength(step))
        else:
            end, inner = path.pointAtPercent(1.0), path.pointAtPercent(path.percentAtLength(length - step))
        along = math.atan2(inner.y() - end.y(), inner.x() - end.x())
        half_width = (strand.width + strand.stroke_width * 2) / 2.0 + 2.0
        slab = QPainterPath()
        slab.addRect(QRectF(-depth, -half_width, depth * 2, half_width * 2))
        return QTransform().translate(end.x(), end.y()).rotate(math.degrees(along)).map(slab)
    except Exception:
        return QPainterPath()


def _ends_at(item, point):
    """Whether *item* is a visible strand with an end on *point*. A mask ends
    where its first strand does, but continues no strand there."""
    if hasattr(item, 'get_mask_path') or getattr(item, 'is_hidden', False):
        return False
    for end in (getattr(item, 'start', None), getattr(item, 'end', None)):
        if end is not None and abs(end.x() - point.x()) < 0.5 and abs(end.y() - point.y()) < 0.5:
            return True
    return False


def _caster_shadow_path(strand):
    """(path, shadow_path, joints) of a caster: its outline, the area its
    shadow starts from (the arrow when the arrow casts the shadow), and
    [(centre, disc)] of its joints hidden by a transparent circle.

    A transparent circle asks for no shadow halo around its end, which the
    flat end of the body would otherwise cast. At a free end the disc around
    it (_transparent_ends) is cut out of the whole shadow. At a joint it is
    cut only out of the shadow on the strands that end there and continue
    the caster (_pair_shadow): any other strand passing the joint gets the
    whole shadow, as anywhere else along the caster, less a thin band at the
    joint itself (_seam_slab). The disc reaches past the caster's edge by a
    sixth of its full width; cut out of every shadow, it cut short, with a
    round end, the soft edge on each strand crossing near a joint (a strand
    three grid squares wide lost 14 px of the 15 px edge the default blur
    gives)."""
    # Check if arrow shading is enabled and use arrow path instead
    if getattr(strand, 'full_arrow_visible', False) and getattr(strand, 'arrow_casts_shadow', False):
        # Use the arrow path for shadow casting
        arrow_shadow_path = strand.get_arrow_shadow_path() if hasattr(strand, 'get_arrow_shadow_path') else QPainterPath()
        if not arrow_shadow_path.isEmpty():
            path = arrow_shadow_path
            shadow_path = arrow_shadow_path  # Use arrow path directly as shadow path
        else:
            path = get_proper_masked_strand_path(strand)
            shadow_path = build_shadow_geometry(strand, 0, include_circles=False)
    else:
        path = get_proper_masked_strand_path(strand)
        shadow_path = build_shadow_geometry(strand, 0, include_circles=False)  # Exclude circles, we'll handle them separately

    joints = []
    others = getattr(getattr(strand, 'canvas', None), 'strands', None) or []
    for idx, centre, disc in _transparent_ends(strand):
        if any(item is not strand and _ends_at(item, centre) for item in others):
            joints.append((centre, disc))
            shadow_path = QPainterPath(shadow_path).subtracted(_seam_slab(strand, idx))
        else:
            shadow_path = QPainterPath(shadow_path).subtracted(disc)
    return path, shadow_path, joints


def draw_strand_shadow(painter, strand, shadow_color=None, num_steps=3, max_blur_radius=None,
                       collect_only=False):
    """
    Draw shadow for a strand that overlaps with other strands.
    This function should be called before drawing the strand itself.

    Args:
        painter: The QPainter to draw with
        strand: The strand to draw shadow for
        shadow_color: Custom shadow color or None to use strand's shadow_color
        collect_only: Paint nothing and return the computed paths instead
            (see draw_mask_lift_shadow): a dict with the stroked outline
            ``stroke_path``, the shadow on mask partners ``lift_path``, the
            other filled areas ``fill_path`` and the ``color``, or None when
            there is no shadow.
    """
    # Check if the strand is hidden - hidden strands should not cast shadows
    if hasattr(strand, 'is_hidden') and strand.is_hidden:
        # Exception: arrow can cast shadow even when strand is hidden
        if not (getattr(strand, 'full_arrow_visible', False) and getattr(strand, 'arrow_casts_shadow', False)):
            pass
            return

    # Per-layer "Hide Shadow" option - the strand casts no shadow at all
    if getattr(strand, 'hide_shadow', False):
        return

    # A mask draws a piece of its first strand over its second strand. All the
    # shadows around that piece are the first strand's own (its pass computes
    # them as at a genuine crossing, and the mask re-applies the part on the
    # second strand, see draw_mask_lift_shadow). As a caster of its own the
    # mask only contributed the slivers where its fill overhangs the second
    # strand's outline, whose blurred edges landed on whatever was drawn in
    # between (a strand's rounded end, a third strand crossing nearby).
    if hasattr(strand, 'get_mask_path'):
        return
    
    # Auto-calculate blur radius based on strand thickness if not provided
    if max_blur_radius is None:
        strand_width = getattr(strand, 'width', 10)
        # Use consistent shadow extension regardless of strand thickness
        max_blur_radius = 30.0  # Fixed shadow extension for all strand thicknesses
        pass
    
    if not hasattr(strand, 'canvas') or not strand.canvas:
        return
        
    # Check if shadowing is disabled in the canvas
    if hasattr(strand.canvas, 'shadow_enabled') and not strand.canvas.shadow_enabled:
        return
    
    # Use strand's shadow color with consistent opacity
    if shadow_color:
        # If custom color provided, use it
        color_to_use = QColor(shadow_color)
    elif hasattr(strand, 'shadow_color') and strand.shadow_color:
        # If strand has a shadow color, create a copy
        color_to_use = QColor(strand.shadow_color)
    else:
        # Default shadow color with moderate opacity
        color_to_use = QColor(0, 0, 0, 150)  # ~59% opacity
    
    # Remove the cap on opacity to respect user's chosen alpha value
    # if color_to_use.alpha() > 150:
    #     color_to_use.setAlpha(150)

    # A mask re-applies this strand's shadow paths later in the same paint (see
    # draw_mask_lift_shadow); compute them only once.
    cache = _frame_cache(painter)
    collected_key = ('collected', id(strand), num_steps, float(max_blur_radius), color_to_use.rgba())
    if collect_only and collected_key in cache:
        return cache[collected_key]
    
    # Reduced high-frequency logging for performance during moves
    # logging.info(f"Drawing shadow for strand {strand.layer_name} with color {color_to_use.name()} alpha={color_to_use.alpha()}")
    
    # Obtain the base path (without circles) for operations that still expect
    # the raw strand outline, then build a geometry path that already contains the strand body **and** any
    # visible end-circles.  This single path will be used for all subsequent
    # shadow computations, eliminating the need for special-casing circles.

    path, shadow_path, joints = _caster_shadow_path(strand)

    # ------------------------------------------------------------------
    # Manual circle-exclusion logic removed – visible circles are already
    # merged into `shadow_path` by `build_rendered_geometry`, while hidden or
    # deliberately transparent circles are *not* included in that helper.
    # Keeping extra subtraction here would create gaps and duplicated shadow
    # edges.  All related logging and special-case handling was therefore
    # deleted for clarity and correctness.
    # ------------------------------------------------------------------

    # Create a list to hold individual shadow intersections
    # Instead of combining them with united() which can cause issues with multiple overlaps,
    # we'll keep them separate and handle them properly
    individual_shadow_paths = []
    # The outlines the soft edge is stroked along. Same as the filled areas,
    # except near a mask where lifted strands must not cut them (see
    # _subtract_intermediates).
    individual_stroke_paths = []
    # The receiver of each of those outlines (see draw_mask_restored_shadows).
    stroke_receivers = []
    # Shadow on the second strand of a mask this strand is the first strand of,
    # near the mask: stroked together with everything else (so the soft edges
    # meet exactly as at a genuine crossing), but painted by the mask on top of
    # the second strand instead of here, underneath it.
    lift_shadow_paths = []
    combined_shadow_path = QPainterPath()
    has_shadow_content = False
    all_shadow_paths = []
    clip_path = QPainterPath()  # Will collect the union of underlying strand areas to clip the faded shadow
    plain_clip = True  # clip_path is only strand outlines added together (see below)

    # Try to get layer ordering from layer state manager
    canvas = strand.canvas
    if hasattr(canvas, 'layer_state_manager') and canvas.layer_state_manager:
        manager = canvas.layer_state_manager
        layer_order = manager.getOrder()
        connections = manager.getConnections()  # Get the connections map
        
        # Get this strand's layer name
        this_layer = strand.layer_name
        
        # Log layer order for debugging
        # logging.info(f"Current layer order: {layer_order}")
        # logging.info(f"Current strand being processed: {this_layer}")
        # logging.info(f"Current connections: {connections}")
        
        # Track masked strands and their components for special handling
        masked_strands_map = _frame_masks_map(canvas, layer_order, cache)
        near_masks = _masks_near(strand, masked_strands_map, canvas, layer_order, max_blur_radius, cache) \
            if this_layer in layer_order else []
        lifted_near_masks = _lifted_near_masks(strand, near_masks)
        lowered_near_masks = _lowered_near_masks(strand, near_masks, layer_order)

        # logging.info(f"Checking shadow for : {strand.layer_name}")
        # Check against all other strands
        for other_strand in canvas.strands:
            pair = _pair_shadow(strand, other_strand, shadow_path, canvas, layer_order, masked_strands_map,
                                near_masks, lifted_near_masks, lowered_near_masks, max_blur_radius, cache,
                                joints)
            if pair is None:
                continue
            if pair['lift'] is not None:
                lift_shadow_paths.append(pair['outline'])
                continue
            try:
                # Expand the clipping path by the receiver's area, so the faded
                # shadow only renders where an underlying strand exists.
                receiver_clip, other_stroke_path = pair['clip'], pair['receiver_path']
                # A receiver with a lowered cap is a boolean union (see
                # build_rendered_geometry), not a plain outline.
                plain_receiver = ((receiver_clip is other_stroke_path or receiver_clip == other_stroke_path)
                                  and not lowered_caps_of(other_strand))
                if clip_path.isEmpty():
                    clip_path = QPainterPath(receiver_clip)
                    plain_clip = plain_receiver
                elif plain_clip and plain_receiver:
                    clip_path.addPath(QPainterPath(receiver_clip))
                else:
                    # A boolean result is odd-even, or its winding may run the
                    # other way round: adding a path to it, or it to the clip,
                    # would cancel their overlap. Unite instead.
                    clip_path = QPainterPath(clip_path).united(receiver_clip)
                    plain_clip = False

                if not pair['clip_blocker'].isEmpty():
                    try:
                        clip_path = QPainterPath(clip_path).subtracted(pair['clip_blocker'])
                        plain_clip = False
                    except Exception:
                        pass

                # Add this intersection to the list of individual shadows
                # This preserves each shadow intersection separately to avoid issues with united()
                individual_shadow_paths.append(pair['outline'] if pair['fill'] is None else pair['fill'])
                individual_stroke_paths.append(pair['outline'])
                stroke_receivers.append(other_strand.layer_name)
                has_shadow_content = True
            except Exception:
                pass
        
        # Combine individual shadow paths properly
        if has_shadow_content and individual_shadow_paths:
            # Create combined path by carefully merging individual paths
            # This approach handles multiple overlapping regions better than repeated united() calls
            combined_shadow_path = QPainterPath()
            
            # Method 1: Add all paths as subpaths to preserve overlapping regions
            for shadow_path in individual_shadow_paths:
                if not shadow_path.isEmpty():
                    # Add each path as a subpath to preserve its geometry
                    combined_shadow_path.addPath(shadow_path)
            
            # Set fill rule to handle overlapping regions correctly
            combined_shadow_path.setFillRule(Qt.WindingFill)
            
            # Draw shadow (uncommented to actually render the solid shadow core)
            if not collect_only:
                painter.save()
                try:
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(color_to_use))

                    # IMPORTANT: Use SourceOver composition mode to prevent shadow darkening
                    painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                    # Uncommented to fix the missing shadow rendering
                    painter.drawPath(combined_shadow_path)
                finally:
                    painter.restore()
            
            # Initialize shadow_paths and all_shadow_paths
            combined_stroke_path = QPainterPath()
            for stroke_region in individual_stroke_paths:
                if not stroke_region.isEmpty():
                    combined_stroke_path.addPath(stroke_region)
            combined_stroke_path.setFillRule(Qt.WindingFill)
            all_shadow_paths = [combined_stroke_path]
            
            pass
    else:
        # If no layer manager available, draw simple shadow
        # This is a fallback method
        pass
        # Still use a unified approach even in fallback case
        if not shadow_path.isEmpty():
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color_to_use))
            #painter.drawPath(shadow_path)
            
            # Initialize shadow_paths and add shadow_path to all_shadow_paths
            all_shadow_paths = [shadow_path]
            clip_path = QPainterPath(shadow_path)  # In fallback, clip to the simple shadow path
    # ------------------------------------------------------------------
    # Legacy circle-shadow branch disabled – visible circles are now part
    # of the main `shadow_path` via `build_rendered_geometry`, so a
    # separate pass would double-render. Retain the variable so that later
    # logic still compiles but leave it empty so the subsequent blocks are
    # skipped naturally.
    # ------------------------------------------------------------------
    circle_shadow_paths = []  # List[Tuple[QPainterPath, QPointF]]

    # ----------------------------------------------------------
    # Prepare strand body stroke path once (needed for subtracting from circle shadows)
    # ----------------------------------------------------------
    strand_body_path = QPainterPath()
    try:
        body_stroker = QPainterPathStroker()
        body_stroker.setWidth(strand.width + strand.stroke_width * 2)
        body_stroker.setJoinStyle(Qt.RoundJoin)
        body_stroker.setCapStyle(Qt.FlatCap)
        strand_body_path = body_stroker.createStroke(path)
    except Exception as e:
        # logging.error(f"Error computing strand body path for {strand.layer_name}: {e}")
        pass

    # ----------------------------------------------------------
    # For each circle shadow path, calculate intersections with lower strands (layer ordering)
    # and append to all_shadow_paths just like the main body shadows.
    # ----------------------------------------------------------

    if circle_shadow_paths and hasattr(canvas, 'layer_state_manager') and canvas.layer_state_manager:
        layer_order = canvas.layer_state_manager.getOrder()

        this_layer = strand.layer_name

        for other_strand in canvas.strands:
            if other_strand is strand or not hasattr(other_strand, 'layer_name') or not other_strand.layer_name:
                continue
            
            # Skip hidden strands - hidden strands should not receive shadows on their circles
            # EXCEPT if they have a visible full arrow that should receive shadows
            if hasattr(other_strand, 'is_hidden') and other_strand.is_hidden:
                # Only skip if there's NO full arrow visible
                if not getattr(other_strand, 'full_arrow_visible', False):
                    pass
                    continue

            other_layer = other_strand.layer_name
            if other_layer not in layer_order:
                continue

            self_index = layer_order.index(this_layer) if this_layer in layer_order else -1
            other_index = layer_order.index(other_layer) if other_layer in layer_order else -1

            should_be_above = self_index > other_index
            if not should_be_above:
                continue

            # Bounding-box quick reject for performance – for each circle
            try:
                other_rect = other_strand.boundingRect() if hasattr(other_strand, 'boundingRect') else QRectF()
            except Exception:
                other_rect = QRectF()

            # Build other stroke path once per other_strand
            try:
                other_stroke_path = build_rendered_geometry(other_strand)

                if hasattr(other_strand, 'get_mask_path'):
                    try:
                        other_stroke_path = get_proper_masked_strand_path(other_strand)
                        pass
                    except Exception as ee:
                        # logging.error(f"Error getting mask path for {other_layer}: {ee}")
                        pass

                # build_rendered_geometry() already includes cap geometry. Keep this
                # legacy circle-shadow branch from adding stale circular receiver caps
                # if it is re-enabled later.
            except Exception as e:
                # logging.error(f"Could not create stroke path for other strand {other_layer}: {e}")
                pass
                continue

            for circle_path, center in circle_shadow_paths:
                # Improved quick bounding check: enlarge other_rect to include the rendered stroke,
                # its blur and the lower-strand's own end-circle geometry so that grazing contacts
                # are no longer missed.
                if not other_rect.isNull():
                    try:
                        # Inflate for stroke thickness + blur
                        inflate_other = (other_strand.width + other_strand.stroke_width * 2 + max_blur_radius) / 2.0
                        inflated_rect = QRectF(other_rect)
                        inflated_rect.adjust(-inflate_other, -inflate_other, inflate_other, inflate_other)

                        # Also merge the lower-strand's visible circle geometry (if any)
                        if hasattr(other_strand, 'has_circles') and any(other_strand.has_circles):
                            base_circle_radius_br = other_strand.width + other_strand.stroke_width * 2
                            for oc_idx_br, oc_flag_br in enumerate(other_strand.has_circles):
                                if not oc_flag_br:
                                    continue
                                if hasattr(other_strand, 'circle_stroke_color'):
                                    oc_color_br = other_strand.circle_stroke_color
                                    if oc_color_br and oc_color_br.alpha() == 0:
                                        continue  # transparent, ignore
                                oc_center_br = other_strand.start if oc_idx_br == 0 else other_strand.end
                                circle_rect_br = QRectF(
                                    oc_center_br.x() - base_circle_radius_br / 2,
                                    oc_center_br.y() - base_circle_radius_br / 2,
                                    base_circle_radius_br,
                                    base_circle_radius_br,
                                )
                                inflated_rect = inflated_rect.united(circle_rect_br)

                        # If the centre of the casting circle still lies outside the inflated area, skip.
                        if not inflated_rect.contains(center):
                            continue
                    except Exception as bc_err:
                        # logging.error(f"Error during improved circle bounding check between {this_layer} and {other_layer}: {bc_err}")
                        pass

                # Subtract body path only if some area survives – otherwise the shadow would vanish when the strand leaves the joint
                final_circle_path = QPainterPath(circle_path)
                if not strand_body_path.isEmpty():
                    candidate = QPainterPath(final_circle_path).subtracted(strand_body_path)
                    if not candidate.isEmpty():
                        final_circle_path = candidate

                # Intersect with other stroke
                intersection = QPainterPath(final_circle_path).intersected(other_stroke_path)

                # --- Apply Mask Subtraction to Circle Shadow Intersection ---
                if not intersection.isEmpty():
                    # Apply the same mask subtraction logic as for the main body shadow
                    for mask_name_sub_c, mask_info_sub_c in masked_strands_map.items():
                        mask_strand_sub_c = mask_info_sub_c['masked_strand']
                        mask_layer_sub_c = mask_name_sub_c

                        # Check if mask is visible and in layer order (backward compatible)
                        is_mask_hidden = getattr(mask_strand_sub_c, 'is_hidden', False)
                        if (not is_mask_hidden and mask_layer_sub_c in layer_order):

                            mask_index_sub_c = layer_order.index(mask_layer_sub_c)

                            # Skip if we're casting onto this mask itself
                            if mask_layer_sub_c == other_layer:
                                continue

                            # Only apply mask blocking if mask is ABOVE the casting strand
                            # A mask can only block shadows from strands below it in the layer order
                            if mask_index_sub_c <= self_index:
                                # Mask is at or below the casting strand - cannot visually block
                                continue

                            # Mask is above casting strand, apply blocking
                            try:
                                # Early check: First verify if the mask even intersects with the underlying layer
                                if hasattr(mask_strand_sub_c, 'get_mask_path'):
                                    mask_actual_path_c = mask_strand_sub_c.get_mask_path()
                                    if mask_actual_path_c.isEmpty() or not mask_actual_path_c.intersects(other_stroke_path):
                                        pass
                                        continue

                                # Calculate the mask's subtraction path (blurred)
                                subtraction_path_c = QPainterPath()
                                if hasattr(mask_strand_sub_c, 'first_selected_strand') and mask_strand_sub_c.first_selected_strand and \
                                   hasattr(mask_strand_sub_c, 'second_selected_strand') and mask_strand_sub_c.second_selected_strand:

                                    s1_c = mask_strand_sub_c.first_selected_strand
                                    s2_c = mask_strand_sub_c.second_selected_strand

                                    stroker1_c = QPainterPathStroker()
                                    # Use user-edited width: + max_blur_radius*2
                                    stroker1_c.setWidth(s1_c.width + s1_c.stroke_width * 2 + max_blur_radius/2)
                                    stroker1_c.setJoinStyle(Qt.MiterJoin)
                                    stroker1_c.setCapStyle(Qt.FlatCap)
                                    path1_c = stroker1_c.createStroke(s1_c.get_path())

                                    stroker2_c = QPainterPathStroker()
                                    # Use user-edited width: + max_blur_radius*2
                                    stroker2_c.setWidth(s2_c.width + s2_c.stroke_width * 2 + max_blur_radius/2)
                                    stroker2_c.setJoinStyle(Qt.MiterJoin)
                                    stroker2_c.setCapStyle(Qt.FlatCap)
                                    path2_c = stroker2_c.createStroke(s2_c.get_path())

                                    subtraction_path_c = path1_c.intersected(path2_c)

                                    # --------------------------------------------------
                                    # NEW: Respect deletion rectangles on the mask so
                                    #      that shadows can appear in regions where the
                                    #      mask has been manually deleted.
                                    # --------------------------------------------------


                                if not subtraction_path_c.isEmpty():
                                    # Check if the mask actually intersects with the underlying layer
                                    mask_intersects_underlying_c = subtraction_path_c.intersects(other_stroke_path)

                                    if mask_intersects_underlying_c:
                                        intersection = QPainterPath(intersection).subtracted(subtraction_path_c)
                                        # Basic logging for circle shadow subtraction
                                        if intersection.isEmpty(): # Check if subtraction removed everything
                                             pass
                                    else:
                                        pass

                            except Exception as e_c:
                                # logging.error(f"Error subtracting mask '{mask_layer_sub_c}' from circle shadow intersection: {e_c}")
                                pass
                # --- End Mask Subtraction ---

                # --- Subtract Intermediate Strands for Circle Shadows ---
                if not intersection.isEmpty():
                    # Determine the range of indices between casting and receiving
                    min_index = min(self_index, other_index)
                    max_index = max(self_index, other_index)

                    # Loop through all strands to find intermediate ones
                    for intermediate_strand in canvas.strands:
                        if not hasattr(intermediate_strand, 'layer_name') or not intermediate_strand.layer_name:
                            continue

                        intermediate_layer = intermediate_strand.layer_name
                        if intermediate_layer not in layer_order:
                            continue

                        intermediate_index = layer_order.index(intermediate_layer)

                        # Check if this strand is between casting and receiving
                        if min_index < intermediate_index < max_index:
                            # Skip if this is a hidden strand
                            if hasattr(intermediate_strand, 'is_hidden') and intermediate_strand.is_hidden:
                                continue

                            try:
                                # Get the rendered geometry of the intermediate strand
                                intermediate_path = build_rendered_geometry(intermediate_strand)
                                if hasattr(intermediate_strand, 'get_mask_path'):
                                    intermediate_path = get_proper_masked_strand_path(intermediate_strand)

                                # Subtract the intermediate strand from the circle shadow
                                if not intermediate_path.isEmpty():
                                    intersection = QPainterPath(intersection).subtracted(intermediate_path)
                            except Exception:
                                pass
                # --- End Intermediate Strand Subtraction ---

                if not intersection.isEmpty():
                    # Add circle shadows to the same list as body shadows for consistent handling
                    individual_shadow_paths.append(intersection)
                    # Expand clip path as well
                    if clip_path.isEmpty():
                        clip_path = QPainterPath(other_stroke_path)
                    else:
                        clip_path.addPath(QPainterPath(other_stroke_path))
                    pass

    elif circle_shadow_paths:
        # Fallback: no layer manager; simply subtract body and add whole circle shadow path
        for circle_path, _ in circle_shadow_paths:
            final_circle_path = QPainterPath(circle_path)
            if not strand_body_path.isEmpty():
                candidate = QPainterPath(final_circle_path).subtracted(strand_body_path)
                if not candidate.isEmpty():
                    final_circle_path = candidate

            # Add to individual shadow paths for consistent handling
            individual_shadow_paths.append(final_circle_path)
            if clip_path.isEmpty():
                clip_path = QPainterPath(final_circle_path)
            else:
                clip_path.addPath(QPainterPath(final_circle_path))
            pass

    # ----------------------------------------------------------
    # Draw all shadow paths at once using the faded effect (existing logic below)
    # ----------------------------------------------------------
    # If we have individual shadow paths but all_shadow_paths wasn't set, create the combined path now
    if not all_shadow_paths and individual_shadow_paths:
        # Combine all individual paths for the faded effect
        combined_path = QPainterPath()
        for path in individual_shadow_paths:
            if not path.isEmpty():
                combined_path.addPath(path)
        combined_path.setFillRule(Qt.WindingFill)
        all_shadow_paths = [combined_path]
        pass
    
    lift_path = QPainterPath()
    for path in lift_shadow_paths:
        lift_path.addPath(path)
    lift_path.setFillRule(Qt.WindingFill)
    if not lift_path.isEmpty():
        stroke_source = QPainterPath(all_shadow_paths[0]) if all_shadow_paths else QPainterPath()
        stroke_source.addPath(lift_path)
        stroke_source.setFillRule(Qt.WindingFill)
        all_shadow_paths = [stroke_source]

    # Draw all shadow paths at once using the faded effect
    # logging.info(f"Shadow paths for strand {getattr(strand, 'layer_name', 'unknown')}: count={len(all_shadow_paths)}, empty_paths={sum(1 for p in all_shadow_paths if p.isEmpty())}, non_empty={sum(1 for p in all_shadow_paths if not p.isEmpty())}")

    if all_shadow_paths:
        for i, path in enumerate(all_shadow_paths):
            if not path.isEmpty():
                pass
    if all_shadow_paths:
        # Combine all paths into one for the fading effect
        # (all_shadow_paths should contain only one path now, either combined intersections or fallback)
        if len(all_shadow_paths) == 1:
            total_shadow_path = QPainterPath(all_shadow_paths[0])
        elif len(all_shadow_paths) > 1:
             # This case might happen if the layer manager logic failed but fallback succeeded partially
             # Let's unite them just in case, though ideally it should be one path.
             # logging.warning(f"Expected one shadow path but found {len(all_shadow_paths)}, uniting them.")
             total_shadow_path = QPainterPath()
             for p in all_shadow_paths:
                 total_shadow_path.addPath(p)
        else:
             # This means all_shadow_paths was empty, log and return
             # logging.warning(f"No shadow paths in all_shadow_paths for strand {strand.layer_name}, skipping draw.")
             # NOTE: No painter.restore() needed here because painter.save() happens after this check
             return # Nothing to draw

        # Only add circle shadows if not using arrow shadow
        circle_shadow_path = QPainterPath()
        if not (getattr(strand, 'full_arrow_visible', False) and getattr(strand, 'arrow_casts_shadow', False)):
            circle_shadow_path = build_shadow_circle_geometry(strand, max_blur_radius)
            total_shadow_path.addPath(circle_shadow_path)

        # The filled areas as at a genuine crossing (the outlines, which strands
        # a mask restacks do not cut), combined like the normal fill.
        fill_path = QPainterPath()
        for stroke_region in individual_stroke_paths:
            fill_path.addPath(stroke_region)
        fill_path.setFillRule(Qt.WindingFill)
        cache[collected_key] = {'stroke_path': total_shadow_path, 'lift_path': lift_path,
                                'fill_path': fill_path, 'color': QColor(color_to_use),
                                'clip': QPainterPath(clip_path),
                                'outlines': list(zip(stroke_receivers, individual_stroke_paths)),
                                'circles': circle_shadow_path}
        if collect_only:
            return cache[collected_key]
        if clip_path.isEmpty():
            # Only a mask partner receives this strand's shadow; the mask paints it.
            return

        # Reduced high-frequency logging for performance during moves
        # logging.info(f"Drawing faded shadow for strand {strand.layer_name}")
        # Draw the combined path with a faded edge effect
        base_color = color_to_use
        base_alpha = base_color.alpha()
        core_color = QColor(base_color)

        # Prepare painter with clipping so the shadow cannot appear where no underlying strand exists
        painter.save()
        try:
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setBrush(Qt.NoBrush)  # We are stroking, not filling

            # --- Add Logging --- 
            current_comp_mode = painter.compositionMode()
            # logging.info(f"DrawMaskShadow - Before Clip/Stroke: total_shadow_path empty={total_shadow_path.isEmpty()}, bounds={total_shadow_path.boundingRect()}")
            # logging.info(f"DrawMaskShadow - Before Clip/Stroke: clip_path empty={clip_path.isEmpty()}, bounds={clip_path.boundingRect()}")
            # logging.info(f"DrawMaskShadow - Before Clip/Stroke: Painter composition mode={current_comp_mode}")
            # --- End Logging ---

            # --- Explicitly set composition mode before stroking --- 
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)  # Ensure correct blending

            # Apply clipping – use the collected clip_path, or fallback to the shadow path itself
            if not clip_path.isEmpty():
                painter.setClipPath(clip_path)

            # Check if path is valid before attempting to stroke
            if not total_shadow_path.isEmpty():
                # ------------------------------------------------------------------
                # NEW: Paint a solid fill for the shadow core so the centre area is
                #      not left transparent.  This guarantees the interior of the
                #      shadow uses the same colour/opacity before we add the blurred
                #      outline.
                # ------------------------------------------------------------------
            
   
                # --- Wrap stroking in try...except ---
                try:
                    for i in range(num_steps):
                        # Alpha fades from base_alpha down towards zero
                        # Distribute alpha across steps for smoother look
                        # Adjusted alpha calculation slightly for potentially better distribution
                        progress = (float(num_steps - i) / num_steps)
                        current_alpha = base_alpha * progress * (1.0 / num_steps) * 2.0 # Exponential decay, adjust multiplier

                        # Width increases
                        current_width = max_blur_radius * (float(i + 1) / num_steps)

                        pen_color = QColor(base_color.red(), base_color.green(), base_color.blue(), max(0, min(255, int(current_alpha))))
                        pen = QPen(pen_color)
                        pen.setWidthF(current_width)
                        pen.setCapStyle(Qt.FlatCap)  # Keep ends squared off
                        pen.setJoinStyle(Qt.RoundJoin)

                        painter.setPen(pen)
                        painter.strokePath(total_shadow_path, pen)  # <-- actual drawing: main shadow strokes for normal strands
                except Exception as stroke_error:
                    # logging.error(f"DrawMaskShadow - Error during shadow stroking loop: {stroke_error}")
                    pass
                # --- End try...except ---

                # logging.info(f"Drew faded shadow stroke path with {num_steps} steps for strand {strand.layer_name} bounds {total_shadow_path.boundingRect()}")
            else:
                 # logging.warning(f"Total shadow path became empty unexpectedly for strand {strand.layer_name}, cannot draw faded shadow.")
                 pass

        finally:
            painter.restore() # Restore painter state (render hints, brush, composition mode)

    else:
        # ADDED: Create a fallback shadow path when no paths are found
        # logging.warning(f"No shadow paths for strand {getattr(strand, 'layer_name', 'unknown')}, creating fallback")
        # Create a simple shadow based on the strand's own path
        fallback_path = get_proper_masked_strand_path(strand)
        if not fallback_path.isEmpty():
            all_shadow_paths = [fallback_path]    

def get_proper_masked_strand_path(strand):
    """
    Helper function to get the proper path for a masked strand.
    This ensures we use the actual mask path that accounts for all deletions.

    Args:
        strand: The strand to get path from, which might be a MaskedStrand

    Returns:
        QPainterPath: The correct path to use for the strand
    """
    # Check if strand is hidden with a visible arrow that casts shadows
    if (getattr(strand, 'is_hidden', False) and
        getattr(strand, 'full_arrow_visible', False) and
        getattr(strand, 'arrow_casts_shadow', False)):
        # Use arrow path for shadow casting when strand is hidden
        arrow_path = strand.get_arrow_shadow_path() if hasattr(strand, 'get_arrow_shadow_path') else QPainterPath()
        if not arrow_path.isEmpty():
            return arrow_path

    # Check if this is a masked strand
    if hasattr(strand, 'get_mask_path'):
        try:
            # Get the actual mask path which includes all deletions
            mask_path = strand.get_mask_path()
            if not mask_path.isEmpty():
                pass
                return mask_path
            else:
                # logging.warning(f"Empty mask path for MaskedStrand, falling back to standard path")
                pass
        except Exception as e:
            # logging.error(f"Error getting mask path: {e}, falling back to standard path")
            pass

    # For normal strands or fallback, use the regular path
    if hasattr(strand, 'get_shadow_path'):
        path = strand.get_shadow_path()
    else:
        path = QPainterPath()  # Empty path as last resort

    return path 

# --------------------------------------------------
# New helper: build_rendered_geometry
# --------------------------------------------------
def get_side_line_exclusion_path(strand, shadow_width_multiplier=None):
    """
    Creates exclusion paths exactly at strand starting and ending points to prevent shadows 
    from being rendered there.
    
    Args:
        strand: The strand to create exclusion paths for
        shadow_width_multiplier: Multiplier for the exclusion width. If None, automatically 
                                calculates based on strand width (width/2 for grid units)
        
    Returns:
        QPainterPath: Combined exclusion path for both start and end points
    """
    exclusion_path = QPainterPath()
    
    try:
        # Ensure side lines are calculated
        if hasattr(strand, 'update_side_line'):
            strand.update_side_line()
        elif not (hasattr(strand, 'start_line_start') and hasattr(strand, 'start_line_end') and 
                  hasattr(strand, 'end_line_start') and hasattr(strand, 'end_line_end')):
            return exclusion_path  # Return empty path if no side line support
        
        # Auto-calculate exclusion width based on strand thickness
        if shadow_width_multiplier is None:
            strand_width = getattr(strand, 'width', 10)
            # Use a simple proportional scaling: thicker strands need wider exclusion zones
            # Base exclusion should be at least max_blur_radius (~30px) plus proportional to strand width
            shadow_width = max(35.0, strand_width * 1.5)  # Minimum 35px, or 1.5x strand width, whichever is larger
            pass
        else:
            # Calculate exclusion width based on provided multiplier
            shadow_width = getattr(strand, 'width', 10) * shadow_width_multiplier
        

        
 
        
        pass
        
    except Exception as e:
        pass
    
    return exclusion_path

def build_rendered_geometry(strand):
    """The *visual* geometry of a strand (see _build_rendered_geometry), with
    the lowered start caps it paints for its attached strands
    (lowered_start_cap): they lie at its layer, so the strands crossing there
    shade them and they block what lies below, like the strand itself."""
    geometry = _build_rendered_geometry(strand)
    if hasattr(strand, 'get_mask_path'):
        return geometry
    lowered = lowered_caps_of(strand)
    if len(lowered) == 1:
        return QPainterPath(lowered[0][1]['parent_geometry'])
    for _child, info in lowered:
        geometry = QPainterPath(geometry).united(info['cap'])
    return geometry


def _build_rendered_geometry(strand):
    """
    Returns the *visual* geometry of a strand as a single QPainterPath.

    The path includes:
      • The stroked body path (taking `width` & `stroke_width` into account)
      • Every *visible* end-circle (if `has_circles` is set and the circle
        stroke colour is not fully transparent).
      • The arrow path if full_arrow_visible is True (for receiving shadows on arrow)

    Having one consistent geometry for both the casting and receiving side of
    the shadow calculation removes the need for the separate
    `circle_shadow_paths` branch and for the various ad-hoc "add circle"
    unions that existed before.

    NOTE: For a `MaskedStrand` the routine delegates to
    `get_proper_masked_strand_path` so that we get the mask intersection path
    (which deliberately *excludes* circles).
    """

    # For masked strands keep the specialised mask path – circles would leak
    # shadow around the mask edges otherwise.
    if hasattr(strand, 'get_mask_path'):
        return get_proper_masked_strand_path(strand)

    # Check if we should use arrow path for receiving shadows
    # The arrow should receive shadows regardless of arrow_casts_shadow setting
    # arrow_casts_shadow only controls if arrow casts shadows, not if it receives them
    if getattr(strand, 'full_arrow_visible', False):
        # Get the arrow path which includes shaft and head (for receiving shadows)
        arrow_path = strand.get_arrow_path(for_receiving_shadows=True) if hasattr(strand, 'get_arrow_path') else QPainterPath()

        if not arrow_path.isEmpty():
            # If strand is hidden, only return arrow path
            if getattr(strand, 'is_hidden', False):
                return arrow_path
            # If strand is visible, combine arrow with strand body
            # Continue to build the normal strand geometry and unite with arrow

    # Import AttachedStrand class for isinstance checks
    try:
        from attached_strand import AttachedStrand as AttachedStrandClass
    except ImportError:
        AttachedStrandClass = None

    try:
        # ------------------------------------------------------------------
        # 1) Base body stroke
        # ------------------------------------------------------------------
        if hasattr(strand, 'get_shadow_path'):
            body_source = strand.get_shadow_path()
        elif hasattr(strand, 'get_path'):
            body_source = strand.get_path()
        else:
            body_source = QPainterPath()

        stroker = QPainterPathStroker()
        stroker.setWidth(strand.width + strand.stroke_width * 2)
        stroker.setJoinStyle(Qt.RoundJoin)  # Smooth corners at curves
        stroker.setCapStyle(Qt.FlatCap)     # Squared ends (no false circles)
        result_path = stroker.createStroke(body_source)

        # Stylized free ends: start from the styled footprint (built on the
        # same shadow path, so the unstyled end keeps its extension)
        if hasattr(strand, 'get_footprint_path'):
            styled = strand.get_footprint_path(shadow_base=hasattr(strand, 'get_shadow_path'))
            if not styled.isEmpty():
                result_path = QPainterPath(styled)

        # ------------------------------------------------------------------
        # 2) Union with visible circles
        # ------------------------------------------------------------------
        if hasattr(strand, 'has_circles') and any(strand.has_circles):
            # Check if the circle stroke is fully transparent – if so, we treat
            # the circles as invisible and skip them entirely.
            transparent_circles = (
                hasattr(strand, 'circle_stroke_color') and
                strand.circle_stroke_color and
                strand.circle_stroke_color.alpha() == 0
            )

            if not transparent_circles:
                # Only process circles if the strand actually has attached children
                if not (hasattr(strand, 'attached_strands') and strand.attached_strands and AttachedStrandClass):
                    # No attachments at all, skip circle processing entirely
                    pass
                else:
                    radius = (strand.width + strand.stroke_width * 2) / 2.0
                    
                    # Check if this is an AttachedStrand (by checking class name)
                    is_attached_strand = strand.__class__.__name__ == 'AttachedStrand'
                    
                    for idx, enabled in enumerate(strand.has_circles):
                        if not enabled:
                            continue
                        
                        # Check if this specific circle has transparent stroke
                        is_circle_transparent = False
                        if idx == 0 and hasattr(strand, 'start_circle_stroke_color'):
                            if strand.start_circle_stroke_color and strand.start_circle_stroke_color.alpha() == 0:
                                is_circle_transparent = True
                        elif idx == 1 and hasattr(strand, 'end_circle_stroke_color'):
                            if strand.end_circle_stroke_color and strand.end_circle_stroke_color.alpha() == 0:
                                is_circle_transparent = True
                        
                        # Skip transparent circles
                        if is_circle_transparent:
                            continue
                        
                        # Check if there are actual attachments at this specific point
                        if idx == 0:  # Start point
                            has_attachment = any(isinstance(child, AttachedStrandClass) and child.start == strand.start 
                                               for child in strand.attached_strands)
                        else:  # End point
                            has_attachment = any(isinstance(child, AttachedStrandClass) and child.start == strand.end 
                                               for child in strand.attached_strands)
                        
                        # Skip if no actual attachment at this point
                        if not has_attachment:
                            continue
                        
                        centre = strand.start if idx == 0 else strand.end
                        
                        # For AttachedStrand with actual attachments, create half-circles instead of full circles
                        if is_attached_strand:
                            # Create full circle first
                            full_circle = QPainterPath()
                            full_circle.addEllipse(centre, radius, radius)
                            
                            # Create masking rectangle to get half circle
                            if idx == 0:  # Start circle
                                # Calculate angle based on tangent at start
                                if hasattr(strand, 'calculate_start_tangent'):
                                    angle = strand.calculate_start_tangent()
                                else:
                                    angle = 0
                            else:  # End circle
                                # Calculate angle based on tangent at end
                                if hasattr(strand, 'calculate_cubic_tangent'):
                                    tangent = strand.calculate_cubic_tangent(1.0)
                                    angle = math.atan2(tangent.y(), tangent.x())
                                else:
                                    angle = 0

                            # If this end has an elliptical cap, use the same ellipse
                            # shape so the receiving/blocking geometry matches the
                            # drawn cap (the mask below still halves it).
                            _cap_pt = strand._partner_cap_dims(idx)[0] if hasattr(strand, '_partner_cap_dims') else None
                            if _cap_pt:
                                full_circle = strand._make_cap_ellipse(centre, angle, idx, _cap_pt)

                            # Create masking rectangle for half circle
                            mask_rect = QPainterPath()
                            rect_width = radius * 4
                            rect_height = radius * 4
                            mask_rect.addRect(0, -rect_height / 2, rect_width, rect_height)
                            
                            # Transform the mask to the correct position and angle
                            transform = QTransform()
                            transform.translate(centre.x(), centre.y())
                            if idx == 0:
                                transform.rotate(math.degrees(angle))
                            else:
                                transform.rotate(math.degrees(angle - math.pi))
                            mask_rect = transform.map(mask_rect)
                            
                            # Get half circle by subtracting mask from full circle
                            half_circle = QPainterPath(full_circle).subtracted(mask_rect)
                            result_path.addPath(half_circle)
                        else:
                            # Use the elliptical cap when this end has one, else a
                            # regular full circle for non-AttachedStrand.
                            _cap_pt = strand._partner_cap_dims(idx)[0] if hasattr(strand, '_partner_cap_dims') else None
                            if _cap_pt:
                                _t = strand.calculate_cubic_tangent(0.0001 if idx == 0 else 0.9999)
                                _a = math.atan2(_t.y(), _t.x())
                                circle_path = strand._make_cap_ellipse(centre, _a, idx, _cap_pt)
                            else:
                                circle_path = QPainterPath()
                                circle_path.addEllipse(centre, radius, radius)
                            result_path.addPath(circle_path)

        # Unite arrow path with result if we have one (for visible strands)
        if getattr(strand, 'full_arrow_visible', False) and not getattr(strand, 'is_hidden', False):
            arrow_path = strand.get_arrow_path(for_receiving_shadows=True) if hasattr(strand, 'get_arrow_path') else QPainterPath()
            if not arrow_path.isEmpty():
                result_path.addPath(arrow_path)

        return result_path
    except Exception as e:
        # logging.error(
        #     f"build_rendered_geometry: failed for {getattr(strand, 'layer_name', 'unknown')} – {e}"
        # )
        pass
        return QPainterPath()

def build_shadow_circle_geometry(strand, fixed_shadow_extension=30.0):
    """
    Returns shadow geometry for strand circles only.
    
    Args:
        strand: The strand to create circle shadow geometry for
        fixed_shadow_extension: Fixed distance (in pixels) to extend shadow beyond circle edge
        
    Returns:
        QPainterPath: Circle shadow geometry with consistent extension
    """
    circle_path = QPainterPath()
    
    try:
        # Check if strand has visible circles
        if not hasattr(strand, 'has_circles') or not any(strand.has_circles):
            return circle_path
            
        # Check if any circles are transparent
        has_transparent_circles = False
        if hasattr(strand, 'start_circle_stroke_color'):
            start_color = strand.start_circle_stroke_color
            if start_color and start_color.alpha() == 0:
                has_transparent_circles = True
        if hasattr(strand, 'end_circle_stroke_color'):
            end_color = strand.end_circle_stroke_color
            if end_color and end_color.alpha() == 0:
                has_transparent_circles = True
        
        # Skip shadow generation only if ALL circles are transparent
        all_transparent = True
        for idx, enabled in enumerate(strand.has_circles):
            if not enabled:
                continue
            
            is_circle_transparent = False
            if idx == 0:  # Start circle
                start_color = strand.start_circle_stroke_color
                if start_color and start_color.alpha() == 0:
                    is_circle_transparent = True
            elif idx == 1:  # End circle
                end_color = strand.end_circle_stroke_color
                if end_color and end_color.alpha() == 0:
                    is_circle_transparent = True
            
            if not is_circle_transparent:
                all_transparent = False
                break
        
        if all_transparent and has_transparent_circles:
            return circle_path
            
        # Circle radius includes the fixed shadow extension
        radius = (strand.width + strand.stroke_width * 2) / 2.0 + 2
        depth_margin = 2

        for idx, enabled in enumerate(strand.has_circles):
            if not enabled:
                continue

            # Check if this specific circle is transparent
            is_circle_transparent = False
            if idx == 0:  # Start circle
                start_color = strand.start_circle_stroke_color
                if start_color and start_color.alpha() == 0:
                    is_circle_transparent = True
            elif idx == 1:  # End circle
                end_color = strand.end_circle_stroke_color
                if end_color and end_color.alpha() == 0:
                    is_circle_transparent = True

            # Skip shadow generation for transparent circles
            if is_circle_transparent:
                continue

            if hasattr(strand, '_cap_shadow_path'):
                single_circle = strand._cap_shadow_path(idx, radius, depth_margin)
            else:
                centre = strand.start if idx == 0 else strand.end
                single_circle = QPainterPath()
                single_circle.addEllipse(centre, radius, radius)
            circle_path.addPath(single_circle)

        return circle_path
    except Exception as e:
        pass
        return QPainterPath()

def build_shadow_geometry(strand, fixed_shadow_extension=30.0, include_circles=True):
    """
    Returns shadow geometry that extends a fixed distance beyond the strand edge,
    ensuring consistent shadow length regardless of strand thickness.
    
    Args:
        strand: The strand to create shadow geometry for
        fixed_shadow_extension: Fixed distance (in pixels) to extend shadow beyond strand edge
        include_circles: Whether to include circle geometry in the shadow path
        
    Returns:
        QPainterPath: Shadow geometry with consistent extension
    """
    # For masked strands keep the specialised mask path
    if hasattr(strand, 'get_mask_path'):
        return get_proper_masked_strand_path(strand)

    try:
        # Get the base strand path
        if hasattr(strand, 'get_shadow_path'):
            body_source = strand.get_shadow_path()
        elif hasattr(strand, 'get_path'):
            body_source = strand.get_path()
        else:
            body_source = QPainterPath()

        # Create shadow geometry that extends fixed distance beyond strand edge
        stroker = QPainterPathStroker()
        # Use actual strand width plus fixed shadow extension
        shadow_width = strand.width + strand.stroke_width * 2 + (fixed_shadow_extension * 2)
        stroker.setWidth(shadow_width)
        stroker.setJoinStyle(Qt.RoundJoin)  # Smooth corners at curves
        stroker.setCapStyle(Qt.FlatCap)     # Squared ends (no false circles)
        result_path = stroker.createStroke(body_source)

        # Stylized free ends: the styled footprint pushed outward by the same
        # fixed extension, so the cast shadow follows the end's profile
        if hasattr(strand, 'get_footprint_path'):
            styled = strand.get_footprint_path(
                margin=fixed_shadow_extension, join=Qt.RoundJoin,
                shadow_base=hasattr(strand, 'get_shadow_path'))
            if not styled.isEmpty():
                result_path = QPainterPath(styled)

        # Add visible circles with same fixed extension if requested
        if include_circles and hasattr(strand, 'has_circles') and any(strand.has_circles):
            transparent_circles = (
                hasattr(strand, 'circle_stroke_color') and
                strand.circle_stroke_color and
                strand.circle_stroke_color.alpha() == 0
            )

            if not transparent_circles:
                # Circle radius includes the fixed shadow extension
                radius = (strand.width + strand.stroke_width * 2) / 2.0 + fixed_shadow_extension
                for idx, enabled in enumerate(strand.has_circles):
                    if not enabled:
                        continue
                    if hasattr(strand, '_cap_shadow_path'):
                        circle_path = strand._cap_shadow_path(
                            idx, radius, depth_margin=fixed_shadow_extension
                        )
                    else:
                        centre = strand.start if idx == 0 else strand.end
                        circle_path = QPainterPath()
                        circle_path.addEllipse(centre, radius, radius)
                    result_path.addPath(circle_path)

        return result_path
    except Exception as e:
        return QPainterPath()

# --------------------------------------------------
# Helper: shadow-blocker path (cached)
# --------------------------------------------------

def get_shadow_blocker_path(mask_strand, blur_px):
    """
    Return a path that blocks shadows beneath *mask_strand*.

    It is the union of the mask's actual geometry (already respecting
    deletion rectangles) and a stroked outline that extends by the full
    blur radius so that the soft edge is also blocked.

    The result is cached on the *mask_strand* instance so that we only
    run the heavy QPainterPath maths when the mask (or the blur amount)
    really changes.  Any method that mutates the mask should simply
    delete the attribute ``_shadow_blocker_cache`` so a fresh one is
    generated automatically next time.
    """
    from PyQt5.QtGui import QPainterPathStroker  # local import → avoids Qt costs when not needed

    if mask_strand is None:
        return QPainterPath()

    # --- Per-instance cache (dict blur_px -> path) --------------------
    cache = getattr(mask_strand, "_shadow_blocker_cache", None)
    if cache is None:
        cache = {}
        setattr(mask_strand, "_shadow_blocker_cache", cache)

    key = float(blur_px)
    if key in cache:
        return cache[key]

    try:
        base_path = _get_mask_visual_path(mask_strand)
        if base_path.isEmpty():
            cache[key] = QPainterPath()
            return cache[key]

        stroker = QPainterPathStroker()
        stroker.setWidth(blur_px)
        stroker.setJoinStyle(Qt.MiterJoin)
        stroker.setCapStyle(Qt.FlatCap)
        extended = stroker.createStroke(base_path)
        blocker = QPainterPath(base_path)
        blocker.addPath(extended)

        cache[key] = blocker
        return blocker
    except Exception:
        # On any error just return an empty path so we never block painting.
        return QPainterPath()


def shadow_preview(canvas, casting_strand, receiving_strand, casting_layer, receiving_layer, painter=None):
    """Where the canvas draws the shadow *casting_layer* casts on
    *receiving_layer*, for the Shadow Editor's preview, as (area, clips), or
    None when it casts none there. Filled with the painter clipped to every
    path in *clips* in turn, *area* covers the shadow's filled area and its
    soft edge as far as the edge reaches onto the receiver.

    It is computed by the code the canvas draws with (_pair_shadow; for a
    mask, the paths draw_mask_lift_shadow paints), so the preview shows what
    is drawn. A mask casts one shadow, on its second strand: its first
    strand's shadow there, which the mask paints over the second strand.
    The painter does the clipping, as it does for the shadow itself, and
    also leaves out what is drawn over the shadow later (see
    _outside_covering_pieces): Qt's boolean operations lose whole bands of a
    stroke's self-overlapping outline, and can return nothing at all for a
    strand with an end circle.
    *painter* is the paint in progress, if any; the preview then reuses the
    mask geometry that paint has already worked out.
    """
    manager = getattr(canvas, 'layer_state_manager', None)
    if not manager or casting_strand is None or receiving_strand is None:
        return None
    layer_order = manager.getOrder()
    if casting_layer not in layer_order or receiving_layer not in layer_order:
        return None
    max_blur_radius = float(getattr(canvas, 'max_blur_radius', 30.0) or 30.0)
    num_steps = getattr(canvas, 'num_steps', 3)
    cache = _frame_cache(painter)

    if hasattr(casting_strand, 'get_mask_path'):
        first = getattr(casting_strand, 'first_selected_strand', None)
        second = getattr(casting_strand, 'second_selected_strand', None)
        if (first is None or second is None or second.layer_name != receiving_layer
                or getattr(casting_strand, 'is_hidden', False)
                or not casting_strand._intersection_shadow_visible()):
            return None
        collected = draw_strand_shadow(painter, first, None, num_steps=num_steps,
                                       max_blur_radius=max_blur_radius, collect_only=True)
        if not collected or collected['lift_path'].isEmpty():
            return None
        clips = [_mask_lift_clip(casting_strand, max_blur_radius, cache)]
        fill = collected['lift_path']
        lifted_layer = first.layer_name
    else:
        # As in draw_strand_shadow: a hidden strand casts only through its
        # arrow, and "Hide Shadow" switches a strand's shadow off.
        if getattr(casting_strand, 'is_hidden', False) and not (
                getattr(casting_strand, 'full_arrow_visible', False)
                and getattr(casting_strand, 'arrow_casts_shadow', False)):
            return None
        if getattr(casting_strand, 'hide_shadow', False):
            return None
        if layer_order.index(receiving_layer) >= layer_order.index(casting_layer):
            # Only a mask lifts a strand's shadow onto a strand above it, and
            # that shadow is previewed on the mask's row.
            return None
        masked_strands_map = _frame_masks_map(canvas, layer_order, cache)
        near_masks = _masks_near(casting_strand, masked_strands_map, canvas, layer_order, max_blur_radius, cache)
        _outline, shadow_path, joints = _caster_shadow_path(casting_strand)
        pair = _pair_shadow(casting_strand, receiving_strand, shadow_path, canvas, layer_order,
                            masked_strands_map, near_masks, _lifted_near_masks(casting_strand, near_masks),
                            _lowered_near_masks(casting_strand, near_masks, layer_order), max_blur_radius, cache,
                            joints)
        if pair is None or pair['lift'] is not None:
            return None
        clips = [pair['clip']]
        if not pair['clip_blocker'].isEmpty():
            clips.append(_outside(pair['clip_blocker'], pair['clip'].boundingRect()))
        fill = pair['outline'] if pair['fill'] is None else pair['fill']
        # The soft edge is stroked along all the caster's outlines at once
        # (its other crossings and its end circles too), so the parts of them
        # near the receiver land on it as well.
        collected = draw_strand_shadow(painter, casting_strand, None, num_steps=num_steps,
                                       max_blur_radius=max_blur_radius, collect_only=True)
        if not collected:
            return None
        lifted_layer = casting_layer
    if clips[0].isEmpty():
        return None
    rect = clips[0].boundingRect()
    clips += _outside_covering_pieces(casting_strand, lifted_layer, layer_order, canvas, cache, rect)
    stroker = QPainterPathStroker()
    stroker.setWidth(max_blur_radius)
    stroker.setJoinStyle(Qt.RoundJoin)
    stroker.setCapStyle(Qt.FlatCap)
    area = QPainterPath(fill)
    area.addPath(stroker.createStroke(
        _stroke_source_near(collected, rect, max_blur_radius / 2.0 + 2.0)))
    area.setFillRule(Qt.WindingFill)
    return area, clips


def _outside(path, rect):
    """A clip path for the part of *rect* outside *path*. The painter clips
    to it exactly, where subtracting *path* from another path can fail."""
    outside = QPainterPath()
    outside.addRect(QRectF(rect).adjusted(-2.0, -2.0, 2.0, 2.0))
    # Under the odd-even rule a point of the rectangle is inside exactly when
    # it is outside *path*; simplified() gives *path* that rule.
    outside.addPath(path if path.fillRule() == Qt.OddEvenFill else path.simplified())
    outside.setFillRule(Qt.OddEvenFill)
    return outside


def _outside_covering_pieces(caster, lifted_layer, layer_order, canvas, cache, rect):
    """Clip paths that leave out, within *rect*, the pieces of the masks
    drawn after *caster*, which cover its shadow there: one per piece, since
    pieces can overlap. A mask lifting *lifted_layer* (the strand that casts)
    is left alone: its piece is that strand itself."""
    if caster.layer_name not in layer_order:
        return []
    above = set(layer_order[layer_order.index(caster.layer_name) + 1:])
    clips = []
    for item in canvas.strands:
        if (not hasattr(item, 'get_mask_path') or getattr(item, 'layer_name', None) not in above
                or getattr(item, 'is_hidden', False)
                or getattr(getattr(item, 'first_selected_strand', None), 'layer_name', None) == lifted_layer):
            continue
        piece = _piece_of(item, cache)
        if not piece.isEmpty() and piece.boundingRect().intersects(rect):
            clips.append(_outside(piece, rect))
    return clips
