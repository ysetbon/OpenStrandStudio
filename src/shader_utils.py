import logging
from PyQt5.QtGui import QPainterPath, QPainterPathStroker, QPen, QBrush, QColor, QPainter
from PyQt5.QtCore import Qt, QRectF



def draw_mask_strand_shadow(painter, path, strand, shadow_color=None):
    """
    Draw shadow for a masked strand 
    """
    # Use lower opacity for masked strand shadows to prevent darkening
    # when combined with regular strand shadows
    # Use strand's shadow color with the exact same opacity as the strand shadow
    # to ensure perfect matching between circle and strand shadows
    if shadow_color:
        # If custom color provided, use it
        shadow_opacity = QColor(shadow_color)
    elif hasattr(strand, 'shadow_color') and strand.shadow_color:
        # If strand has a shadow color, create a copy without modifying opacity
        shadow_opacity = QColor(strand.shadow_color)
    else:
        # Default shadow color - match the strand shadow default exactly (150 alpha)
        shadow_opacity = QColor(0, 0, 0, 0)
    
    # Remove the cap on opacity to respect user's chosen alpha value
    # if shadow_opacity.alpha() > 150:
    #     shadow_opacity.setAlpha(150)
    
    # Handle the case when a strand object is passed instead of a color
    if shadow_color and not isinstance(shadow_color, QColor):
        # Check if this is a MaskedStrand object
        if hasattr(shadow_color, 'get_mask_path') and hasattr(shadow_color, 'deletion_rectangles'):
            # It's a masked strand, use its properties
            masked_strand = shadow_color
            
            # Check for custom display color
            if hasattr(masked_strand, 'color') and masked_strand.color:
                # Derive shadow color from strand color, with proper opacity
                strand_color = masked_strand.color
                shadow_color = QColor(0, 0, 0, shadow_opacity.alpha())  # Default to black with lower opacity
            else:
                # Always use standard shadow color with consistent opacity
                shadow_color = QColor(0, 0, 0, shadow_opacity.alpha())
                
            logging.info(f"Using proper MaskedStrand shadow properties for {getattr(masked_strand, 'layer_name', 'unknown')}")
        else:
            # Not a MaskedStrand, use standard shadow
            shadow_color = QColor(0, 0, 0, shadow_opacity.alpha())
    else:
        # If a QColor was passed directly, ensure it has standard opacity
        if isinstance(shadow_color, QColor):
            # Create new color with same RGB but reduced opacity
            color_to_use = QColor(shadow_color)
            # Cap opacity at a lower level for masked strands
            color_to_use.setAlpha(shadow_opacity.alpha())
            shadow_color = color_to_use
        else:
            shadow_color = QColor(0, 0, 0, shadow_opacity.alpha())
    
    logging.info(f"Drawing masked strand shadow with color {shadow_color.name()} alpha={shadow_color.alpha()}")
    
    # Save painter state
    painter.save()
    
    # IMPORTANT FIX: Use SourceOver composition mode to prevent shadow darkening
    # when overlapping with other shadows
    painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
    
    # Calculate base shadow properties
    num_steps = 8
    max_blur_radius = 40.0
    base_color = shadow_color
    base_alpha = base_color.alpha()

    # Check if the path is empty
    if path.isEmpty():
        logging.warning("Attempt to draw empty masked strand shadow path, skipping")
        painter.restore()
        return

    # --- Fill the core shadow area first ---
    painter.setPen(Qt.NoPen) # No outline for the core fill
    painter.setBrush(Qt.NoBrush)  # Ensure no fill, we only stroke for blur effect
    # Use the base color for the fill. Adjust alpha slightly if needed, 
    # or keep it the same if strokes should blend outwards.
    # For now, use the base color as calculated.

    
    logging.info(f"Drew filled core masked shadow area with color {base_color.name()}")
    
    # --- Now add the faded edge using stroking ---
    painter.setRenderHint(QPainter.Antialiasing, True)
 
    # --- Determine an appropriate clipping path so the shadow can extend
    #     outward just like regular strand shadows.  We want the shadow of
    #     the mask to be able to draw anywhere the *component* strands exist
    #     (i.e. the union of the two stroked paths), not just inside the
    #     small intersection region.  This mirrors the logic that
    #     draw_strand_shadow uses for the regular strands.

    clip_path = QPainterPath()

    # If this "strand" is actually a MaskedStrand it should have references
    # to its component strands.  Build a union of their stroke paths so we
    # can allow the fade to draw over their full width.
    try:
        width_masked_strand = 15
        if hasattr(strand, 'first_selected_strand') and strand.first_selected_strand:
            s1 = strand.first_selected_strand
            stroker1 = QPainterPathStroker()
            stroker1.setWidth(s1.width + s1.stroke_width * 2 + width_masked_strand)
            stroker1.setJoinStyle(Qt.MiterJoin)
            stroker1.setCapStyle(Qt.FlatCap)
            first_path = stroker1.createStroke(s1.get_path())
            if clip_path.isEmpty():
                clip_path_first = first_path
            else:
                clip_path_first = clip_path.united(first_path)
        if hasattr(strand, 'second_selected_strand') and strand.second_selected_strand:
            s2 = strand.second_selected_strand
            stroker2 = QPainterPathStroker()
            stroker2.setWidth(s2.width + s2.stroke_width * 2 + 0)
            stroker2.setJoinStyle(Qt.MiterJoin)
            stroker2.setCapStyle(Qt.FlatCap)
            second_path = stroker2.createStroke(s2.get_path())

            if clip_path.isEmpty():
                clip_path_second = second_path
            else:
                clip_path_second = clip_path.united(second_path)
    except Exception as e:
        logging.error(f"Error constructing clip path for masked strand shadow: {e}")

    # Fall back to the original path if we could not build a better clip path
    if clip_path.isEmpty():
        clip_path = clip_path_first.intersected(clip_path_second)

    # Finally apply the clip
    painter.setClipPath(clip_path)
    # ---------------------------------------------

    if not path.isEmpty(): # Redundant check, but safe
        for i in range(num_steps):
            # Alpha fades from base_alpha down towards zero
            progress = (float(num_steps - i) / num_steps)
            # Make the stroke alpha slightly less intense than the fill maybe?
            # Or keep it consistent with draw_strand_shadow logic.
            current_alpha = base_alpha * progress * progress * (1.0 / num_steps) * 2.0 # Exponential decay

            # Width increases
            current_width = max_blur_radius * (float(i + 1) / num_steps)

            pen_color = QColor(base_color.red(), base_color.green(), base_color.blue(), max(0, min(255, int(current_alpha))))
            pen = QPen(pen_color)
            pen.setWidthF(current_width)
            pen.setCapStyle(Qt.RoundCap) # Use RoundCap/Join for softer edges
            pen.setJoinStyle(Qt.RoundJoin)

            # painter.intersect(path) # REMOVED - Use setClipPath before the loop instead
            painter.setPen(pen)
            painter.strokePath(path, pen) # Stroke the input path outline (will be clipped)

        logging.info(f"Drew faded masked shadow stroke path with {num_steps} steps, clipped to path")
    else:
         # This case should not be reached due to the check above
         logging.warning("Masked shadow path was empty, cannot draw faded stroke.")
    # --- End of Faded Shadow Logic ---
    
    # Restore painter state
    painter.restore()


