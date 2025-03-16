from PyQt5.QtCore import QPointF, QTimer, pyqtSignal, QObject, QRect, QRectF, Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QApplication
import math
import logging
import time

from strand import Strand, AttachedStrand, MaskedStrand

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
        if not self.canvas.current_strand:
            return
            
        # Frame limiting - don't update too frequently
        current_time = int(time.time() * 1000)  # Convert to milliseconds
        time_since_last = current_time - self.last_update_time
        if time_since_last < self.frame_limit_ms and self.last_update_time > 0:
            return
        self.last_update_time = current_time
        
        # Process pending events to ensure UI responsiveness
        QApplication.instance().processEvents()
        
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
        """Get the bounding rectangle of the entire canvas."""
        # Return the full canvas bounds instead of calculating strand-specific bounds
        if hasattr(self.canvas, 'viewport'):
            return self.canvas.viewport().rect()
        return self.canvas.rect()
            
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
            import PyQt5.QtGui as QtGui
            from PyQt5.QtCore import Qt
            import logging
            
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
            painter = QtGui.QPainter(self_canvas)
            
            try:
                # Store original strands list before any manipulation
                original_strands = list(self_canvas.strands)
                
                # Force full redraw on first attachment operation
                if self.is_attaching and not getattr(self_canvas, 'attachment_first_draw', False):
                    self_canvas.background_cache_valid = False
                    self_canvas.attachment_first_draw = True
                
                # Use background cache if available
                if (hasattr(self_canvas, 'background_cache') and 
                    getattr(self_canvas, 'use_background_cache', True)):  # Default to True if not set
                    # Update cache if needed - only once per application cycle
                    if not getattr(self_canvas, 'background_cache_valid', False):
                        try:
                            # Draw everything except the active strand to the cache
                            cache_painter = QtGui.QPainter(self_canvas.background_cache)
                            cache_painter.setRenderHint(QtGui.QPainter.Antialiasing)
                            
                            # Clear the cache
                            cache_painter.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
                            cache_painter.fillRect(self_canvas.background_cache.rect(), Qt.transparent)
                            cache_painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
                            
                            # Temporarily remove the active strand from the strands list for cache drawing
                            temp_index = -1
                            if active_strand in self_canvas.strands:
                                temp_index = self_canvas.strands.index(active_strand)
                                self_canvas.strands.remove(active_strand)
                                
                            # Draw background and all strands except active one
                            try:
                                # Keep background transparent
                                
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
                                # Try a simpler approach if render fails
                                # Use transparent background instead of palette color
                                cache_painter.fillRect(self_canvas.background_cache.rect(), Qt.transparent)
                            
                            # Restore the strand if needed
                            if temp_index >= 0:
                                self_canvas.strands.insert(temp_index, active_strand)
                                
                            cache_painter.end()
                            self_canvas.background_cache_valid = True
                        except Exception as e:
                            logging.error(f"Error updating cache: {e}")
                            # Make sure cache is reset if there's an error
                            self_canvas.background_cache_valid = False
                            # Restore original strands list in case of error
                            self_canvas.strands = original_strands
                    
                    # Draw the cached background to the update region
                    try:
                        update_rect_adjusted = update_rect.intersected(self_canvas.rect())
                        painter.drawPixmap(update_rect_adjusted, self_canvas.background_cache, update_rect_adjusted)
                    except Exception as draw_error:
                        logging.error(f"Error drawing cached background: {draw_error}")
                        # If we can't draw the cache, maintain transparency
                        painter.fillRect(update_rect, Qt.transparent)
                        
                        # Draw the grid first if it's enabled
                        if getattr(self_canvas, 'show_grid', False):
                            if hasattr(self_canvas, 'draw_grid'):
                                self_canvas.draw_grid(painter)
                                
                        # Then draw all strands except active one
                        for strand in self_canvas.strands:
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
                    for strand in self_canvas.strands:
                        if strand != active_strand and hasattr(strand, 'draw'):
                            strand.draw(painter)
                
                # Save state for safety
                painter.save()
                
                # Set clip rect for efficient drawing
                painter.setClipRect(update_rect)
                
                # Draw the highlight for the affected strand first
                affected_strand = getattr(self_canvas.current_mode, 'affected_strand', None) if hasattr(self_canvas, 'current_mode') else None
                if affected_strand and hasattr(self_canvas, 'draw_highlighted_strand'):
                    # Temporarily set is_selected to ensure highlighting
                    was_selected = getattr(affected_strand, 'is_selected', False)
                    affected_strand.is_selected = True
                    self_canvas.draw_highlighted_strand(painter, affected_strand)
                    # Restore original selection state
                    affected_strand.is_selected = was_selected
                
                # Draw any interaction elements
                if hasattr(self_canvas, 'draw_interaction_elements'):
                    self_canvas.draw_interaction_elements(painter)
                
                # Now draw the active strand last (on top of everything)
                active_strand.draw(painter)
                
                # Make sure control points are drawn properly
                if hasattr(self_canvas, 'show_control_points') and self_canvas.show_control_points and hasattr(self_canvas, 'draw_control_points'):
                    self_canvas.draw_control_points(painter)
                
                # Always restore what we saved
                painter.restore()
                
                # Ensure strands list is restored to its original state
                self_canvas.strands = original_strands
                
            except Exception as e:
                logging.error(f"Error in optimized paint event: {e}")
                # Restore original strands list in case of error
                self_canvas.strands = original_strands
            finally:
                # End the painter properly
                if painter.isActive():
                    painter.end()
        
        # Replace with our optimized paint event
        self.canvas.paintEvent = optimized_paint_event.__get__(self.canvas, type(self.canvas))

    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if self.canvas.current_strand:
            # Snap the final position to the grid once on release
            final_snapped_pos = self.canvas.snap_to_grid(event.pos())
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

        if self.canvas.is_first_strand:
            # If it's the first strand and it has a non-zero length, create it
            if self.canvas.current_strand and self.canvas.current_strand.start != self.canvas.current_strand.end:
                self.strand_created.emit(self.canvas.current_strand)
                self.canvas.is_first_strand = False
        else:
            # If we're attaching a strand, create it
            if self.is_attaching and self.canvas.current_strand:
                self.strand_created.emit(self.canvas.current_strand)
            self.is_attaching = False
        
        # Reset all properties including affected_strand
        self.affected_strand = None
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
        if self.canvas.current_mode == "move":
            return

        if self.canvas.is_first_strand:
            # Get current set from layer panel, ensuring we skip masked strands
            current_set = 1
            if hasattr(self.canvas, 'layer_panel'):
                existing_sets = {int(s.layer_name.split('_')[0]) for s in self.canvas.strands 
                            if not isinstance(s, MaskedStrand) and '_' in s.layer_name}
                while current_set in existing_sets:
                    current_set += 1
                self.canvas.layer_panel.current_set = current_set
            
            self.start_pos = self.canvas.snap_to_grid(event.pos())
            new_strand = Strand(self.start_pos, self.start_pos, self.canvas.strand_width,
                            self.canvas.strand_color, self.canvas.stroke_color,
                            self.canvas.stroke_width)
            new_strand.is_first_strand = True
            new_strand.set_number = current_set
            
            if hasattr(self.canvas, 'layer_panel'):
                count = 1  # First strand in the set
                new_strand.layer_name = f"{current_set}_{count}"
                self.canvas.layer_panel.set_counts[current_set] = count
                logging.info(f"Created first strand with set {current_set}, count {count}")
                
            self.canvas.current_strand = new_strand
            self.current_end = self.start_pos
            self.last_snapped_pos = self.start_pos
            self.last_update_rect = None  # Clear the update rect on new strand creation
            self.move_timer.start(16)
        elif not self.is_attaching:
            # Remove the requirement for a selected strand
            self.handle_strand_attachment(event.pos())

    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        if self.canvas.current_strand:
            # 1) Move freely, no snap, for a smooth drag
            free_pos = event.pos()
            self.canvas.current_strand.end = free_pos
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
        if self.canvas.is_first_strand:
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

    def handle_strand_attachment(self, pos):
        """Handle the attachment of a new strand to an existing one."""
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
        """Check if the strand has any free sides for attachment."""
        return not all(strand.has_circles)

    def try_attach_to_strand(self, strand, pos, circle_radius):
        """Try to attach a new strand to either end of an existing strand."""
        distance_to_start = (pos - strand.start).manhattanLength()
        distance_to_end = (pos - strand.end).manhattanLength()

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

        new_strand = AttachedStrand(parent_strand, attach_point)
        new_strand.canvas = self.canvas
        
        # Set properties from parent strand
        new_strand.color = parent_strand.color  # Directly set color property
        new_strand.set_number = parent_strand.set_number
        new_strand.is_first_strand = False
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
            count = len([s for s in self.canvas.strands if s.set_number == set_number]) + 1
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
