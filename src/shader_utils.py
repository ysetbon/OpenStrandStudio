import logging
from PyQt5.QtGui import QPainterPath, QPainterPathStroker, QPen, QBrush, QColor, QPainter
from PyQt5.QtCore import Qt, QRectF, QPointF



def draw_mask_strand_shadow(
    painter,
    first_path: QPainterPath,
    second_path: QPainterPath,
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

    if intersection_path.isEmpty():
        logging.warning("draw_mask_strand_shadow: intersection path is empty – nothing to draw")
        return

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
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
    
    # ------------------------------------------------------------------
    # 1) Fill the solid shadow core.
    # ------------------------------------------------------------------
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(base_color))
    painter.drawPath(intersection_path)
    painter.setBrush(Qt.NoBrush)

    # ------------------------------------------------------------------
    # 2) Add a blurred / faded edge by repeatedly stroking the path with
    #    increasing width and decreasing alpha.
    # ------------------------------------------------------------------
    # We allow the blurred edge to extend anywhere the ORIGINAL component
    # paths exist (their union) so that the blur is not clipped too early.
    union_path = QPainterPath(first_path)
    union_path.addPath(second_path)
    painter.setClipPath(union_path)
    painter.setClipPath(second_path)
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
        painter.strokePath(intersection_path, pen)

    painter.restore()
    logging.info(
        f"draw_mask_strand_shadow: rendered shadow (steps={num_steps}, blur={max_blur_radius})"
    )

def draw_circle_shadow(painter, strand, shadow_color=None):
    """
    Draw shadow for a circle at the start or end of a strand.
    """
    pass

