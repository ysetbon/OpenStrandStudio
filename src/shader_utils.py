import logging
from PyQt5.QtGui import QPainterPath, QPainterPathStroker, QPen, QBrush, QColor, QPainter
from PyQt5.QtCore import Qt, QRectF, QPointF
from typing import List
import math
from functools import lru_cache


def draw_mask_strand_shadow(
    painter,
    first_path: QPainterPath,
    second_path: QPainterPath,
    deletion_rects: List[QRectF] = None,
    shadow_color: QColor = None,
    num_steps: int = 3,
    max_blur_radius: float = 29.99,
):
    """Draw a blurred shadow for the **intersection** between *first_path* and *second_path*.

    The function no longer depends on a *MaskedStrand* instance – instead it
    receives the fully-stroked paths of the two component strands and derives
    everything it needs from them.  This greatly simplifies the implementation
    and removes a large amount of canvas / layer specific logic that is not
    required for the basic visual effect.
    """
    painter.save()
    # ------------------------------------------------------------------
    # Determine the region that should receive the shadow – this is the
    # intersection of the two supplied paths.
    # ------------------------------------------------------------------
    # Log geometry of input paths
    logging.info(f"draw_mask_strand_shadow: first_path bounds={first_path.boundingRect()}, elements={first_path.elementCount()} | second_path bounds={second_path.boundingRect()}, elements={second_path.elementCount()}")
    # Compute intersection of component paths
    intersection_path = QPainterPath(first_path).intersected(second_path)
    # Log intersection geometry
    logging.info(f"draw_mask_strand_shadow: intersection_path bounds={intersection_path.boundingRect()}, elements={intersection_path.elementCount()}")

    if not first_path.isEmpty() and not second_path.isEmpty():
        intersection_path = QPainterPath(first_path).intersected(second_path)
        logging.info("draw_mask_strand_shadow: using first_path as fallback")

    else:
        # logging.warning("draw_mask_strand_shadow: both paths empty - nothing to draw")
        return

    # Apply deletion rectangles to intersection_path if provided
    if deletion_rects:
        for rect in deletion_rects:
            rect_path = QPainterPath()
            try:
                # Support both QRectF instances and dicts with corner coordinates
                if isinstance(rect, QRectF):
                    rect_path.addRect(rect)
                elif isinstance(rect, dict) and all(k in rect for k in ("top_left", "top_right", "bottom_left", "bottom_right")):
                    tl = QPointF(*rect["top_left"])
                    tr = QPointF(*rect["top_right"])
                    br = QPointF(*rect["bottom_right"])
                    bl = QPointF(*rect["bottom_left"])

                    rect_path.moveTo(tl)
                    rect_path.lineTo(tr)
                    rect_path.lineTo(br)
                    rect_path.lineTo(bl)
                    rect_path.closeSubpath()
                else:
                    # Fallback to axis-aligned QRectF if rectangular data present
                    if all(k in rect for k in ("x", "y", "width", "height")):
                        rect_path.addRect(QRectF(rect["x"], rect["y"], rect["width"], rect["height"]))
            except Exception as de_err:
                # logging.error(f"draw_mask_strand_shadow: error constructing deletion rect path from {rect}: {de_err}")
                continue

            if not rect_path.isEmpty():
                intersection_path = intersection_path.subtracted(rect_path)
        logging.info(f"draw_mask_strand_shadow: applied {len(deletion_rects)} deletion rects; new bounds={intersection_path.boundingRect()}, empty={intersection_path.isEmpty()}")

    # ------------------------------------------------------------------
    # Resolve shadow colour.  If the caller did not provide one we default
    # to a semi-transparent black (matching the normal strand shadow).
    # ------------------------------------------------------------------
    if shadow_color is None:
        shadow_color = QColor(0, 0, 0, 150)  # ~59 % opacity by default
    elif not isinstance(shadow_color, QColor):
        # Allow callers to pass e.g. a `Qt.GlobalColor` or a tuple.
        shadow_color = QColor(shadow_color)

    # Ensure we have an *independent* QColor instance so that we can safely
    # tweak its alpha value later.
    base_color = QColor(shadow_color)
    base_alpha = base_color.alpha()

    # ------------------------------------------------------------------
    # Prepare painter state.
    # ------------------------------------------------------------------

    
    # ------------------------------------------------------------------
    # 1) Fill the solid shadow core.
    # ------------------------------------------------------------------
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(base_color))
    painter.drawPath(intersection_path)  # <-- actual drawing: solid core of the mask shadow
    painter.setBrush(Qt.NoBrush)

    # ------------------------------------------------------------------
    # 2) Add a blurred / faded edge by repeatedly stroking the path with
    #    increasing width and decreasing alpha.
    # ------------------------------------------------------------------
    # We allow the blurred edge to extend anywhere the ORIGINAL component
    # paths exist (their union) so that the blur is not clipped too early.
 

    # ------------------------------------------------------------------
    # Restrict the blurred stroke so that it can expand inside the
    # *receiving* strand (``second_path``) but never draws over the
    # *casting* strand (``first_strand``).
    #
    # We therefore construct a clipping path that equals the second
    # strand **minus** the first strand and apply that as the painter's
    # clipping region.  QPainter::setClipPath replaces the previous
    # clip region by default, so we build the final region explicitly
    # and set it only once.
    # ------------------------------------------------------------------

    clip_path = QPainterPath(second_path)            # Start with the full receiver geometry
       # Remove the area covered by the caster
    clip_path.intersected(intersection_path)
    painter.setClipPath(clip_path)

    for i in range(num_steps):
        progress = (num_steps - i) / num_steps  # 1 → 0
        current_alpha = base_alpha * progress * (1.0 / num_steps) * 2.0
        current_width = max_blur_radius * ((i + 1) / num_steps)

        pen_color = QColor(base_color.red(), base_color.green(), base_color.blue(),
                           max(0, min(255, int(current_alpha))))
        pen = QPen(pen_color)
        pen.setWidthF(current_width)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)

        painter.setPen(pen)
        painter.strokePath(intersection_path, pen)  # <-- actual drawing: blurred/faded shadow strokes

    painter.restore()
    logging.info(
        f"draw_mask_strand_shadow: rendered shadow (steps={num_steps}, blur={max_blur_radius})"
    )

