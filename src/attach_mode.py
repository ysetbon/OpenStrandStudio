from PyQt5.QtCore import QPointF, QTimer, pyqtSignal, QObject, QRect, QRectF, Qt
from PyQt5.QtGui import QCursor, QPainter, QPixmap, QPainterPath
from PyQt5.QtWidgets import QApplication
from render_utils import RenderUtils
import math
import time

from strand import Strand
from attached_strand import AttachedStrand
from masked_strand import MaskedStrand

class AttachMode(QObject):
    # Signal emitted when a new strand is created
    strand_created = pyqtSignal(object)
    strand_attached = pyqtSignal(object, object)  # New signal: parent_strand, new_strand

    def __init__(self, canvas):
        """Initialize the AttachMode."""
        super().__init__()
        self.canvas = canvas
        self.affected_strand = None
        self.affected_point = None
        self.initialize_properties()
        self.setup_timer()
        self.last_update_rect = None  # Track the last update region
        
        
        # Store the canvas's control points visibility setting
        self.original_control_points_visible = False
        if hasattr(self.canvas, 'show_control_points'):
            self.original_control_points_visible = self.canvas.show_control_points

    def initialize_properties(self):
        """Initialize all properties used in the AttachMode."""
        self.is_attaching = False  # Flag to indicate if we're currently attaching a strand
        self.start_pos = None  # Starting position of the strand
        self.current_end = None  # Current end position of the strand
        self.target_pos = None  # Target position for gradual movement
        self.last_snapped_pos = None  # Last position snapped to grid
        self.accumulated_delta = QPointF(0, 0)  # Accumulated movement delta
        self.move_speed = 1  # Speed of movement in grid units per step
        self.last_update_time = 0  # Time of last update for frame limiting
        self.frame_limit_ms = 16  # Min time between updates (~ 60 fps)

    def setup_timer(self):
        """Set up the timer for gradual movement."""
        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.gradual_move)

    def partial_update(self):
        """
        Update only the current strand being dragged using highly optimized approach.
        This avoids redrawing all strands on every mouse movement.
        """
        # When the user zooms *out* (zoom_factor < 1.0) the visible region is
        # larger than the original viewport.  Our background-cache approach
        # is based on a pixmap that matches the widget size, so portions of
        # the newly visible area may not be refreshed correctly.  In that
        # scenario we simply fall back to a normal full-canvas repaint which
        # guarantees that everything on-screen is redrawn.

        if not self.canvas.current_strand:
            return
            
            
        # When zoomed OR panned we need the entire widget repainted **immediately**
        # on every mouse-move; using ``update()`` often coalesces several
        # requests and the intermediate frames never appear, which looks
        # like the strand is being cropped.  ``repaint()`` forces an
        # immediate full paint of the widget (synchronous) so the whole
        # strand is always visible.
        zoom_active = hasattr(self.canvas, "zoom_factor") and self.canvas.zoom_factor != 1.0
        pan_active = hasattr(self.canvas, "pan_offset_x") and (self.canvas.pan_offset_x != 0 or self.canvas.pan_offset_y != 0)
        
        if zoom_active or pan_active:
            # Don't use optimized paint handler when zoomed
            if hasattr(self.canvas, 'original_paintEvent'):
                self.canvas.paintEvent = self.canvas.original_paintEvent
                delattr(self.canvas, 'original_paintEvent')
                # Clear optimization flags
                if hasattr(self.canvas, 'active_strand_for_drawing'):
                    self.canvas.active_strand_for_drawing = None
            # Use update() instead of repaint() to avoid synchronous painting
            self.canvas.update()
            return
            
        # Frame limiting - don't update too frequently
        current_time = int(time.time() * 1000)  # Convert to milliseconds
        time_since_last = current_time - self.last_update_time
        if time_since_last < self.frame_limit_ms and self.last_update_time > 0:
            return
        self.last_update_time = current_time
        
        # REMOVED: processEvents() call that was causing temporary windows
        # QApplication.instance().processEvents()
        
        # Store the current strand and calculate minimal update region
        strand = self.canvas.current_strand
        
        # Setup background caching if needed
        if not hasattr(self.canvas, 'background_cache'):
            # Initialize background caching
            self._setup_background_cache()
            
        # If the canvas already has a method to handle this, use it
        if hasattr(self.canvas, 'set_active_strand_update'):
            self.canvas.set_active_strand_update(strand, None)
        else:
            # Create rectangles for efficient updates
            current_rect = self._get_strand_bounds()
            
            # Store previous rectangle for erasing
            prev_rect = getattr(self.canvas, 'last_strand_rect', None)
            update_rect = current_rect
            
            if prev_rect:
                # Union the current and previous rects for complete update
                update_rect = current_rect.united(prev_rect)
            
            # Store for next update
            self.canvas.last_strand_rect = current_rect
            
            # Set active strand
            self.canvas.active_strand_for_drawing = strand
            self.canvas.active_strand_update_rect = update_rect
            
            # Setup efficient paint handler if needed
            if not hasattr(self.canvas, 'original_paintEvent'):
                self._setup_optimized_paint_handler()
            
            # Only update the canvas - can't use update(rect) as it's not supported
            self.canvas.update()

    def _get_strand_bounds(self):
        """Return a rectangle that fully covers the *visible* logical area.
        


        When the user zooms *out* (``zoom_factor`` < 1) the logical area that
        fits into the widget becomes larger than the widget physical
        rectangle.  If we continue to use ``self.canvas.rect()`` the update
        region will be too small and anything that lies outside that rectangle
        (in logical coordinates) will never be repainted.  To avoid the clipped
        updates we expand the rectangle by the inverse of the current zoom
        factor so that it encloses the whole region that is actually visible
        on screen.
        
        Note: This method is now primarily used for fallback cases since we
        use full repaints for any zoom level != 1.0.
        """

        # If we are zoomed-out make a larger rectangle that, once scaled, maps
        # exactly onto the widget.
        if hasattr(self.canvas, "zoom_factor") and self.canvas.zoom_factor < 1.0:
            inv_scale = 1.0 / self.canvas.zoom_factor  # > 1.0 when zoomed-out

            # Size of the logical area that fills the widget after scaling.
            width  = int(self.canvas.width()  * inv_scale)
            height = int(self.canvas.height() * inv_scale)

            # Centre the rectangle on the widget centre so that translation in
            # the paint routine still works as expected.
            cx = self.canvas.width()  // 2
            cy = self.canvas.height() // 2

            left   = cx - width  // 2
            top    = cy - height // 2

            bounds = QRect(left, top, width, height)
            return bounds

        # Normal (zoom == 1.0 or zoomed-in) – widget rectangle is fine.
        if hasattr(self.canvas, 'viewport'):
            bounds = self.canvas.viewport().rect()
        else:
            bounds = self.canvas.rect()
        return bounds
            
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
            
            # NOTE: Do NOT upscale the cache when zoomed-out. It causes the
            # cached area to exceed the widget rectangle, so only the original
            # (0,0,width,height) portion is ever blitted back, leaving the
            # extra visible area unchanged.  By keeping the cache the same
            # size as the widget we ensure the full onscreen region is always
            # refreshed, regardless of the current zoom factor.
            # (Zoom itself is handled via the painter's scale transform.)
            # Therefore, we intentionally skip any width/height adjustment
            # based on zoom_factor here.
            
            # Create the pixmap and fill it
            self.canvas.background_cache = QtGui.QPixmap(width, height)
            # Fill with transparent color, not white
            self.canvas.background_cache.fill(Qt.transparent)
            
            # Create a flag to indicate when the cache needs refreshing
            self.canvas.background_cache_valid = False
            
            # Add method to canvas to invalidate cache when needed
            def invalidate_cache(self_canvas):
                self_canvas.background_cache_valid = False
            
            self.canvas.invalidate_background_cache = invalidate_cache.__get__(self.canvas, type(self.canvas))
        except Exception:
            # If we can't set up the cache, set a flag to disable it
            self.canvas.use_background_cache = False

    def _setup_optimized_paint_handler(self):
        """Setup a highly optimized paint handler for strand editing."""
        # Store the original paintEvent only once
        self.canvas.original_paintEvent = self.canvas.paintEvent
        
        def optimized_paint_event(self_canvas, event):
            """Optimized paint event that uses background caching for efficiency."""
            from PyQt5.QtGui import QPainter, QPixmap
            from PyQt5.QtCore import Qt, QPointF, QRectF
            
            # --------------------------------------------------
            # Global operations such as undo\/redo temporarily set
            # ``_suppress_repaint`` on the canvas so that *no* intermediate
            # frames are rendered.  Because AttachMode replaces the canvas'
            # paintEvent with this optimised handler, we replicate the same
            # early-exit guard used in the standard paintEvent to prevent
            # partial frames (e.g. circles without the corresponding strand)
            # from flashing on screen.
            # --------------------------------------------------
            if getattr(self_canvas, "_suppress_repaint", False):
                return

            # Regular paint if no active strand
            if not hasattr(self_canvas, 'active_strand_for_drawing') or self_canvas.active_strand_for_drawing is None:
                self_canvas.original_paintEvent(event)
                return
                
            # Get the active strand and update rect
            active_strand = self_canvas.active_strand_for_drawing
            update_rect = getattr(self_canvas, 'active_strand_update_rect', event.rect())
            
            # Check if the update rect intersects with the event rect
            # Only proceed with our custom drawing if it does
            if isinstance(update_rect, QRectF):
                # If update_rect is QRectF, convert event.rect() to QRectF too
                if not update_rect.intersects(QRectF(event.rect())):
                    self_canvas.original_paintEvent(event)
                    return
            else:
                # If update_rect is QRect, use event.rect() directly
                if not update_rect.intersects(event.rect()):
                    self_canvas.original_paintEvent(event)
                    return

            # Start the painter
            painter = QPainter(self_canvas)
            RenderUtils.setup_painter(painter, enable_high_quality=True)
            
            # Apply zoom and pan transformation to match main canvas
            painter.save()
            canvas_center = QPointF(self_canvas.width() / 2, self_canvas.height() / 2)
            painter.translate(canvas_center)
            # Apply pan offset before scaling to match main canvas behavior
            if hasattr(self_canvas, 'pan_offset_x'):
                painter.translate(self_canvas.pan_offset_x, self_canvas.pan_offset_y)
            painter.scale(self_canvas.zoom_factor, self_canvas.zoom_factor)
            painter.translate(-canvas_center)
            
            # Disable clipping whenever zoomed out, zoomed in, OR a pan offset is active.
            # When panning, the logical drawing area is translated, so a static
            # clip rect based on widget coordinates would crop the active strand.
            if (hasattr(self_canvas, 'zoom_factor') and self_canvas.zoom_factor != 1.0) or \
               (hasattr(self_canvas, 'pan_offset_x') and (self_canvas.pan_offset_x != 0 or self_canvas.pan_offset_y != 0)):
                painter.setClipping(False)
            else:
                # Normal clipping when not zoomed and not panned
                painter.setClipRect(update_rect)
            
            try:
                # Store original strands list before any manipulation
                original_strands = list(self_canvas.strands)
                
                # Use background cache if available
                if (hasattr(self_canvas, 'background_cache') and 
                    getattr(self_canvas, 'use_background_cache', True)):
                    # Update cache if needed
                    if not getattr(self_canvas, 'background_cache_valid', False):
                        try:
                            # Draw everything except the active strand to the cache
                            cache_painter = QPainter(self_canvas.background_cache)
                            RenderUtils.setup_painter(cache_painter, enable_high_quality=True)
                            
                            # Clear the cache
                            cache_painter.setCompositionMode(QPainter.CompositionMode_Clear)
                            cache_painter.fillRect(self_canvas.background_cache.rect(), Qt.transparent)
                            cache_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                            
                            # Temporarily remove the active strand from the strands list for cache drawing
                            temp_index = -1
                            if active_strand in self_canvas.strands:
                                temp_index = self_canvas.strands.index(active_strand)
                                self_canvas.strands.remove(active_strand)
            
                            # Draw background and all strands except active one
                            try:
                                # Draw the grid first if it's enabled
                                if getattr(self_canvas, 'show_grid', False):
                                    if hasattr(self_canvas, 'draw_grid'):
                                        self_canvas.draw_grid(cache_painter)
                                
                                # Then manually draw each strand except the active one
                                for strand in self_canvas.strands:
                                    if hasattr(strand, 'draw'):
                                        strand.draw(cache_painter)
                            except Exception:
                                # Clear the cache region if rendering to cache fails
                                cache_painter.fillRect(self_canvas.background_cache.rect(), Qt.transparent)
                            
                            # Restore the strand if needed
                            if temp_index >= 0:
                                self_canvas.strands.insert(temp_index, active_strand)
                                
                            cache_painter.end()
                            self_canvas.background_cache_valid = True
                        except Exception:
                            self_canvas.background_cache_valid = False
                            self_canvas.strands = original_strands
                    
                    # Draw the cached background to the update region
                    try:
                        update_rect_adjusted = update_rect.intersected(self_canvas.rect())
                        painter.drawPixmap(update_rect_adjusted, self_canvas.background_cache, update_rect_adjusted)
                    except Exception:
                        painter.fillRect(update_rect, Qt.transparent)
                        
                        # Draw the grid first if it's enabled
                        if getattr(self_canvas, 'show_grid', False):
                            if hasattr(self_canvas, 'draw_grid'):
                                self_canvas.draw_grid(painter)
                                
                        # Then draw all strands except active one
                        for strand in self.canvas.strands:
                            if strand != active_strand and hasattr(strand, 'draw'):
                                strand.draw(painter, skip_painter_setup=True)
                else:
                    # Fallback: Use transparent background
                    painter.fillRect(update_rect, Qt.transparent)
                    
                    # Draw the grid first if it's enabled
                    if getattr(self_canvas, 'show_grid', False):
                        if hasattr(self_canvas, 'draw_grid'):
                            self_canvas.draw_grid(painter)
                            
                    # Then draw all strands except active one
                    for strand in self.canvas.strands:
                        if strand != active_strand and hasattr(strand, 'draw'):
                            strand.draw(painter, skip_painter_setup=True)
                
                # Draw the active strand last (on top of everything)
                if not hasattr(active_strand, 'canvas'):
                    active_strand.canvas = self_canvas
                active_strand.draw(painter)
                
                # Ensure strands list is restored to its original state
                self_canvas.strands = original_strands
                
            except Exception:
                # Restore original strands list in case of error
                self_canvas.strands = original_strands
            finally:
                painter.restore()
                # End the painter properly
                if painter.isActive():
                    painter.end()

        # Replace with our optimized paint event
        self.canvas.paintEvent = optimized_paint_event.__get__(self.canvas, type(self.canvas))

    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if self.canvas.current_strand:
            # The event position is already in canvas coordinates (converted by the canvas)
            canvas_pos = event.pos() if hasattr(event.pos(), 'x') else event.pos()
            
            # No need for coordinate conversion - canvas_pos is already in canvas coordinates
            # Just constrain and snap
            constrained_pos = self.constrain_coordinates_to_visible_viewport(canvas_pos)
            
            final_snapped_pos = self._get_snapped_attachment_position(constrained_pos)
            self.canvas.current_strand.end = final_snapped_pos
            self.canvas.current_strand.update_shape()
            self.target_pos = final_snapped_pos
            self.last_snapped_pos = final_snapped_pos
            
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
            if hasattr(self.canvas, 'attachment_first_draw'):
                delattr(self.canvas, 'attachment_first_draw')
            
            # Restore original control points visibility
            if hasattr(self.canvas, 'show_control_points'):
                self.canvas.show_control_points = self.original_control_points_visible
            
            # Reset time limiter
            self.last_update_time = 0
                
            # Use full update on release to ensure everything is drawn correctly
            self.canvas.update()

        # Check if we're finishing a strand creation (have a current_strand being dragged)
        if self.canvas.current_strand:
            # If the strand has a non-zero length, create it
            if self.canvas.current_strand.start != self.canvas.current_strand.end:
                # No-op: previously logged strand creation details
                
                self.strand_created.emit(self.canvas.current_strand)
                
                # State saving will be handled by the enhanced mouseReleaseEvent in undo_redo_manager.py
        else:
            # If we're attaching a strand, create it
            if self.is_attaching and self.canvas.current_strand:
                # No-op: previously logged strand creation details
                
                self.strand_created.emit(self.canvas.current_strand)
                
                # State saving will be handled by the enhanced mouseReleaseEvent in undo_redo_manager.py
                    
            self.is_attaching = False
        
        # Reset all properties including affected_strand
        self.affected_strand = None
        # Ensure current_strand is set to None *after* potential logging
        self.canvas.current_strand = None 
        self.move_timer.stop()
        self.start_pos = None
        self.current_end = None
        self.target_pos = None
        self.last_snapped_pos = None
        self.last_update_rect = None  # Clear the last update rect
        self.accumulated_delta = QPointF(0, 0)

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        # Store canvas's original control points visibility setting
        if hasattr(self.canvas, 'show_control_points'):
            self.original_control_points_visible = self.canvas.show_control_points
            # Do NOT force control points to be visible - respect user setting
        
        if self.canvas.current_mode == "move":
            return
        
        # In attach mode, we should NOT allow control point movement
        # Comment out this entire section to prevent control point interaction in attach mode
        # canvas_pos = event.pos() if hasattr(event.pos(), 'x') else event.pos()
        # if hasattr(self.canvas, 'move_mode') and self.canvas.move_mode:
        #     # Try to handle control points using the move mode's logic
        #     for strand in self.canvas.strands:
        #         if not getattr(strand, 'deleted', False):
        #             if self.canvas.move_mode.try_move_control_points(strand, canvas_pos, event):
        #                 # Control point was clicked, switch to move mode temporarily
        #                 self.canvas.current_mode = self.canvas.move_mode
        #                 self.canvas.move_mode.mousePressEvent(event)
        #                 return
        #             # Also check attached strands
        #             if hasattr(strand, 'attached_strands'):
        #                 for attached in strand.attached_strands:
        #                     if not getattr(attached, 'deleted', False):
        #                         if self.canvas.move_mode.try_move_control_points(attached, canvas_pos, event):
        #                             # Control point was clicked, switch to move mode temporarily
        #                             self.canvas.current_mode = self.canvas.move_mode
        #                             self.canvas.move_mode.mousePressEvent(event)
        #                             return

        # Check if we're in new strand creation mode (initiated by button)
        if hasattr(self.canvas, 'is_drawing_new_strand') and self.canvas.is_drawing_new_strand:
            # Handle new strand creation initiated by button
            # The event position is already in canvas coordinates (converted by the canvas)
            canvas_pos = event.pos() if hasattr(event.pos(), 'x') else event.pos()
            # No need for coordinate conversion - canvas_pos is already in canvas coordinates
            constrained_pos = self.constrain_coordinates_to_visible_viewport(canvas_pos)
            self.start_pos = self.canvas.snap_to_grid_for_attach(constrained_pos)
            
            # Determine the current set based on existing strands (handles loaded JSON)
            current_set = 1
            if hasattr(self.canvas, 'layer_panel'):
                # Find existing sets from current strands, skipping masked strands
                existing_sets = set()
                for s in self.canvas.strands:
                    if not isinstance(s, MaskedStrand) and hasattr(s, 'layer_name') and s.layer_name and '_' in s.layer_name:
                        try:
                            set_num = int(s.layer_name.split('_')[0])
                            existing_sets.add(set_num)
                        except (ValueError, IndexError):
                            # Skip strands with invalid layer names
                            continue
                
                
                # Use the set number from the button click, or find next available
                button_set = getattr(self.canvas, 'new_strand_set_number', None)
                if button_set and button_set not in existing_sets:
                    current_set = button_set
                else:
                    # Find the next available set number
                    while current_set in existing_sets:
                        current_set += 1
                self.canvas.layer_panel.current_set = current_set
            
            strand_color = getattr(self.canvas, 'default_strand_color', self.canvas.strand_color)
            
            new_strand = Strand(self.start_pos, self.start_pos, self.canvas.strand_width,
                            strand_color, self.canvas.default_stroke_color,
                            self.canvas.stroke_width)
            new_strand.set_number = current_set
            
            # Ensure the color is set in the canvas's color management system
            if hasattr(self.canvas, 'strand_colors'):
                self.canvas.strand_colors[current_set] = strand_color
            
            if hasattr(self.canvas, 'layer_panel'):
                # Get the next count for this set based on existing strands
                existing_counts_in_set = []
                for s in self.canvas.strands:
                    if not isinstance(s, MaskedStrand) and hasattr(s, 'layer_name') and s.layer_name and '_' in s.layer_name:
                        try:
                            parts = s.layer_name.split('_')
                            if len(parts) >= 2 and int(parts[0]) == current_set:
                                count_num = int(parts[1])
                                existing_counts_in_set.append(count_num)
                        except (ValueError, IndexError):
                            # Skip strands with invalid layer names
                            continue
                
                count = max(existing_counts_in_set, default=0) + 1
                
                new_strand.layer_name = f"{current_set}_{count}"
                self.canvas.layer_panel.set_counts[current_set] = count
                
            self.canvas.current_strand = new_strand
            self.current_end = self.start_pos
            self.last_snapped_pos = self.start_pos
            self.last_update_rect = None
            
            
            # Clear the new strand creation flag
            self.canvas.is_drawing_new_strand = False
            self.move_timer.start(16)
        elif not self.is_attaching:
            # Handle attachment to existing strands
            # The event position is already in canvas coordinates (converted by the canvas)
            canvas_pos = event.pos() if hasattr(event.pos(), 'x') else event.pos()
            # No need for coordinate conversion - canvas_pos is already in canvas coordinates
            self.handle_strand_attachment(canvas_pos)

    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        if self.canvas.current_strand:
            # The event position is already in canvas coordinates (converted by the canvas)
            canvas_pos = event.pos() if hasattr(event.pos(), 'x') else event.pos()
            
            # No need for coordinate conversion - canvas_pos is already in canvas coordinates
            # Just constrain coordinates to stay within visible viewport when zoomed out
            constrained_pos = self.constrain_coordinates_to_visible_viewport(canvas_pos)

            snapped_pos = self._get_snapped_attachment_position(constrained_pos)
            self.canvas.current_strand.end = snapped_pos
            self.canvas.current_strand.update_shape()
            self.target_pos = snapped_pos
            self.last_snapped_pos = snapped_pos

            if not self.move_timer.isActive():
                self.move_timer.start(16)

            # Use partial update instead of full canvas update
            self.partial_update()

    def gradual_move(self):
        """Perform gradual movement of the strand end point."""
        if not self.target_pos or not self.last_snapped_pos:
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

        new_pos = self._get_snapped_attachment_position(QPointF(new_x, new_y))

        if new_pos != self.last_snapped_pos:
            # Update the strand position and cursor
            self.update_strand_position(new_pos)
            self.update_cursor_position(new_pos)
            self.last_snapped_pos = new_pos

        if new_pos == self.target_pos:
            # If we've reached the target, stop the timer
            self.move_timer.stop()

    def update_strand_position(self, new_pos):
        """Update the position of the current strand."""
        if self.canvas.current_strand and not self.is_attaching:
            self.update_first_strand(new_pos)
        elif self.is_attaching:
            self.canvas.current_strand.update(new_pos)
        # Use partial update instead of full canvas update
        self.partial_update()

    def update_first_strand(self, end_pos):
        """Update the position of the first strand, snapping to 45-degree angles."""
        if not self.canvas.current_strand:
            return

        # Calculate the angle and round it to the nearest 45 degrees
        dx = end_pos.x() - self.start_pos.x()
        dy = end_pos.y() - self.start_pos.y()
        angle = math.degrees(math.atan2(dy, dx))
        rounded_angle = round(angle / 45) * 45
        rounded_angle = rounded_angle % 360

        # Calculate the new end point with gradual movement
        current_length = (self.canvas.current_strand.end - self.start_pos).manhattanLength()
        target_length = max(self.canvas.grid_size, math.hypot(dx, dy))
        
        # Move the length gradually
        step_size = self.canvas.grid_size * self.move_speed
        new_length = min(current_length + step_size, target_length)
        
        # Calculate the new end position
        new_x = self.start_pos.x() + new_length * math.cos(math.radians(rounded_angle))
        new_y = self.start_pos.y() + new_length * math.sin(math.radians(rounded_angle))
        new_end = self._get_snapped_attachment_position(QPointF(new_x, new_y))

        # Update the strand
        self.canvas.current_strand.end = new_end
        self.canvas.current_strand.update_shape()
        self.canvas.current_strand.update_side_line()

    def update_cursor_position(self, pos):
        """Update the cursor position to match the strand end point."""
        # Convert canvas coordinates to screen coordinates accounting for zoom/pan
        if hasattr(self.canvas, 'canvas_to_screen'):
            screen_pos = self.canvas.canvas_to_screen(pos)
            if isinstance(screen_pos, QPointF):
                screen_pos = screen_pos.toPoint()
            global_pos = self.canvas.mapToGlobal(screen_pos)
            QCursor.setPos(global_pos)
        else:
            # Fallback: don't move cursor if transformation not available
            # This prevents incorrect cursor positioning
            pass

    def constrain_coordinates_to_visible_viewport(self, pos):
        """Constrain coordinates to reasonable bounds based on zoom level and pan offset."""
        if not hasattr(self.canvas, 'zoom_factor'):
            return pos
            
        zoom_factor = getattr(self.canvas, 'zoom_factor', 1.0)
        
        # Get the actual visible area in canvas coordinates accounting for pan
        top_left_canvas = self.canvas.screen_to_canvas(QPointF(0, 0))
        bottom_right_canvas = self.canvas.screen_to_canvas(QPointF(self.canvas.width(), self.canvas.height()))
        
        if zoom_factor < 1.0:
            # When zoomed out, allow larger bounds but not extreme negatives
            # Calculate reasonable bounds based on the visible area
            visible_width = bottom_right_canvas.x() - top_left_canvas.x()
            visible_height = bottom_right_canvas.y() - top_left_canvas.y()
            
            extra_factor = 0.5  # Allow some extension beyond visible area
            
            # Define expanded bounds based on actual visible area
            min_x = top_left_canvas.x() - visible_width * extra_factor
            max_x = bottom_right_canvas.x() + visible_width * extra_factor
            min_y = top_left_canvas.y() - visible_height * extra_factor
            max_y = bottom_right_canvas.y() + visible_height * extra_factor
            
            # Apply bounds
            constrained_x = max(min_x, min(pos.x(), max_x))
            constrained_y = max(min_y, min(pos.y(), max_y))
            
            return QPointF(constrained_x, constrained_y)
        else:
            # Normal zoom or zoomed in - allow more freedom when panning is active
            if hasattr(self.canvas, 'pan_offset_x') and (self.canvas.pan_offset_x != 0 or self.canvas.pan_offset_y != 0):
                # When panning, be more permissive - allow drawing outside visible area
                visible_width = bottom_right_canvas.x() - top_left_canvas.x()
                visible_height = bottom_right_canvas.y() - top_left_canvas.y()
                
                # Allow drawing up to 2x the visible area outside the current view
                extension = 2.0
                min_x = top_left_canvas.x() - visible_width * extension
                max_x = bottom_right_canvas.x() + visible_width * extension
                min_y = top_left_canvas.y() - visible_height * extension
                max_y = bottom_right_canvas.y() + visible_height * extension
                
                constrained_x = max(min_x, min(pos.x(), max_x))
                constrained_y = max(min_y, min(pos.y(), max_y))
            else:
                # Not panning - use tighter constraints
                margin = 50 / zoom_factor  # Adjust margin for zoom level
                constrained_x = max(top_left_canvas.x() + margin, min(pos.x(), bottom_right_canvas.x() - margin))
                constrained_y = max(top_left_canvas.y() + margin, min(pos.y(), bottom_right_canvas.y() - margin))
            
            return QPointF(constrained_x, constrained_y)

    def _get_snapped_attachment_position(self, raw_pos):
        """Return a snapped position that never collapses back onto the strand start."""
        if not self.canvas.current_strand:
            return self.canvas.snap_to_grid_for_attach(raw_pos)

        snapped = self.canvas.snap_to_grid_for_attach(raw_pos)

        # If snapping is disabled or we already have a non-zero length, keep it as-is
        if (not getattr(self.canvas, 'snap_to_grid_attach_enabled', False) or
                snapped != self.canvas.current_strand.start):
            return snapped

        start_point = self.canvas.current_strand.start
        grid = getattr(self.canvas, 'grid_size', 28)

        delta_x = raw_pos.x() - start_point.x()
        delta_y = raw_pos.y() - start_point.y()

        # If the raw pos is exactly on the start point, pick a default direction
        if abs(delta_x) < 1e-6 and abs(delta_y) < 1e-6:
            delta_x = grid
            delta_y = 0.0

        offsets = []
        if abs(delta_x) >= abs(delta_y):
            offsets.append(QPointF(grid if delta_x >= 0 else -grid, 0))
            offsets.append(QPointF(0, grid if delta_y >= 0 else -grid))
        else:
            offsets.append(QPointF(0, grid if delta_y >= 0 else -grid))
            offsets.append(QPointF(grid if delta_x >= 0 else -grid, 0))

        # Diagonal fallback
        offsets.append(QPointF(
            grid if delta_x >= 0 else -grid,
            grid if delta_y >= 0 else -grid
        ))

        for offset in offsets:
            candidate = QPointF(start_point.x() + offset.x(), start_point.y() + offset.y())
            snapped_candidate = self.canvas.snap_to_grid_for_attach(candidate)
            if snapped_candidate != start_point:
                return snapped_candidate

        # Final fallback: step one grid unit along +X
        fallback = QPointF(start_point.x() + grid, start_point.y())
        return self.canvas.snap_to_grid_for_attach(fallback)

    def handle_strand_attachment(self, pos):
        """Handle the attachment of a new strand to an existing one."""
        # pos is already in canvas coordinates, just constrain if needed
        constrained_pos = self.constrain_coordinates_to_visible_viewport(pos)

        for strand in self.canvas.strands:
            if not isinstance(strand, MaskedStrand) and not getattr(strand, 'is_hidden', False) and strand in self.canvas.strands:
                # Check if the strand has any free sides
                if self.has_free_side(strand):
                    # Try to attach to the strand
                    if self.try_attach_to_strand(strand, constrained_pos, None):
                        return
                    # If that fails, try to attach to any of its attached strands
                    if self.try_attach_to_attached_strands(strand.attached_strands, constrained_pos, None):
                        return
            elif isinstance(strand, MaskedStrand):
                pass

    def has_free_side(self, strand):
        """Check if the strand has any free sides for attachment.

        Notes
        -----
        For *AttachedStrand* instances the *start* side (index ``0``) is the point
        where the strand itself is already attached to its parent.  Even if the
        visual half-circle at that location is hidden by the user we must treat
        that side as **permanently occupied** so that additional strands cannot
        be connected there.  Therefore, for an ``AttachedStrand`` only the *end*
        side (index ``1``) is considered when determining if the strand is
        attachable.
        """

        from attached_strand import AttachedStrand  # Local import to avoid cycles

        # For regular Strand we keep previous behaviour: a strand is free if at
        # least one of its ends does **not** have a circle.
        if not isinstance(strand, AttachedStrand):
            return not all(strand.has_circles)

        # AttachedStrand: ignore the start side (index 0) – it is never
        # attachable.  Only report free if the *end* side (index 1) is free.
        return not strand.has_circles[1]

    def get_attachment_area(self, strand, side):
        """Get the attachment area for a strand endpoint, accounting for zoom level."""
        # Use same base size as move mode for consistency, but adjust for zoom
        base_area_size = 120
        
        # Adjust attachment area size based on zoom level to maintain consistent click targets
        if hasattr(self.canvas, 'zoom_factor'):
            # When zoomed out, make area larger in canvas coordinates to maintain consistent screen size
            # When zoomed in, make area smaller in canvas coordinates to maintain consistent screen size
            area_size = base_area_size / self.canvas.zoom_factor
        else:
            area_size = base_area_size
            
        half_size = area_size / 2
        
        if side == 0:  # start point
            point = strand.start
        else:  # end point
            point = strand.end
            
        area_rect = QRectF(
            point.x() - half_size,
            point.y() - half_size,
            area_size,
            area_size
        )
        
        path = QPainterPath()
        path.addRect(area_rect)
        return path

    def try_attach_to_strand(self, strand, pos, circle_radius):
        """Try to attach a new strand to either end of an existing strand."""
        # Get attachment areas for both ends
        start_area = self.get_attachment_area(strand, 0)
        end_area = self.get_attachment_area(strand, 1)
        
        # Check if position is within attachment areas
        start_hit = start_area.contains(pos)
        end_hit = end_area.contains(pos)

        # ------------------------------------------------------------
        # START-SIDE ATTACHMENT RULES
        # ------------------------------------------------------------
        # The *start* point of an AttachedStrand is itself connected to another
        # strand.  Even if the user hides the visual circle at that location we
        # must still treat the side as occupied.  Consequently the start side
        # is **never** attachable for AttachedStrand instances.
        from attached_strand import AttachedStrand  # Local import to avoid cycles

        if isinstance(strand, AttachedStrand):
            start_attachable = False
        else:
            start_attachable = start_hit and not strand.has_circles[0]
        end_attachable = end_hit and not strand.has_circles[1]

        if start_attachable:
            self.start_attachment(strand, strand.start, 0)
            return True
        elif end_attachable:
            self.start_attachment(strand, strand.end, 1)
            return True
        return False

    def start_attachment(self, parent_strand, attach_point, side):
        """Start the attachment process for a new strand."""
        
        # Clear any previous selection/highlighting before starting attachment
        if self.canvas.selected_strand:
            # Clear selection flags on the previously highlighted strand
            if hasattr(self.canvas.selected_strand, 'is_selected'):
                self.canvas.selected_strand.is_selected = False
            # Clear semi-circle highlighting flags, if present (for attached strands)
            if hasattr(self.canvas.selected_strand, 'start_selected'):
                self.canvas.selected_strand.start_selected = False
            if hasattr(self.canvas.selected_strand, 'end_selected'):
                self.canvas.selected_strand.end_selected = False
            self.canvas.selected_strand = None
        if self.canvas.selected_attached_strand:
            # Clear selection flags on the previously highlighted attached strand
            if hasattr(self.canvas.selected_attached_strand, 'is_selected'):
                self.canvas.selected_attached_strand.is_selected = False
            # Clear semi-circle highlighting flags so they are not rendered anymore
            if hasattr(self.canvas.selected_attached_strand, 'start_selected'):
                self.canvas.selected_attached_strand.start_selected = False
            if hasattr(self.canvas.selected_attached_strand, 'end_selected'):
                self.canvas.selected_attached_strand.end_selected = False
            self.canvas.selected_attached_strand = None
        
        # Find the parent strand's group before creating new strand
        parent_group = None
        parent_group_name = None
        if hasattr(self.canvas, 'groups') and self.canvas.groups:
            for group_name, group_data in self.canvas.groups.items():
                if parent_strand.layer_name in group_data.get('layers', []):
                    parent_group = group_data
                    parent_group_name = group_name
                    break
            
            # Previously logged case where parent_group was not found
        
        self.affected_strand = parent_strand
        self.affected_point = side

        new_strand = AttachedStrand(parent_strand, attach_point, side)
        new_strand.canvas = self.canvas
        
        # Set properties from parent strand
        new_strand.color = parent_strand.color  # Directly set color property
        new_strand.stroke_color = parent_strand.stroke_color  # Copy stroke color from parent
        new_strand.set_number = parent_strand.set_number
        new_strand.is_start_side = False
        # Apply control point influence parameters from canvas settings
        new_strand.curve_response_exponent = self.canvas.curve_response_exponent
        new_strand.control_point_base_fraction = self.canvas.control_point_base_fraction
        new_strand.distance_multiplier = self.canvas.distance_multiplier
        
        # Ensure the color is properly set in the canvas's color management system
        if hasattr(self.canvas, 'strand_colors'):
            self.canvas.strand_colors[new_strand.set_number] = parent_strand.color
        
        # Update parent strand
        parent_strand.attached_strands.append(new_strand)
        parent_strand.has_circles[side] = True
        
        # Clear knot freed flag for this side since we're making a new connection
        if hasattr(parent_strand, 'knot_freed_ends'):
            side_name = 'start' if side == 0 else 'end'
            parent_strand.knot_freed_ends.discard(side_name)
        
        parent_strand.update_attachable()
        
        # Setup canvas and position
        self.canvas.current_strand = new_strand
        self.is_attaching = True
        self.last_snapped_pos = self.canvas.snap_to_grid_for_attach(attach_point)
        self.target_pos = self.last_snapped_pos
        # Reset the update rect for the new attachment
        self.last_update_rect = None
        
        # Reset the attachment drawing flags to ensure full redraw
        if hasattr(self.canvas, 'background_cache_valid'):
            self.canvas.background_cache_valid = False
        if hasattr(self.canvas, 'attachment_first_draw'):
            self.canvas.attachment_first_draw = False
        
        # Force a full update to ensure all strands are visible
        self.canvas.update()

        # Update layer name
        if self.canvas.layer_panel:
            set_number = parent_strand.set_number
            # Instead of just counting strands, find the next available number
            existing_numbers = set()
            for s in self.canvas.strands:
                if s.set_number == set_number and hasattr(s, 'layer_name'):
                    parts = s.layer_name.split('_')
                    if len(parts) >= 2 and parts[1].isdigit():
                        existing_numbers.add(int(parts[1]))
            
            # Find the first available number
            count = 1
            while count in existing_numbers:
                count += 1
                
            new_strand.layer_name = f"{set_number}_{count}"

        # Call canvas's attach_strand method FIRST to handle any group cleanup
        self.canvas.attach_strand(parent_strand, new_strand)

        # If parent was in a group and the group still exists after attach_strand processing, update group data
        if parent_group and parent_group_name and parent_group_name in self.canvas.groups:
            # Add new strand to group
            self.canvas.groups[parent_group_name]['layers'].append(new_strand.layer_name)
            self.canvas.groups[parent_group_name]['strands'].append(new_strand)
        elif parent_group and parent_group_name:
            # Group was deleted or not found after attach_strand processing
            pass
        
        # Update connections in layer state manager
        # NOTE: Don't manually update connections here - let LayerStateManager.save_current_state() 
        # calculate them based on the actual strand relationships (parent/child, attachment_side, etc.)
        # This ensures connections are always in the correct format: [start_connection(end_point), end_connection(end_point)]
        if hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
            # Force a state save to recalculate connections properly
            self.canvas.layer_state_manager.save_current_state()
            # Note: State saving will be handled by the undo_redo_manager through strand_created signal
        
        # Emit signals
        self.strand_attached.emit(parent_strand, new_strand)

    def try_attach_to_attached_strands(self, attached_strands, pos, circle_radius):
        """Recursively try to attach to any of the attached strands."""
        for attached_strand in attached_strands:
            if not getattr(attached_strand, 'is_hidden', False) and attached_strand in self.canvas.strands and self.has_free_side(attached_strand):
                if self.try_attach_to_strand(attached_strand, pos, None):
                    return True
                if self.try_attach_to_attached_strands(attached_strand.attached_strands, pos, None):
                    return True
        return False

    def cleanup_deleted_strands(self):
        """Remove deleted strands and update references after strand deletion."""
        # Remove deleted strands from the canvas
        self.canvas.strands = [strand for strand in self.canvas.strands if not getattr(strand, 'deleted', False)]
        
        # Update attached strands for remaining strands
        for strand in self.canvas.strands:
            if isinstance(strand, Strand):
                strand.attached_strands = [attached for attached in strand.attached_strands if not getattr(attached, 'deleted', False)]
        
        # Clear selection if the selected strand was deleted
        if self.canvas.selected_strand and getattr(self.canvas.selected_strand, 'deleted', False):
            self.canvas.selected_strand = None
            self.canvas.selected_strand_index = None
        
        # For deletion, we need a full canvas update since multiple strands may be affected
        # Reset the last_update_rect since we're doing a full update
        self.last_update_rect = None
        self.canvas.update()
