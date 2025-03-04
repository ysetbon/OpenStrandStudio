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
        shadow_opacity = QColor(0, 0, 0, 150)
    
    # Cap opacity at the same level as strand shadows for perfect consistency
    if shadow_opacity.alpha() > 150:
        shadow_opacity.setAlpha(150)
    
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
    
    # Set up painter for shadow
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(shadow_color))
    
    # Check if the path is empty
    if path.isEmpty():
        logging.warning("Attempt to draw empty masked strand shadow path, skipping")
        painter.restore()
        return
    
    # Draw the shadow path
    painter.drawPath(path)
    
    # Restore painter state
    painter.restore()

def draw_circle_shadow(painter, strand, shadow_color=None):
    """
    Draw shadow for a circle that overlaps with other strands.
    This function should be called before drawing the circle itself.
    
    Args:
        painter: The QPainter to draw with
        strand: The strand with circle to draw shadow for
        shadow_color: Custom shadow color or None to use strand's shadow_color
    """
    if not hasattr(strand, 'canvas') or not strand.canvas:
        return
        
    # Check if shadowing is disabled in the canvas
    if hasattr(strand.canvas, 'shadow_enabled') and not strand.canvas.shadow_enabled:
        return
    
    # Skip drawing circle shadows for MaskedStrands - they don't have real circles
    if hasattr(strand, 'get_masked_shadow_path'):
        logging.info(f"Skipping circle shadow for MaskedStrand {strand.layer_name}")
        return
    
    # Use strand's shadow color with the exact same opacity as the strand shadow
    # to ensure perfect matching between circle and strand shadows
    if shadow_color:
        # If custom color provided, use it
        color_to_use = QColor(shadow_color)
    elif hasattr(strand, 'shadow_color') and strand.shadow_color:
        # If strand has a shadow color, create a copy without modifying opacity
        color_to_use = QColor(strand.shadow_color)
    else:
        # Default shadow color - match the strand shadow default exactly (150 alpha)
        color_to_use = QColor(0, 0, 0, 150)
    
    # Cap opacity at the same level as strand shadows for perfect consistency
    if color_to_use.alpha() > 150:
        color_to_use.setAlpha(150)
    
    logging.info(f"Drawing circle shadow for strand {strand.layer_name} with color {color_to_use.name()} alpha={color_to_use.alpha()}")
    
    # Create circle shadow paths for start and end points if they have circles
    shadow_paths = []
    
    if hasattr(strand, 'has_circles'):
        # Get circle radius with added shadow width
        circle_radius = strand.width + strand.stroke_width * 2 + 10
        
        # Check which points have circles and add their paths
        for idx, has_circle in enumerate(strand.has_circles):
            if has_circle:
                # Skip drawing shadow for transparent circles
                if hasattr(strand, 'circle_stroke_color'):
                    circle_color = strand.circle_stroke_color
                    if circle_color and circle_color.alpha() == 0:
                        logging.info(f"Skipping shadow for transparent circle at {'start' if idx == 0 else 'end'} point")
                        continue
                        
                point = strand.start if idx == 0 else strand.end
                circle_path = QPainterPath()
                circle_path.addEllipse(point, circle_radius/2, circle_radius/2)
                shadow_paths.append((circle_path, point))
                logging.info(f"Added circle shadow at {'start' if idx == 0 else 'end'} point for {strand.layer_name}")
    
    # If no circles found, exit early
    if not shadow_paths:
        return
    
    # Get the strand body path to subtract from circle shadows to avoid double shadows
    strand_body_path = None
    try:
        path = strand.get_path()
        stroke_stroker = QPainterPathStroker()
        stroke_stroker.setWidth(strand.width + strand.stroke_width * 2 + 10)
        stroke_stroker.setJoinStyle(Qt.MiterJoin)
        stroke_stroker.setCapStyle(Qt.FlatCap)
        strand_body_path = stroke_stroker.createStroke(path)
    except Exception as e:
        logging.error(f"Error creating strand body path for shadow subtraction: {e}")
        
    # Try to get layer ordering from layer state manager
    canvas = strand.canvas
    if hasattr(canvas, 'layer_state_manager') and canvas.layer_state_manager:
        manager = canvas.layer_state_manager
        layer_order = manager.getOrder()
        
        # Get this strand's layer name
        this_layer = strand.layer_name
        
        # Check against all other strands
        for other_strand in canvas.strands:
            # Skip self or strands without layer names
            if other_strand is strand or not hasattr(other_strand, 'layer_name') or not other_strand.layer_name:
                continue
            
            # Skip if other strand isn't in layer order
            other_layer = other_strand.layer_name
            if other_layer not in layer_order:
                continue
            
            # Get positions in layer order
            if this_layer in layer_order and other_layer in layer_order:
                self_index = layer_order.index(this_layer)
                other_index = layer_order.index(other_layer)
                
                # Standard layer order: higher index is above lower index
                should_be_above = self_index > other_index
                
                # Debug info
                if should_be_above:
                    logging.info(f"Layer {this_layer} (index {self_index}) should cast shadow on {other_layer} (index {other_index})")
                else:
                    logging.info(f"Layer {this_layer} (index {self_index}) should NOT cast shadow on {other_layer} (index {other_index})")
            else:
                logging.warning(f"Layer index issue: {this_layer} or {other_layer} not in layer_order")
            
            # Only draw shadow if this strand should be above the other
            if should_be_above:
                # For each circle we need to draw shadow
                for shadow_path, circle_center in shadow_paths:
                    # Quick reject using distance check for efficiency
                    if hasattr(other_strand, 'boundingRect'):
                        # If the circle center is too far from other strand's bounding rect, skip
                        rect = other_strand.boundingRect()
                        if (circle_center.x() < rect.left() - circle_radius/2 or 
                            circle_center.x() > rect.right() + circle_radius/2 or
                            circle_center.y() < rect.top() - circle_radius/2 or
                            circle_center.y() > rect.bottom() + circle_radius/2):
                            continue
                    
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
                                logging.info(f"Using mask path for circle interaction with MaskedStrand {other_layer}")
                            except Exception as e:
                                logging.error(f"Error getting mask path from MaskedStrand {other_layer} for circle shadow: {e}")
                        
                        # Subtract the strand body path from the circle shadow to avoid double shadows
                        final_shadow_path = QPainterPath(shadow_path)
                        if strand_body_path:
                            # Leave some overlap (1-2 pixels) for smooth transition between shadows
                            # Create a slightly smaller body path for subtraction
                            smaller_body_stroker = QPainterPathStroker()
                            smaller_body_stroker.setWidth(strand.width + strand.stroke_width * 2 + 10)
                            smaller_body_stroker.setJoinStyle(Qt.MiterJoin)
                            smaller_body_stroker.setCapStyle(Qt.FlatCap)
                            smaller_body_path = smaller_body_stroker.createStroke(path)
                            
                            # Subtract the smaller body path from the circle
                            final_shadow_path = final_shadow_path.subtracted(smaller_body_path)
                        
                        # Calculate intersection with other strand
                        intersection = QPainterPath(final_shadow_path)
                        intersection = intersection.intersected(other_stroke_path)
                        
                        # Only draw if there's an actual intersection
                        if not intersection.isEmpty():
                            # Draw shadow
                            painter.setPen(Qt.NoPen)
                            painter.setBrush(color_to_use)
                            painter.drawPath(intersection)
                    except Exception as e:
                        logging.error(f"Error drawing circle shadow: {e}")
    else:
        # If no layer manager available, draw simple circle shadows
        logging.info("No layer state manager available for circle shadow drawing")
        # Draw full circle shadows as fallback
        for shadow_path, _ in shadow_paths:
            # Subtract strand body path from circle shadows
            if strand_body_path:
                # Leave some overlap for smooth transition
                smaller_body_stroker = QPainterPathStroker()
                smaller_body_stroker.setWidth(strand.width + strand.stroke_width * 2 + 10)
                smaller_body_stroker.setJoinStyle(Qt.MiterJoin)
                smaller_body_stroker.setCapStyle(Qt.FlatCap)
                smaller_body_path = smaller_body_stroker.createStroke(path)
                
                shadow_path = shadow_path.subtracted(smaller_body_path)
            
            # Draw the shadows
            painter.setPen(Qt.NoPen)
            painter.setBrush(color_to_use)
            painter.drawPath(shadow_path)