def draw_circle_shadow(painter, strand, shadow_color=None):
    """
    Draw shadow for a circle at the start or end of a strand.
    """
    pass

def draw_strand_shadow(painter, strand, shadow_color=None, num_steps=3, max_blur_radius=None):
    """
    Draw shadow for a strand that overlaps with other strands.
    This function should be called before drawing the strand itself.
    
    Args:
        painter: The QPainter to draw with
        strand: The strand to draw shadow for
        shadow_color: Custom shadow color or None to use strand's shadow_color
    """
    # Check if the strand is hidden - hidden strands should not cast shadows
    if hasattr(strand, 'is_hidden') and strand.is_hidden:
        logging.info(f"Skipping shadow for hidden strand {getattr(strand, 'layer_name', 'unknown')}")
        return
    
    # Auto-calculate blur radius based on strand thickness if not provided
    if max_blur_radius is None:
        strand_width = getattr(strand, 'width', 10)
        # Use consistent shadow extension regardless of strand thickness
        max_blur_radius = 30.0  # Fixed shadow extension for all strand thicknesses
        logging.info(f"Using consistent blur radius={max_blur_radius} for strand width={strand_width}")
    
    # Early return for masked strands to avoid double shading
    # If this is a masked strand (has get_mask_path method), its shadow 
    # will already be drawn by draw_mask_strand_shadow
    if hasattr(strand, "get_mask_path"):
        logging.info(f"Skipping extra shadow for masked strand {getattr(strand, 'layer_name', 'unknown')} to avoid double shading")
        return
    if strand.__class__.__name__ == 'MaskedStrand':
        return
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
    
    # Reduced high-frequency logging for performance during moves
    # logging.info(f"Drawing shadow for strand {strand.layer_name} with color {color_to_use.name()} alpha={color_to_use.alpha()}")
    
    # Obtain the base path (without circles) for operations that still expect
    # the raw strand outline, then build a geometry path that already contains the strand body **and** any
    # visible end-circles.  This single path will be used for all subsequent
    # shadow computations, eliminating the need for special-casing circles.
    path = get_proper_masked_strand_path(strand)
    shadow_path = build_shadow_geometry(strand, 0)
        
    # --------------------------------------------------
    # If this strand has a *transparent* circle at either end, the circle is
    # NOT part of the rendered geometry, but the rectangular end-cap produced
    # by the body stroke can still cast a little square shadow.  To guarantee
    # that absolutely no shadow halo appears where the user explicitly asked
    # for a fully-transparent cap, we subtract a slightly enlarged circle
    # region from the shadow path.
    # --------------------------------------------------
    try:
        if (
            hasattr(strand, "circle_stroke_color")
            and strand.circle_stroke_color
            and strand.circle_stroke_color.alpha() == 0
            and hasattr(strand, "has_circles")
            and any(strand.has_circles)
        ):
            radius_base = (strand.width + strand.stroke_width * 2) / 1.5
            adj_radius = radius_base   # ensure we cut beyond blur

            for idx, enabled in enumerate(strand.has_circles):
                if not enabled:
                    continue  # Circle already hidden by flag

                centre = strand.start if idx == 0 else strand.end
                cut = QPainterPath()
                cut.addEllipse(centre, adj_radius, adj_radius)
                shadow_path = shadow_path.subtracted(cut)
                logging.info(
                    f"Transparent circle exclusion applied ({'start' if idx == 0 else 'end'}) on {strand.layer_name} – r={adj_radius:.1f}"
                )
    except Exception as exc:
        # logging.error(f"Error subtracting transparent circle from shadow_path of {getattr(strand, 'layer_name', 'unknown')}: {exc}")
        pass

    # ------------------------------------------------------------------
    # Manual circle-exclusion logic removed – visible circles are already
    # merged into `shadow_path` by `build_rendered_geometry`, while hidden or
    # deliberately transparent circles are *not* included in that helper.
    # Keeping extra subtraction here would create gaps and duplicated shadow
    # edges.  All related logging and special-case handling was therefore
    # deleted for clarity and correctness.
    # ------------------------------------------------------------------

    # Create a combined shadow path that will hold all intersections
    combined_shadow_path = QPainterPath()
    has_shadow_content = False
    all_shadow_paths = []
    clip_path = QPainterPath()  # Will collect the union of underlying strand areas to clip the faded shadow

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
        masked_strands_map = {}
        
        # First pass: identify all masked strands and their components
        for s in canvas.strands:
            if hasattr(s, '__class__') and s.__class__.__name__ == 'MaskedStrand':
                if hasattr(s, 'first_selected_strand') and hasattr(s, 'second_selected_strand'):
                    # Store the masked strand and its components
                    first_layer = s.first_selected_strand.layer_name if hasattr(s.first_selected_strand, 'layer_name') else None
                    second_layer = s.second_selected_strand.layer_name if hasattr(s.second_selected_strand, 'layer_name') else None
                    
                    if first_layer and second_layer:
                        masked_name = s.layer_name if hasattr(s, 'layer_name') else f"{first_layer}_{second_layer}"
                        masked_strands_map[masked_name] = {
                            'masked_strand': s,
                            'components': [first_layer, second_layer]
                        }
                        logging.info(f"Identified masked strand {masked_name} with components {first_layer} and {second_layer}")
        # logging.info(f"Checking shadow for : {strand.layer_name}")
        # Check against all other strands
        for other_strand in canvas.strands:
            # logging.info(f"Checking shadow for other strand : {other_strand.layer_name}")
            # Skip self or strands without layer names
            if other_strand is strand or not hasattr(other_strand, 'layer_name') or not other_strand.layer_name:
                continue
            # Skip hidden strands - hidden strands should not receive shadows
            if hasattr(other_strand, 'is_hidden') and other_strand.is_hidden:
                logging.info(f"Skipping shadow calculation onto hidden strand {other_strand.layer_name}")
                continue
            # Skip masked strands
            if other_strand.__class__.__name__ == 'MaskedStrand':
                continue
            # Prevent shadow calculation if the other strand is a component of the *same* masked strand
            # (This check is redundant if part_of_same_visible_mask check is working correctly, but kept for safety)
            # Check if other strand is a component of any masked strand
     
                    
            # Skip if other strand isn't in layer order
            other_layer = other_strand.layer_name
            if other_layer not in layer_order:
                # logging.warning(f"Layer {other_layer} not in layer order list, skipping shadow check")
                continue
            
            # Normal layer order rules apply
            if this_layer in layer_order and other_layer in layer_order:
                self_index = layer_order.index(this_layer)
                other_index = layer_order.index(other_layer)
                should_be_above = self_index > other_index
            
                # Only calculate shadow if this strand should be above the other
                if should_be_above:
                    
                    # Check if both strands are components of the same VISIBLE masked strand
                    part_of_same_visible_mask = False # Renamed for clarity
                    for masked_name, masked_info in masked_strands_map.items():
                        components = masked_info['components']
                        if this_layer in components and other_layer in components:
                            # Found the mask they belong to. Check if it's hidden.
                            masked_strand_obj = masked_info['masked_strand']
                            # Ensure is_hidden attribute exists and check its value
                            if hasattr(masked_strand_obj, 'is_hidden') and not masked_strand_obj.is_hidden:
                                # Mask exists and is VISIBLE, set flag and break
                                part_of_same_visible_mask = True
                                logging.info(f"Skipping shadow between components {this_layer} and {other_layer} of the same VISIBLE masked strand {masked_name}")
                                # Only skip if the mask has NO deletion rectangles (i.e. the mask fully occludes)
                                if not hasattr(masked_strand_obj, 'deletion_rectangles') or not masked_strand_obj.deletion_rectangles:
                                    continue  # Mask is solid, so no shadow needed
                                else:
                                    # Mask has holes; allow shadow calculation so it can appear through them.
                                    part_of_same_visible_mask = False  # Treat as if not masked for this purpose
                                break
                            else:
                                # Mask exists but is HIDDEN, do not skip shadow based on this mask
                                logging.info(f"Components {this_layer} and {other_layer} belong to HIDDEN masked strand {masked_name}, shadow will NOT be skipped for this reason.")
                                # Continue checking other potential masks, although unlikely

                    if part_of_same_visible_mask:
                        continue # Skip shadow calculation for this pair
                        
                    # Quick reject using bounding rectangles
                    # Calculate bounding rectangle safely
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
                            except Exception as br_e:
                                # logging.error(f"Error extending bounding rect with circle geometry for {other_layer}: {br_e}")
                                pass
                        # Inflate the rectangles by half the rendered stroke width plus max blur so that
                        # the quick bounding-box test does not miss near-tangent crossings.
                        try:
                            inflate_self = (strand.width + strand.stroke_width * 2 + max_blur_radius) / 2.0
                            inflate_other = (other_strand.width + other_strand.stroke_width * 2 + max_blur_radius) / 2.0

                            strand_rect.adjust(-inflate_self, -inflate_self, inflate_self, inflate_self)
                            other_strand_rect.adjust(-inflate_other, -inflate_other, inflate_other, inflate_other)
                        except Exception as inflate_err:
                            # Should never happen, but be robust in case a strand misses width attributes.
                            # logging.error(f"Error inflating bounding rects for quick reject: {inflate_err}")
                            pass
                        if not strand_rect.intersects(other_strand_rect):
                            logging.info(f"Bounding rectangles don't intersect, skipping shadow for {this_layer} on {other_layer}")
                            continue
                    except Exception as e:
                        # logging.warning(f"Could not get bounding rectangles for shadow check between {this_layer} and {other_layer}: {e}")
                        # Optionally continue or handle error, continuing for now
                        pass
                        
                    try:
                        # Build the full rendered geometry (body + visible circles) of the
                        # underlying strand in a single call.  This guarantees that any
                        # end-circles are already part of the path we test against, avoiding
                        # later ad-hoc unions.
                        other_stroke_path = build_rendered_geometry(other_strand)
                        
                        # Special handling for masked strands
                        # If the other strand is a MaskedStrand, use its actual mask path
                        # instead of just the stroke path to get the correct intersection area
                        if hasattr(other_strand, 'get_mask_path'):
                            try:
                                # Get the actual mask path which represents the true intersection area
                                # using our helper function
                                other_stroke_path = get_proper_masked_strand_path(other_strand)
                                logging.info(f"Using mask path for interaction with MaskedStrand {other_layer}")
                            except Exception as e:
                                # logging.error(f"Error getting mask path from MaskedStrand {other_layer}: {e}")
                                pass
                        
                        # ---------------------------------------------------------
                        # NEW LOGIC: Include visible circle geometry from the underlying
                        # strand into its stroke path so that circle areas also receive
                        # shadow from the current strand's circles.
                        # ---------------------------------------------------------
                        if hasattr(other_strand, 'has_circles') and any(other_strand.has_circles):
                            try:
                                base_circle_radius_o = other_strand.width + other_strand.stroke_width * 2
                                for oc_idx, oc_flag in enumerate(other_strand.has_circles):
                                    if not oc_flag:
                                        continue
                                    if hasattr(other_strand, 'circle_stroke_color'):
                                        oc_color = other_strand.circle_stroke_color
                                        if oc_color and oc_color.alpha() == 0:
                                            continue  # Transparent circle, ignore
                                    oc_center = other_strand.start if oc_idx == 0 else other_strand.end
                                    oc_path_tmp = QPainterPath()
                                    oc_path_tmp.addEllipse(oc_center, (base_circle_radius_o / 2) + 1, (base_circle_radius_o / 2) + 1)
                                    other_stroke_path = other_stroke_path.united(oc_path_tmp)
                            except Exception as oc_e:
                                # logging.error(f"Error adding circle geometry from {other_layer} to stroke path for circle-shadow calculation: {oc_e}")
                                pass
                        
                        # Calculate intersection
                        intersection = QPainterPath(shadow_path)
                        intersection = intersection.intersected(other_stroke_path)
                        # logging.info(f"Intersection path for {this_layer} onto {other_layer}: bounds={intersection.boundingRect()}, elements={intersection.elementCount()}")
                        
                        # Skip shadow if there's no actual intersection between the paths
                        if intersection.isEmpty():
                            logging.info(f"No actual path intersection between {this_layer} and {other_layer}, skipping shadow")
                            continue
                            
                        width_masked_strand = max_blur_radius
                        # --- NEW MASK SUBTRACTION LOGIC ---
                        # Check if any VISIBLE mask is layered ABOVE this_layer.
                        # If so, subtract the mask's area from the calculated intersection BEFORE adding it
                        # to the combined shadow path for this specific underlying strand.
                        # This ensures the mask blocks shadow *only* where it covers the specific intersection.

                        # Create a temporary path for the current intersection to modify
                        current_intersection_shadow = QPainterPath(intersection)

                        if not current_intersection_shadow.isEmpty(): # Check if there's any shadow intersection to modify
                            for mask_name_sub, mask_info_sub in masked_strands_map.items():
                                mask_strand_sub = mask_info_sub['masked_strand']
                                mask_layer_sub = mask_name_sub # Assuming mask_name is the layer name

                                # Ensure mask is visible and its layer name is in the order
                                if (hasattr(mask_strand_sub, 'is_hidden') and not mask_strand_sub.is_hidden and
                                        mask_layer_sub in layer_order):

                                    mask_index_sub = layer_order.index(mask_layer_sub)

                                    # --------------------------------------------------
                                    # Fast-path: use (and cache) the mask's pre-computed
                                    # shadow-blocking geometry.  If we can subtract the
                                    # blocker right away we can skip all of the legacy
                                    # QPainterPath maths below.
                                    # --------------------------------------------------
                                    fast_blocker = get_shadow_blocker_path(mask_strand_sub, max_blur_radius)
                                    if not fast_blocker.isEmpty():
                                        current_intersection_shadow = current_intersection_shadow.subtracted(fast_blocker)
                                        # Nothing left to do for this mask in the current
                                        # intersection – jump to the next mask.
                                        continue
                                    
                                    try:
                                        # Early check: First verify if the mask even intersects with the underlying layer
                                        # Get the mask's actual path to check intersection
                                        if hasattr(mask_strand_sub, 'get_mask_path'):
                                            mask_actual_path = mask_strand_sub.get_mask_path()
                                            if mask_actual_path.isEmpty() or not mask_actual_path.intersects(other_stroke_path):
                                                logging.info(f"Mask '{mask_layer_sub}' does not intersect with underlying layer '{other_layer}', skipping shadow subtraction entirely")
                                                continue
                                        
                                        # IMPROVED: Use the mask's actual rendered path (which already respects deletions)
                                        # and extend it by the shadow blur radius for accurate shadow blocking.
                                        # This approach is simpler and more accurate than manually calculating intersections.
                                        subtraction_path = QPainterPath()
                                        
                                        # Get the mask's actual path that already includes all deletions
                                        if hasattr(mask_strand_sub, 'get_mask_path'):
                                            try:
                                                # Get the base mask path which already respects deletion rectangles
                                                base_mask_path = mask_strand_sub.get_mask_path()
                                                
                                                if not base_mask_path.isEmpty():
                                                    # Extend the mask path by the shadow blur radius to create
                                                    # the shadow blocking area. This simulates how the shadow
                                                    # would be blocked by the mask's blur effect.
                                                    stroker = QPainterPathStroker()
                                                    # Extend by blur radius to match shadow rendering
                                                    stroker.setWidth(max_blur_radius)
                                                    stroker.setJoinStyle(Qt.RoundJoin)  # Smoother joins for blur simulation
                                                    stroker.setCapStyle(Qt.RoundCap)   # Smoother caps for blur simulation
                                                    
                                                    # Create the extended path for shadow blocking
                                                    extended_mask = stroker.createStroke(base_mask_path)
                                                    
                                                    # Unite the original mask with its extended border to create
                                                    # the complete shadow blocking area
                                                    subtraction_path = base_mask_path.united(extended_mask)
                                                    
                                                    logging.info(f"Created improved subtraction path using mask's actual geometry for '{mask_layer_sub}'")
                                                else:
                                                    logging.info(f"Empty mask path for '{mask_layer_sub}', skipping shadow subtraction")
                                                    
                                            except Exception as mask_path_err:
                                                logging.error(f"Error getting mask path for '{mask_layer_sub}': {mask_path_err}")
                                                # Fallback to original approach if mask path fails
                                                subtraction_path = QPainterPath()
                                        else:
                                            # Fallback: if no get_mask_path method, use the original intersection approach
                                            # but without separate deletion rectangle handling since they should already be in the mask
                                            if hasattr(mask_strand_sub, 'first_selected_strand') and mask_strand_sub.first_selected_strand and \
                                               hasattr(mask_strand_sub, 'second_selected_strand') and mask_strand_sub.second_selected_strand:

                                                s1 = mask_strand_sub.first_selected_strand
                                                s2 = mask_strand_sub.second_selected_strand

                                                # Calculate base component paths
                                                stroker1 = QPainterPathStroker()
                                                stroker1.setWidth(s1.width + s1.stroke_width * 2)
                                                stroker1.setJoinStyle(Qt.MiterJoin)
                                                stroker1.setCapStyle(Qt.FlatCap)
                                                path1 = stroker1.createStroke(s1.get_path())

                                                stroker2 = QPainterPathStroker()
                                                stroker2.setWidth(s2.width + s2.stroke_width * 2)
                                                stroker2.setJoinStyle(Qt.MiterJoin)
                                                stroker2.setCapStyle(Qt.FlatCap)
                                                path2 = stroker2.createStroke(s2.get_path())

                                                # Get intersection and extend by blur radius
                                                base_intersection = path1.intersected(path2)
                                                if not base_intersection.isEmpty():
                                                    stroker = QPainterPathStroker()
                                                    stroker.setWidth(max_blur_radius * 2)
                                                    stroker.setJoinStyle(Qt.RoundJoin)
                                                    stroker.setCapStyle(Qt.RoundCap)
                                                    extended_intersection = stroker.createStroke(base_intersection)
                                                    subtraction_path = base_intersection.united(extended_intersection)
                                                    
                                                logging.info(f"Used fallback intersection approach for '{mask_layer_sub}'")

                                        if not subtraction_path.isEmpty():
                                            # Check if the mask actually intersects with the underlying layer Y
                                            # Only subtract if there's an actual intersection
                                            mask_intersects_underlying = subtraction_path.intersects(other_stroke_path)
                                            
                                            if mask_intersects_underlying:
                                                original_rect_intersect = current_intersection_shadow.boundingRect()
                                                current_intersection_shadow = current_intersection_shadow.subtracted(subtraction_path) # Apply to current intersection
                                                new_rect_intersect = current_intersection_shadow.boundingRect()

                                                original_area_intersect = original_rect_intersect.width() * original_rect_intersect.height()
                                                new_area_intersect = new_rect_intersect.width() * new_rect_intersect.height()

                                                if abs(original_area_intersect - new_area_intersect) > 1e-6 or \
                                                   (original_area_intersect > 1e-6 and current_intersection_shadow.isEmpty()):
                                                    logging.info(f"Subtracted overlying mask '{mask_layer_sub}' (using its area) from shadow intersection of '{this_layer}' on '{other_layer}'")
                                            else:
                                                logging.info(f"Mask '{mask_layer_sub}' does not intersect with underlying layer '{other_layer}', skipping shadow subtraction")
                                            # (duplicate else branch removed)


                                    except Exception as e:
                                        # logging.error(f"Error calculating or subtracting overlying mask '{mask_layer_sub}' from shadow intersection: {e}")
                                        pass
                        # --- END MASK SUBTRACTION FOR THIS INTERSECTION ---


                        # Apply side line exclusion for both casting and receiving strands
                        if not current_intersection_shadow.isEmpty():
                            # Get side line exclusion paths for both strands
                            try:
                                # Exclusion for the casting strand (this strand) - auto-calculate multiplier
                                casting_exclusion = get_side_line_exclusion_path(strand)
                                if not casting_exclusion.isEmpty():
                                    current_intersection_shadow = current_intersection_shadow.subtracted(casting_exclusion)
                                    logging.info(f"Applied side line exclusion for casting strand {this_layer}")
                                
                                # Exclusion for the receiving strand (other strand) - auto-calculate multiplier
                                receiving_exclusion = get_side_line_exclusion_path(other_strand)
                                if not receiving_exclusion.isEmpty():
                                    current_intersection_shadow = current_intersection_shadow.subtracted(receiving_exclusion)
                                    logging.info(f"Applied side line exclusion for receiving strand {other_layer}")
                                    
                            except Exception as exclusion_err:
                                logging.error(f"Error applying side line exclusions: {exclusion_err}")
                        
                        # Only add the (potentially modified) intersection if it's still not empty
                        if not current_intersection_shadow.isEmpty():
                            # Add the calculated intersection area to the path that will be drawn
                            # as the final shadow for this strand. Also, expand the clipping path
                            # to include the area of the underlying strand, ensuring the faded
                            # shadow effect only renders where an underlying strand exists.
                            # Include the underlying strand area in the clip path so the shadow can't draw where there is no strand
                            if clip_path.isEmpty():
                                clip_path = other_stroke_path
                            else:
                                clip_path = clip_path.united(other_stroke_path)
                            # Add this intersection to the combined path
                            if has_shadow_content:
                                combined_shadow_path = combined_shadow_path.united(current_intersection_shadow)
                            else:
                                combined_shadow_path = current_intersection_shadow
                                has_shadow_content = True
                                
                            # logging.info(f"Added shadow from {this_layer} onto {other_layer} to combined path")
                        else:
                            logging.info(f"No intersection between {this_layer} and {other_layer} paths")
                    except Exception as e:
                        # logging.error(f"Error calculating strand shadow: {e}")
                        pass
                else:
                    logging.info(f"Layer {this_layer} should NOT be above {other_layer}, no shadow calculated")
        
        # Draw the combined shadow path once
        if has_shadow_content and not combined_shadow_path.isEmpty():
            # Draw shadow
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color_to_use))
            
            # IMPORTANT: Use SourceOver composition mode to prevent shadow darkening
            old_composition = painter.compositionMode()
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            #painter.drawPath(combined_shadow_path)
            painter.setCompositionMode(old_composition)
            
            # Initialize shadow_paths and all_shadow_paths
            all_shadow_paths = [combined_shadow_path]
            
            # logging.info(f"Drew unified shadow path for strand {this_layer}")
    else:
        # If no layer manager available, draw simple shadow
        # This is a fallback method
        logging.info("No layer state manager available for shadow drawing")
        # Still use a unified approach even in fallback case
        if not shadow_path.isEmpty():
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color_to_use))
            #painter.drawPath(shadow_path)
            
            # Initialize shadow_paths and add shadow_path to all_shadow_paths
            all_shadow_paths = [shadow_path]
            clip_path = shadow_path  # In fallback, clip to the simple shadow path
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
        body_stroker.setJoinStyle(Qt.MiterJoin)
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
            if hasattr(other_strand, 'is_hidden') and other_strand.is_hidden:
                logging.info(f"Skipping circle shadow calculation onto hidden strand {other_strand.layer_name}")
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
                        logging.info(f"Using mask path for interaction with MaskedStrand {other_layer}")
                    except Exception as ee:
                        # logging.error(f"Error getting mask path for {other_layer}: {ee}")
                        pass

                # ---------------------------------------------------------
                # NEW LOGIC: Include visible circle geometry from the underlying
                # strand into its stroke path so that circle areas also receive
                # shadow from the current strand's circles.
                # ---------------------------------------------------------
                if hasattr(other_strand, 'has_circles') and any(other_strand.has_circles):
                    try:
                        base_circle_radius_o = other_strand.width + other_strand.stroke_width * 2
                        for oc_idx, oc_flag in enumerate(other_strand.has_circles):
                            if not oc_flag:
                                continue
                            if hasattr(other_strand, 'circle_stroke_color'):
                                oc_color = other_strand.circle_stroke_color
                                if oc_color and oc_color.alpha() == 0:
                                    continue  # Transparent circle, ignore
                            oc_center = other_strand.start if oc_idx == 0 else other_strand.end
                            oc_path_tmp = QPainterPath()
                            oc_path_tmp.addEllipse(oc_center, (base_circle_radius_o / 2) + 1, (base_circle_radius_o / 2) + 1)
                            other_stroke_path = other_stroke_path.united(oc_path_tmp)
                    except Exception as oc_e:
                        logging.error(f"Error adding circle geometry from {other_layer} to stroke path for circle-shadow calculation: {oc_e}")
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
                    candidate = final_circle_path.subtracted(strand_body_path)
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

                        if (hasattr(mask_strand_sub_c, 'is_hidden') and not mask_strand_sub_c.is_hidden and
                                mask_layer_sub_c in layer_order):

                            mask_index_sub_c = layer_order.index(mask_layer_sub_c)

                            # Check if mask is above the *casting strand* (this_layer)
                            if mask_index_sub_c > self_index:
                                try:
                                    # Early check: First verify if the mask even intersects with the underlying layer
                                    if hasattr(mask_strand_sub_c, 'get_mask_path'):
                                        mask_actual_path_c = mask_strand_sub_c.get_mask_path()
                                        if mask_actual_path_c.isEmpty() or not mask_actual_path_c.intersects(other_stroke_path):
                                            logging.info(f"Mask '{mask_layer_sub_c}' does not intersect with underlying layer '{other_layer}', skipping circle shadow subtraction entirely")
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
                                        if hasattr(mask_strand_sub_c, 'deletion_rectangles') and mask_strand_sub_c.deletion_rectangles:
                                            try:
                                                for del_rect in mask_strand_sub_c.deletion_rectangles:
                                                    del_path = QPainterPath()
                                                    # Support QRectF directly
                                                    if isinstance(del_rect, QRectF):
                                                        del_path.addRect(del_rect)
                                                    # Support dict with corner coordinates
                                                    elif isinstance(del_rect, dict) and all(k in del_rect for k in ("top_left", "top_right", "bottom_left", "bottom_right")):
                                                        tl = QPointF(*del_rect["top_left"])
                                                        tr = QPointF(*del_rect["top_right"])
                                                        br = QPointF(*del_rect["bottom_right"])
                                                        bl = QPointF(*del_rect["bottom_left"])
                                                        del_path.moveTo(tl)
                                                        del_path.lineTo(tr)
                                                        del_path.lineTo(br)
                                                        del_path.lineTo(bl)
                                                        del_path.closeSubpath()
                                                    # Support axis-aligned rectangle dict
                                                    elif all(k in del_rect for k in ("x", "y", "width", "height")):
                                                        del_path.addRect(QRectF(del_rect["x"], del_rect["y"], del_rect["width"], del_rect["height"]))

                                                    if not del_path.isEmpty():
                                                        subtraction_path_c = subtraction_path_c.subtracted(del_path)
                                            except Exception as del_ex:
                                                # logging.error(f"Error applying deletion rectangles to mask subtraction path for '{mask_layer_sub_c}': {del_ex}")
                                                pass

                                    if not subtraction_path_c.isEmpty():
                                        # Check if the mask actually intersects with the underlying layer
                                        mask_intersects_underlying_c = subtraction_path_c.intersects(other_stroke_path)
                                        
                                        if mask_intersects_underlying_c:
                                            intersection = intersection.subtracted(subtraction_path_c)
                                            # Basic logging for circle shadow subtraction
                                            if intersection.isEmpty(): # Check if subtraction removed everything
                                                 logging.info(f"Subtracted mask '{mask_layer_sub_c}' completely removed circle shadow intersection of '{this_layer}' on '{other_layer}'")
                                        else:
                                            logging.info(f"Mask '{mask_layer_sub_c}' does not intersect with underlying layer '{other_layer}', skipping circle shadow subtraction")

                                except Exception as e_c:
                                    # logging.error(f"Error subtracting mask '{mask_layer_sub_c}' from circle shadow intersection: {e_c}")
                                    pass
                # --- End Mask Subtraction ---

                if not intersection.isEmpty():
                    all_shadow_paths.append(intersection)
                    # Expand clip path as well
                    if clip_path.isEmpty():
                        clip_path = other_stroke_path
                    else:
                        clip_path = clip_path.united(other_stroke_path)
                    logging.info(f"Added circle shadow intersection for {strand.layer_name} onto {other_layer}")

    elif circle_shadow_paths:
        # Fallback: no layer manager; simply subtract body and add whole circle shadow path
        for circle_path, _ in circle_shadow_paths:
            final_circle_path = QPainterPath(circle_path)
            if not strand_body_path.isEmpty():
                candidate = final_circle_path.subtracted(strand_body_path)
                if not candidate.isEmpty():
                    final_circle_path = candidate

            all_shadow_paths.append(final_circle_path)
            if clip_path.isEmpty():
                clip_path = final_circle_path
            else:
                clip_path = clip_path.united(final_circle_path)
            logging.info(f"Added fallback circle shadow path for {strand.layer_name}")

    # ----------------------------------------------------------
    # Draw all shadow paths at once using the faded effect (existing logic below)
    # ----------------------------------------------------------
    # Draw all shadow paths at once using the faded effect
    # logging.info(f"Shadow paths for strand {getattr(strand, 'layer_name', 'unknown')}: count={len(all_shadow_paths)}, empty_paths={sum(1 for p in all_shadow_paths if p.isEmpty())}, non_empty={sum(1 for p in all_shadow_paths if not p.isEmpty())}")

    if all_shadow_paths and logging.getLogger().isEnabledFor(logging.DEBUG):
        for i, path in enumerate(all_shadow_paths):
            if not path.isEmpty():
                logging.debug(f"  Shadow path #{i+1}: bounds={path.boundingRect()}, elements={path.elementCount()}")
    if all_shadow_paths:
        # Combine all paths into one for the fading effect
        # (all_shadow_paths should contain only one path now, either combined intersections or fallback)
        if len(all_shadow_paths) == 1:
            total_shadow_path = all_shadow_paths[0]
        elif len(all_shadow_paths) > 1:
             # This case might happen if the layer manager logic failed but fallback succeeded partially
             # Let's unite them just in case, though ideally it should be one path.
             # logging.warning(f"Expected one shadow path but found {len(all_shadow_paths)}, uniting them.")
             total_shadow_path = QPainterPath()
             for p in all_shadow_paths:
                 if total_shadow_path.isEmpty():
                     total_shadow_path = p
                 else:
                     total_shadow_path = total_shadow_path.united(p)
        else:
             # This means all_shadow_paths was empty, log and return
             # logging.warning(f"No shadow paths in all_shadow_paths for strand {strand.layer_name}, skipping draw.")
             return # Nothing to draw


        # Reduced high-frequency logging for performance during moves
        # logging.info(f"Drawing faded shadow for strand {strand.layer_name}")
        # Draw the combined path with a faded edge effect
        base_color = color_to_use
        base_alpha = base_color.alpha()

        # Prepare painter with clipping so the shadow cannot appear where no underlying strand exists
        painter.save()
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
            # --- Wrap stroking in try...except ---
            try:
                for i in range(num_steps):
                    # Alpha fades from base_alpha down towards zero
                    # Distribute alpha across steps for smoother look
                    # Adjusted alpha calculation slightly for potentially better distribution
                    progress = (float(num_steps - i) / num_steps)
                    current_alpha = base_alpha * progress*(1.0 / num_steps) * 2.0 # Exponential decay, adjust multiplier

                    # Width increases
                    current_width = max_blur_radius * (float(i + 1) / num_steps)

                    pen_color = QColor(base_color.red(), base_color.green(), base_color.blue(), max(0, min(255, int(current_alpha))))
                    pen = QPen(pen_color)
                    pen.setWidthF(current_width)
                    pen.setCapStyle(Qt.RoundCap) # Use RoundCap/Join for softer edges
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
    # Check if this is a masked strand
    if hasattr(strand, 'get_mask_path'):
        try:
            # Get the actual mask path which includes all deletions
            mask_path = strand.get_mask_path()
            if not mask_path.isEmpty():
                logging.info(f"Using mask path for MaskedStrand {strand.layer_name if hasattr(strand, 'layer_name') else 'unknown'}")
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
            logging.info(f"Auto-calculated exclusion width={shadow_width} for strand width={strand_width}")
        else:
            # Calculate exclusion width based on provided multiplier
            shadow_width = getattr(strand, 'width', 10) * shadow_width_multiplier
        
        # Create exclusion area exactly at the start point
        if hasattr(strand, 'start') and hasattr(strand, 'start_line_start') and hasattr(strand, 'start_line_end'):
            # Use the actual side line positions to create a precise exclusion zone
            start_exclusion = QPainterPath()
            start_exclusion.moveTo(strand.start_line_start)
            start_exclusion.lineTo(strand.start_line_end)
            
            # Extend the exclusion area perpendicular to the side line by shadow_width
            line_vec = strand.start_line_end - strand.start_line_start
            line_length = math.sqrt(line_vec.x()**2 + line_vec.y()**2)
            
            if line_length > 0:
                # Normalize line vector
                norm_line = QPointF(line_vec.x() / line_length, line_vec.y() / line_length)
                # Perpendicular vector pointing away from strand
                perp_vec = QPointF(-norm_line.y(), norm_line.x())
                
                # Determine which direction extends BEYOND the strand endpoint
                # Calculate direction from strand end toward strand start to find the "forward" direction
                strand_direction = strand.end - strand.start
                strand_length = math.sqrt(strand_direction.x()**2 + strand_direction.y()**2)
                
                if strand_length > 0:
                    # Normalize strand direction vector
                    norm_strand_dir = QPointF(strand_direction.x() / strand_length, strand_direction.y() / strand_length)
                    
                    # At the start point, we want to extend in the OPPOSITE direction (beyond the start)
                    beyond_start_vec = QPointF(-norm_strand_dir.x(), -norm_strand_dir.y())
                else:
                    # Fallback: extend perpendicular to side line
                    beyond_start_vec = perp_vec
                
                # Create wider rectangle extending BEYOND the start point to cover all shadow width
                # Scale the extended width based on strand thickness
                stroke_width = getattr(strand, 'stroke_width', 2)
                total_strand_width = strand.width + stroke_width * 2
                # Simple scaling: wider strands need proportionally wider exclusion zones
                extended_width = total_strand_width + shadow_width
                half_extended_width = extended_width / 2.0
                
                # Create corners that extend both along the strand direction AND perpendicular to cover full shadow
                corner3 = QPointF(
                    strand.start_line_end.x() + beyond_start_vec.x() * shadow_width + norm_line.x() * half_extended_width,
                    strand.start_line_end.y() + beyond_start_vec.y() * shadow_width + norm_line.y() * half_extended_width
                )
                corner4 = QPointF(
                    strand.start_line_start.x() + beyond_start_vec.x() * shadow_width - norm_line.x() * half_extended_width,
                    strand.start_line_start.y() + beyond_start_vec.y() * shadow_width - norm_line.y() * half_extended_width
                )
                
                start_exclusion.lineTo(corner3)
                start_exclusion.lineTo(corner4)
                start_exclusion.closeSubpath()
                
                exclusion_path = exclusion_path.united(start_exclusion)
        
        # Create exclusion area exactly at the end point
        if hasattr(strand, 'end') and hasattr(strand, 'end_line_start') and hasattr(strand, 'end_line_end'):
            # Use the actual side line positions to create a precise exclusion zone
            end_exclusion = QPainterPath()
            end_exclusion.moveTo(strand.end_line_start)
            end_exclusion.lineTo(strand.end_line_end)
            
            # Extend the exclusion area perpendicular to the side line by shadow_width
            line_vec = strand.end_line_end - strand.end_line_start
            line_length = math.sqrt(line_vec.x()**2 + line_vec.y()**2)
            
            if line_length > 0:
                # Normalize line vector
                norm_line = QPointF(line_vec.x() / line_length, line_vec.y() / line_length)
                # Perpendicular vector pointing away from strand
                perp_vec = QPointF(-norm_line.y(), norm_line.x())
                
                # Determine which direction extends BEYOND the strand endpoint
                # Calculate direction from strand start toward strand end to find the "forward" direction
                strand_direction = strand.end - strand.start
                strand_length = math.sqrt(strand_direction.x()**2 + strand_direction.y()**2)
                
                if strand_length > 0:
                    # Normalize strand direction vector
                    norm_strand_dir = QPointF(strand_direction.x() / strand_length, strand_direction.y() / strand_length)
                    
                    # At the end point, we want to extend in the SAME direction (beyond the end)
                    beyond_end_vec = norm_strand_dir
                else:
                    # Fallback: extend perpendicular to side line
                    beyond_end_vec = perp_vec
                
                # Create wider rectangle extending BEYOND the end point to cover all shadow width
                # Scale the extended width based on strand thickness
                stroke_width = getattr(strand, 'stroke_width', 2)
                total_strand_width = strand.width + stroke_width * 2
                # Simple scaling: wider strands need proportionally wider exclusion zones
                extended_width = total_strand_width + shadow_width
                half_extended_width = extended_width / 2.0
                
                # Create corners that extend both along the strand direction AND perpendicular to cover full shadow
                corner3 = QPointF(
                    strand.end_line_end.x() + beyond_end_vec.x() * shadow_width + norm_line.x() * half_extended_width,
                    strand.end_line_end.y() + beyond_end_vec.y() * shadow_width + norm_line.y() * half_extended_width
                )
                corner4 = QPointF(
                    strand.end_line_start.x() + beyond_end_vec.x() * shadow_width - norm_line.x() * half_extended_width,
                    strand.end_line_start.y() + beyond_end_vec.y() * shadow_width - norm_line.y() * half_extended_width
                )
                
                end_exclusion.lineTo(corner3)
                end_exclusion.lineTo(corner4)
                end_exclusion.closeSubpath()
                
                exclusion_path = exclusion_path.united(end_exclusion)
        
        logging.info(f"Created end-point exclusion path for strand {getattr(strand, 'layer_name', 'unknown')} with bounds={exclusion_path.boundingRect()}")
        
    except Exception as e:
        logging.error(f"Error creating end-point exclusion path for strand {getattr(strand, 'layer_name', 'unknown')}: {e}")
    
    return exclusion_path

