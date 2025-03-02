import logging
from PyQt5.QtGui import QPainterPath, QPainterPathStroker, QPen, QBrush, QColor
from PyQt5.QtCore import Qt, QRectF


def draw_mask_strand_shadow(painter, path, shadow_color=None):
    """
    Draw shadow for a masked strand 
    """
    # Handle the case when a strand object is passed instead of a color
    if shadow_color and not isinstance(shadow_color, QColor):
        # Try to get shadow_color attribute from the strand
        shadow_color = getattr(shadow_color, 'shadow_color', None)
    
    # Fall back to default if no valid color was found
    if not shadow_color or not isinstance(shadow_color, QColor):
        # Use a shadow with moderate opacity for realistic effect
        shadow_color = QColor(0, 0, 0, 150)  # 160/255 = ~63% opacity
    
    # Make sure the color doesn't exceed reasonable opacity
    if shadow_color.alpha() > 150:  # Cap at ~70% opacity for natural look
        shadow_color.setAlpha(150)
        
    logging.info(f"Drawing masked strand shadow with color {shadow_color.name()} alpha={shadow_color.alpha()}")
    
    # Save painter state
    painter.save()
    
    # Set up painter for shadow
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(shadow_color))
    
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
            
            # Check if this layer should be above the other layer
            should_be_above = False
            
            # 1. First check the special mask case: if this layer is the first component of a masked strand
            # and the other layer is between this layer and the masked strand in the order
            if strand.__class__.__name__ != 'MaskedStrand':
                for s in canvas.strands:
                    if s.__class__.__name__ == 'MaskedStrand' and hasattr(s, 'first_selected_strand'):
                        # If this strand is the first component of a masked strand
                        if strand == s.first_selected_strand:
                            # Get masked strand's layer name
                            masked_layer = s.layer_name
                            if masked_layer in layer_order and this_layer in layer_order and other_layer in layer_order:
                                # Check positions in layer order
                                self_index = layer_order.index(this_layer)
                                masked_index = layer_order.index(masked_layer)
                                other_index = layer_order.index(other_layer)
                                
                                # Only cast shadow if:
                                # 1. Masked strand is above the other strand AND
                                # 2. This layer is below the other layer in normal order AND
                                # 3. The other layer is not part of the masked strand name (to avoid casting on components like '1_3' in '1_1_1_3')
                                if (masked_index > other_index and 
                                    self_index < other_index and 
                                    '_' + other_layer not in masked_layer):
                                    should_be_above = True
                                    logging.info(f"Circle for layer {this_layer} is above {other_layer} because it's the first component of masked layer {masked_layer} which is above {other_layer}")
                                    break
            
            # 2. If no special case, use normal order rules
            if not should_be_above:
                # Get positions in layer order
                self_index = layer_order.index(this_layer)
                other_index = layer_order.index(other_layer)
                
                # Standard layer order: higher index is above lower index
                should_be_above = self_index > other_index
            
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
    
    # Normal strand handling (or fallback for masked strand if error above)
    path = strand.get_path()
    
    # Create base shadow path without circles first
    shadow_stroker = QPainterPathStroker()
    shadow_stroker.setWidth(strand.width + strand.stroke_width * 2 + 10)
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
        
        # Get this strand's layer name
        this_layer = strand.layer_name
        
        # Log layer order for debugging
        logging.info(f"Current layer order: {layer_order}")
        logging.info(f"Current strand being processed: {this_layer}")
        
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
            
            # Check if this layer should be above the other layer
            should_be_above = False
            
            # 1. First check the special mask case: if this layer is the first component of a masked strand
            # and the other layer is between this layer and the masked strand in the order
            if strand.__class__.__name__ != 'MaskedStrand':
                for s in canvas.strands:
                    if s.__class__.__name__ == 'MaskedStrand' and hasattr(s, 'first_selected_strand'):
                        # If this strand is the first component of a masked strand
                        if strand == s.first_selected_strand:
                            # Get masked strand's layer name
                            masked_layer = s.layer_name
                            if masked_layer in layer_order and this_layer in layer_order and other_layer in layer_order:
                                # Check positions in layer order
                                self_index = layer_order.index(this_layer)
                                masked_index = layer_order.index(masked_layer)
                                other_index = layer_order.index(other_layer)
                                
                                # Only cast shadow if:
                                # 1. Masked strand is above the other strand AND
                                # 2. This layer is below the other layer in normal order AND
                                # 3. The other layer is not part of the masked strand name (to avoid casting on components like '1_3' in '1_1_1_3')
                                if (masked_index > other_index and 
                                    self_index < other_index and 
                                    '_' + other_layer not in masked_layer):
                                    should_be_above = True
                                    logging.info(f"Layer {this_layer} is above {other_layer} because it's the first component of masked layer {masked_layer} which is above {other_layer}")
                                    break
            
            # 2. If no special case, use normal order rules
            if not should_be_above:
                # Get positions in layer order
                if this_layer in layer_order and other_layer in layer_order:
                    self_index = layer_order.index(this_layer)
                    other_index = layer_order.index(other_layer)
                    
                    # Standard layer order: higher index is above lower index
                    should_be_above = self_index > other_index
                    
                    # Debug info
                    if self_index > other_index:
                        logging.info(f"Layer {this_layer} (index {self_index}) should cast shadow on {other_layer} (index {other_index})")
                    else:
                        logging.info(f"Layer {this_layer} (index {self_index}) should NOT cast shadow on {other_layer} (index {other_index})")
                else:
                    logging.warning(f"Layer index issue: {this_layer} or {other_layer} not in layer_order")
            
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
                    
                    # Calculate intersection
                    intersection = QPainterPath(shadow_path)
                    intersection = intersection.intersected(other_stroke_path)
                    
                    # Only draw if there's an actual intersection
                    if not intersection.isEmpty():
                        # Draw shadow
                        painter.setPen(Qt.NoPen)
                        painter.setBrush(color_to_use)
                        painter.drawPath(intersection)
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