def draw_circle_shadow(painter, strand, shadow_color=None):
    """
    Draw shadow for a circle at the start or end of a strand.
    """
    pass

def draw_strand_shadow(painter, strand, shadow_color=None):
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
    shadow_width = 0
    # Create base shadow path without circles first
    shadow_stroker = QPainterPathStroker()
    shadow_stroker.setWidth(strand.width + strand.stroke_width * 2 + shadow_width)
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
                #shadow_path = shadow_path.subtracted(exclude_circle)
                logging.info(f"Excluded transparent circle at {'start' if idx == 0 else 'end'} point for {strand.layer_name}")

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
                #shadow_path = shadow_path.subtracted(exclude_end_circle)
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
        
        # Check against all other strands
        for other_strand in canvas.strands:
            # Skip self or strands without layer names
            if other_strand is strand or not hasattr(other_strand, 'layer_name') or not other_strand.layer_name:
                continue

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
                        
                        # Calculate intersection
                        intersection = QPainterPath(shadow_path)
                        intersection = intersection.intersected(other_stroke_path)
                        
                        # Special case: Check if the other strand is a component of a masked strand
                        # and if this strand should be above the masked strand
                        for masked_name, masked_info in masked_strands_map.items():
                            if other_layer in masked_info['components']:
                                masked_strand = masked_info['masked_strand']
                                masked_layer = masked_name
                                
                                # Check if this strand should be above the masked strand
                                if masked_layer in layer_order:
                                    masked_index = layer_order.index(masked_layer)
                                    should_be_above_masked = self_index > masked_index
                                    
                                    if should_be_above_masked:
                                        # This strand should be above both the component and the masked strand
                                        # Get the masked area to exclude from shadow
                                        try:
                                            mask_path = get_proper_masked_strand_path(masked_strand)
                                            
                                            # Remove the masked area from the intersection
                                            # This prevents shadow from appearing on the z_w component in the masked area
                                            intersection = intersection.subtracted(mask_path)
                                            logging.info(f"Excluded masked area of {masked_layer} from shadow of {this_layer} on {other_layer}")
                                        except Exception as e:
                                            logging.error(f"Error excluding masked area: {e}")
                        
                        # Only add if there's an actual intersection
                        if not intersection.isEmpty():
                            # Include the underlying strand area in the clip path so the shadow can't draw where there is no strand
                            if clip_path.isEmpty():
                                clip_path = other_stroke_path
                            else:
                                clip_path = clip_path.united(other_stroke_path)
                            # Add this intersection to the combined path
                            if has_shadow_content:
                                combined_shadow_path = combined_shadow_path.united(intersection)
                            else:
                                combined_shadow_path = intersection
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
    if hasattr(strand, 'has_circles'):
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
                    except Exception as ee:
                        logging.error(f"Error getting mask path for {other_layer}: {ee}")
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
        num_steps = 8  # Fewer steps for performance, adjust as needed
        max_blur_radius = 40.0 # Larger radius for more pronounced fade
        base_color = color_to_use
        base_alpha = base_color.alpha()

        # Prepare painter with clipping so the shadow cannot appear where no underlying strand exists
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(Qt.NoBrush)  # We are stroking, not filling
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)  # Ensure correct blending
        # Apply clipping – use the collected clip_path, or fallback to the shadow path itself
        if not clip_path.isEmpty():
            painter.setClipPath(clip_path)

        # Check if path is valid before attempting to stroke
        if not total_shadow_path.isEmpty():
            for i in range(num_steps):
                # Alpha fades from base_alpha down towards zero
                # Distribute alpha across steps for smoother look
                # Adjusted alpha calculation slightly for potentially better distribution
                progress = (float(num_steps - i) / num_steps)
                current_alpha = base_alpha * progress * progress * (1.0 / num_steps) * 2.0 # Exponential decay, adjust multiplier

                # Width increases
                current_width = max_blur_radius * (float(i + 1) / num_steps)

                pen_color = QColor(base_color.red(), base_color.green(), base_color.blue(), max(0, min(255, int(current_alpha))))
                pen = QPen(pen_color)
                pen.setWidthF(current_width)
                pen.setCapStyle(Qt.RoundCap) # Use RoundCap/Join for softer edges
                pen.setJoinStyle(Qt.RoundJoin)

                painter.setPen(pen)
                painter.strokePath(total_shadow_path, pen) # Stroke the path outline

            logging.info(f"Drew faded shadow stroke path with {num_steps} steps for strand {strand.layer_name} bounds {total_shadow_path.boundingRect()}")
        else:
             logging.warning(f"Total shadow path became empty unexpectedly for strand {strand.layer_name}, cannot draw faded shadow.")

        painter.restore() # Restore painter state (render hints, brush, composition mode)

    else:
        logging.warning(f"No shadow paths generated to draw for strand {strand.layer_name}")


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