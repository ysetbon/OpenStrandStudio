from PyQt5.QtCore import QPointF, QTimer, pyqtSignal, QObject, QRect, QRectF, Qt
from PyQt5.QtGui import QCursor, QPainter, QPixmap
from PyQt5.QtWidgets import QApplication
import math
import logging
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
            
            
        # When zoomed (either in or out) we need the entire widget repainted **immediately**
        # on every mouse-move; using ``update()`` often coalesces several
        # requests and the intermediate frames never appear, which looks
        # like the strand is being cropped.  ``repaint()`` forces an
        # immediate full paint of the widget (synchronous) so the whole
        # strand is always visible.
        if hasattr(self.canvas, "zoom_factor") and self.canvas.zoom_factor != 1.0:
            logging.info(f"[AttachMode.partial_update] Zoomed (zoom={self.canvas.zoom_factor}), using full repaint for attached strand")
            logging.info(f"  Current strand type: {type(self.canvas.current_strand).__name__}")
            logging.info(f"  Current strand pos: start={self.canvas.current_strand.start}, end={self.canvas.current_strand.end}")
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
        # logging.info(f"[AttachMode.partial_update] Normal zoom partial update for strand {getattr(strand, 'layer_name', 'unknown')}")
        
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
            # logging.info(f"[AttachMode.partial_update] Calling canvas.update() with active_strand_update_rect: {update_rect}")
            self.canvas.update()

    def _get_strand_bounds(self):
        """Return a rectangle that fully covers the *visible* logical area.
        
        logging.info(f"[AttachMode._get_strand_bounds] Called with zoom_factor: {getattr(self.canvas, 'zoom_factor', 1.0)}")

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
            logging.info(f"[AttachMode._get_strand_bounds] Zoomed out - inv_scale: {inv_scale}, logical size: {width}x{height}")

            # Centre the rectangle on the widget centre so that translation in
            # the paint routine still works as expected.
            cx = self.canvas.width()  // 2
            cy = self.canvas.height() // 2

            left   = cx - width  // 2
            top    = cy - height // 2

            bounds = QRect(left, top, width, height)
            logging.info(f"[AttachMode._get_strand_bounds] Returning zoomed-out bounds: {bounds}")
            return bounds

        # Normal (zoom == 1.0 or zoomed-in) – widget rectangle is fine.
        if hasattr(self.canvas, 'viewport'):
            bounds = self.canvas.viewport().rect()
        else:
            bounds = self.canvas.rect()
        # logging.info(f"[AttachMode._get_strand_bounds] Normal zoom - returning widget bounds: {bounds}")
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
            
            logging.info(f"Background cache initialized: {width}x{height} pixels (transparent)")
        except Exception as e:
            logging.error(f"Error setting up background cache: {e}")
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
            import logging
            
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
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Apply zoom transformation
            painter.save()
            canvas_center = QPointF(self_canvas.width() / 2, self_canvas.height() / 2)
            painter.translate(canvas_center)
            # ------------------------------------------------------------
            # Apply pan translation BEFORE scaling so that logical
            # coordinates match the main canvas paintEvent transformation.
            # This keeps the active strand aligned correctly when the
            # user has panned the view.
            # ------------------------------------------------------------
            if hasattr(self_canvas, 'pan_offset_x') and (
                self_canvas.pan_offset_x != 0 or self_canvas.pan_offset_y != 0):
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
                            cache_painter.setRenderHint(QPainter.Antialiasing)
                            
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
                            except Exception as render_error:
                                logging.error(f"Error rendering to cache: {render_error}")
                                cache_painter.fillRect(self_canvas.background_cache.rect(), Qt.transparent)
                            
                            # Restore the strand if needed
                            if temp_index >= 0:
                                self_canvas.strands.insert(temp_index, active_strand)
                                
                            cache_painter.end()
                            self_canvas.background_cache_valid = True
                        except Exception as e:
                            logging.error(f"Error updating cache: {e}")
                            self_canvas.background_cache_valid = False
                            self_canvas.strands = original_strands
                    
                    # Draw the cached background to the update region
                    try:
                        update_rect_adjusted = update_rect.intersected(self_canvas.rect())
                        painter.drawPixmap(update_rect_adjusted, self_canvas.background_cache, update_rect_adjusted)
                    except Exception as draw_error:
                        logging.error(f"Error drawing cached background: {draw_error}")
                        painter.fillRect(update_rect, Qt.transparent)
                        
                        # Draw the grid first if it's enabled
                        if getattr(self_canvas, 'show_grid', False):
                            if hasattr(self_canvas, 'draw_grid'):
                                self_canvas.draw_grid(painter)
                                
                        # Then draw all strands except active one
                        for strand in self.canvas.strands:
                            if strand != active_strand and hasattr(strand, 'draw'):
                                strand.draw(painter)
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
                            strand.draw(painter)
                
                # Draw the active strand last (on top of everything)
                if not hasattr(active_strand, 'canvas'):
                    active_strand.canvas = self_canvas
                # Log for debugging zoom-out issues
                if hasattr(self_canvas, 'zoom_factor') and self_canvas.zoom_factor < 1.0:
                    logging.info(f"Drawing active_strand while zoomed out (zoom={self_canvas.zoom_factor}): {type(active_strand).__name__} {getattr(active_strand, 'layer_name', 'no_name')} start={active_strand.start} end={active_strand.end}")
                active_strand.draw(painter)
                
                # Ensure strands list is restored to its original state
                self_canvas.strands = original_strands
                
            except Exception as e:
                logging.error(f"Error in optimized paint event: {e}")
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
            # Use the already-converted coordinates from the event
            # The main canvas has already converted from screen to canvas coordinates
            canvas_pos = event.pos() if hasattr(event.pos(), 'x') else event.pos()
            
            # Constrain coordinates to stay within visible viewport when zoomed out
            constrained_pos = self.constrain_coordinates_to_visible_viewport(canvas_pos)
            
            final_snapped_pos = self.canvas.snap_to_grid(constrained_pos)
            self.canvas.current_strand.end = final_snapped_pos
            self.canvas.current_strand.update_shape()
            
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
                # --- ADD LOGGING FOR STRAND CREATION ---
                strand_ref = self.canvas.current_strand
                # Check *before* accessing attributes for logging
                if strand_ref:
                    logging.info(f"Strand Creation: Name={strand_ref.layer_name}, Start={strand_ref.start}, End={strand_ref.end}")
                # --- END LOGGING ---
                
                self.strand_created.emit(self.canvas.current_strand)
                
                # State saving will be handled by the enhanced mouseReleaseEvent in undo_redo_manager.py
        else:
            # If we're attaching a strand, create it
            if self.is_attaching and self.canvas.current_strand:
                # --- ADD LOGGING FOR STRAND CREATION ---
                strand_ref = self.canvas.current_strand
                # Check *before* accessing attributes for logging
                if strand_ref:
                    logging.info(f"Strand Creation: Name={strand_ref.layer_name}, Start={strand_ref.start}, End={strand_ref.end}")
                # --- END LOGGING ---
                
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

        # Check if we're in new strand creation mode (initiated by button)
        logging.info(f"AttachMode.mousePressEvent: is_drawing_new_strand={getattr(self.canvas, 'is_drawing_new_strand', False)}")
        if hasattr(self.canvas, 'is_drawing_new_strand') and self.canvas.is_drawing_new_strand:
            # Handle new strand creation initiated by button
            canvas_pos = event.pos() if hasattr(event.pos(), 'x') else event.pos()
            constrained_pos = self.constrain_coordinates_to_visible_viewport(canvas_pos)
            self.start_pos = self.canvas.snap_to_grid(constrained_pos)
            
            # Determine the current set based on existing strands (handles loaded JSON)
            current_set = 1
            if hasattr(self.canvas, 'layer_panel'):
                # Find existing sets from current strands, skipping masked strands
                existing_sets = set()
                logging.info(f"AttachMode: Found {len(self.canvas.strands)} total strands")
                for s in self.canvas.strands:
                    if not isinstance(s, MaskedStrand) and hasattr(s, 'layer_name') and s.layer_name and '_' in s.layer_name:
                        try:
                            set_num = int(s.layer_name.split('_')[0])
                            existing_sets.add(set_num)
                            logging.info(f"AttachMode: Found strand {s.layer_name}, set_num={set_num}")
                        except (ValueError, IndexError):
                            # Skip strands with invalid layer names
                            logging.info(f"AttachMode: Skipping strand with invalid layer_name: {s.layer_name}")
                            continue
                
                logging.info(f"AttachMode: Existing sets: {existing_sets}")
                
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
                logging.info(f"AttachMode: Set strand_colors[{current_set}] to {strand_color.red()},{strand_color.green()},{strand_color.blue()},{strand_color.alpha()}")
            
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
                logging.info(f"Created new strand with set {current_set}, count {count}")
                
            self.canvas.current_strand = new_strand
            self.current_end = self.start_pos
            self.last_snapped_pos = self.start_pos
            self.last_update_rect = None
            
            
            # Clear the new strand creation flag
            self.canvas.is_drawing_new_strand = False
            self.move_timer.start(16)
        elif not self.is_attaching:
            # Handle attachment to existing strands
            canvas_pos = event.pos() if hasattr(event.pos(), 'x') else event.pos()
            self.handle_strand_attachment(canvas_pos)

    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        if self.canvas.current_strand:
            # Use the already-converted coordinates from the event
            # The main canvas has already converted from screen to canvas coordinates
            canvas_pos = event.pos() if hasattr(event.pos(), 'x') else event.pos()
            
            # Constrain coordinates to stay within visible viewport when zoomed out
            constrained_pos = self.constrain_coordinates_to_visible_viewport(canvas_pos)
            
            self.canvas.current_strand.end = constrained_pos
            self.canvas.current_strand.update_shape()

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

        new_pos = self.canvas.snap_to_grid(QPointF(new_x, new_y))

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
        new_end = self.canvas.snap_to_grid(QPointF(new_x, new_y))

        # Update the strand
        self.canvas.current_strand.end = new_end
        self.canvas.current_strand.update_shape()
        self.canvas.current_strand.update_side_line()

    def update_cursor_position(self, pos):
        """Update the cursor position to match the strand end point."""
        if isinstance(pos, QPointF):
            pos = pos.toPoint()
        global_pos = self.canvas.mapToGlobal(pos)
        QCursor.setPos(global_pos)

    def constrain_coordinates_to_visible_viewport(self, pos):
        """Constrain coordinates to reasonable bounds based on zoom level."""
        if not hasattr(self.canvas, 'zoom_factor'):
            return pos
            
        zoom_factor = getattr(self.canvas, 'zoom_factor', 1.0)
        
        # Get canvas dimensions
        canvas_width = self.canvas.width()
        canvas_height = self.canvas.height()
        
        if zoom_factor < 1.0:
            # When zoomed out, allow larger bounds but not extreme negatives
            # Calculate reasonable bounds based on zoom level
            extra_factor = (1.0 / zoom_factor) * 0.8  # 80% of theoretical max to be safe
            
            # Define expanded bounds
            min_x = -canvas_width * extra_factor * 0.3  # Allow some negative space but not too much
            max_x = canvas_width * (1 + extra_factor * 0.3)
            min_y = -canvas_height * extra_factor * 0.3
            max_y = canvas_height * (1 + extra_factor * 0.3)
            
            # Apply bounds
            constrained_x = max(min_x, min(pos.x(), max_x))
            constrained_y = max(min_y, min(pos.y(), max_y))
            
            logging.info(f"[AttachMode.constrain_coordinates] Zoomed out - bounds: x=[{min_x}, {max_x}], y=[{min_y}, {max_y}]")
            logging.info(f"[AttachMode.constrain_coordinates] Constrained pos: ({constrained_x}, {constrained_y})")
            return QPointF(constrained_x, constrained_y)
        else:
            # Normal zoom or zoomed in - apply tighter constraints
            margin = 50
            
            # Constrain position to canvas bounds with margin
            constrained_x = max(margin, min(pos.x(), canvas_width - margin))
            constrained_y = max(margin, min(pos.y(), canvas_height - margin))
            
            return QPointF(constrained_x, constrained_y)

    def handle_strand_attachment(self, pos):
        """Handle the attachment of a new strand to an existing one."""
        # Constrain coordinates to stay within visible viewport when zoomed out
        pos = self.constrain_coordinates_to_visible_viewport(pos)
        
        circle_radius = self.canvas.strand_width * 1.1

        for strand in self.canvas.strands:
            if not isinstance(strand, MaskedStrand) and strand in self.canvas.strands:
                # Check if the strand has any free sides
                if self.has_free_side(strand):
                    # Try to attach to the strand
                    if self.try_attach_to_strand(strand, pos, circle_radius):
                        return
                    # If that fails, try to attach to any of its attached strands
                    if self.try_attach_to_attached_strands(strand.attached_strands, pos, circle_radius):
                        return
            elif isinstance(strand, MaskedStrand):
                print("Cannot attach to a masked strand layer.")

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

    def try_attach_to_strand(self, strand, pos, circle_radius):
        """Try to attach a new strand to either end of an existing strand."""
        distance_to_start = (pos - strand.start).manhattanLength()
        distance_to_end = (pos - strand.end).manhattanLength()

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
            start_attachable = distance_to_start <= circle_radius and not strand.has_circles[0]
        end_attachable = distance_to_end <= circle_radius and not strand.has_circles[1]

        if start_attachable:
            self.start_attachment(strand, strand.start, 0)
            return True
        elif end_attachable:
            self.start_attachment(strand, strand.end, 1)
            return True
        return False

    def start_attachment(self, parent_strand, attach_point, side):
        """Start the attachment process for a new strand."""
        logging.info(f"[AttachMode.start_attachment] Starting attachment to parent strand {parent_strand.layer_name} at side {side}")
        
        # Clear any previous selection/highlighting before starting attachment
        if self.canvas.selected_strand:
            logging.info(f"[AttachMode.start_attachment] Clearing previous selected strand: {self.canvas.selected_strand.layer_name}")
            # Also clear the is_selected property on the strand itself
            if hasattr(self.canvas.selected_strand, 'is_selected'):
                self.canvas.selected_strand.is_selected = False
            self.canvas.selected_strand = None
        if self.canvas.selected_attached_strand:
            logging.info(f"[AttachMode.start_attachment] Clearing previous selected attached strand: {self.canvas.selected_attached_strand.layer_name}")
            # Also clear the is_selected property on the strand itself
            if hasattr(self.canvas.selected_attached_strand, 'is_selected'):
                self.canvas.selected_attached_strand.is_selected = False
            self.canvas.selected_attached_strand = None
        
        # Find the parent strand's group before creating new strand
        parent_group = None
        parent_group_name = None
        if hasattr(self.canvas, 'groups'):
            for group_name, group_data in self.canvas.groups.items():
                if parent_strand.layer_name in group_data.get('layers', []):
                    parent_group = group_data
                    parent_group_name = group_name
                    logging.info(f"[AttachMode.start_attachment] Found parent strand in group: {group_name}")
                    break
        
        self.affected_strand = parent_strand
        self.affected_point = side

        new_strand = AttachedStrand(parent_strand, attach_point, side)
        new_strand.canvas = self.canvas
        
        # Set properties from parent strand
        new_strand.color = parent_strand.color  # Directly set color property
        new_strand.stroke_color = parent_strand.stroke_color  # Copy stroke color from parent
        new_strand.set_number = parent_strand.set_number
        new_strand.is_start_side = False
        
        # Ensure the color is properly set in the canvas's color management system
        if hasattr(self.canvas, 'strand_colors'):
            self.canvas.strand_colors[new_strand.set_number] = parent_strand.color
            logging.info(f"[AttachMode.start_attachment] Set color for set {new_strand.set_number} to {parent_strand.color}")
        
        # Update parent strand
        parent_strand.attached_strands.append(new_strand)
        parent_strand.has_circles[side] = True
        parent_strand.update_attachable()
        
        # Setup canvas and position
        self.canvas.current_strand = new_strand
        self.is_attaching = True
        self.last_snapped_pos = self.canvas.snap_to_grid(attach_point)
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
                
            logging.info(f"Finding next available number for set {set_number}. Existing numbers: {sorted(existing_numbers)}, using: {count}")
            new_strand.layer_name = f"{set_number}_{count}"
            logging.info(f"Created new strand with layer name: {new_strand.layer_name}")

        # If parent was in a group, update group data
        if parent_group and parent_group_name:
            if parent_group_name not in self.canvas.groups:
                logging.warning(f"Group {parent_group_name} not found in canvas.groups")
                logging.info(f"Recreating group with data: {parent_group}")
                self.canvas.groups[parent_group_name] = parent_group
                
            logging.info(f"Group {parent_group_name} main_strands before adding new strand: {self.canvas.groups[parent_group_name].get('main_strands', [])}")
            # Add new strand to group
            self.canvas.groups[parent_group_name]['layers'].append(new_strand.layer_name)
            self.canvas.groups[parent_group_name]['strands'].append(new_strand)
            logging.info(f"Added new strand {new_strand.layer_name} to group {parent_group_name}")
            logging.info(f"Group {parent_group_name} main_strands after adding new strand: {self.canvas.groups[parent_group_name].get('main_strands', [])}")

        # Call canvas's attach_strand method
        self.canvas.attach_strand(parent_strand, new_strand)
        
        # Update connections in layer state manager
        if hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
            # Add the connection between parent and new strand
            connections = self.canvas.layer_state_manager.getConnections()
            if parent_strand.layer_name not in connections:
                connections[parent_strand.layer_name] = []
            connections[parent_strand.layer_name].append(new_strand.layer_name)
            # Also add reverse connection
            if new_strand.layer_name not in connections:
                connections[new_strand.layer_name] = []
            connections[new_strand.layer_name].append(parent_strand.layer_name)
            logging.info(f"Added connection between {parent_strand.layer_name} and {new_strand.layer_name} in layer state manager")
            # Save the updated state
            self.canvas.layer_state_manager.save_current_state()
        
        # Emit signals
        self.strand_attached.emit(parent_strand, new_strand)

    def try_attach_to_attached_strands(self, attached_strands, pos, circle_radius):
        """Recursively try to attach to any of the attached strands."""
        for attached_strand in attached_strands:
            if attached_strand in self.canvas.strands and self.has_free_side(attached_strand):
                if self.try_attach_to_strand(attached_strand, pos, circle_radius):
                    return True
                if self.try_attach_to_attached_strands(attached_strand.attached_strands, pos, circle_radius):
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
