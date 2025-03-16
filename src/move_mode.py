from PyQt5.QtCore import QPointF, QRectF, QTimer, Qt
from PyQt5.QtGui import QCursor, QPen, QColor, QPainterPathStroker, QTransform, QBrush
from PyQt5.QtWidgets import QApplication
import math
import time
import logging
from PyQt5.QtGui import (
     QPainterPath
)
from strand import Strand, AttachedStrand, MaskedStrand

class MoveMode:
    def __init__(self, canvas):
        """
        Initialize the MoveMode.

        Args:
            canvas (StrandDrawingCanvas): The canvas this mode operates on.
        """
        self.canvas = canvas
        self.initialize_properties()
        self.setup_timer()
        self.originally_selected_strand = None
        self.in_move_mode = False
        self.temp_selected_strand = None
        self.last_update_time = 0  # Time of last update for frame limiting
        self.frame_limit_ms = 16  # Min time between updates (~ 60 fps)
        # Store the canvas's control points visibility setting
        self.original_control_points_visible = False
        if hasattr(self.canvas, 'show_control_points'):
            self.original_control_points_visible = self.canvas.show_control_points
        # Initialize position tracking
        self.last_strand_position = None
        # Flag to indicate if we're currently moving a control point
        self.is_moving_control_point = False

    def initialize_properties(self):
        """Initialize all properties used in the MoveMode."""
        self.moving_point = None  # The point being moved
        self.is_moving = False  # Flag to indicate if we're currently moving a point
        self.affected_strand = None  # The strand being affected by the move
        self.moving_side = None  # Which side of the strand is being moved (0 for start, 1 for end, 'control_point1', 'control_point2')
        self.selected_rectangle = None  # The rectangle representing the selected point
        self.last_update_pos = None  # The last position update
        self.accumulated_delta = QPointF(0, 0)  # Accumulated movement delta
        self.last_snapped_pos = None  # Last position snapped to grid
        self.target_pos = None  # Target position for gradual movement
        self.move_speed = 1  # Speed of movement in grid units per step
        self.locked_layers = set()  # Set of locked layer indices
        self.lock_mode_active = False  # Flag to indicate if lock mode is active
        self.last_update_rect = None  # Track the last update region
        self.last_strand_position = None  # Track the last position for strand movement

    def setup_timer(self):
        """Set up the timer for gradual movement."""
        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.gradual_move)

    def set_locked_layers(self, locked_layers, lock_mode_active):
        """
        Set the locked layers and lock mode state.

        Args:
            locked_layers (set): Set of indices of locked layers.
            lock_mode_active (bool): Whether lock mode is active.
        """
        self.locked_layers = locked_layers
        self.lock_mode_active = lock_mode_active

    def update_cursor_position(self, pos):
        """
        Update the cursor position to match the strand end point.

        Args:
            pos (QPointF): The new position for the cursor.
        """
        if isinstance(pos, QPointF):
            pos = pos.toPoint()
        global_pos = self.canvas.mapToGlobal(pos)
        QCursor.setPos(global_pos)

    def partial_update(self):
        """
        Update only the current strand being moved using highly optimized approach.
        This avoids redrawing all strands on every mouse movement.
        """
        if not self.affected_strand:
            return
            
        # Get the affected strands
        affected_strands = getattr(self.canvas, 'affected_strands_for_drawing', [self.affected_strand])
        
        # If no strands are affected, no need to update
        if not affected_strands:
            return
            
        # Setup background caching if needed
        if not hasattr(self.canvas, 'background_cache'):
            # Initialize background caching
            self._setup_background_cache()
            
        # If the canvas already has a method to handle this, use it
        if hasattr(self.canvas, 'set_active_strand_update'):
            self.canvas.set_active_strand_update(self.affected_strand, None)
            return  # Exit early to avoid duplicate work
        
        # Determine if we need a full update
        # Do full updates less frequently, but always include more context
        full_update = False
        if not hasattr(self, '_update_counter'):
            self._update_counter = 0
        self._update_counter = (self._update_counter + 1) % 15  # Reduced frequency for full updates
        if self._update_counter == 0:
            full_update = True
            
        # Optimization: Only calculate strand bounds if we don't already have them
        # or if the strand has moved significantly
        current_rect = None
        significant_movement = False
        
        if (hasattr(self, 'last_strand_position') and self.last_strand_position is not None and 
            hasattr(self, 'moving_point') and self.moving_point is not None):
            # Check if the strand has moved more than 5 pixels in any direction
            last_pos = self.last_strand_position
            dx = abs(self.moving_point.x() - last_pos.x())
            dy = abs(self.moving_point.y() - last_pos.y())
            significant_movement = dx > 5 or dy > 5
            
        # Calculate a wider viewing rectangle to ensure no cropping during movement
        if full_update or not hasattr(self.canvas, 'last_strand_rect') or significant_movement:
            # Calculate a rectangle that encompasses the entire affected strand, not just the square
            current_rect = self._get_strand_bounds(affected_strands)
            
            # Store the current position for future comparison
            if hasattr(self, 'moving_point') and self.moving_point is not None:
                self.last_strand_position = QPointF(self.moving_point.x(), self.moving_point.y())
        else:
            # Reuse the existing rect to avoid expensive recalculations
            current_rect = getattr(self.canvas, 'last_strand_rect', None)
            
        # If doing a full update, use a large area of the canvas, not the entire canvas
        # This gives us a compromise between a targeted update and a full canvas refresh
        if full_update:
            # Use a large portion of the viewport for full updates
            # but keep it centered on the affected strands to maintain context
            if hasattr(self.canvas, 'viewport'):
                viewport_rect = self.canvas.viewport().rect()
                
                # If we have a current rect, center the update on that
                if current_rect and not current_rect.isNull():
                    center_x = current_rect.center().x()
                    center_y = current_rect.center().y()
                    
                    # Make the update rect 80% of the viewport size
                    width = viewport_rect.width() * 0.8
                    height = viewport_rect.height() * 0.8
                    
                    # Center it on the current strands
                    current_rect = QRectF(
                        center_x - width/2,
                        center_y - height/2,
                        width,
                        height
                    )
                else:
                    # If no current rect, use the viewport
                    current_rect = viewport_rect
            else:
                # If there's no viewport, use the entire canvas
                current_rect = self.canvas.rect()
        
        # Store previous rectangle for erasing
        prev_rect = getattr(self.canvas, 'last_strand_rect', None)
        update_rect = current_rect
        
        if prev_rect and not full_update and current_rect:
            # Convert both rectangles to QRectF to ensure type compatibility
            if not isinstance(prev_rect, QRectF):
                prev_rect = QRectF(prev_rect)
            if not isinstance(current_rect, QRectF):
                current_rect = QRectF(current_rect)
                
            # For safety, ensure both rects are valid
            if not prev_rect.isValid():
                prev_rect = QRectF(0, 0, 1, 1)
            if not current_rect.isValid():
                current_rect = QRectF(0, 0, 1, 1)
                
            # Always union the rectangles to ensure all relevant areas are covered
            # This avoids leaving artifacts during fast movement
            update_rect = current_rect.united(prev_rect)
            
        # Add padding to ensure entire strand is visible, even with large movements
        # Significantly increased padding for better visibility
        if not full_update:
            # Use much larger padding to ensure movement is never cropped
            # Calculate based on grid size and viewport size
            if hasattr(self.canvas, 'viewport'):
                viewport_rect = self.canvas.viewport().rect()
                min_dimension = min(viewport_rect.width(), viewport_rect.height()) 
                # Use 25% of the smallest viewport dimension as padding
                viewport_padding = min_dimension * 0.25
                base_padding = max(200, self.canvas.grid_size * 4, viewport_padding)
            else:
                base_padding = max(200, self.canvas.grid_size * 4)
            
            # Increase padding proportionally to movement speed if we're tracking position
            if hasattr(self, 'last_strand_position') and self.last_strand_position is not None and significant_movement:
                movement_scale = 2.0  # Double padding for fast movements
            else:
                movement_scale = 1.5  # Use 1.5x padding even for normal movement
                
            padding = int(base_padding * movement_scale)
            update_rect = update_rect.adjusted(-padding, -padding, padding, padding)
            
        # If update_rect is null, use the entire canvas to avoid errors
        if update_rect is None or update_rect.isNull():
            if hasattr(self.canvas, 'viewport'):
                update_rect = self.canvas.viewport().rect()
            else:
                update_rect = self.canvas.rect()
        
        # Store for next update only if it's changed
        if current_rect and (not hasattr(self.canvas, 'last_strand_rect') or 
                            getattr(self.canvas, 'last_strand_rect', None) is None or
                            (isinstance(current_rect, QRectF) and 
                             not current_rect.isNull() and 
                             current_rect != getattr(self.canvas, 'last_strand_rect', None))):
            self.canvas.last_strand_rect = current_rect
            self.last_update_rect = current_rect  # Also store in the MoveMode instance
            
        # Set active strand and update rect
        self.canvas.active_strand_for_drawing = self.affected_strand
        self.canvas.active_strand_update_rect = update_rect
        
        # Setup efficient paint handler if needed
        if not hasattr(self.canvas, 'original_paintEvent'):
            self._setup_optimized_paint_handler()
        
        # We also need to ensure the background is invalidated when strands move
        # Always invalidate during movement for cleaner rendering
        if hasattr(self.canvas, 'background_cache_valid'):
            # Be more aggressive with invalidation to prevent rendering artifacts
            if full_update or significant_movement or self.is_moving:
                self.canvas.background_cache_valid = False
        
        # Force an immediate update of the canvas
        # Note: Cannot use update(rect) as the canvas doesn't support it
        self.canvas.update()

    def _get_strand_bounds(self, affected_strands=None):
        """Get the bounding rectangle of all affected strands or entire canvas if no strands provided."""
        if not affected_strands:
            # Return the full canvas bounds if no specific strands
            if hasattr(self.canvas, 'viewport'):
                return self.canvas.viewport().rect()
            return self.canvas.rect()
        
        # Start with null rect
        bounds = QRectF()
        
        # If we're moving, include both current and initial positions in the bounds
        # This ensures a smoother viewing experience during movement
        if (self.is_moving and 
            hasattr(self, 'last_strand_position') and self.last_strand_position and 
            hasattr(self, 'moving_point') and self.moving_point):
            # Create a rect that contains both the starting and current positions
            if bounds.isNull():
                pos_rect = QRectF()
                pos_rect.setLeft(min(self.last_strand_position.x(), self.moving_point.x()))
                pos_rect.setTop(min(self.last_strand_position.y(), self.moving_point.y()))
                pos_rect.setRight(max(self.last_strand_position.x(), self.moving_point.x()))
                pos_rect.setBottom(max(self.last_strand_position.y(), self.moving_point.y()))
                
                # Add some extra space
                pos_rect.adjust(-100, -100, 100, 100)
                bounds = pos_rect
        
        for strand in affected_strands:
            # Get path that encompasses the entire strand
            if hasattr(strand, 'path') and strand.path:
                strand_rect = strand.path.boundingRect()
                # Union with existing bounds
                if bounds.isNull():
                    bounds = strand_rect
                else:
                    bounds = bounds.united(strand_rect)
            else:
                # Fallback to calculating from points
                points = []
                if hasattr(strand, 'start'):
                    points.append(strand.start)
                if hasattr(strand, 'end'):
                    points.append(strand.end)
                if hasattr(strand, 'control_point1'):
                    points.append(strand.control_point1)
                if hasattr(strand, 'control_point2'):
                    points.append(strand.control_point2)
                
                for p in points:
                    if bounds.isNull():
                        bounds = QRectF(p.x(), p.y(), 1, 1)
                    else:
                        bounds = bounds.united(QRectF(p.x(), p.y(), 1, 1))
        
        # If bounds still null, return entire canvas
        if bounds.isNull():
            if hasattr(self.canvas, 'viewport'):
                return self.canvas.viewport().rect()
            return self.canvas.rect()
            
        # Add significant padding to ensure entire strand is visible even with large movements
        # Use at least 3x the grid size or 150 pixels
        padding = max(150, self.canvas.grid_size * 3)
        return bounds.adjusted(-padding, -padding, padding, padding)
    


    def _setup_background_cache(self):
        """Setup background caching for efficient updates."""
        import PyQt5.QtGui as QtGui
        from PyQt5.QtCore import Qt
        
        try:
            # Create a background cache pixmap the size of the visible area
            viewport_rect = self.canvas.viewport().rect() if hasattr(self.canvas, 'viewport') else self.canvas.rect()
            
            # Ensure valid dimensions
            width = max(1, viewport_rect.width())
            height = max(1, viewport_rect.height())
            
            # Create the pixmap and fill it
            self.canvas.background_cache = QtGui.QPixmap(width, height)
            # Fill with transparent color, not white
            self.canvas.background_cache.fill(Qt.transparent)
            
            # Create a flag to indicate when the cache needs refreshing
            self.canvas.background_cache_valid = False
            
            # Add method to canvas to invalidate cache when needed
            def invalidate_cache():
                """Simple method to invalidate the background cache."""
                if hasattr(self.canvas, 'background_cache_valid'):
                    self.canvas.background_cache_valid = False
            
            # Bind the method directly
            self.canvas.invalidate_background_cache = invalidate_cache
            
            logging.info(f"Background cache initialized: {width}x{height} pixels (transparent)")
        except Exception as e:
            logging.error(f"Error setting up background cache: {e}")
            # If we can't set up the cache, set a flag to disable it
            self.canvas.use_background_cache = False

    def _setup_optimized_paint_handler(self):
        """Setup a highly optimized paint handler for strand editing."""
        # Store the original paintEvent only once
        self.canvas.original_paintEvent = self.canvas.paintEvent
        
        # Store a reference to self (MoveMode instance)
        move_mode_ref = self
        
        def optimized_paint_event(self_canvas, event):
            """Optimized paint event for drawing moving strands on top."""
            import PyQt5.QtGui as QtGui
            from PyQt5.QtCore import Qt
            import logging
            
            # Access the MoveMode instance through the stored reference
            move_mode = move_mode_ref
            
            # Regular paint if no active strand - exit early
            if not hasattr(self_canvas, 'active_strand_for_drawing') or self_canvas.active_strand_for_drawing is None:
                self_canvas.original_paintEvent(event)
                return
                
            # Get the active strand and affected strands
            active_strand = self_canvas.active_strand_for_drawing
            affected_strands = getattr(self_canvas, 'affected_strands_for_drawing', [active_strand])
            
            # Create a temporary copy of the strands list
            original_strands = list(self_canvas.strands)
            
            try:
                # Remove the affected strands from the list to prevent drawing them twice
                temp_strands = [s for s in original_strands if s not in affected_strands]
                
                # Replace with temporary list that excludes moving strands
                self_canvas.strands = temp_strands
                
                # Call original paint event to draw background, grid, and all non-moving strands
                self_canvas.original_paintEvent(event)
                
                # Restore the original strands list
                self_canvas.strands = original_strands
                
                # Now draw only our moving strands on top
                painter = QtGui.QPainter(self_canvas)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                
                try:
                    # Draw all affected strands on top
                    for strand in affected_strands:
                        if hasattr(strand, 'draw'):
                            strand.draw(painter)
                    
                    # Draw the yellow selection rectangle on top of everything else
                    if move_mode.is_moving and move_mode.selected_rectangle and move_mode.affected_strand:
                        move_mode.draw_selection_square(painter)
                    
                    # Draw any interaction elements
                    if hasattr(self_canvas, 'draw_interaction_elements'):
                        self_canvas.draw_interaction_elements(painter)
                    
                    # Make sure control points are drawn properly but only if we're not moving a control point
                    # or only draw the control point being moved
                    if hasattr(self_canvas, 'show_control_points') and self_canvas.show_control_points and hasattr(self_canvas, 'draw_control_points'):
                        self_canvas.draw_control_points(painter)
                    
                    # Draw the C-shape specifically for the active strand
                    if hasattr(move_mode, 'draw_selected_attached_strand'):
                        move_mode.draw_selected_attached_strand(painter)
                    
                except Exception as e:
                    logging.error(f"Error in optimized paint event strand drawing: {e}")
                finally:
                    # End the painter properly
                    if painter.isActive():
                        painter.end()
                        
            except Exception as e:
                logging.error(f"Error in optimized paint event: {e}")
                # Restore strands if an error occurs
                self_canvas.strands = original_strands
        
        # Replace with our optimized paint event
        self.canvas.paintEvent = optimized_paint_event.__get__(self.canvas, type(self.canvas))

    def draw_selection_square(self, painter):
        """Draw the yellow selection square for the currently selected point."""
        if not self.is_moving or not self.selected_rectangle or not self.affected_strand:
            return
            
        # Set up semi-transparent yellow color
        square_color = QColor(255, 230, 160, 140)  # Yellow with transparency
        painter.setBrush(QBrush(square_color))
        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))  # Solid line for better visibility
        
        # Draw the appropriate yellow rectangle based on moving_side
        yellow_square_size = 85  # Size for the yellow selection square
        half_yellow_size = yellow_square_size / 2
        square_control_size = 35  # Size for control points
        half_control_size = square_control_size / 2
        
        # Only draw the currently moving point's selection square
        if self.moving_side == 0:  # Start point
            yellow_rect = QRectF(
                self.affected_strand.start.x() - half_yellow_size,
                self.affected_strand.start.y() - half_yellow_size,
                yellow_square_size,
                yellow_square_size
            )
            painter.drawRect(yellow_rect)
        elif self.moving_side == 1:  # End point
            yellow_rect = QRectF(
                self.affected_strand.end.x() - half_yellow_size,
                self.affected_strand.end.y() - half_yellow_size,
                yellow_square_size,
                yellow_square_size
            )
            painter.drawRect(yellow_rect)
        elif self.moving_side == 'control_point1' and hasattr(self.affected_strand, 'control_point1'):
            # Use control point size for control points
            yellow_rect = QRectF(
                self.affected_strand.control_point1.x() - half_control_size,
                self.affected_strand.control_point1.y() - half_control_size,
                square_control_size,
                square_control_size
            )
            painter.drawRect(yellow_rect)
        elif self.moving_side == 'control_point2' and hasattr(self.affected_strand, 'control_point2'):
            # Use control point size for control points
            yellow_rect = QRectF(
                self.affected_strand.control_point2.x() - half_control_size,
                self.affected_strand.control_point2.y() - half_control_size,
                square_control_size,
                square_control_size
            )
            painter.drawRect(yellow_rect)

    def mousePressEvent(self, event):
        """
        Handle mouse press events.

        Args:
            event (QMouseEvent): The mouse event.
        """
        pos = event.pos()
        
        # Store canvas's original control points visibility setting
        if hasattr(self.canvas, 'show_control_points'):
            self.original_control_points_visible = self.canvas.show_control_points
            # Show control points during movement for better user feedback
            self.canvas.show_control_points = True
        
        if not self.in_move_mode:
            # Set the originally_selected_strand to the currently selected strand in the layer panel
            self.originally_selected_strand = self.canvas.selected_strand
            self.in_move_mode = True
            # Reset time limiter at the start of move mode
            self.last_update_time = 0
            
            print(f"Entering move mode. self.canvas.selected_strand: {self.canvas.selected_strand}")

        # Store the current selection state
        previously_selected = self.canvas.selected_strand

        print(f"Previously selected strand: {previously_selected}")

        # Log currently selected strands before deselection
        print("Currently selected strands before deselection:")
        for strand in self.canvas.strands:
            if strand.is_selected:
                print(f"- {strand}")
            if isinstance(strand, AttachedStrand):
                for attached in strand.attached_strands:
                    if attached.is_selected:
                        print(f"  - Attached: {attached}")

        # Deselect all strands
        for strand in self.canvas.strands:
            strand.is_selected = False
            if isinstance(strand, AttachedStrand):
                for attached in strand.attached_strands:
                    attached.is_selected = False

        # Setup background cache early
        if not hasattr(self.canvas, 'background_cache'):
            self._setup_background_cache()
                    
        # Handle strand selection and movement
        self.handle_strand_movement(pos)
        
        if self.is_moving:
            self.last_update_pos = pos
            self.accumulated_delta = QPointF(0, 0)
            self.last_snapped_pos = self.canvas.snap_to_grid(pos)
            self.target_pos = self.last_snapped_pos
            
            # Set the temporary selected strand
            self.temp_selected_strand = self.affected_strand
            if self.temp_selected_strand:
                self.temp_selected_strand.is_selected = True
                # Only set originally_selected_strand's selection if it exists
                if self.originally_selected_strand:
                    self.originally_selected_strand.is_selected = True
                self.canvas.selected_attached_strand = self.temp_selected_strand
                
            # Setup efficient paint handler
            if not hasattr(self.canvas, 'original_paintEvent'):
                self._setup_optimized_paint_handler()
                
            # Reset movement flags to ensure proper rendering
            if hasattr(self.canvas, 'movement_first_draw'):
                delattr(self.canvas, 'movement_first_draw')
                
            # Invalidate the background cache to force a clean redraw
            if hasattr(self.canvas, 'invalidate_background_cache'):
                self.canvas.invalidate_background_cache()

        else:
            # If no strand was clicked, revert to the original selection
            if self.originally_selected_strand:
                self.originally_selected_strand.is_selected = True
                self.canvas.selected_attached_strand = self.originally_selected_strand
            elif previously_selected:
                previously_selected.is_selected = True
                self.canvas.selected_attached_strand = previously_selected

        # Update the canvas (full update on initial press)
        self.canvas.update()

    def mouseMoveEvent(self, event):
        """
        Handle mouse move events.
        """
        if self.is_moving and self.moving_point:
            # Frame limiting - use a very responsive value for dragging (16ms = ~60fps)
            current_time = int(time.time() * 1000)  # Convert to milliseconds
            time_since_last = current_time - self.last_update_time
            if time_since_last < 16 and self.last_update_time > 0:  # More responsive frame limiting
                return
                
            self.last_update_time = current_time
            
            # Process events to ensure UI responsiveness
            QApplication.instance().processEvents()
            
            # Get the new position
            new_pos = event.pos()
            
            # 1) Move freely (no grid snap) in real time
            self.update_strand_position(new_pos)

            # Ensure the affected strands are stored for drawing
            affected_strands = getattr(self.canvas, 'affected_strands_for_drawing', [self.affected_strand])
            
            # Calculate a more accurate update rectangle based on the entire strand path
            update_rect = None
            for strand in affected_strands:
                if hasattr(strand, 'path') and strand.path:
                    strand_rect = strand.path.boundingRect()
                    # Add padding to the strand bounding rect for smoother drawing
                    padding = 100
                    strand_rect = strand_rect.adjusted(-padding, -padding, padding, padding)
                    
                    if update_rect is None:
                        update_rect = strand_rect
                    else:
                        update_rect = update_rect.united(strand_rect)
            
            # If we have a previous update rect, include it for clean redrawing
            if self.last_update_rect:
                if update_rect:
                    update_rect = update_rect.united(self.last_update_rect)
                else:
                    update_rect = self.last_update_rect
            
            # If we still don't have an update_rect, fall back to a reasonable area
            if not update_rect:
                # Create a larger rect around the cursor position
                cursor_size = 200
                update_rect = QRectF(
                    new_pos.x() - cursor_size/2,
                    new_pos.y() - cursor_size/2,
                    cursor_size,
                    cursor_size
                )
            
            # Store the update rectangle for next time
            self.canvas.active_strand_update_rect = update_rect
            self.last_update_rect = update_rect
                    
            # Make sure the background cache is invalidated to show the movements
            if hasattr(self.canvas, 'invalidate_background_cache'):
                self.canvas.invalidate_background_cache()
                
            # Force an immediate update for smoother dragging
            self.canvas.update()

            # Use partial update mechanism for optimal performance
            self.partial_update()

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release events.
        """
        # Store if we were moving control points
        was_moving_control_point = self.is_moving and self.moving_point and (
            self.moving_side == 'control_point1' or self.moving_side == 'control_point2')
        
        if self.is_moving and self.moving_point:
            # 3) Snap the final position once on release
            final_snapped_pos = self.canvas.snap_to_grid(event.pos())
            self.update_strand_position(final_snapped_pos)

            # Restore original paint event
            if hasattr(self.canvas, 'original_paintEvent'):
                self.canvas.paintEvent = self.canvas.original_paintEvent
                delattr(self.canvas, 'original_paintEvent')
            
            # Clean up all temp attributes
            if hasattr(self.canvas, 'active_strand_for_drawing'):
                self.canvas.active_strand_for_drawing = None
            if hasattr(self.canvas, 'active_strand_update_rect'):
                self.canvas.active_strand_update_rect = None
            if hasattr(self.canvas, 'last_strand_rect'):
                delattr(self.canvas, 'last_strand_rect')
            if hasattr(self.canvas, 'background_cache'):
                delattr(self.canvas, 'background_cache')
            if hasattr(self.canvas, 'background_cache_valid'):
                delattr(self.canvas, 'background_cache_valid')
            if hasattr(self.canvas, 'movement_first_draw'):
                delattr(self.canvas, 'movement_first_draw')
            if hasattr(self.canvas, 'affected_strands_for_drawing'):
                delattr(self.canvas, 'affected_strands_for_drawing')
            
            # Reset control point movement flag
            self.is_moving_control_point = False
            
            # Restore original control points visibility
            if hasattr(self.canvas, 'show_control_points'):
                self.canvas.show_control_points = self.original_control_points_visible
            
            # Reset time limiter
            self.last_update_time = 0

        # Deselect all strands
        for strand in self.canvas.strands:
            strand.is_selected = False
            if isinstance(strand, AttachedStrand):
                for attached in strand.attached_strands:
                    attached.is_selected = False

        # Restore the selection of the originally selected strand
        if self.originally_selected_strand:
            self.originally_selected_strand.is_selected = True
            self.canvas.selected_attached_strand = self.originally_selected_strand
        # If we were moving a control point, restore selection for the affected strand
        elif was_moving_control_point and self.affected_strand:
            self.affected_strand.is_selected = True
            self.canvas.selected_attached_strand = self.affected_strand

        # Reset all properties
        self.is_moving = False
        self.moving_point = None
        self.affected_strand = None
        self.moving_side = None
        self.selected_rectangle = None
        self.last_update_pos = None
        self.accumulated_delta = QPointF(0, 0)
        self.last_snapped_pos = None
        self.target_pos = None
        self.move_timer.stop()
        self.in_move_mode = False
        self.temp_selected_strand = None  # Reset temporary selection
        self.last_update_rect = None  # Clear the last update rect

        self.canvas.update()

    def gradual_move(self):
        """
        Perform gradual movement of the strand point being moved.
        """
        if not self.target_pos or not self.last_snapped_pos or not self.is_moving:
            self.move_timer.stop()
            return

        # Calculate the distance to move
        dx = self.target_pos.x() - self.last_snapped_pos.x()
        dy = self.target_pos.y() - self.last_snapped_pos.y()

        # Calculate the step size, limited by move_speed
        step_x = min(abs(dx), self.move_speed * self.canvas.grid_size) * (1 if dx > 0 else -1)
        step_y = min(abs(dy), self.move_speed * self.canvas.grid_size) * (1 if dy > 0 else -1)

        # Calculate the new position
        new_x = self.last_snapped_pos.x() + step_x
        new_y = self.last_snapped_pos.y() + step_y

        new_pos = self.canvas.snap_to_grid(QPointF(new_x, new_y))

        if new_pos != self.last_snapped_pos:
            # Update the strand position and cursor
            self.update_strand_position(new_pos)
            self.update_cursor_position(new_pos)
            self.last_snapped_pos = new_pos
            
            # Use partial update for more efficient rendering
            self.partial_update()

        if new_pos == self.target_pos:
            # If we've reached the target, stop the timer
            self.move_timer.stop()

    def handle_strand_movement(self, pos):
        """
        Handle the movement of strands.

        Args:
            pos (QPointF): The position of the mouse click.
        """
        self.is_moving = False  # Reset this flag at the start

        # First pass: Check all control points for all strands
        for strand in self.canvas.strands:
            if not getattr(strand, 'deleted', False):
                if self.try_move_control_points(strand, pos):
                    return
                if self.try_move_attached_strands_control_points(strand.attached_strands, pos):
                    return

        # Second pass: Check start and end points for all strands
        for i, strand in enumerate(self.canvas.strands):
            if not getattr(strand, 'deleted', False) and (not self.lock_mode_active or i not in self.locked_layers):
                if self.try_move_strand(strand, pos, i):
                    return
                if self.try_move_attached_strands_start_end(strand.attached_strands, pos):
                    return

    def try_move_attached_strands_control_points(self, attached_strands, pos):
        """
        Recursively try to move control points of attached strands.

        Args:
            attached_strands (list): List of attached strands to check.
            pos (QPointF): The position to check.

        Returns:
            bool: True if a control point of an attached strand was moved, False otherwise.
        """
        for attached_strand in attached_strands:
            if not getattr(attached_strand, 'deleted', False):
                if self.try_move_control_points(attached_strand, pos):
                    return True
                if self.try_move_attached_strands_control_points(attached_strand.attached_strands, pos):
                    return True
        return False

    def try_move_attached_strands_start_end(self, attached_strands, pos):
        """
        Recursively try to move start and end points of attached strands.

        Args:
            attached_strands (list): List of attached strands to check.
            pos (QPointF): The position to check.

        Returns:
            bool: True if a start or end point of an attached strand was moved, False otherwise.
        """
        for attached_strand in attached_strands:
            if not getattr(attached_strand, 'deleted', False):
                if self.try_move_strand(attached_strand, pos, -1):  # Pass -1 if not in main strands list
                    return True
                if self.try_move_attached_strands_start_end(attached_strand.attached_strands, pos):
                    return True
        return False

    def try_move_control_points(self, strand, pos):
        """
        Try to move a strand's control points if the position is within their selection areas.

        Args:
            strand (Strand): The strand to try moving.
            pos (QPointF): The position to check.

        Returns:
            bool: True if a control point was moved, False otherwise.
        """
        # Skip control point checks for MaskedStrands
        if isinstance(strand, MaskedStrand):
            return False

        control_point1_rect = self.get_control_point_rectangle(strand, 1)
        control_point2_rect = self.get_control_point_rectangle(strand, 2)

        if control_point1_rect.contains(pos):
            self.start_movement(strand, 'control_point1', control_point1_rect)
            # Ensure we only display this control point's selection indicator
            self.affected_strand.is_selected = False  # Temporarily deselect to prevent drawing other indicators
            return True
        elif control_point2_rect.contains(pos):
            self.start_movement(strand, 'control_point2', control_point2_rect)
            # Ensure we only display this control point's selection indicator
            self.affected_strand.is_selected = False  # Temporarily deselect to prevent drawing other indicators
            return True
        return False

    def try_move_strand(self, strand, pos, strand_index):
        """
        Try to move a strand if the position is within its selection areas.

        Args:
            strand (Strand): The strand to try moving.
            pos (QPointF): The position to check.
            strand_index (int): The index of the strand in the canvas's strand list.

        Returns:
            bool: True if the strand was moved, False otherwise.
        """
        # Get selection areas
        start_area = self.get_start_area(strand)
        end_area = self.get_end_area(strand)

        # Only check control points for non-MaskedStrands
        if not isinstance(strand, MaskedStrand):
            control_point1_rect = self.get_control_point_rectangle(strand, 1)
            control_point2_rect = self.get_control_point_rectangle(strand, 2)

            if control_point1_rect.contains(pos):
                self.start_movement(strand, 'control_point1', control_point1_rect)
                # Ensure we only display this control point's selection indicator
                self.affected_strand.is_selected = False  # Temporarily deselect to prevent drawing other indicators
                return True
            elif control_point2_rect.contains(pos):
                self.start_movement(strand, 'control_point2', control_point2_rect)
                # Ensure we only display this control point's selection indicator
                self.affected_strand.is_selected = False  # Temporarily deselect to prevent drawing other indicators
                return True

        if start_area.contains(pos) and self.can_move_side(strand, 0, strand_index):
            self.start_movement(strand, 0, start_area)
            if isinstance(strand, AttachedStrand):
                self.canvas.selected_attached_strand = strand
                strand.is_selected = True
            return True
        elif end_area.contains(pos) and self.can_move_side(strand, 1, strand_index):
            self.start_movement(strand, 1, end_area)
            return True
        return False

    def get_control_point_rectangle(self, strand, control_point_number):
        """Get the rectangle around the specified control point for hit detection."""
        size = 35  # Size of the area for control point selection
        if control_point_number == 1:
            center = strand.control_point1
        elif control_point_number == 2:
            center = strand.control_point2
        else:
            return QRectF()
        return QRectF(center.x() - size / 2, center.y() - size / 2, size, size)

    def get_start_area(self, strand):
        """
        Get the selection area for the start point of a strand.

        Args:
            strand (Strand): The strand to get the area for.

        Returns:
            QPainterPath: The selection area path.
        """
        # Define the outer rectangle (120x120 square)
        outer_size = 120
        half_outer_size = outer_size / 2
        outer_rect = QRectF(
            strand.start.x() - half_outer_size,
            strand.start.y() - half_outer_size,
            outer_size,
            outer_size
        )

        # Create the selection area as the outer rectangle only
        path = QPainterPath()
        path.addRect(outer_rect)

        return path

    def get_end_area(self, strand):
        """
        Get the selection area for the end point of a strand.

        Args:
            strand (Strand): The strand to get the area for.

        Returns:
            QPainterPath: The selection area path.
        """
        # Define the outer rectangle (120x120 square)
        outer_size = 120
        half_outer_size = outer_size / 2
        outer_rect = QRectF(
            strand.end.x() - half_outer_size,
            strand.end.y() - half_outer_size,
            outer_size,
            outer_size
        )

        # Create the selection area as the outer rectangle only
        path = QPainterPath()
        path.addRect(outer_rect)

        return path

    def can_move_side(self, strand, side, strand_index):
        """
        Check if the side of a strand can be moved.

        Args:
            strand (Strand): The strand to check.
            side (int or str): Which side of the strand to check (0 for start, 1 for end, 'control_point1', 'control_point2').
            strand_index (int): The index of the strand in the canvas's strand list.

        Returns:
            bool: True if the side can be moved, False otherwise.
        """
        if not self.lock_mode_active:
            return True

        # Check if the strand itself is locked
        if strand_index in self.locked_layers:
            return False

        if side in ('control_point1', 'control_point2'):
            return True  # Assume control points can be moved unless specific locking is needed

        # Check if the side is shared with a locked strand
        point = strand.start if side == 0 else strand.end
        for i, other_strand in enumerate(self.canvas.strands):
            if i in self.locked_layers:
                if point == other_strand.start or point == other_strand.end:
                    return False

        return True

    def start_movement(self, strand, side, area):
        """
        Start the movement of a strand's point without changing its selection state.
        """
        self.moving_side = side
        
        # For QPainterPath, get the bounding rectangle and center
        if isinstance(area, QPainterPath):
            bounding_rect = area.boundingRect()
            self.moving_point = bounding_rect.center()
        elif isinstance(area, QRectF):
            self.moving_point = area.center()
        else:
            # Default to using the strand's point
            if side == 0:
                self.moving_point = strand.start
            elif side == 1:
                self.moving_point = strand.end
            else:
                self.moving_point = QPointF(0, 0)

        self.affected_strand = strand
        self.selected_rectangle = area
        self.is_moving = True
        # Set the flag if we're moving a control point
        self.is_moving_control_point = side == 'control_point1' or side == 'control_point2'
        
        snapped_pos = self.canvas.snap_to_grid(self.moving_point)
        self.update_cursor_position(snapped_pos)
        self.last_snapped_pos = snapped_pos
        self.target_pos = snapped_pos

        # Find any other strands connected to this point using layer_state_manager
        moving_point = strand.start if side == 0 else strand.end
        connected_strand = self.find_connected_strand(strand, side, moving_point)

        # Only set strands as selected when not moving control points
        is_moving_control_point = side == 'control_point1' or side == 'control_point2'
        
        if not is_moving_control_point:
            # Set both strands as selected for start/end points only
            if isinstance(strand, AttachedStrand):
                self.canvas.selected_attached_strand = strand
                strand.is_selected = True
            
            if connected_strand:
                connected_strand.is_selected = True
                if isinstance(connected_strand, AttachedStrand):
                    self.temp_selected_strand = connected_strand

        # Update the canvas
        self.canvas.update()

    def points_are_close(self, point1, point2, tolerance=5.0):
        """Check if two points are within a certain tolerance."""
        return (abs(point1.x() - point2.x()) <= tolerance and
                abs(point1.y() - point2.y()) <= tolerance)

    def update_strand_position(self, new_pos):
        """
        Update the position of the affected strand's point.

        Args:
            new_pos (QPointF): The new position.
        """
        if not self.affected_strand:
            return

        # Keep track of what strands are affected for optimization
        affected_strands = set([self.affected_strand])
        
        # Store the old path of the affected strand for proper redrawing
        old_path_rect = None
        if hasattr(self.affected_strand, 'path') and self.affected_strand.path:
            old_path_rect = self.affected_strand.path.boundingRect()
            # Add padding
            old_path_rect = old_path_rect.adjusted(-100, -100, 100, 100)

        if self.moving_side == 'control_point1':
            # Move the first control point
            self.affected_strand.control_point1 = new_pos
            self.affected_strand.update_shape()
            self.affected_strand.update_side_line()
            # Update the selection rectangle to the new position
            self.selected_rectangle = self.get_control_point_rectangle(self.affected_strand, 1)
            # Keep the strand deselected to prevent drawing other indicators
            self.affected_strand.is_selected = False
        elif self.moving_side == 'control_point2':
            # Move the second control point
            self.affected_strand.control_point2 = new_pos
            self.affected_strand.update_shape()
            self.affected_strand.update_side_line()
            # Update the selection rectangle to the new position
            self.selected_rectangle = self.get_control_point_rectangle(self.affected_strand, 2)
            # Keep the strand deselected to prevent drawing other indicators
            self.affected_strand.is_selected = False
        elif self.moving_side == 0 or self.moving_side == 1:
            # Moving start or end point - already tracks affected strands
            self.move_strand_and_update_attached(self.affected_strand, new_pos, self.moving_side)
            # Update the selection area
            if self.moving_side == 0:
                self.selected_rectangle = QRectF(
                    self.affected_strand.start.x() - 85/2,
                    self.affected_strand.start.y() - 85/2,
                    85,
                    85
                )
            else:
                self.selected_rectangle = QRectF(
                    self.affected_strand.end.x() - 85/2,
                    self.affected_strand.end.y() - 85/2,
                    85,
                    85
                )
            
            # Get the list of affected strands from move_strand_and_update_attached
            if hasattr(self.canvas, 'affected_strands_for_drawing'):
                affected_strands = set(self.canvas.affected_strands_for_drawing)
                
            # Ensure the affected strand remains selected when moving start/end points
            self.affected_strand.is_selected = True
            self.canvas.selected_attached_strand = self.affected_strand
        else:
            # Invalid moving_side
            pass  # Or handle unexpected cases

        # Create a more accurate update rectangle that includes both the old and new path positions
        update_rect = None
        
        # First, include the old path in the update rect if available
        if old_path_rect:
            update_rect = old_path_rect
        
        # Get all new strand paths and include them
        for strand in affected_strands:
            if hasattr(strand, 'path') and strand.path:
                strand_rect = strand.path.boundingRect()
                # Add padding
                padding = 100
                strand_rect = strand_rect.adjusted(-padding, -padding, padding, padding)
                
                if update_rect is None:
                    update_rect = strand_rect
                else:
                    update_rect = update_rect.united(strand_rect)
        
        # If we still don't have an update_rect, create one from the selection point
        if not update_rect and isinstance(self.selected_rectangle, QRectF):
            # Make it much larger than the selection rectangle to ensure the whole strand is visible
            padding = 200
            update_rect = self.selected_rectangle.adjusted(-padding, -padding, padding, padding)
        elif not update_rect:
            # Fallback to a default size around the new position
            update_rect = QRectF(
                new_pos.x() - 250,
                new_pos.y() - 250,
                500,
                500
            )
        
        # Store the update rectangle for optimized rendering
        self.canvas.active_strand_update_rect = update_rect
        self.last_update_rect = update_rect
        
        # Store affected strands for optimized rendering
        self.canvas.affected_strands_for_drawing = list(affected_strands)
        
        # For immediate visual feedback during dragging, invalidate the cache here too
        if hasattr(self.canvas, 'background_cache_valid'):
            self.canvas.background_cache_valid = False

    def move_strand_and_update_attached(self, strand, new_pos, moving_side):
        """Move the strand's point and update attached strands without resetting control points.

        Args:
            strand (Strand): The strand to move.
            new_pos (QPointF): The new position.
            moving_side (int or str): Which side of the strand is being moved.
        """
        old_start, old_end = strand.start, strand.end
        
        # Keep track of all affected strands for optimized drawing
        affected_strands = set([strand])

        if moving_side == 0:
            # Update control points if they coincide with the start point
            if hasattr(strand, 'control_point1') and strand.control_point1 == strand.start:
                strand.control_point1 = new_pos
            if hasattr(strand, 'control_point2') and strand.control_point2 == strand.start:
                strand.control_point2 = new_pos
            strand.start = new_pos

        elif moving_side == 1:
            # Update control points if they coincide with the end point
            if hasattr(strand, 'control_point1') and strand.control_point1 == strand.end:
                strand.control_point1 = new_pos
            if hasattr(strand, 'control_point2') and strand.control_point2 == strand.end:
                strand.control_point2 = new_pos
            strand.end = new_pos

        strand.update_shape()
        strand.update_side_line()

        # Update parent strands recursively
        parent_strands = self.update_parent_strands(strand)
        affected_strands.update(parent_strands)

        # Update all attached strands without resetting their control points
        attached_strands = self.update_all_attached_strands(strand, old_start, old_end)
        affected_strands.update(attached_strands)

        # If it's an AttachedStrand, update its parent's side line
        if isinstance(strand, AttachedStrand):
            strand.parent.update_side_line()
            affected_strands.add(strand.parent)

        # If it's a MaskedStrand, update both selected strands
        if isinstance(strand, MaskedStrand):
            if strand.first_selected_strand and hasattr(strand.first_selected_strand, 'update'):
                strand.first_selected_strand.update(new_pos)
                affected_strands.add(strand.first_selected_strand)
            if strand.second_selected_strand and hasattr(strand.second_selected_strand, 'update'):
                # For non-AttachedStrand, manually update position
                if not hasattr(strand.second_selected_strand, 'update'):
                    if moving_side == 0:
                        strand.second_selected_strand.start = new_pos
                    else:
                        strand.second_selected_strand.end = new_pos
                    strand.second_selected_strand.update_shape()
                    strand.second_selected_strand.update_side_line()
                else:
                    strand.second_selected_strand.update(new_pos)
                affected_strands.add(strand.second_selected_strand)
                
        # Find any connected strands
        moving_point = strand.start if moving_side == 0 else strand.end
        connected_strand = self.find_connected_strand(strand, moving_side, moving_point)
        if connected_strand:
            affected_strands.add(connected_strand)
            
        # Store affected strands for optimized rendering
        self.canvas.affected_strands_for_drawing = list(affected_strands)

    def update_parent_strands(self, strand):
        """
        Recursively update parent strands.

        Args:
            strand (Strand): The strand whose parents need updating.
            
        Returns:
            set: The set of updated parent strands
        """
        updated_strands = set()
        
        if isinstance(strand, AttachedStrand):
            parent = self.find_parent_strand(strand)
            if parent:
                if strand.start == parent.start:
                    parent.start = strand.start
                else:
                    parent.end = strand.start
                parent.update_shape()
                parent.update_side_line()
                updated_strands.add(parent)
                # Recursively update the parent's parent
                parent_updated = self.update_parent_strands(parent)
                updated_strands.update(parent_updated)
                
        return updated_strands

    def update_all_attached_strands(self, strand, old_start, old_end):
        """Recursively update all attached strands without resetting control points.

        Args:
            strand (Strand): The strand whose attached strands need updating.
            old_start (QPointF): The old start position of the strand.
            old_end (QPointF): The old end position of the strand.
            
        Returns:
            set: The set of updated attached strands
        """
        updated_strands = set()
        
        for attached in strand.attached_strands:
            if attached.start == old_start:
                attached.start = strand.start
            elif attached.start == old_end:
                attached.start = strand.end
            # Update attached strand without resetting control points
            attached.update(attached.end, reset_control_points=False)
            attached.update_side_line()
            updated_strands.add(attached)
            # Recursively update attached strands
            child_updated = self.update_all_attached_strands(attached, attached.start, attached.end)
            updated_strands.update(child_updated)
            
        return updated_strands

    def find_parent_strand(self, attached_strand):
        """
        Find the parent strand of an attached strand.

        Args:
            attached_strand (AttachedStrand): The attached strand to find the parent for.

        Returns:
            Strand: The parent strand, or None if not found.
        """
        for strand in self.canvas.strands:
            if attached_strand in strand.attached_strands:
                return strand
            parent = self.find_parent_in_attached(strand, attached_strand)
            if parent:
                return parent
        return None

    def find_parent_in_attached(self, strand, target):
        """
        Recursively find the parent strand in attached strands.

        Args:
            strand (Strand): The strand to search in.
            target (AttachedStrand): The attached strand to find the parent for.

        Returns:
            Strand: The parent strand, or None if not found.
        """
        for attached in strand.attached_strands:
            if attached == target:
                return strand
            parent = self.find_parent_in_attached(attached, target)
            if parent:
                return parent
        return None

    def cleanup_deleted_strands(self):
        """Remove deleted strands and update references after strand deletion."""
        # Remove deleted strands from the canvas
        self.canvas.strands = [strand for strand in self.canvas.strands if not getattr(strand, 'deleted', False)]

        # Update attached strands for remaining strands
        for strand in self.canvas.strands:
            if isinstance(strand, Strand):
                strand.attached_strands = [attached for attached in strand.attached_strands if not getattr(attached, 'deleted', False)]

        # Clear selection if the selected strand was deleted
        if self.affected_strand and getattr(self.affected_strand, 'deleted', False):
            self.affected_strand = None
            self.is_moving = False
            self.moving_point = None
            self.moving_side = None
            self.selected_rectangle = None
            
        # Invalidate the background cache
        if hasattr(self.canvas, 'invalidate_background_cache'):
            self.canvas.invalidate_background_cache()
            
        # Reset the last_update_rect since we're doing a full update
        self.last_update_rect = None

        # Update the canvas
        self.canvas.update()

    def draw_selected_attached_strand(self, painter):
        """
        Draw a circle around the selected attached strand or the temporary selected strand.

        Args:
            painter (QPainter): The painter object to draw with.
        """
        # Skip drawing all C-shapes if a main strand's starting point is being moved
        if self.is_moving and self.affected_strand and not isinstance(self.affected_strand, AttachedStrand) and self.moving_side == 0:
            return
            
        # Also skip drawing when moving control points
        if self.is_moving and self.affected_strand and self.is_moving_control_point:
            return
            
        # Get list of affected strands if available - these are the only ones we need to highlight
        affected_strands = getattr(self.canvas, 'affected_strands_for_drawing', [])
        
        # Only draw C-shapes for actively moving strands to improve performance
        if self.is_moving and affected_strands:
            for strand in affected_strands:
                if strand.is_selected and hasattr(strand, 'has_circles'):
                    self.draw_c_shape_for_strand(painter, strand)
            return
            
        # Fallback to original logic if we're not in moving mode or don't have affected strands
        # Determine which strand to highlight
        strand_to_highlight = None
        if self.is_moving and self.temp_selected_strand:
            strand_to_highlight = self.temp_selected_strand
        elif not self.is_moving and self.canvas.selected_attached_strand:
            strand_to_highlight = self.canvas.selected_attached_strand
            
        # Only highlight the affected strand if it's set, selected, and we're in moving mode
        if self.is_moving and self.affected_strand and self.affected_strand.is_selected:
            self.draw_c_shape_for_strand(painter, self.affected_strand)
            
            # If the affected strand has attached strands, only draw C-shapes for selected ones
            if hasattr(self.affected_strand, 'attached_strands') and self.affected_strand.attached_strands:
                for attached_strand in self.affected_strand.attached_strands:
                    if attached_strand.is_selected:
                        self.draw_c_shape_for_strand(painter, attached_strand)

        # Only proceed if we have a strand to highlight and it's selected
        if strand_to_highlight and strand_to_highlight.is_selected:
            self.draw_c_shape_for_strand(painter, strand_to_highlight)

    def draw_c_shape_for_strand(self, painter, strand):
        """
        Draw C-shape for a specific strand.
        
        Args:
            painter (QPainter): The painter object to draw with.
            strand: The strand to draw the C-shape for.
        """
        painter.save()
        
        # Skip drawing C-shape highlights if this is the main strand that's moving
        is_main_strand = not isinstance(strand, AttachedStrand)
        is_moving_strand = self.is_moving and self.affected_strand == strand
        
        if is_main_strand and is_moving_strand:
            painter.restore()
            return
        
        # Draw the circles at connection points
        for i, has_circle in enumerate(strand.has_circles):
            # Only draw the start circle (i == 0) for all highlighted strands
            # For end circles (i == 1), don't draw them at all
            if i == 1:
                continue
                
            # Check if this is a main strand (not an attached strand)
            is_main_strand = not isinstance(strand, AttachedStrand)
            
            # Skip drawing C-shapes for main strands at attachment points
            if is_main_strand:
                # If this is a start point (i == 0) and it has an attachment, skip drawing
                if i == 0 and strand.has_circles[0]:
                    continue
                # If this is an end point (i == 1) and it has an attachment, skip drawing
                elif i == 1 and strand.has_circles[1]:
                    continue
            
            # Check if the strand has attached strands on both sides
            has_attached_on_both_sides = False
            if hasattr(strand, 'has_circles'):
                has_attached_on_both_sides = all(strand.has_circles)
            
            # Skip drawing the C-shape for the starting point of a main strand 
            # that doesn't have attached strands on both sides
            if i == 0 and is_main_strand and not has_attached_on_both_sides and not has_circle:
                continue
                
            # Draw the C-shape for the starting point if it has a circle or for attached strands
            if i == 0 or has_circle:
                # Save painter state
                painter.save()
                
                center = strand.start if i == 0 else strand.end
                
                # Calculate the proper radius for the highlight
                outer_radius = strand.width / 2 + strand.stroke_width + 4
                inner_radius = strand.width / 2 + 6
                
                # Create a full circle path for the outer circle
                outer_circle = QPainterPath()
                outer_circle.addEllipse(center, outer_radius, outer_radius)
                
                # Create a path for the inner circle
                inner_circle = QPainterPath()
                inner_circle.addEllipse(center, inner_radius, inner_radius)
                
                # Create a ring path by subtracting the inner circle from the outer circle
                ring_path = outer_circle.subtracted(inner_circle)
                
                # Get the tangent angle at the connection point
                tangent = strand.calculate_cubic_tangent(0.0 if i == 0 else 1.0)
                angle = math.atan2(tangent.y(), tangent.x())
                
                # Create a masking rectangle to create a C-shape
                mask_rect = QPainterPath()
                rect_width = (outer_radius + 5) * 2  # Make it slightly larger to ensure clean cut
                rect_height = (outer_radius + 5) * 2
                rect_x = center.x() - rect_width / 2
                rect_y = center.y()
                mask_rect.addRect(rect_x, rect_y, rect_width, rect_height)
                
                # Apply rotation transform to the masking rectangle
                transform = QTransform()
                transform.translate(center.x(), center.y())
                # Adjust angle based on whether it's start or end point
                if i == 0:
                    transform.rotate(math.degrees(angle - math.pi / 2))
                else:
                    transform.rotate(math.degrees(angle - math.pi / 2) + 180)
                transform.translate(-center.x(), -center.y())
                mask_rect = transform.map(mask_rect)
                
                # Create the C-shaped highlight by subtracting the mask from the ring
                c_shape_path = ring_path.subtracted(mask_rect)
                
                # Draw the C-shaped highlight
                # First draw the stroke (border) with the strand's stroke color
                stroke_pen = QPen(QColor(255, 0, 0, 255), strand.stroke_width)
                stroke_pen.setJoinStyle(Qt.MiterJoin)
                stroke_pen.setCapStyle(Qt.FlatCap)
                painter.setPen(stroke_pen)
                painter.setBrush(QColor(255, 0, 0, 255))  # Fill with red color
                painter.drawPath(c_shape_path)
                
                # Restore painter state
                painter.restore()
        
        painter.restore()

    def find_connected_strand(self, strand, side, moving_point):
        """Find a strand connected to the given strand at the specified side."""
        if not hasattr(self.canvas, 'layer_state_manager') or not self.canvas.layer_state_manager:
            return None

        connections = self.canvas.layer_state_manager.getConnections()
        strand_connections = connections.get(strand.layer_name, [])

        # Get prefix of the current strand
        prefix = strand.layer_name.split('_')[0]

        for connected_layer_name in strand_connections:
            # Only check strands with the same prefix
            if not connected_layer_name.startswith(f"{prefix}_"):
                continue

            # Find the connected strand
            connected_strand = next(
                (s for s in self.canvas.strands 
                 if s.layer_name == connected_layer_name 
                 and not isinstance(s, MaskedStrand)), 
                None
            )

            if connected_strand and connected_strand != strand:
                # Check if the connection point matches the side we're moving
                if (side == 0 and self.points_are_close(connected_strand.end, moving_point)) or \
                   (side == 1 and self.points_are_close(connected_strand.start, moving_point)):
                    return connected_strand

        return None

    def draw(self, painter):
        """
        Draw method called by the canvas during paintEvent.
        
        Args:
            painter (QPainter): The painter object to draw with.
        """
        # Draw the selected attached strand with C-shaped highlights
        self.draw_selected_attached_strand(painter)