def draw_strand_shadow(painter, strand, shadow_color=None):
    """
    Draw shadow for a strand that overlaps with other strands.
    This function should be called before drawing the strand itself.
    
    Args:
        painter: The QPainter to draw with
        strand: The strand to draw shadow for
        shadow_color: Custom shadow color or None to use strand's shadow_color
    """

        
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
    
    # Cap opacity at a reasonable level for consistent shadows
    if color_to_use.alpha() > 150:
        color_to_use.setAlpha(150)
    
    logging.info(f"Drawing shadow for strand {strand.layer_name} with color {color_to_use.name()} alpha={color_to_use.alpha()}")
    
    # Normal strand handling - use helper function to get proper path for any type of strand
    path = get_proper_masked_strand_path(strand)
    shadow_width = 10
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
                circle_radius = strand.width + strand.stroke_width * 2 + 15  # Increased from 10 to 15
                exclude_circle = QPainterPath()
                exclude_circle.addEllipse(point, circle_radius/2, circle_radius/2)
                
                # Subtract the circle area from the shadow path
                shadow_path = shadow_path.subtracted(exclude_circle)
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
                circle_radius = strand.width + strand.stroke_width * 2 + 15  # Increased from 10 to 15
                exclude_end_circle = QPainterPath()
                exclude_end_circle.addEllipse(strand.end, circle_radius/2, circle_radius/2)
                shadow_path = shadow_path.subtracted(exclude_end_circle)
                logging.info(f"Excluded transparent end circle for AttachedStrand: {strand.layer_name}")
            else:
                # IMPORTANT: Do NOT add end circle to shadow - this will be handled by draw_circle_shadow
                logging.info(f"End circle shadow for AttachedStrand will be handled by draw_circle_shadow")
                
        # Only add start circle shadow if the circle is not transparent AND this is special parent connection
        # This is the ONLY case where we add circle shadow here instead of draw_circle_shadow
        if not has_transparent_start_circle and hasattr(strand, 'parent'):
            if hasattr(strand, 'has_circles') and strand.has_circles and not strand.has_circles[0]:
                # Add circular area at start point where it connects to parent
                circle_radius = strand.width + strand.stroke_width * 2 + 10  # Match shadow width
                circle_rect = QRectF(
                    strand.start.x() - circle_radius/2,
                    strand.start.y() - circle_radius/2,
                    circle_radius,
                    circle_radius
                )
                
                # Create circle path and add to shadow path
                circle_path = QPainterPath()
                circle_path.addEllipse(circle_rect)
                
                # Combine with existing shadow path
                shadow_path.addPath(circle_path)
                logging.info(f"Added parent connection shadow for AttachedStrand: {strand.layer_name}")
            else:
                # Normal case is handled by draw_circle_shadow
                logging.info(f"Start circle shadow will be handled by draw_circle_shadow")

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
            
                # Only draw shadow if this strand should be above the other
                if should_be_above:
                    # Quick reject using bounding rectangles
                    if not strand.boundingRect().intersects(other_strand.boundingRect()):
                        logging.info(f"Bounding rectangles don't intersect, skipping shadow for {this_layer} on {other_layer}")
                        continue
                        
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
                        
                        # Only draw if there's an actual intersection
                        if not intersection.isEmpty():
                            # Draw shadow
                            painter.setPen(Qt.NoPen)
                            painter.setBrush(color_to_use)
                            
                            # IMPORTANT FIX: Use SourceOver composition mode to prevent shadow darkening
                            # for ALL strands to ensure consistent shadow opacity
                            old_composition = painter.compositionMode()
                            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                            painter.drawPath(intersection)
                            painter.setCompositionMode(old_composition)
                                
                            logging.info(f"Drew shadow from {this_layer} onto {other_layer}")
                        else:
                            logging.info(f"No intersection between {this_layer} and {other_layer} paths")
                    except Exception as e:
                        logging.error(f"Error drawing strand shadow: {e}")
                else:
                    logging.info(f"Layer {this_layer} should NOT be above {other_layer}, no shadow drawn")
    else:
        # If no layer manager available, draw simple shadow
        # This is a fallback method
        logging.info("No layer state manager available for shadow drawing") 

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
    if hasattr(strand, 'get_path'):
        path = strand.get_path()
    else:
        path = QPainterPath()  # Empty path as last resort
        
    return path 