def draw_strand_shadow(painter, strand, shadow_color=None, num_steps=3, max_blur_radius=29.99):
    """
    Draw shadow for a strand that overlaps with other strands.
    This function should be called before drawing the strand itself.
    
    Args:
        painter: The QPainter to draw with
        strand: The strand to draw shadow for
        shadow_color: Custom shadow color or None to use strand's shadow_color
    """
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
    
    logging.info(f"Drawing shadow for strand {strand.layer_name} with color {color_to_use.name()} alpha={color_to_use.alpha()}")
    
    # Normal strand handling - use helper function to get proper path for any type of strand
    path = get_proper_masked_strand_path(strand)
    shadow_width = max_blur_radius
    # Create base shadow path without circles first
    shadow_stroker = QPainterPathStroker()
    shadow_stroker.setWidth(strand.width + strand.stroke_width * 2)
    shadow_stroker.setJoinStyle(Qt.MiterJoin)
    shadow_stroker.setCapStyle(Qt.FlatCap)
    shadow_path = shadow_stroker.createStroke(path)
        
    # Check if this strand has transparent circles that should not get shadows
    has_transparent_circles = False
    if hasattr(strand, 'circle_stroke_color'):
        circle_color = strand.circle_stroke_color
        # Check if color exists and has zero alpha (fully transparent)
        if circle_color and circle_color.alpha() == 0:
            has_transparent_circles = True
            
    # If strand has circles at either end and they are transparent, 
    # we need to exclude circle areas from the shadow
    if has_transparent_circles and hasattr(strand, 'has_circles'):
        # For each circle that's enabled, remove its area from shadow
        for idx, has_circle in enumerate(strand.has_circles):
            if has_circle:
                # Determine which point (start or end) to exclude
                point = strand.start if idx == 0 else strand.end
                
                # Create a circle path for exclusion - use larger diameter for complete exclusion
                # Add extra pixels to the radius to ensure complete removal of the circle shadow
                circle_radius = strand.width + strand.stroke_width * 2 + 10  # Increased from 10 to 15
                exclude_circle = QPainterPath()
                exclude_circle.addEllipse(point, circle_radius/2, circle_radius/2)
                
                # Subtract the circle area from the shadow path
                shadow_path = shadow_path.subtracted(exclude_circle)
                logging.info(f"Excluded transparent circle at {'start' if idx == 0 else 'end'} point for {strand.layer_name}: exclude path bounds={exclude_circle.boundingRect()}")

    # Only exclude hidden circle areas when the strand truly has circles
    if hasattr(strand, 'has_circles') and any(strand.has_circles):
        # Determine a reasonable radius for exclusion – use the same base radius that is
        # employed when *adding* circle shadows below (width + stroke_width * 2).
        hidden_circle_radius = strand.width + strand.stroke_width * 2 + 10  # +10 for safe margin
        for idx, circle_visible in enumerate(strand.has_circles):
            # Skip circles that are still visible – we only care about hidden ones here
            if circle_visible:
                continue
            # Safety: also respect manual overrides if present (it should already be reflected
            # in has_circles but we double-check for robustness).
            if hasattr(strand, 'manual_circle_visibility') and isinstance(strand.manual_circle_visibility, (list, tuple)):
                manual_override = strand.manual_circle_visibility[idx] if idx < len(strand.manual_circle_visibility) else None
                # If the manual override explicitly keeps the circle visible, skip exclusion
                if manual_override is True:
                    continue
            # Determine circle center (start or end point)
            circle_center = strand.start if idx == 0 else strand.end
            exclude_circle_path = QPainterPath()
            exclude_circle_path.addEllipse(circle_center, hidden_circle_radius / 2, hidden_circle_radius / 2)
            # Subtract the circle area from the shadow path if it intersects
            if 'shadow_path' in locals() and not shadow_path.isEmpty():
                shadow_path = shadow_path.subtracted(exclude_circle_path)
                logging.info(f"Excluded hidden circle at {'start' if idx == 0 else 'end'} for {strand.layer_name}: exclude path bounds={exclude_circle_path.boundingRect()}")
            try:
                if 'shadow_path' in locals() and not shadow_path.isEmpty():
                    shadow_path = shadow_path.subtracted(exclude_circle_path)
                    logging.info(f"Excluded hidden circle at {'start' if idx == 0 else 'end'} for {strand.layer_name}: exclude path bounds={exclude_circle_path.boundingRect()}")
            except Exception as e_ex:
                logging.error(f"Error subtracting hidden circle (index {idx}) from shadow path of {strand.layer_name}: {e_ex}")

    # Special case for AttachedStrand
    if strand.__class__.__name__ == 'AttachedStrand':
        # Check for transparent circles at the start
        has_transparent_start_circle = False
        if hasattr(strand, 'circle_stroke_color'):
            circle_color = strand.circle_stroke_color
            if circle_color and circle_color.alpha() == 0:
                has_transparent_start_circle = True
        
        # Special handling for end circle if strand has_circles[1] is True (has end circle)
        if hasattr(strand, 'has_circles') and len(strand.has_circles) > 1 and strand.has_circles[1]:
            # Check if end circle should be transparent too (use same transparency as start)
            if has_transparent_start_circle:
                # Exclude end circle from shadow with increased radius
                circle_radius = strand.width + strand.stroke_width * 2 + 10  # Increased from 10 to 15
                exclude_end_circle = QPainterPath()
                exclude_end_circle.addEllipse(strand.end, circle_radius/2, circle_radius/2)
                shadow_path = shadow_path.subtracted(exclude_end_circle)
                logging.info(f"Excluded transparent end circle for AttachedStrand: {strand.layer_name}")
            else:
                # IMPORTANT: Do NOT add end circle to shadow - this will be handled by draw_circle_shadow
                logging.info(f"End circle shadow for AttachedStrand will be handled by draw_circle_shadow")
                
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
        logging.info(f"Current layer order: {layer_order}")
        logging.info(f"Current strand being processed: {this_layer}")
        logging.info(f"Current connections: {connections}")
        
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
        logging.info(f"Checking shadow for : {strand.layer_name}")
        # Check against all other strands
        for other_strand in canvas.strands:
            logging.info(f"Checking shadow for other strand : {other_strand.layer_name}")
            # Skip self or strands without layer names
            if other_strand is strand or not hasattr(other_strand, 'layer_name') or not other_strand.layer_name:
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
                logging.warning(f"Layer {other_layer} not in layer order list, skipping shadow check")
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
                                logging.error(f"Error extending bounding rect with circle geometry for {other_layer}: {br_e}")
                        if not strand_rect.intersects(other_strand_rect):
                            logging.info(f"Bounding rectangles don't intersect, skipping shadow for {this_layer} on {other_layer}")
                            continue
                    except Exception as e:
                        logging.warning(f"Could not get bounding rectangles for shadow check between {this_layer} and {other_layer}: {e}")
                        # Optionally continue or handle error, continuing for now
                        
                    try:
                        # Get other strand's path
                        other_path = other_strand.get_path()
                        other_stroker = QPainterPathStroker()
                        other_stroker.setWidth(other_strand.width + other_strand.stroke_width * 2)
                        other_stroker.setJoinStyle(Qt.MiterJoin)
                        other_stroker.setCapStyle(Qt.FlatCap)
                        other_stroke_path = other_stroker.createStroke(other_path)
                        
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
                                logging.error(f"Error getting mask path from MaskedStrand {other_layer}: {e}")
                        
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
                        
                        # Calculate intersection
                        intersection = QPainterPath(shadow_path)
                        intersection = intersection.intersected(other_stroke_path)
                        logging.info(f"Intersection path for {this_layer} onto {other_layer}: bounds={intersection.boundingRect()}, elements={intersection.elementCount()}")
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

                                    # Only subtract the mask if it is physically above the casting strand.
                                    # We removed the check `and (other_layer in mask_info_sub['components'] or this_layer in mask_info_sub['components'])`
                                    # so that *any* mask above blocks the shadow in its area.
                                    if mask_index_sub > self_index:

                                        try:
                                            # Calculate the path for subtraction by simulating the mask's "blurred" area.
                                            # We use the intersection of the mask's components, but stroked with max_blur_radius
                                            # added, similar to shadow clipping logic.
                                            subtraction_path = QPainterPath()
                                            if hasattr(mask_strand_sub, 'first_selected_strand') and mask_strand_sub.first_selected_strand and \
                                               hasattr(mask_strand_sub, 'second_selected_strand') and mask_strand_sub.second_selected_strand:

                                                s1 = mask_strand_sub.first_selected_strand
                                                s2 = mask_strand_sub.second_selected_strand

                                                # Calculate widened strokes for both components
                                                stroker1 = QPainterPathStroker()
                                                # Add max_blur_radius to simulate the blurred area
                                                stroker1.setWidth(s1.width + s1.stroke_width * 2 +max_blur_radius)
                                                stroker1.setJoinStyle(Qt.MiterJoin)
                                                stroker1.setCapStyle(Qt.FlatCap)
                                                path1 = stroker1.createStroke(s1.get_path())

                                                stroker2 = QPainterPathStroker()
                                                # Add max_blur_radius to simulate the blurred area
                                                stroker2.setWidth(s2.width + s2.stroke_width * 2 +max_blur_radius)
                                                stroker2.setJoinStyle(Qt.MiterJoin)
                                                stroker2.setCapStyle(Qt.FlatCap)
                                                path2 = stroker2.createStroke(s2.get_path())

                                                # Use the intersection of these widened paths as the subtraction area
                                                subtraction_path = path1.intersected(path2)

                                            if not subtraction_path.isEmpty():
                                                original_rect_intersect = current_intersection_shadow.boundingRect()
                                                current_intersection_shadow = current_intersection_shadow.subtracted(subtraction_path) # Apply to current intersection
                                                new_rect_intersect = current_intersection_shadow.boundingRect()

                                                original_area_intersect = original_rect_intersect.width() * original_rect_intersect.height()
                                                new_area_intersect = new_rect_intersect.width() * new_rect_intersect.height()

                                                if abs(original_area_intersect - new_area_intersect) > 1e-6 or \
                                                   (original_area_intersect > 1e-6 and current_intersection_shadow.isEmpty()):
                                                    logging.info(f"Subtracted overlying mask '{mask_layer_sub}' (using its area) from shadow intersection of '{this_layer}' on '{other_layer}'")
                                            else:
                                                 logging.warning(f"Could not calculate subtraction path for mask '{mask_layer_sub}', subtraction skipped for this intersection.")


                                        except Exception as e:
                                            logging.error(f"Error calculating or subtracting overlying mask '{mask_layer_sub}' from shadow intersection: {e}")
                        # --- END MASK SUBTRACTION FOR THIS INTERSECTION ---


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
                                
                            logging.info(f"Added shadow from {this_layer} onto {other_layer} to combined path")
                        else:
                            logging.info(f"No intersection between {this_layer} and {other_layer} paths")
                    except Exception as e:
                        logging.error(f"Error calculating strand shadow: {e}")
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
            
            logging.info(f"Drew unified shadow path for strand {this_layer}")
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
    # ----------------------------------------------------------
    #  Create circle shadow paths for start and end points if they have circles
    # ----------------------------------------------------------

    circle_shadow_paths = []  # List[Tuple[QPainterPath, QPointF]]
    # Skip circle shadow generation if circle stroke is fully transparent
    if hasattr(strand, 'circle_stroke_color') and strand.circle_stroke_color.alpha() == 0:
        logging.info(f"Skipping circle shadow generation for transparent circle on strand {strand.layer_name}")
    elif hasattr(strand, 'has_circles'):
        # Base circle radius (do not add extra shadow width – fade loop will handle blur)
        circle_radius = strand.width + strand.stroke_width * 2 
        
        # Check which points have circles and add their paths
        for idx, has_circle in enumerate(strand.has_circles):
            if has_circle:
                # Skip drawing shadow for transparent circles
                if hasattr(strand, 'circle_stroke_color'):
                    circle_color = strand.circle_stroke_color
                    if circle_color and circle_color.alpha() == 0:
                        logging.info(f"Skipping shadow for transparent circle at {'start' if idx == 0 else 'end'} point")
                        continue
                
                # ----------------------------------------------------------
                #  Create the actual circle path now
                # -----------------------------------
                point = strand.start if idx == 0 else strand.end
                circle_path = QPainterPath()
                circle_path.addEllipse(point, (circle_radius/2)+1, (circle_radius/2)+1)

                # Store path and center for later processing
                circle_shadow_paths.append((circle_path, point))
                logging.info(f"Prepared circle shadow at {'start' if idx == 0 else 'end'} for {strand.layer_name}")
                # ----------------------------------------------------------

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
        logging.error(f"Error computing strand body path for {strand.layer_name}: {e}")

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
                other_path = other_strand.get_path()
                other_stroker = QPainterPathStroker()
                other_stroker.setWidth(other_strand.width + other_strand.stroke_width * 2)
                other_stroker.setJoinStyle(Qt.MiterJoin)
                other_stroker.setCapStyle(Qt.FlatCap)
                other_stroke_path = other_stroker.createStroke(other_path)

                if hasattr(other_strand, 'get_mask_path'):
                    try:
                        other_stroke_path = get_proper_masked_strand_path(other_strand)
                        logging.info(f"Using mask path for interaction with MaskedStrand {other_layer}")
                    except Exception as ee:
                        logging.error(f"Error getting mask path for {other_layer}: {ee}")

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
                logging.error(f"Could not create stroke path for other strand {other_layer}: {e}")
                continue

            for circle_path, center in circle_shadow_paths:
                # Quick bounding check
                if not other_rect.isNull():
                    if (center.x() < other_rect.left() - circle_radius/2 or
                        center.x() > other_rect.right() + circle_radius/2 or
                        center.y() < other_rect.top() - circle_radius/2 or
                        center.y() > other_rect.bottom() + circle_radius/2):
                        continue

                # Subtract body path to avoid double shadow
                final_circle_path = QPainterPath(circle_path)
                if not strand_body_path.isEmpty():
                    final_circle_path = final_circle_path.subtracted(strand_body_path)

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

                                    if not subtraction_path_c.isEmpty():
                                        intersection = intersection.subtracted(subtraction_path_c)
                                        # Basic logging for circle shadow subtraction
                                        if intersection.isEmpty(): # Check if subtraction removed everything
                                             logging.info(f"Subtracted mask '{mask_layer_sub_c}' completely removed circle shadow intersection of '{this_layer}' on '{other_layer}'")

                                except Exception as e_c:
                                    logging.error(f"Error subtracting mask '{mask_layer_sub_c}' from circle shadow intersection: {e_c}")
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
                final_circle_path = final_circle_path.subtracted(strand_body_path)

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
    logging.info(f"Shadow paths for strand {getattr(strand, 'layer_name', 'unknown')}: count={len(all_shadow_paths)}, empty_paths={sum(1 for p in all_shadow_paths if p.isEmpty())}, non_empty={sum(1 for p in all_shadow_paths if not p.isEmpty())}")
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
             logging.warning(f"Expected one shadow path but found {len(all_shadow_paths)}, uniting them.")
             total_shadow_path = QPainterPath()
             for p in all_shadow_paths:
                 if total_shadow_path.isEmpty():
                     total_shadow_path = p
                 else:
                     total_shadow_path = total_shadow_path.united(p)
        else:
             # This means all_shadow_paths was empty, log and return
             logging.warning(f"No shadow paths in all_shadow_paths for strand {strand.layer_name}, skipping draw.")
             return # Nothing to draw


        logging.info(f"Drawing faded shadow for strand {strand.layer_name}")
        # Draw the combined path with a faded edge effect
        base_color = color_to_use
        base_alpha = base_color.alpha()

        # Prepare painter with clipping so the shadow cannot appear where no underlying strand exists
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(Qt.NoBrush)  # We are stroking, not filling

        # --- Add Logging --- 
        current_comp_mode = painter.compositionMode()
        logging.info(f"DrawMaskShadow - Before Clip/Stroke: total_shadow_path empty={total_shadow_path.isEmpty()}, bounds={total_shadow_path.boundingRect()}")
        logging.info(f"DrawMaskShadow - Before Clip/Stroke: clip_path empty={clip_path.isEmpty()}, bounds={clip_path.boundingRect()}")
        logging.info(f"DrawMaskShadow - Before Clip/Stroke: Painter composition mode={current_comp_mode}")
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
                    painter.strokePath(total_shadow_path, pen) # Stroke the path outline
            except Exception as stroke_error:
                logging.error(f"DrawMaskShadow - Error during shadow stroking loop: {stroke_error}")
            # --- End try...except ---

            logging.info(f"Drew faded shadow stroke path with {num_steps} steps for strand {strand.layer_name} bounds {total_shadow_path.boundingRect()}")
        else:
             logging.warning(f"Total shadow path became empty unexpectedly for strand {strand.layer_name}, cannot draw faded shadow.")

        painter.restore() # Restore painter state (render hints, brush, composition mode)

    else:
        # ADDED: Create a fallback shadow path when no paths are found
        logging.warning(f"No shadow paths for strand {getattr(strand, 'layer_name', 'unknown')}, creating fallback")
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
                logging.warning(f"Empty mask path for MaskedStrand, falling back to standard path")
        except Exception as e:
            logging.error(f"Error getting mask path: {e}, falling back to standard path")
    
    # For normal strands or fallback, use the regular path
    if hasattr(strand, 'get_shadow_path'):
        path = strand.get_shadow_path()
    else:
        path = QPainterPath()  # Empty path as last resort
        
    return path 