def build_rendered_geometry(strand):
    """
    Returns the *visual* geometry of a strand as a single QPainterPath.

    The path includes:
      • The stroked body path (taking `width` & `stroke_width` into account)
      • Every *visible* end-circle (if `has_circles` is set and the circle
        stroke colour is not fully transparent).

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
        stroker.setJoinStyle(Qt.MiterJoin)
        stroker.setCapStyle(Qt.FlatCap)
        result_path = stroker.createStroke(body_source)

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
                radius = (strand.width + strand.stroke_width * 2) / 2.0
                for idx, enabled in enumerate(strand.has_circles):
                    if not enabled:
                        continue
                    centre = strand.start if idx == 0 else strand.end
                    circle_path = QPainterPath()
                    circle_path.addEllipse(centre, radius, radius)
                    result_path = result_path.united(circle_path)

        return result_path
    except Exception as e:
        # logging.error(
        #     f"build_rendered_geometry: failed for {getattr(strand, 'layer_name', 'unknown')} – {e}"
        # )
        pass
        return QPainterPath()

def build_shadow_geometry(strand, fixed_shadow_extension=30.0):
    """
    Returns shadow geometry that extends a fixed distance beyond the strand edge,
    ensuring consistent shadow length regardless of strand thickness.
    
    Args:
        strand: The strand to create shadow geometry for
        fixed_shadow_extension: Fixed distance (in pixels) to extend shadow beyond strand edge
        
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
        stroker.setJoinStyle(Qt.MiterJoin)
        stroker.setCapStyle(Qt.FlatCap)
        result_path = stroker.createStroke(body_source)

        # Add visible circles with same fixed extension
        if hasattr(strand, 'has_circles') and any(strand.has_circles):
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
                    centre = strand.start if idx == 0 else strand.end
                    circle_path = QPainterPath()
                    circle_path.addEllipse(centre, radius, radius)
                    result_path = result_path.united(circle_path)

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
        base_path = mask_strand.get_mask_path() if hasattr(mask_strand, "get_mask_path") else QPainterPath()
        if base_path.isEmpty():
            cache[key] = QPainterPath()
            return cache[key]

        stroker = QPainterPathStroker()
        stroker.setWidth(blur_px)
        stroker.setJoinStyle(Qt.RoundJoin)
        stroker.setCapStyle(Qt.RoundCap)
        extended = stroker.createStroke(base_path)
        blocker = base_path.united(extended)

        cache[key] = blocker
        return blocker
    except Exception:
        # On any error just return an empty path so we never block painting.
        return QPainterPath()

