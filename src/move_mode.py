import logging
import math
import time
from PyQt5.QtCore import QPointF, QRectF, QTimer, Qt, QTime, QEventLoop
from PyQt5.QtGui import QCursor, QPen, QColor, QPainterPathStroker, QTransform, QBrush, QPolygonF, QPainterPath, QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QWidget
import PyQt5.QtGui as QtGui
from render_utils import RenderUtils
from strand import Strand
from attached_strand import AttachedStrand
from masked_strand import MaskedStrand
import os # Required for path normalization

class PerformanceLogger:
    """Logger that can suppress verbose logging during performance-critical operations."""
    
    def __init__(self):
        self.suppress_move_logging = True  # Suppress verbose logging during moves by default
        self.original_level = logging.getLogger().level
        
    def suppress_during_move(self, suppress=True):
        """Temporarily change logging level to reduce performance impact during moves."""
        if suppress and self.suppress_move_logging:
            # Set to WARNING level to suppress INFO logs during movement
            # Apply to root logger and all existing loggers
            logging.getLogger().setLevel(logging.WARNING)
            # Also suppress specific loggers that might have their own levels
            for name in logging.Logger.manager.loggerDict:
                logger = logging.getLogger(name)
                if logger.level < logging.WARNING:
                    logger.setLevel(logging.WARNING)
        else:
            # Restore original logging level
            logging.getLogger().setLevel(self.original_level)
            # Restore other loggers to INFO level
            for name in logging.Logger.manager.loggerDict:
                logger = logging.getLogger(name)
                if logger.level == logging.WARNING:
                    logger.setLevel(logging.INFO)
            
    def log_if_allowed(self, level, message):
        """Log a message only if not suppressing move logging."""
        if not self.suppress_move_logging or level >= logging.WARNING:
            logging.log(level, message)

# Global performance logger instance
perf_logger = PerformanceLogger()

class MoveMode:
    def __init__(self, canvas):
        """
        Initialize the MoveMode.
        
        Args:
            canvas (Canvas): The canvas this mode is attached to.
        """
        self.canvas = canvas
        self.is_moving = False
        self.moving_control_point = -1
        self.moving_side = None
        self.originally_selected_strand = None
        self.highlighted_strand = None
        self.start_position = None
        self.points = []
        self.selection_start = None
        self.selection_end = None
        self.area = None
        self.in_move_mode = False
        self.shift_pressed = False
        self.ctrl_pressed = False
        
        # New property to control drawing behavior during strand movement
        self.draw_only_affected_strand = False
        
        # Initialize properties and set up timers
        self.initialize_properties()
        self.setup_timer()
        
        self.originally_selected_strand = None
        self.in_move_mode = False
        self.temp_selected_strand = None
        self.last_update_time = 0  # Time of last update for frame limiting
        self.frame_limit_ms = 16  # Min time between updates (~ 60 fps)

        # Initialize position tracking
        self.last_strand_position = None
        # Flag to indicate if we're currently moving a control point
        self.is_moving_control_point = False
        # Flag to indicate if we're moving a strand endpoint
        self.is_moving_strand_point = False
        # Track the highlighted strand that should be preserved during operations
        self.highlighted_strand = None
        # Track if user has explicitly deselected all strands
        self.user_deselected_all = False
        # Connect to the canvas's deselect_all signal if available
        if hasattr(self.canvas, 'deselect_all_signal'):
            self.canvas.deselect_all_signal.connect(self.reset_selection)
        # Minimum distance between start and end points of a strand
        self.MIN_STRAND_POINTS_DISTANCE = 10.0
        # Track mouse offset to prevent jumps when starting movement
        self.mouse_offset = QPointF(0, 0)

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
        self.is_moving_control_point = False  # Flag to indicate if we're moving a control point
        self.is_moving_strand_point = False  # Flag to indicate if we're moving a strand endpoint
        self.mouse_offset = QPointF(0, 0)  # Track mouse offset to prevent jumps when starting movement
        
        # Connection caching for performance optimization
        self.connection_cache = {}  # Cache for connection relationships
        self.cache_valid = False  # Flag to track if cache is valid

    def setup_timer(self):
        """Set up the timer for gradual movement."""
        from PyQt5.QtCore import QTimer
        
        # Timer for gradual movement
        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.gradual_move)
        
        # Timer for holding updates (continuous redraw while mouse is held)
        self.hold_timer = QTimer()
        self.hold_timer.timeout.connect(self.force_redraw_while_holding)
        self.hold_timer.setInterval(16)  # ~60fps for smooth updates
        
        # Also set up a redraw timer for continuous updates
        self.redraw_timer = QTimer()
        self.redraw_timer.timeout.connect(self.force_continuous_redraw)
        self.redraw_timer.setInterval(16)  # ~60fps for smooth updates

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
        Properly handles zoom transformation.

        Args:
            pos (QPointF): The new position for the cursor in canvas coordinates.
        """
        # Convert canvas coordinates to widget coordinates accounting for zoom
        # Apply the same transformation that the canvas uses for drawing
        canvas_center = QPointF(self.canvas.width() / 2, self.canvas.height() / 2)
        
        # Apply zoom transformation: translate to center, scale, translate back
        transformed_pos = QPointF(pos)
        
        # Translate to center
        transformed_pos -= canvas_center
        
        # Apply zoom scaling
        if hasattr(self.canvas, 'zoom_factor'):
            transformed_pos *= self.canvas.zoom_factor
        
        # Translate back from center
        transformed_pos += canvas_center
        
        # Convert to integer coordinates
        widget_pos = transformed_pos.toPoint()
        
        # Convert widget coordinates to global screen coordinates
        global_pos = self.canvas.mapToGlobal(widget_pos)
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
        
        # Determine if we need a full update - only do this occasionally to maintain performance
        full_update = False
        if not hasattr(self, '_update_counter'):
            self._update_counter = 0
        self._update_counter = (self._update_counter + 1) % 60  # Reduced frequency for full updates (was 30)
        if self._update_counter == 0:
            full_update = True
            
        # Check if we're moving a C-shape (semi-circle) element
        is_moving_c_shape = False
        if self.is_moving and self.affected_strand and hasattr(self.affected_strand, 'has_circles'):
            # C-shape movement happens when a strand with circles is being moved
            is_moving_c_shape = any(self.affected_strand.has_circles)
            
        # Significant movement check - only for tracking bounds, not for invalidation
        significant_movement = False
        if (hasattr(self, 'last_strand_position') and self.last_strand_position is not None and 
            hasattr(self, 'moving_point') and self.moving_point is not None):
            # Check if the strand has moved more than 5 pixels in any direction
            last_pos = self.last_strand_position
            dx = abs(self.moving_point.x() - last_pos.x())
            dy = abs(self.moving_point.y() - last_pos.y())
            significant_movement = dx > 5 or dy > 5
            
        # Calculate a wider viewing rectangle to ensure no cropping during movement
        # Only recalculate if something significant changed
        if full_update or not hasattr(self.canvas, 'last_strand_rect') or significant_movement:
            # Calculate a rectangle that encompasses the entire affected strand
            current_rect = self._get_strand_bounds(affected_strands)
            
            # Store the current position for future comparison
            if hasattr(self, 'moving_point') and self.moving_point is not None:
                self.last_strand_position = QPointF(self.moving_point.x(), self.moving_point.y())
        else:
            # Reuse the existing rect to avoid expensive recalculations
            current_rect = getattr(self.canvas, 'last_strand_rect', None)
            
        # Store for next update only if it's changed
        if current_rect and (not hasattr(self.canvas, 'last_strand_rect') or 
                          getattr(self.canvas, 'last_strand_rect', None) is None or
                          (isinstance(current_rect, QRectF) and 
                           not current_rect.isNull() and 
                           current_rect != getattr(self.canvas, 'last_strand_rect', None))):
            self.canvas.last_strand_rect = current_rect
            self.last_update_rect = current_rect  # Also store in the MoveMode instance
            
        # Set active strand for drawing
        self.canvas.active_strand_for_drawing = self.affected_strand
        
        # Setup efficient paint handler if needed
        if not hasattr(self.canvas, 'original_paintEvent'):
            self._setup_optimized_paint_handler()
        
        # Track first movement of C-shape
        if is_moving_c_shape and not hasattr(self, '_c_shape_first_move'):
            self._c_shape_first_move = True
            # For first C-shape movement, ensure cache is invalidated
            if hasattr(self.canvas, 'background_cache_valid'):
                self.canvas.background_cache_valid = False
            # Use partial update
            self.canvas.update()
            return
            
        # Only invalidate the background cache on significant events:
        # 1. Full updates (periodically)
        # 2. When strands move significantly, but NOT for C-shapes (that's the key optimization)
        # 3. First time in moving mode
        # 4. Viewport size change
        should_invalidate = (
            full_update or 
            (significant_movement and not is_moving_c_shape) or 
            not hasattr(self.canvas, 'background_cache_valid') or
            not getattr(self.canvas, 'background_cache_valid', False)
        )
        
        if should_invalidate and hasattr(self.canvas, 'background_cache_valid'):
            self.canvas.background_cache_valid = False
        
        # Force an immediate update of the canvas
        self.canvas.update()

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
            
        except Exception as e:
            # If we can't set up the cache, set a flag to disable it
            self.canvas.use_background_cache = False

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
            
            if not perf_logger.suppress_move_logging:
                logging.info("MoveMode: Optimized paint event triggered")
            
            # Access the MoveMode instance through the stored reference
            move_mode = move_mode_ref
            
            # --- MODIFIED ENTRY CONDITION ---
            # Check if we should use the optimized path based on moving state and populated truly_moving_strands
            use_optimized_path = False
            if hasattr(move_mode_ref, 'is_moving') and move_mode_ref.is_moving:
                 truly_moving_strands_check = getattr(self_canvas, 'truly_moving_strands', [])
                 if truly_moving_strands_check: # If there are strands marked for optimized drawing
                     use_optimized_path = True
                 # Fallback: Check if the legacy active_strand is set (less reliable but keep for safety)
                 elif hasattr(self_canvas, 'active_strand_for_drawing') and self_canvas.active_strand_for_drawing is not None:
                      logging.warning("MoveMode: Using optimized path based on fallback active_strand_for_drawing.")
                      use_optimized_path = True

            if not use_optimized_path:
                logging.info(f"MoveMode: Not moving (is_moving={getattr(move_mode_ref, 'is_moving', False)}) or no strands designated for optimized drawing, using original paint event.")
                logging.info(f"MoveMode: show_control_points={getattr(self_canvas, 'show_control_points', False)}")
                # If the original event exists, call it. Otherwise, maybe log an error or do nothing.
                if hasattr(self_canvas, 'original_paintEvent'):
                    self_canvas.original_paintEvent(event)
                else:
                    # This case should ideally not happen if setup is correct
                    logging.error("MoveMode: Optimized paint called but no original_paintEvent found and not in optimized state.")
                return
            # --- END MODIFIED ENTRY CONDITION ---

            # If we reach here, we are using the optimized path.
            # Get the lists needed for drawing.
            active_strand = getattr(self_canvas, 'active_strand_for_drawing', None) # Still useful for some logic/logging
            truly_moving_strands = getattr(self_canvas, 'truly_moving_strands', []) # This is the key list
            affected_strands = getattr(self_canvas, 'affected_strands_for_drawing', truly_moving_strands) # Default to truly_moving if affected not set

        

            # Store original order of all strands for proper z-ordering
            original_strands_order = list(self_canvas.strands)
            
            # --- MODIFIED: Don't exit early if active_strand is None but truly_moving_strands has strands ---
            if not hasattr(self_canvas, 'active_strand_for_drawing') or self_canvas.active_strand_for_drawing is None:
                if truly_moving_strands:
                    # Set the first truly moving strand as the active strand to avoid early exit
                    self_canvas.active_strand_for_drawing = truly_moving_strands[0]
                    active_strand = truly_moving_strands[0]
                else:
                    # Only exit if no truly moving strands AND no active strand
                    self_canvas.original_paintEvent(event)
                    return
            # --- END MODIFIED ---
                
            # Get the active strand and affected strands
            active_strand = self_canvas.active_strand_for_drawing
            affected_strands = getattr(self_canvas, 'affected_strands_for_drawing', [active_strand])
            
            logging.info("MoveMode: Active strand: %s, Affected strands: %d", 
                        active_strand.__class__.__name__, len(affected_strands))
            
            # Special handling for the very first paint during movement to ensure consistent rendering
            first_movement = hasattr(self_canvas, 'movement_first_draw') and self_canvas.movement_first_draw == False
            
            # Create a background cache first time or if it's invalidated
            background_cache_needed = (not hasattr(self_canvas, 'background_cache') or 
                                    not getattr(self_canvas, 'background_cache_valid', False) or
                                    first_movement)
            
            # Always regenerate cache when handling MaskedStrand
            if isinstance(active_strand, MaskedStrand):
                logging.info("MoveMode: Active strand is MaskedStrand, forcing cache regeneration")
                background_cache_needed = True
                # Also ensure the first paint flag is set correctly for edited masks
                if not hasattr(self_canvas, 'movement_first_draw') or self_canvas.movement_first_draw is None:
                    self_canvas.movement_first_draw = False
            
            # Always force a full redraw on the first few frames after clicking
            # This ensures everything is drawn properly even if the mouse isn't moved
            if not hasattr(self_canvas, '_frames_since_click'):
                self_canvas._frames_since_click = 0
                background_cache_needed = True
            elif self_canvas._frames_since_click < 3:
                self_canvas._frames_since_click += 1
                background_cache_needed = True
       
            
            
            if first_movement:
                # Mark that we've completed the first draw
                self_canvas.movement_first_draw = True
                # Always regenerate background on first movement
                background_cache_needed = True
                
                # To ensure consistent rendering, force recreate the background cache
                if hasattr(self_canvas, 'background_cache'):
                    # Force recreation with proper dimensions
                    viewport_rect = self_canvas.viewport().rect() if hasattr(self_canvas, 'viewport') else self_canvas.rect()
                    width = max(1, viewport_rect.width())
                    height = max(1, viewport_rect.height())
                    self_canvas.background_cache = QtGui.QPixmap(width, height)
                    self_canvas.background_cache.fill(Qt.transparent)
            
            # Get truly moving strands from the canvas attribute if available, otherwise create it
            truly_moving_strands = getattr(self_canvas, 'truly_moving_strands', [])
            if not truly_moving_strands and hasattr(move_mode, 'affected_strand') and move_mode.affected_strand:
                truly_moving_strands = [move_mode.affected_strand]
                # For attached strands, we want to also move immediate children but keep parents in original order
                if isinstance(move_mode.affected_strand, AttachedStrand) and hasattr(move_mode.affected_strand, 'attached_strands'):
                    # Include the attached strands of the moving strand
                    truly_moving_strands.extend(move_mode.affected_strand.attached_strands)
                
                # Special handling for MaskedStrand - ensure both selected strands are included
                if isinstance(move_mode.affected_strand, MaskedStrand):
                    if hasattr(move_mode.affected_strand, 'first_selected_strand') and move_mode.affected_strand.first_selected_strand:
                        if move_mode.affected_strand.first_selected_strand not in truly_moving_strands:
                            truly_moving_strands.append(move_mode.affected_strand.first_selected_strand)
                    if hasattr(move_mode.affected_strand, 'second_selected_strand') and move_mode.affected_strand.second_selected_strand:
                        if move_mode.affected_strand.second_selected_strand not in truly_moving_strands:
                            truly_moving_strands.append(move_mode.affected_strand.second_selected_strand)
                
                # Store the truly moving strands for use in drawing
                self_canvas.truly_moving_strands = truly_moving_strands
                
            # When moving control points, ensure the strand gets included in truly_moving_strands
            if getattr(move_mode, 'is_moving_control_point', False) and move_mode.affected_strand:
                if move_mode.affected_strand not in truly_moving_strands:
                    truly_moving_strands = [move_mode.affected_strand]
                    self_canvas.truly_moving_strands = truly_moving_strands
                    
                # Clear the selection when moving control points to prevent unwanted highlighting
                for strand in self_canvas.strands:
                    strand.is_selected = False
                # Also clear the selected_attached_strand
                self_canvas.selected_attached_strand = None
                # Clear the highlighted strand
                move_mode.highlighted_strand = None
            
            # Always provide some truly_moving_strands even when static - critical for MaskedStrand
            if not truly_moving_strands and isinstance(active_strand, MaskedStrand):
                truly_moving_strands = [active_strand]
                if hasattr(active_strand, 'first_selected_strand') and active_strand.first_selected_strand:
                    truly_moving_strands.append(active_strand.first_selected_strand)
                if hasattr(active_strand, 'second_selected_strand') and active_strand.second_selected_strand:
                    truly_moving_strands.append(active_strand.second_selected_strand)
                self_canvas.truly_moving_strands = truly_moving_strands
            
            # Log the number of truly moving strands
            
            if background_cache_needed:
                try:
                    # Create or get the background cache
                    if not hasattr(self_canvas, 'background_cache'):
                        logging.info("MoveMode: Creating new background cache")
                        viewport_rect = self_canvas.viewport().rect() if hasattr(self_canvas, 'viewport') else self_canvas.rect()
                        width = max(1, viewport_rect.width())
                        height = max(1, viewport_rect.height())
                        self_canvas.background_cache = QtGui.QPixmap(width, height)
                        self_canvas.background_cache.fill(Qt.transparent)
                    
                    # Save the original strands list
                    original_strands = list(self_canvas.strands)
                    
                    # Create a temporary list without the truly moving strands
                    # This way, affected but not moving strands (like parent strands) 
                    # will be drawn in their original order
                    static_strands = [s for s in original_strands if s not in truly_moving_strands]
                    
                    # For MaskedStrand, ensure both constituent strands are handled properly
                    if isinstance(active_strand, MaskedStrand):
                        # Add this check to ensure proper handling of edited masks
                        logging.info("MoveMode: Removing MaskedStrand constituent strands from static_strands")
                        if hasattr(active_strand, 'first_selected_strand') and active_strand.first_selected_strand:
                            if active_strand.first_selected_strand in static_strands:
                                static_strands.remove(active_strand.first_selected_strand)
                        if hasattr(active_strand, 'second_selected_strand') and active_strand.second_selected_strand:
                            if active_strand.second_selected_strand in static_strands:
                                static_strands.remove(active_strand.second_selected_strand)
                    
                    # Log strand counts
                    logging.info("MoveMode: Original strands: %d, Static strands: %d", 
                                len(original_strands), len(static_strands))
                    
                    # Temporarily replace the strands list with only static strands
                    self_canvas.strands = static_strands
                    
                    # Draw the entire canvas (background, grid, static strands) to the cache
                    painter = QtGui.QPainter(self_canvas.background_cache)
                    RenderUtils.setup_painter(painter, enable_high_quality=True)
                    
                    # First clear the cache
                    painter.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
                    painter.fillRect(self_canvas.background_cache.rect(), Qt.transparent)
                    painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
                    
                    # Draw the entire canvas without truly moving strands
                    # For edited masks, we need to ensure the original paintEvent is called with the right parameters
                    if not perf_logger.suppress_move_logging:
                        logging.info("MoveMode: Drawing background with original_paintEvent")
                    self_canvas.original_paintEvent(event)
                    
                    # Mark the cache as valid
                    self_canvas.background_cache_valid = True
                    
                    # Restore original strands
                    self_canvas.strands = original_strands
                    
                    if painter.isActive():
                        painter.end()
                        
                except Exception as e:
                    logging.error(f"MoveMode: Error creating background cache: {e}")
                    # Fallback to original paint event if caching fails
                    self_canvas.original_paintEvent(event)
                    return
            
            # Draw the cached background first (has everything except truly moving strands)
            painter = QtGui.QPainter(self_canvas)
            RenderUtils.setup_painter(painter, enable_high_quality=True)
            
            # Apply the same zoom transformation as regular paintEvent
            painter.save()
            canvas_center = QPointF(self_canvas.width() / 2, self_canvas.height() / 2)
            painter.translate(canvas_center)
            painter.translate(self_canvas.pan_offset_x, self_canvas.pan_offset_y)
            painter.scale(self_canvas.zoom_factor, self_canvas.zoom_factor)
            painter.translate(-canvas_center)

            try:
                if hasattr(self_canvas, 'background_cache'):
                    if not perf_logger.suppress_move_logging:
                        logging.info("MoveMode: Drawing background cache")
                    # Draw background cache without transformation since it was pre-rendered
                    painter.save()
                    painter.resetTransform()
                    painter.drawPixmap(0, 0, self_canvas.background_cache)
                    painter.restore()
                else:
                    logging.warning("MoveMode: No background cache to draw!")

                # Get the truly moving strands list prepared by update_strand_position
                truly_moving_strands = getattr(self_canvas, 'truly_moving_strands', [])

                # --- ADD LOGGING HERE ---
                if not perf_logger.suppress_move_logging:
                    logging.info(f"MoveMode (Optimized Paint): Drawing truly_moving_strands: {[s.layer_name for s in truly_moving_strands]}")
                print(f"DEBUG3: TRACKING 1_2 - optimized_paint_event truly_moving_strands: {[s.layer_name for s in truly_moving_strands]}")
                print(f"DEBUG3: TRACKING 1_2 - optimized_paint_event affected_strands_for_drawing: {[s.layer_name for s in getattr(self_canvas, 'affected_strands_for_drawing', [])]}")
                # --- END LOGGING ---

                # --- DRAW C-SHAPE EARLY --- 
                is_moving_strand_point = getattr(move_mode, 'is_moving_strand_point', False)
                affected_strand = getattr(move_mode, 'affected_strand', None)
                if is_moving_strand_point and affected_strand and affected_strand.is_selected:
                    if not perf_logger.suppress_move_logging:
                        logging.info(f"MoveMode: Drawing C-shape EARLY for affected: {affected_strand.layer_name}")
                # --- END DRAW C-SHAPE EARLY ---

                # Now draw only the truly moving strands on top - maintain their original relative order
                sorted_moving_strands = [s for s in original_strands_order if s in truly_moving_strands]

                # --- DRAW ALL MOVING STRAND BODIES (AFTER C-SHAPE) --- 
                if not perf_logger.suppress_move_logging:
                    logging.info("MoveMode: Drawing moving strand bodies")
                for strand in sorted_moving_strands:
                    painter.save() # Ensure clean state for each strand
                    try:
                        if hasattr(strand, 'draw'):
                            strand.draw(painter, skip_painter_setup=True)
                            logging.info(f"MoveMode: Drew strand body for {strand.layer_name}")

                            # --- ADD C-SHAPE DRAW HERE ---
                            # Check if this is the main affected strand and if it should be highlighted
                            is_affected_and_selected = (strand == move_mode.affected_strand and strand.is_selected)
                            if is_affected_and_selected:
                                if not perf_logger.suppress_move_logging:
                                    logging.info(f"MoveMode: Drawing C-shape highlight for affected strand: {strand.layer_name}")
                                move_mode_ref.draw_c_shape_for_strand(painter, strand)
                            # --- END ADD C-SHAPE DRAW --- 
                    finally:
                        painter.restore() # Restore state after drawing strand
                # --- END DRAWING MOVING BODIES AND C-SHAPE ---
                
                # --- ADD POST-BODY C-SHAPE DRAW ---
                is_moving_strand_point = getattr(move_mode, 'is_moving_strand_point', False)
                affected_strand = getattr(move_mode, 'affected_strand', None)
                if is_moving_strand_point and affected_strand and affected_strand.is_selected:
                    if not perf_logger.suppress_move_logging:
                        logging.info(f"MoveMode: Drawing C-shape POST bodies for affected: {affected_strand.layer_name}")
                # --- END POST-BODY C-SHAPE DRAW ---
                
                # Special handling for MaskedStrand (might be redundant if included in truly_moving_strands)
                if isinstance(active_strand, MaskedStrand):
                    logging.info("MoveMode: Special drawing for MaskedStrand")
                    constituent_strands = []
                    if hasattr(active_strand, 'first_selected_strand') and active_strand.first_selected_strand:
                        constituent_strands.append(active_strand.first_selected_strand)
                    if hasattr(active_strand, 'second_selected_strand') and active_strand.second_selected_strand:
                        constituent_strands.append(active_strand.second_selected_strand)
                    for strand in sorted_moving_strands:
                        if strand not in constituent_strands:
                            constituent_strands.append(strand)
                    sorted_moving_strands = constituent_strands
                
                # Control point drawing logic is implicitly handled by the body drawing loop above
                is_moving_control_point = getattr(move_mode, 'is_moving_control_point', False)

                # --- REMOVE POST-BODY C-SHAPE DRAW --- 
                # is_moving_strand_point = getattr(move_mode, 'is_moving_strand_point', False)
                # affected_strand = getattr(move_mode, 'affected_strand', None)
                # if is_moving_strand_point and affected_strand and affected_strand.is_selected:
                #     logging.info(f"MoveMode: Drawing C-shape POST bodies for affected: {affected_strand.layer_name}")
                #     move_mode.draw_c_shape_for_strand(painter, affected_strand)
                # --- END REMOVAL ---

                # --- REMOVE REDUNDANT CALL TO draw_selected_attached_strand --- 
                # (This was already removed in the previous edit, keeping it removed)
                
                # Draw the yellow selection rectangle on top of everything else
                if move_mode.is_moving and move_mode.selected_rectangle and move_mode.affected_strand:
                    if not perf_logger.suppress_move_logging:
                        logging.info("MoveMode: Drawing selection square")
                    move_mode.draw_selection_square(painter)
                
                # Draw any interaction elements
                if hasattr(self_canvas, 'draw_interaction_elements'):
                    self_canvas.draw_interaction_elements(painter)
                
                # Draw control points based on move state and settings
                if hasattr(self_canvas, 'show_control_points') and self_canvas.show_control_points:
                    if hasattr(self_canvas, 'draw_control_points'):
                        if not perf_logger.suppress_move_logging:
                            logging.info("MoveMode: Drawing control points")
                        # Save original strands
                        original_strands = list(self_canvas.strands)
                        
                        # Check if we're moving a control point or a strand endpoint
                        is_moving_control_point = getattr(move_mode, 'is_moving_control_point', False)
                        is_moving_strand_point = getattr(move_mode, 'is_moving_strand_point', False)
                        draw_only_affected = getattr(move_mode, 'draw_only_affected_strand', False)
                        
                        # If draw_only_affected_strand is ON and we're actively moving something
                        if draw_only_affected and (is_moving_control_point or is_moving_strand_point) and sorted_moving_strands:
                            # Only draw control points for truly moving strands
                            self_canvas.strands = sorted_moving_strands
                            self_canvas.draw_control_points(painter)
                        else:
                            # Draw control points for all strands (normal behavior)
                            # Ensure we use the original strands list, not sorted_moving_strands
                            self_canvas.strands = original_strands
                            self_canvas.draw_control_points(painter)
                        
                        # Restore original strands
                        self_canvas.strands = original_strands
                
            except Exception as e:
                logging.error(f"MoveMode: Error in optimized paint event: {e}")
                # If an error occurs, fall back to the original paint event
                if painter.isActive():
                    painter.restore()  # Restore zoom transformation
                    painter.end()
                self_canvas.original_paintEvent(event)
            else:
                if painter.isActive():
                    painter.restore()  # Restore zoom transformation
                    painter.end()
                
            # Log completion
            if not perf_logger.suppress_move_logging:
                logging.info("MoveMode: Optimized paint event completed")
        
        # Replace with our optimized paint event
        self.canvas.paintEvent = optimized_paint_event.__get__(self.canvas, type(self.canvas))

    def draw_selection_square(self, painter):
        """Draw the yellow selection square for the currently selected point."""
        if not self.is_moving or not self.selected_rectangle or not self.affected_strand:
            return
            
        # Set up semi-transparent yellow color
        square_color = QColor(255, 230, 160, 70)  # Yellow with transparency
        painter.setBrush(QBrush(square_color))
        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))  # Solid line for better visibility
        
        # Draw the appropriate yellow rectangle based on moving_side
        # Visual elements need to scale with zoom to appear consistent
        base_yellow_square_size = 120
        yellow_square_size = base_yellow_square_size 
        half_yellow_size = yellow_square_size / 2
        base_square_control_size = 50
        square_control_size = base_square_control_size 
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


    def invalidate_background_cache(self):
        """Invalidate the background cache to force a redraw of non-moving elements."""
        if hasattr(self.canvas, 'background_cache_valid'):
            self.canvas.background_cache_valid = False
            
        # Force an immediate update to ensure the changes are visible
        self.canvas.update()
            
        if hasattr(self.canvas, 'background_cache'):
            # Force recreation of the background pixmap on viewport resize
            viewport_rect = self.canvas.viewport().rect() if hasattr(self.canvas, 'viewport') else self.canvas.rect()
            current_width = self.canvas.background_cache.width()
            current_height = self.canvas.background_cache.height()
            
            # If viewport size has changed, recreate the pixmap
            if current_width != viewport_rect.width() or current_height != viewport_rect.height():
                width = max(1, viewport_rect.width())
                height = max(1, viewport_rect.height())
                self.canvas.background_cache = QtGui.QPixmap(width, height)
                self.canvas.background_cache_valid = False
                self.canvas.update()  # Ensure update after recreating pixmap

    def prepare_optimized_drawing(self):
        """
        Prepare the background cache for optimized drawing when only showing affected strands.
        This method ensures the background is properly cached before strand movement begins.
        """
        import logging
        
        if not self.draw_only_affected_strand:
            return
            
        logging.info("MoveMode: Preparing optimized drawing - caching background")
        
        # Make sure we have a setup_background_cache method
        if not hasattr(self, '_setup_background_cache'):
            logging.info("MoveMode: Setting up background cache method")
            self._setup_background_cache()
        
        # Ensure we have a background cache
        if not hasattr(self.canvas, 'background_cache'):
            if hasattr(self.canvas, '_setup_background_cache'):
                # Try to use the canvas's method if available
                self.canvas._setup_background_cache()
            else:
                # Fall back to our own method
                self._setup_background_cache()
        
        # Force the background to be drawn once
        # Set the flag to indicate the background needs drawing
        if hasattr(self.canvas, 'background_cache_valid'):
            self.canvas.background_cache_valid = False
        
        # Force a redraw to cache the background
        self.canvas.update()
        
        # Mark the cache as valid once done
        if hasattr(self.canvas, 'background_cache_valid'):
            self.canvas.background_cache_valid = True
            logging.info("MoveMode: Background cache is now valid")

    def mousePressEvent(self, event):
        """
        Handle mouse press events.
        
        Args:
            event (QMouseEvent): The mouse event.
        """
        import logging
        pos = event.pos()
        

        # --- Capture selection at the absolute start ---
        selection_at_press_start = self.canvas.selected_strand or self.canvas.selected_attached_strand

        # Start timers and force redraws
        self.hold_timer.stop()  # Ensure any existing timer is stopped first
        self.hold_timer.setInterval(16)  # ~60fps for smooth updates
        self.hold_timer.start()
        
        # Start the continuous redraw timer for even smoother updates
        if hasattr(self, 'redraw_timer'):
            self.redraw_timer.stop()  # Ensure any existing timer is stopped first
            self.redraw_timer.start()
        
        # Immediately force an update to ensure responsiveness
        self.force_redraw_while_holding()
        
        # If draw_only_affected_strand is enabled, prepare the optimized drawing
        if self.draw_only_affected_strand:
            self.prepare_optimized_drawing()
        
        if not self.in_move_mode:
            # Set the originally_selected_strand to the currently selected strand in the layer panel
            # Check both selected_strand and selected_attached_strand
            if self.canvas.selected_strand:
                self.originally_selected_strand = self.canvas.selected_strand
                logging.info("MoveMode: Set originally_selected_strand from selected_strand")
            elif self.canvas.selected_attached_strand:
                self.originally_selected_strand = self.canvas.selected_attached_strand
                logging.info("MoveMode: Set originally_selected_strand from selected_attached_strand")
            # --- REMOVE ELSE BLOCK --- It is handled by current_selection logic and mouseReleaseEvent
            # else:
            #     # If there's no selection, make sure we clear our stored selection
            #     self.originally_selected_strand = None
            #     logging.info("MoveMode: No selected strand, clearing originally_selected_strand")
            # --- END REMOVE ---

            self.in_move_mode = True
            # Reset time limiter at the start of move mode
            self.last_update_time = 0

        # Store the current selection state (useful for comparison, maybe remove later if unused)
        previously_selected = self.canvas.selected_strand or self.canvas.selected_attached_strand

        # --- REMOVE Highlighted Strand Logic --- C-shape should rely purely on is_selected
        # # Save the current highlighted strand before any operations
        # # Only save if there's actually a selected attached strand
        # if self.canvas.selected_attached_strand:
        #     self.highlighted_strand = self.canvas.selected_attached_strand
        #     logging.info("MoveMode: Set highlighted_strand from selected_attached_strand")
        # else:
        #     # Make sure highlighted strand is cleared if nothing is selected
        #     self.highlighted_strand = None
        #     logging.info("MoveMode: No selected attached strand, clearing highlighted_strand")
        # --- END REMOVE ---

        # First try to handle control point movement
        control_point_moved = False
        for strand in self.canvas.strands:
            if not getattr(strand, 'deleted', False):
                if self.try_move_control_points(strand, pos):
                    control_point_moved = True
                    logging.info("MoveMode: Moving control point")
                    
                    # For control point movement, we'll temporarily clear visible selections
                    # but maintain selection state internally for restoration later
                    if control_point_moved:
                        # Clear canvas selections during control point movement 
                        # The originally_selected_strand is already saved above
                        self.canvas.selected_strand = None
                        self.canvas.selected_attached_strand = None
                        # self.highlighted_strand = None  # Also clear highlighted strand (removed highlight logic)

                        # Update the canvas and return early
                        self.canvas.update()
                        return
                    
        logging.info("MoveMode: Control point moved: %s", control_point_moved)

        # If we're not moving a control point, proceed with normal strand movement
        # Store current selection state before handling movement
        current_selection_states = {}
        for strand in self.canvas.strands:
            current_selection_states[strand] = strand.is_selected
            if isinstance(strand, AttachedStrand):
                for attached in strand.attached_strands:
                    current_selection_states[attached] = attached.is_selected
        
        # Handle strand selection and movement
        self.handle_strand_movement(pos)
        
        # If no movement was initiated, restore selection states
        if not self.is_moving:
            for strand, was_selected in current_selection_states.items():
                strand.is_selected = was_selected
        
        logging.info("MoveMode: Is moving: %s, Affected strand: %s", 
                    self.is_moving, 
                    self.affected_strand.__class__.__name__ if self.affected_strand else "None")
        
        if self.is_moving:
            # --- Move originally_selected_strand capture inside if self.is_moving check ---
            # self.originally_selected_strand = None # Initialize

            # --- REMOVE early deselection --- Handled later based on action
            # # Deselect all strands
            # for strand in self.canvas.strands:
            #     strand.is_selected = False
            #     if isinstance(strand, AttachedStrand):
            #         for attached in strand.attached_strands:
            #             attached.is_selected = False

            # Try to initiate movement (control points first)
            # # control_point_moved = False
            # for strand in self.canvas.strands:
            #     if not getattr(strand, 'deleted', False):
            #         if self.try_move_control_points(strand, pos):
            #             control_point_moved = True
            #             logging.info("MoveMode: Moving control point")
            #             
            #             # For control point movement, we'll temporarily clear visible selections
            #             # but maintain selection state internally for restoration later
            #             if control_point_moved:
            #                 # Clear canvas selections during control point movement 
            #                 # The originally_selected_strand is already saved above
            #                 self.canvas.selected_strand = None
            #                 self.canvas.selected_attached_strand = None
            #                 # self.highlighted_strand = None  # Also clear highlighted strand (removed highlight logic)
            #
            #                 # Update the canvas and return early
            #                 self.canvas.update()
            #                 return
            #             
            # --- Selection Logic based on whether a move was initiated --- 
            # if self.is_moving: # A control point or endpoint was clicked
            #     # Capture the selection state *before* this move started
            #     if not self.originally_selected_strand: # Capture only once per move sequence
            #         self.originally_selected_strand = selection_at_press_start 
            #         logging.info(f"MoveMode: Captured originally_selected_strand on move start: {self.originally_selected_strand.layer_name if self.originally_selected_strand else 'None'}")

            #         # Deselect the original strand visually (if it exists and is different from the new one)
            #         if self.originally_selected_strand and self.originally_selected_strand != self.affected_strand:
            #             self.originally_selected_strand.is_selected = False
            #             # Clear canvas selection refs if they point to the old strand
            #             if self.canvas.selected_strand == self.originally_selected_strand: self.canvas.selected_strand = None
            #             if self.canvas.selected_attached_strand == self.originally_selected_strand: self.canvas.selected_attached_strand = None
            #         
            #         # Ensure the new affected strand is selected
            #         if self.affected_strand:
            #             self.affected_strand.is_selected = True
            #             if isinstance(self.affected_strand, MaskedStrand):
            #                 self.canvas.selected_strand = self.affected_strand
            #                 self.canvas.selected_attached_strand = None
            #             else:
            #                 self.canvas.selected_attached_strand = self.affected_strand
            #                 self.canvas.selected_strand = None # Ensure main selection is clear

            #         # --- Moving state setup ---
            #         self.last_update_pos = pos
            #         self.accumulated_delta = QPointF(0, 0)
            #         self.last_snapped_pos = self.canvas.snap_to_grid(pos)
            #         self.target_pos = self.last_snapped_pos

            #         # Special handling for MaskedStrand
            #         if isinstance(self.affected_strand, MaskedStrand):
            #             logging.info("MoveMode: Special handling for MaskedStrand")
            #             # Make sure the MaskedStrand is properly selected
            #             self.affected_strand.is_selected = True
            #             self.canvas.selected_strand = self.affected_strand
            #             self.originally_selected_strand = self.affected_strand
            #             # Ensure we're not setting it as an attached strand
            #             self.canvas.selected_attached_strand = None
            #             # Force cache invalidation
            #             if hasattr(self.canvas, 'background_cache_valid'):
            #                 self.canvas.background_cache_valid = False
            #             
            #             # Store strands that need to be drawn on each update - crucial for static display
            #             truly_moving_strands = [self.affected_strand]
            #             affected_strands = [self.affected_strand]
            #             
            #             # Always include constituent strands for proper rendering
            #             if hasattr(self.affected_strand, 'first_selected_strand') and self.affected_strand.first_selected_strand:
            #                 truly_moving_strands.append(self.affected_strand.first_selected_strand)
            #                 affected_strands.append(self.affected_strand.first_selected_strand)
            #                 
            #             if hasattr(self.affected_strand, 'second_selected_strand') and self.affected_strand.second_selected_strand:
            #                 truly_moving_strands.append(self.affected_strand.second_selected_strand)
            #                 affected_strands.append(self.affected_strand.second_selected_strand)
            #             
            #             # Store these for the optimized paint handler
            #             self.canvas.truly_moving_strands = truly_moving_strands
            #             self.canvas.affected_strands_for_drawing = affected_strands
            #         # Removed the inner 'else' block for setting temp_selected_strand etc., handled above

            #         # Setup efficient paint handler
            #         if not hasattr(self.canvas, 'original_paintEvent'):
            #             logging.info("MoveMode: Setting up optimized paint handler")
            #             self._setup_optimized_paint_handler()
            #             
            #         # Ensure background cache is properly invalidated on first movement
            #         if hasattr(self.canvas, 'background_cache_valid'):
            #             self.canvas.background_cache_valid = False

            # --- End of Move originally_selected_strand capture inside if self.is_moving check ---

            # --- Capture originally_selected_strand ONLY when movement starts ---
            if not self.originally_selected_strand:
                 self.originally_selected_strand = selection_at_press_start
                 logging.info(f"MoveMode: Captured originally_selected_strand on move start: {self.originally_selected_strand.layer_name if self.originally_selected_strand else 'None'}")
            # --- End capture ---

            self.last_update_pos = pos
            self.accumulated_delta = QPointF(0, 0)
            self.last_snapped_pos = self.canvas.snap_to_grid(pos)
            self.target_pos = self.last_snapped_pos
            
            # Special handling for MaskedStrand
            if isinstance(self.affected_strand, MaskedStrand):
                logging.info("MoveMode: Special handling for MaskedStrand")
                # Make sure the MaskedStrand is properly selected
                self.affected_strand.is_selected = True
                self.canvas.selected_strand = self.affected_strand
                self.originally_selected_strand = self.affected_strand
                # Ensure we're not setting it as an attached strand
                self.canvas.selected_attached_strand = None
                # Force cache invalidation
                if hasattr(self.canvas, 'background_cache_valid'):
                    self.canvas.background_cache_valid = False
                
                # Store strands that need to be drawn on each update - crucial for static display
                truly_moving_strands = [self.affected_strand]
                affected_strands = [self.affected_strand]
                
                # Always include constituent strands for proper rendering
                if hasattr(self.affected_strand, 'first_selected_strand') and self.affected_strand.first_selected_strand:
                    truly_moving_strands.append(self.affected_strand.first_selected_strand)
                    affected_strands.append(self.affected_strand.first_selected_strand)
                    
                if hasattr(self.affected_strand, 'second_selected_strand') and self.affected_strand.second_selected_strand:
                    truly_moving_strands.append(self.affected_strand.second_selected_strand)
                    affected_strands.append(self.affected_strand.second_selected_strand)
                
                # Store these for the optimized paint handler
                self.canvas.truly_moving_strands = truly_moving_strands
                self.canvas.affected_strands_for_drawing = affected_strands
            else:
                # Set the temporary selected strand only if not in deselect all mode
                self.temp_selected_strand = self.affected_strand
                if self.temp_selected_strand and not self.is_moving_control_point and not self.user_deselected_all:
                    self.temp_selected_strand.is_selected = True
                    # Only set originally_selected_strand's selection if it exists
                    if self.originally_selected_strand:
                        self.originally_selected_strand.is_selected = True
                    self.canvas.selected_attached_strand = self.temp_selected_strand
                elif self.user_deselected_all and self.temp_selected_strand:
                    # Ensure strand stays deselected in deselect all mode
                    self.temp_selected_strand.is_selected = False
                    self.canvas.selected_attached_strand = None
                
            # Setup efficient paint handler
            if not hasattr(self.canvas, 'original_paintEvent'):
                logging.info("MoveMode: Setting up optimized paint handler")
                self._setup_optimized_paint_handler()
                
            # Ensure background cache is properly invalidated on first movement
            if hasattr(self.canvas, 'background_cache_valid'):
                self.canvas.background_cache_valid = False

        else: # No move initiated (blank space click)
            # Keep the selection from the start of the press
            logging.info("MoveMode: Blank space click, preserving selection")
            # Set selection state atomically to prevent flicker
            for strand in self.canvas.strands: 
                strand.is_selected = (strand == selection_at_press_start)
            # Set canvas selection attributes directly to prevent flicker
            if selection_at_press_start:
                if isinstance(selection_at_press_start, MaskedStrand):
                    self.canvas.selected_strand = selection_at_press_start
                    self.canvas.selected_attached_strand = None
                else:
                    self.canvas.selected_attached_strand = selection_at_press_start
                    self.canvas.selected_strand = None
            else:
                self.canvas.selected_strand = None
                self.canvas.selected_attached_strand = None

        # Final update
        self.canvas.update()
        
    def force_redraw_while_holding(self):
        """Force periodic redraws while holding the mouse button, even without movement."""
        import logging
        
        if not self.is_moving:
            # If not in moving state, stop the timer
            self.hold_timer.stop()
            return
            
        logging.info("MoveMode: Forcing redraw while holding")
        
        # Reset the frame counter to ensure full redraws
        if hasattr(self.canvas, '_frames_since_click'):
            self.canvas._frames_since_click = 0
            
        # Handle background cache based on optimization setting
        if self.draw_only_affected_strand:
            # When drawing only affected strands, we want to keep the background cache valid
            # This prevents redrawing all strands on every frame
            if hasattr(self.canvas, 'background_cache_valid') and not self.canvas.background_cache_valid:
                # Throttle cache recreation to prevent excessive recreations during movement
                import time
                current_time = time.time()
                if not hasattr(self, '_last_cache_recreation') or (current_time - self._last_cache_recreation) > 0.1:
                    # If the cache is invalidated and enough time has passed, recreate it once
                    logging.info("MoveMode: Recreating background cache for optimized drawing")
                    self.prepare_optimized_drawing()
                    self._last_cache_recreation = current_time
        else:
            # If we're not optimizing, invalidate the cache to ensure all strands are redrawn
            if hasattr(self.canvas, 'background_cache_valid'):
                self.canvas.background_cache_valid = False

        # Force a full redraw of the canvas
        self.canvas.update()
        
        # Ensure this method is called again on the next event loop iteration
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, self.canvas.update)

    def cancel_movement(self):
        """Externally cancel any ongoing move operation."""
        import logging
        if self.is_moving:
            logging.info("MoveMode: Movement cancelled externally.")
            self.reset_movement_state()
            # Restore selection to what it was before the move started
            final_selected_strand = self.originally_selected_strand
            if final_selected_strand:
                if isinstance(final_selected_strand, MaskedStrand):
                    self.canvas.selected_strand = final_selected_strand
                    self.canvas.selected_attached_strand = None
                else:
                    self.canvas.selected_attached_strand = final_selected_strand
                    self.canvas.selected_strand = None
                final_selected_strand.is_selected = True

            self.originally_selected_strand = None # Clear after use
            self.canvas.update()

    def reset_movement_state(self):
        """Resets all state related to an active move operation."""
        from PyQt5.QtCore import QPointF

        # --- 1. Stop Timers ---
        if hasattr(self, 'hold_timer'):
            self.hold_timer.stop()
        if hasattr(self, 'redraw_timer'):
            self.redraw_timer.stop()
 
        # --- 2. Reset MoveMode State COMPLETELY ---
        self.is_moving = False
        self.moving_point = None
        self.affected_strand = None
        self.moving_side = None
        self.selected_rectangle = None
        self.last_update_pos = None
        self.accumulated_delta = QPointF(0, 0)
        self.last_snapped_pos = None
        self.target_pos = None
        
        # Invalidate connection cache when movement ends
        self.invalidate_connection_cache()
        
        # Restore normal logging level when movement ends
        perf_logger.suppress_during_move(False)
        
        self.mouse_offset = QPointF(0, 0)
        if hasattr(self, 'move_timer'):
            self.move_timer.stop()
        self.in_move_mode = False
        self.temp_selected_strand = None
        self.last_update_rect = None
        self.is_moving_control_point = False
        self.is_moving_strand_point = False
        self.user_deselected_all = False
        self.last_update_time = 0

        # --- 3. Clean up Canvas Temp Attributes & Restore Paint Event ---
        if hasattr(self.canvas, 'original_paintEvent'):
            self.canvas.paintEvent = self.canvas.original_paintEvent
            delattr(self.canvas, 'original_paintEvent')
        attrs_to_clean = ['active_strand_for_drawing', 'active_strand_update_rect',
                          'last_strand_rect', 'background_cache', 'background_cache_valid',
                          'movement_first_draw', 'affected_strands_for_drawing',
                          'truly_moving_strands', '_frames_since_click']
        for attr in attrs_to_clean:
            if hasattr(self.canvas, attr):
                try:
                    delattr(self.canvas, attr)
                except AttributeError:
                    pass

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release events.
        """
        import logging
        from PyQt5.QtCore import QPointF, QTimer

        # Store relevant state before resetting
        was_moving = self.is_moving
        final_pos = event.pos()
        # Capture selection state *before* reset
        selection_at_release_start = self.canvas.selected_strand or self.canvas.selected_attached_strand
        original_selection_ref = self.originally_selected_strand # Keep reference used during move
        was_moving_control_point = self.is_moving_control_point
        
        self.reset_movement_state()
        
        # --- 4. Restore Selection State --- 
        # Determine the final selection based on whether it was a click or a move
        final_selected_strand = None
        if was_moving:
            # Restore the selection from *before* the move started
            final_selected_strand = original_selection_ref
            logging.info(f"MoveMode: Restoring selection after move: {final_selected_strand.layer_name if final_selected_strand else 'None'}")
        else: # It was a click (either on blank space or an element without dragging)
            # Restore the selection that was active *just before* this release event started
            final_selected_strand = selection_at_release_start
            logging.info(f"MoveMode: Restoring selection after click: {final_selected_strand.layer_name if final_selected_strand else 'None'}")

        # Set selection state atomically to prevent flicker - clear all first, then set final selection
        for strand in self.canvas.strands:
            strand.is_selected = (strand == final_selected_strand)
            if hasattr(strand, 'attached_strands'):
                for attached in strand.attached_strands:
                    attached.is_selected = (attached == final_selected_strand)

        # Set canvas selection attributes directly to final state to prevent flicker
        if final_selected_strand and final_selected_strand in self.canvas.strands:
            if isinstance(final_selected_strand, MaskedStrand):
                self.canvas.selected_strand = final_selected_strand
                self.canvas.selected_attached_strand = None
            else:
                # Assume it's an attached strand if not MaskedStrand
                self.canvas.selected_attached_strand = final_selected_strand
                self.canvas.selected_strand = None
        else:
            # No valid selection
            self.canvas.selected_strand = None
            self.canvas.selected_attached_strand = None
            logging.info("MoveMode: Final selection - No strand selected")

        # Clear the originally_selected_strand reference ONLY AFTER the release event is fully processed
        self.originally_selected_strand = None

        # --- 5. Save State if Control Point Moved ---
        if was_moving_control_point and hasattr(self, 'undo_redo_manager'):
             logging.info("MoveMode: Control point movement finished, saving state.")
             if hasattr(self.undo_redo_manager, '_last_save_time'): self.undo_redo_manager._last_save_time = 0
             self.undo_redo_manager.save_state()

        # --- 6. Force Updates ---
        self.canvas.update() # Force immediate redraw with restored state
        QTimer.singleShot(0, self.canvas.update) # Schedule another for next cycle

    def update_strand_geometry_only(self, new_pos):
        """ Update strand geometry without triggering drawing optimizations or selection changes."""
        if not self.affected_strand: return
        # Apply minimum distance constraint
        if self.moving_side == 0:
            other_point = self.affected_strand.end
            if self.calculate_distance(new_pos, other_point) < self.MIN_STRAND_POINTS_DISTANCE:
                new_pos = self.adjust_position_to_maintain_distance(new_pos, other_point)
        elif self.moving_side == 1:
            other_point = self.affected_strand.start
            if self.calculate_distance(new_pos, other_point) < self.MIN_STRAND_POINTS_DISTANCE:
                new_pos = self.adjust_position_to_maintain_distance(new_pos, other_point)

        # Update based on moving side
        if self.moving_side == 'control_point1':
            self.affected_strand.control_point1 = new_pos
        elif self.moving_side == 'control_point2':
            self.affected_strand.control_point2 = new_pos
        elif self.moving_side == 'control_point_center':
             self.affected_strand.control_point_center = new_pos
             self.affected_strand.control_point_center_locked = True
        elif self.moving_side == 0:
            self.affected_strand.start = new_pos
        elif self.moving_side == 1:
            self.affected_strand.end = new_pos
        
        # Update shape and potentially connected strands (geometry only)
        self.affected_strand.update_shape()
        if hasattr(self.affected_strand, 'update_side_line'): self.affected_strand.update_side_line()

        # Update connected strands to maintain connection synchronization
        # This is critical to prevent disconnection on mouse release
        is_moving_endpoint = self.moving_side == 0 or self.moving_side == 1
        if is_moving_endpoint:
            moving_point_coord = self.affected_strand.start if self.moving_side == 0 else self.affected_strand.end
            
            if moving_point_coord and hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
                # Get connections from layer state manager
                connections = self.canvas.layer_state_manager.getConnections()
                connected_strand_names = set(connections.get(self.affected_strand.layer_name, []))
                # Also check reverse connections
                for name, connected_list in connections.items():
                    if self.affected_strand.layer_name in connected_list:
                        connected_strand_names.add(name)
                
                # Update positions of connected strands
                for other_strand in self.canvas.strands:
                    if other_strand == self.affected_strand or isinstance(other_strand, MaskedStrand):
                        continue
                    
                    # Check if they are connected according to the state manager (bidirectional)
                    is_connected = (other_strand.layer_name in connected_strand_names or
                                  self.affected_strand.layer_name in connections.get(other_strand.layer_name, []))
                    
                    if is_connected:
                        # Only update connected strand positions if they are in the truly_moving_strands list
                        # This prevents automatic position correction based on proximity
                        truly_moving_strands = getattr(self.canvas, 'truly_moving_strands', [])
                        if other_strand in truly_moving_strands:
                            # Determine which end of the connected strand needs to move
                            # Use original positions to determine connection point, not current positions
                            original_moving_point = self.affected_strand.start if self.moving_side == 0 else self.affected_strand.end
                            connected_moving_side = -1
                            
                            # Use the original positions to determine which end is connected
                            if self.points_are_close(other_strand.start, original_moving_point):
                                connected_moving_side = 0
                            elif self.points_are_close(other_strand.end, original_moving_point):
                                connected_moving_side = 1
                            
                            # Update the appropriate end to maintain connection
                            if connected_moving_side == 0:
                                other_strand.start = new_pos
                                other_strand.update_shape()
                                if hasattr(other_strand, 'update_side_line'):
                                    other_strand.update_side_line()
                            elif connected_moving_side == 1:
                                other_strand.end = new_pos
                                other_strand.update_shape()
                                if hasattr(other_strand, 'update_side_line'):
                                    other_strand.update_side_line()

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
        # --- CORRECTED: Iterate in reverse to check topmost strands first --- 
        # for i, strand in enumerate(self.canvas.strands):
        for i, strand in reversed(list(enumerate(self.canvas.strands))):
        # --- END CORRECTION ---
            if not getattr(strand, 'deleted', False) and (not self.lock_mode_active or i not in self.locked_layers):
                if self.try_move_strand(strand, pos, i):
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
            
        # Check if the strand is locked
        if self.lock_mode_active and strand in self.canvas.strands:
            strand_index = self.canvas.strands.index(strand)
            if strand_index in self.locked_layers:
                # logging.info(f"Skipping control point movement for locked strand {strand.layer_name}")
                return False

        control_point1_rect = self.get_control_point_rectangle(strand, 1)
        control_point2_rect = self.get_control_point_rectangle(strand, 2)
        
        # Only get the center control point rectangle if it's enabled
        control_point_center_rect = None
        if hasattr(self.canvas, 'enable_third_control_point') and self.canvas.enable_third_control_point:
            control_point_center_rect = self.get_control_point_rectangle(strand, 3)

        if control_point1_rect.contains(pos):
            self.start_movement(strand, 'control_point1', control_point1_rect, pos)
            # Mark that we're moving a control point
            self.is_moving_control_point = True
            # Store the strand explicitly in truly_moving_strands for proper z-ordering
            if hasattr(self.canvas, 'truly_moving_strands'):
                self.canvas.truly_moving_strands = [strand]
            else:
                self.canvas.truly_moving_strands = [strand]
            # Clear any existing highlighting
            self.highlighted_strand = None
            return True
        elif control_point2_rect.contains(pos):
            self.start_movement(strand, 'control_point2', control_point2_rect, pos)
            # Mark that we're moving a control point
            self.is_moving_control_point = True
            if hasattr(self.canvas, 'truly_moving_strands'):
                self.canvas.truly_moving_strands = [strand]
            else:
                self.canvas.truly_moving_strands = [strand]
            # Clear any existing highlighting
            self.highlighted_strand = None
            return True
        # Only check center control point if it's enabled
        elif control_point_center_rect is not None and control_point_center_rect.contains(pos):
            self.start_movement(strand, 'control_point_center', control_point_center_rect, pos)
            # Mark that we're moving a control point
            self.is_moving_control_point = True
            if hasattr(self.canvas, 'truly_moving_strands'):
                self.canvas.truly_moving_strands = [strand]
            else:
                self.canvas.truly_moving_strands = [strand]
            # Clear any existing highlighting
            self.highlighted_strand = None
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
        # --- ADDED: Skip MaskedStrand instances for direct endpoint movement ---
        if isinstance(strand, MaskedStrand):
            return False
        # --- END ADDED ---

        # Get selection areas
        start_area = self.get_start_area(strand)
        end_area = self.get_end_area(strand)

        if start_area.contains(pos) and self.can_move_side(strand, 0, strand_index):
            self.start_movement(strand, 0, start_area, pos)
            # Ensure the strand is selected when movement starts
            strand.is_selected = True
            # logging.info(f"Selected strand {strand.layer_name} for start movement")
            if isinstance(strand, AttachedStrand):
                self.canvas.selected_attached_strand = strand
            else:
                # Regular strand - treat as attached strand for selection
                self.canvas.selected_attached_strand = strand
            return True
        elif end_area.contains(pos) and self.can_move_side(strand, 1, strand_index):
            self.start_movement(strand, 1, end_area, pos)
            # Ensure the strand is selected when movement starts
            strand.is_selected = True
            # logging.info(f"Selected strand {strand.layer_name} for end movement")
            if isinstance(strand, AttachedStrand):
                self.canvas.selected_attached_strand = strand
            else:
                # Regular strand - treat as attached strand for selection
                self.canvas.selected_attached_strand = strand
            return True
        return False

    def get_control_point_rectangle(self, strand, control_point_number):
        """Get the rectangle around the specified control point for hit detection."""
        # Use fixed size in canvas coordinates - canvas handles zoom transformation
        size = 50  # Size for control point selection
        if control_point_number == 1:
            center = strand.control_point1
        elif control_point_number == 2:
            center = strand.control_point2
        elif control_point_number == 3:
            # Only return a valid rectangle for center control point if feature is enabled
            if hasattr(self.canvas, 'enable_third_control_point') and self.canvas.enable_third_control_point:
                center = strand.control_point_center
            else:
                # Return an empty rectangle that won't match any position
                return QRectF()
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

    def start_movement(self, strand, side, area, actual_click_pos=None):
        """Start movement tracking for a strand."""
        # Save the currently selected strand before starting a new movement operation
        if self.canvas.selected_strand is not None:
            self.originally_selected_strand = self.canvas.selected_strand
        elif self.canvas.selected_attached_strand is not None:
            self.originally_selected_strand = self.canvas.selected_attached_strand

        # Store a reference to the undo_redo_manager if it exists
        if hasattr(self.canvas, 'undo_redo_manager') and not hasattr(self, 'undo_redo_manager'):
            self.undo_redo_manager = self.canvas.undo_redo_manager

        # Build connection cache for performance optimization
        self.build_connection_cache()
        
        # Suppress verbose logging during movement for better performance
        perf_logger.suppress_during_move(True)

        # Rest of the existing function
        self.moving = True
        self.moving_side = side
        
        # INITIAL POSITION CAPTURE: record the starting coordinates of the strand endpoint or control point here
        # Get the exact current position of the strand point being moved
        if side == 0:
            strand_pos = QPointF(strand.start)
        elif side == 1:
            strand_pos = QPointF(strand.end)
        elif side == 'control_point1':
            strand_pos = QPointF(strand.control_point1)
        elif side == 'control_point2':
            strand_pos = QPointF(strand.control_point2)
        elif side == 'control_point_center':
            strand_pos = QPointF(strand.control_point_center)
        else:
            strand_pos = QPointF(0, 0)
        
        # Use the actual click position if provided
        if actual_click_pos:
            # This is where the user actually clicked
            self.initial_mouse_pos = QPointF(actual_click_pos)
            # Calculate offset from click position to strand position
            # This offset will be maintained during movement
            self.mouse_offset = QPointF(strand_pos.x() - actual_click_pos.x(), 
                                       strand_pos.y() - actual_click_pos.y())
            import logging
            zoom_info = f", zoom={self.canvas.zoom_factor:.2f}" if hasattr(self.canvas, 'zoom_factor') else ""
            logging.info(f"ZOOM_START: strand_pos={strand_pos}, click_pos={actual_click_pos}, offset={self.mouse_offset}{zoom_info}")
            
            # Additional logging for zoom-out debugging
            if hasattr(self.canvas, 'zoom_factor') and self.canvas.zoom_factor < 0.8:
                logging.info(f"ZOOM_DEBUG: ZOOMED_OUT detected! Initial strand point will be at {strand_pos}")
                logging.info(f"ZOOM_DEBUG: Click was at {actual_click_pos} (canvas coordinates)")
                logging.info(f"ZOOM_DEBUG: Calculated offset: {self.mouse_offset}")
        else:
            # Fallback: assume click was directly on the strand
            self.initial_mouse_pos = QPointF(strand_pos)
            self.mouse_offset = QPointF(0, 0)
            import logging
            logging.warning("start_movement: No actual_click_pos provided, using strand position")
            # Do not move cursor in fallback case to prevent jumps
            
        # Store the moving point as the strand position
        self.moving_point = strand_pos

        self.affected_strand = strand
        self.selected_rectangle = area
        self.is_moving = True
        # Set the flag if we're moving a control point
        self.is_moving_control_point = side in ['control_point1', 'control_point2', 'control_point_center']
        # Set the flag if we're moving a strand endpoint
        self.is_moving_strand_point = side in [0, 1]
        
        # Set initial positions to the strand position
        self.last_snapped_pos = strand_pos
        self.target_pos = strand_pos
        
        # Keep the mouse offset to maintain accurate positioning without cursor jumps
        # The offset represents the difference between where user clicked and strand position
        # This prevents visual jumps while maintaining precise control
        logging.info(f"Maintaining mouse offset for smooth movement: {self.mouse_offset}")
        
        # Do not move cursor or reset offset - this prevents the visual jump
        # The offset will be applied during mouse movement to maintain correct positioning

        # Find any other strands connected to this point using layer_state_manager
        moving_point = strand.start if side == 0 else strand.end
        connected_strand = self.find_connected_strand(strand, side, moving_point)
        
        # --- REVISED CODE: Initialize truly_moving_strands at start of movement ---
        truly_moving_strands = [strand] # Start with the strand being directly interacted with
        moving_point_coord = strand.start if side == 0 else strand.end # Define the point being moved

        # Explicitly check ALL other strands for shared points at the moving coordinate
        # UNLESS the initially clicked strand is a MaskedStrand (its components are handled separately)
        if not isinstance(strand, MaskedStrand): # Check if the *initiating* strand is NOT a MaskedStrand
            for other_strand in self.canvas.strands:
                if other_strand == strand: # Skip self
                    continue
                # --- ADDED: Skip MaskedStrand instances ---
                if isinstance(other_strand, MaskedStrand):
                    continue
                # --- END ADDED ---
                # Check if the other strand shares the start or end point being moved
                should_add_strand = False
                
                if self.draw_only_affected_strand:
                    # When "drag only affected strand" is enabled:
                    # ONLY use proximity detection, but ONLY for strands that are connected in state
                    # This ensures we only show strands that are both connected AND at the moving point
                    if hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
                        connections = self.canvas.layer_state_manager.getConnections()
                        # Check bidirectional connections
                        affected_connections = connections.get(self.affected_strand.layer_name, [])
                        other_connections = connections.get(other_strand.layer_name, [])
                        
                        # Only consider proximity if they're connected in the state
                        are_connected = (other_strand.layer_name in affected_connections or 
                                       self.affected_strand.layer_name in other_connections)
                        
                        # Only add if connected in state AND actually at the moving point
                        at_moving_point = (self.points_are_close(other_strand.start, moving_point_coord) or \
                                         self.points_are_close(other_strand.end, moving_point_coord))
                        
                        if are_connected and at_moving_point:
                            should_add_strand = True
                            print(f"DEBUG: Adding {other_strand.layer_name} - connected in state: {are_connected}, at moving point: {at_moving_point}")
                            print(f"DEBUG: Moving point: {moving_point_coord}, Other start: {other_strand.start}, Other end: {other_strand.end}")
                        elif are_connected:
                            print(f"DEBUG: NOT adding {other_strand.layer_name} - connected in state: {are_connected}, but NOT at moving point: {at_moving_point}")
                            print(f"DEBUG: Moving point: {moving_point_coord}, Other start: {other_strand.start}, Other end: {other_strand.end}")
                else:
                    # When setting is disabled, only include strands that are actually connected in state manager
                    # AND are connected at the specific moving point - no proximity-based connections
                    if hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
                        connections = self.canvas.layer_state_manager.getConnections()
                        affected_connections = connections.get(self.affected_strand.layer_name, [])
                        other_connections = connections.get(other_strand.layer_name, [])
                        are_connected = (other_strand.layer_name in affected_connections or 
                                       self.affected_strand.layer_name in other_connections)
                        
                        # Even when setting is OFF, only add strands connected at the specific moving point
                        if are_connected:
                            at_moving_point = (self.points_are_close(other_strand.start, moving_point_coord) or \
                                             self.points_are_close(other_strand.end, moving_point_coord))
                            if at_moving_point:
                                should_add_strand = True
                                print(f"DEBUG: Adding {other_strand.layer_name} (setting OFF) - connected in state AND at moving point")
                            else:
                                print(f"DEBUG: NOT adding {other_strand.layer_name} (setting OFF) - connected in state but NOT at moving point")
                
                if should_add_strand and other_strand not in truly_moving_strands:
                    truly_moving_strands.append(other_strand)
                    logging.info(f"MoveMode: Added strand {other_strand.layer_name} to truly_moving_strands (connection-based: {self.draw_only_affected_strand})")
        # If the initiating strand *was* a MaskedStrand, truly_moving_strands remains just [MaskedStrand],
        # and its components will be handled by the MaskedStrand-specific move logic.


        # Store the list on the canvas for use in optimized_paint_event
        self.canvas.truly_moving_strands = truly_moving_strands
        print(f"DEBUG3: TRACKING 1_2 - start_movement INITIAL truly_moving_strands: {[s.layer_name for s in truly_moving_strands]}")
        # Ensure affected_strands_for_drawing also contains all truly moving strands initially
        self.canvas.affected_strands_for_drawing = list(truly_moving_strands)
        print(f"DEBUG3: TRACKING 1_2 - start_movement INITIAL affected_strands_for_drawing: {[s.layer_name for s in self.canvas.affected_strands_for_drawing]}")
        # --- END REVISED CODE ---

        # Control point movement specific handling
        if self.is_moving_control_point:
            # Before clearing selections, ensure we have saved the originally_selected_strand
            # This is crucial for restoring selection after control point movement
            if not self.originally_selected_strand:
                if self.canvas.selected_strand:
                    self.originally_selected_strand = self.canvas.selected_strand
                elif self.canvas.selected_attached_strand:
                    self.originally_selected_strand = self.canvas.selected_attached_strand
                    
            # When moving control points, temporarily clear visible selections to maintain proper z-ordering
            # but remember the original selection state for restoration later
            for s in self.canvas.strands:
                s.is_selected = False
                # Also clear selections in attached strands
                if hasattr(s, 'attached_strands'):
                    for attached in s.attached_strands:
                        attached.is_selected = False
                        
            # Temporarily clear selected attached strand
            self.canvas.selected_attached_strand = None
            self.temp_selected_strand = None
            # Clear highlighted strand to ensure no highlighting during control point movement
            self.highlighted_strand = None
            # Ensure the affected strand itself is not visibly selected during control point movement
            if self.affected_strand:
                self.affected_strand.is_selected = False
        else:
            # For normal strand movement, ensure the strand stays selected
            if self.affected_strand:
                self.affected_strand.is_selected = True
                if isinstance(self.affected_strand, MaskedStrand):
                    self.canvas.selected_strand = self.affected_strand
                    self.canvas.selected_attached_strand = None
                elif isinstance(self.affected_strand, AttachedStrand):
                    self.canvas.selected_attached_strand = self.affected_strand
                    self.canvas.selected_strand = None
                else:
                    # Regular strand - treat as attached strand
                    self.canvas.selected_attached_strand = self.affected_strand
                    self.canvas.selected_strand = None
                
                # Also handle connected strands
                if connected_strand:
                    connected_strand.is_selected = True
                    if isinstance(connected_strand, AttachedStrand):
                        self.temp_selected_strand = connected_strand
        # --- REPLACE print with logging.info ---
        logging.info("--------------------------------")
        logging.info(f"StartMovement: affected_strand={self.affected_strand.layer_name if self.affected_strand else 'None'}")
        logging.info(f"StartMovement: moving_side={side}") 
        # We need to check if original_start and original_end are defined before logging
        # These were defined in the context of the previous move_masked_strand or update_strand_position
        # They are NOT directly available here. We should log the current start/end instead.
        logging.info(f"StartMovement: current_start={strand.start}")
        logging.info(f"StartMovement: current_end={strand.end}")
        logging.info("--------------------------------")
        # --- END REPLACE ---
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
        
        # Always invalidate the background cache during strand movement
        # to ensure the grid and all strands remain visible
        if hasattr(self.canvas, 'background_cache_valid'):
            self.canvas.background_cache_valid = False
            
        if not self.affected_strand:
            return

        # Check if the new position would cause start and end points to be too close
        if self.moving_side == 0:  # Moving start point
            other_point = self.affected_strand.end
            # Calculate the distance between the proposed new position and the end point
            if self.calculate_distance(new_pos, other_point) < self.MIN_STRAND_POINTS_DISTANCE:
                # Adjust the new position to maintain minimum distance
                new_pos = self.adjust_position_to_maintain_distance(new_pos, other_point)
        elif self.moving_side == 1:  # Moving end point
            other_point = self.affected_strand.start
            # Calculate the distance between the proposed new position and the start point
            if self.calculate_distance(new_pos, other_point) < self.MIN_STRAND_POINTS_DISTANCE:
                # Adjust the new position to maintain minimum distance
                new_pos = self.adjust_position_to_maintain_distance(new_pos, other_point)
        # Control point moves don't need this restriction
        
        # Keep track of what strands are affected for optimization
        affected_strands = set([self.affected_strand])
        
        # Identify truly moving strands (ones being dragged by user, not just connected)
        # --- CORRECTED: Preserve truly_moving_strands from start_movement --- 
        # truly_moving_strands = [self.affected_strand] # OLD LOGIC
        # Retrieve the list set by start_movement and ensure it's treated as read-only here
        truly_moving_strands_read_only = getattr(self.canvas, 'truly_moving_strands', [self.affected_strand])
        print(f"DEBUG3: TRACKING 1_2 - Retrieved truly_moving_strands_read_only: {[s.layer_name for s in truly_moving_strands_read_only]}")
        # --- END CORRECTION ---
        
        # --- Find and include connected strands for drawing --- NEW BLOCK
        connected_strands_at_moving_point = set()
        moving_point_coord = None
        is_moving_endpoint = self.moving_side == 0 or self.moving_side == 1

        if is_moving_endpoint:
            if self.moving_side == 0:
                moving_point_coord = self.affected_strand.start
            else: # moving_side == 1
                moving_point_coord = self.affected_strand.end

            if moving_point_coord:
                # Check for connected strands using the layer state manager
                connected_strand_names = set()
                if hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
                    connections = self.canvas.layer_state_manager.getConnections()
                    connected_strand_names = set(connections.get(self.affected_strand.layer_name, []))
                    # logging.info(f"MoveMode: Direct connections for {self.affected_strand.layer_name}: {connected_strand_names}")
                    # Also check the reverse connection
                    for name, connected_list in connections.items():
                         if self.affected_strand.layer_name in connected_list:
                              connected_strand_names.add(name)
                    # logging.info(f"MoveMode: All connections for {self.affected_strand.layer_name}: {connected_strand_names}")

                for other_strand in self.canvas.strands:
                    if other_strand == self.affected_strand or isinstance(other_strand, MaskedStrand):
                        continue

                    # Check if they should be added as connected strands
                    should_add_connected = False
                    
                    # Always use state manager connections only, regardless of draw_only_affected_strand setting
                    # Never use proximity to create new connections that weren't already in the state
                    is_manager_connected = (other_strand.layer_name in connected_strand_names or
                                          self.affected_strand.layer_name in connections.get(other_strand.layer_name, []))
                    
                    if self.draw_only_affected_strand:
                        # When "drag only affected strand" is enabled, only show connected strands at the specific moving point
                        if is_manager_connected:
                            # Verify they're actually connected at this specific moving point
                            at_moving_point = (self.points_are_close(other_strand.start, moving_point_coord) or \
                                             self.points_are_close(other_strand.end, moving_point_coord))
                            
                            if at_moving_point:
                                should_add_connected = True
                                print(f"DEBUG2: Adding {other_strand.layer_name} - connected in state AND at moving point")
                            else:
                                print(f"DEBUG2: NOT adding {other_strand.layer_name} - connected in state but NOT at moving point")
                    else:
                        # When setting is disabled, show all connected strands but still verify connection at moving point
                        if is_manager_connected:
                            # Even when setting is OFF, we should only add strands connected at the specific moving point
                            at_moving_point = (self.points_are_close(other_strand.start, moving_point_coord) or \
                                             self.points_are_close(other_strand.end, moving_point_coord))
                            
                            if at_moving_point:
                                should_add_connected = True
                                print(f"DEBUG2: Adding {other_strand.layer_name} - connected in state manager AND at moving point")
                            else:
                                print(f"DEBUG2: NOT adding {other_strand.layer_name} - connected in state manager but NOT at moving point")

                    if should_add_connected:
                        connected_strands_at_moving_point.add(other_strand)
                        print(f"DEBUG3: TRACKING 1_2 - Added {other_strand.layer_name} to connected_strands_at_moving_point SET. Current set: {[s.layer_name for s in connected_strands_at_moving_point]}")
                        affected_strands.add(other_strand)
                        print(f"DEBUG3: TRACKING 1_2 - Added {other_strand.layer_name} to affected_strands via connection logic")
                        # logging.info(f"MoveMode (Update Pos): Adding {other_strand.layer_name} to affected (points close AND manager connected to {self.affected_strand.layer_name})")
                    #elif points_close:
                         # Optional: Log when points are close but not connected
                         # logging.info(f"MoveMode (Update Pos): Points close for {other_strand.layer_name}, but not manager-connected to {self.affected_strand.layer_name}. Not adding to affected.")
        # --- End finding and including connected strands ---

        # --- NEW BLOCK: Explicitly include attached strands sharing the same starting point ---
        if is_moving_endpoint and self.moving_side == 0 and hasattr(self.affected_strand, 'attached_strands'):
            moving_point_coord = self.affected_strand.start # Get the start point being moved
            for attached_strand in self.affected_strand.attached_strands:
                # Check if the attached strand starts at the same point being moved
                # Skip proximity detection if "drag only affected strand" is enabled
                if not self.draw_only_affected_strand and self.points_are_close(attached_strand.start, moving_point_coord):
                    # --- CORRECTED: Don't add to truly moving here --- 
                    # if attached_strand not in truly_moving_strands:
                    #     truly_moving_strands.append(attached_strand) # Add to the list for drawing
                    # --- END CORRECTION ---
                    
                    affected_strands.add(attached_strand) # Ensure it's also in affected
                    print(f"DEBUG3: TRACKING 1_2 - Added attached strand {attached_strand.layer_name} to affected_strands (shares start point)")
                    # Corrected Log Message:
                    # logging.info(f"MoveMode (Update Pos): Added attached strand {attached_strand.layer_name} sharing start point to affected_strands.")
        # --- End NEW BLOCK ---

        # Special handling for MaskedStrand - add both selected strands to affected_strands (not truly_moving)
        is_masked_strand = isinstance(self.affected_strand, MaskedStrand)
        if is_masked_strand:
            if hasattr(self.affected_strand, 'first_selected_strand') and self.affected_strand.first_selected_strand:
                # --- CORRECTED: Don't add to truly moving here --- 
                affected_strands.add(self.affected_strand.first_selected_strand)
            if hasattr(self.affected_strand, 'second_selected_strand') and self.affected_strand.second_selected_strand:
                 # --- CORRECTED: Don't add to truly moving here --- 
                affected_strands.add(self.affected_strand.second_selected_strand)
        
        # For attached strands, ensure children are in affected set too (not truly_moving)
        if isinstance(self.affected_strand, AttachedStrand) and hasattr(self.affected_strand, 'attached_strands'):
            for attached in self.affected_strand.attached_strands:
                 # --- CORRECTED: Don't add to truly moving here --- 
                 affected_strands.add(attached) # Ensure children are in affected set too
        # --- End finding and including connected strands ---

        # Store the old path of the affected strand for proper redrawing
        old_path_rect = None
        if hasattr(self.affected_strand, 'path') and self.affected_strand.path:
            old_path_rect = self.affected_strand.path.boundingRect()
            # Add padding
            old_path_rect = old_path_rect.adjusted(-100, -100, 100, 100)

        # For MaskedStrand, store the old paths of constituent strands
        if is_masked_strand:
            if hasattr(self.affected_strand, 'first_selected_strand') and self.affected_strand.first_selected_strand and hasattr(self.affected_strand.first_selected_strand, 'path'):
                first_old_rect = self.affected_strand.first_selected_strand.path.boundingRect().adjusted(-100, -100, 100, 100)
                if old_path_rect:
                    old_path_rect = old_path_rect.united(first_old_rect)
                else:
                    old_path_rect = first_old_rect
                    
            if hasattr(self.affected_strand, 'second_selected_strand') and self.affected_strand.second_selected_strand and hasattr(self.affected_strand.second_selected_strand, 'path'):
                second_old_rect = self.affected_strand.second_selected_strand.path.boundingRect().adjusted(-100, -100, 100, 100)
                if old_path_rect:
                    old_path_rect = old_path_rect.united(second_old_rect)
                else:
                    old_path_rect = second_old_rect

        # Store original positions to preserve non-moving endpoints
        original_start = None
        original_end = None
        if self.moving_side == 0 or self.moving_side == 1:
            original_start = QPointF(self.affected_strand.start)
            original_end = QPointF(self.affected_strand.end)
 

        if self.moving_side == 'control_point1':
            # Move the first control point
            self.affected_strand.control_point1 = new_pos
            # Don't recalculate the center control point, just update shape
            self.affected_strand.update_shape()
            self.affected_strand.update_side_line()
            # Update the selection rectangle to the new position
            self.selected_rectangle = self.get_control_point_rectangle(self.affected_strand, 1)
            # Keep the strand deselected to prevent highlighting during control point movement
            self.affected_strand.is_selected = False
            self.canvas.selected_attached_strand = None
            self.highlighted_strand = None
        elif self.moving_side == 'control_point2':
            # Move the second control point
            self.affected_strand.control_point2 = new_pos

            
            # Don't recalculate the center control point, just update shape
            self.affected_strand.update_shape()
            self.affected_strand.update_side_line()  # Call again to ensure it's updated
            # Update the selection rectangle to the new position
            self.selected_rectangle = self.get_control_point_rectangle(self.affected_strand, 2)
            # Keep the strand deselected to prevent highlighting during control point movement
            self.affected_strand.is_selected = False
            self.canvas.selected_attached_strand = None
            self.highlighted_strand = None
        elif self.moving_side == 'control_point_center':
            # Move the center control point
            self.affected_strand.control_point_center = new_pos
            # Set the flag to indicate the center control point has been manually positioned
            self.affected_strand.control_point_center_locked = True
            # Update the strand shape
            self.affected_strand.update_shape()
            self.affected_strand.update_side_line()
            # Update the selection rectangle to the new position
            self.selected_rectangle = self.get_control_point_rectangle(self.affected_strand, 3)
            # Keep the strand deselected to prevent highlighting during control point movement
            self.affected_strand.is_selected = False
            self.canvas.selected_attached_strand = None
            self.highlighted_strand = None

        elif self.moving_side == 0 or self.moving_side == 1:
            # Moving start or end point
            if is_masked_strand:
                # Special handling for MaskedStrand
                self.move_masked_strand(new_pos, self.moving_side)
                # Update the selection area  
                if self.moving_side == 0:
                    base_size = 90
                    # For visual consistency, scale the selection rectangle with zoom
                    visual_size = base_size / self.canvas.zoom_factor
                    self.selected_rectangle = QRectF(
                        self.affected_strand.start.x() - visual_size/2,
                        self.affected_strand.start.y() - visual_size/2,
                        visual_size,
                        visual_size
                    )
                else:
                    base_size = 90
                    # For visual consistency, scale the selection rectangle with zoom
                    visual_size = base_size / self.canvas.zoom_factor
                    self.selected_rectangle = QRectF(
                        self.affected_strand.end.x() - visual_size/2,
                        self.affected_strand.end.y() - visual_size/2,
                        visual_size,
                        visual_size
                    )
            else:
                # Standard handling for normal strands
                parent_strand = self.move_strand_and_update_attached(self.affected_strand, new_pos, self.moving_side)
                
                # If we found a parent strand, add it to affected strands but NOT truly_moving_strands
                if parent_strand:
                    affected_strands.add(parent_strand)

                # --- Update connected strands positions (moved from within move_strand_and_update_attached) ---
                # The connected strands were already found and added to truly_moving_strands/affected_strands above
                if moving_point_coord:
                    print(f"DEBUG3: TRACKING 1_2 - About to process connected_strands_at_moving_point: {[s.layer_name for s in connected_strands_at_moving_point]}")
                    for connected_strand in connected_strands_at_moving_point:
                        # Only update connected strand positions if they are in the truly_moving_strands list
                        # This prevents automatic position correction based on proximity
                        truly_moving_strands = getattr(self.canvas, 'truly_moving_strands', [])
                        if connected_strand in truly_moving_strands:
                            # Determine which end of the connected strand needs to move based on the original position
                            # Since connected_strands_at_moving_point was already filtered to only include strands
                            # connected at the specific moving point, we use the original moving point position
                            original_moving_point = self.affected_strand.start if self.moving_side == 0 else self.affected_strand.end
                            
                            connected_moving_side = -1
                            # Use the original moving point position to determine which end to update
                            if self.points_are_close(connected_strand.start, original_moving_point):
                                connected_moving_side = 0
                            elif self.points_are_close(connected_strand.end, original_moving_point):
                                connected_moving_side = 1

                            if connected_moving_side == 0:
                                connected_strand.start = new_pos
                                connected_strand.update_shape()
                                connected_strand.update_side_line()
                            elif connected_moving_side == 1:
                                connected_strand.end = new_pos
                                connected_strand.update_shape()
                                connected_strand.update_side_line()
                # --- End update connected strands positions ---

            # ... (update selection rectangle and selection state)

        # ... (calculate update_rect)

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
                padding = 140
                strand_rect = strand_rect.adjusted(-padding, -padding, padding, padding)
                
                if update_rect is None:
                    update_rect = strand_rect
                else:
                    update_rect = update_rect.united(strand_rect)
                    
            # For MaskedStrand, also include the child strands' paths
            if isinstance(strand, MaskedStrand):
                if hasattr(strand, 'first_selected_strand') and strand.first_selected_strand and hasattr(strand.first_selected_strand, 'path'):
                    first_rect = strand.first_selected_strand.path.boundingRect().adjusted(-100, -100, 100, 100)
                    if update_rect:
                        update_rect = update_rect.united(first_rect)
                    else:
                        update_rect = first_rect
                        
                if hasattr(strand, 'second_selected_strand') and strand.second_selected_strand and hasattr(strand.second_selected_strand, 'path'):
                    second_rect = strand.second_selected_strand.path.boundingRect().adjusted(-100, -100, 100, 100)
                    if update_rect:
                        update_rect = update_rect.united(second_rect)
                    else:
                        update_rect = second_rect
        
        # If we still don't have an update_rect, create one from the selection point
        if not update_rect and isinstance(self.selected_rectangle, QRectF):
            # Make it much larger than the selection rectangle to ensure the whole strand is visible
            base_padding = 200
            # Scale padding for visual consistency
            padding = base_padding / self.canvas.zoom_factor
            update_rect = self.selected_rectangle.adjusted(-padding, -padding, padding, padding)
        elif not update_rect:
            # Fallback to a default size around the new position
            base_radius = 250
            # Scale radius for visual consistency
            radius = base_radius / self.canvas.zoom_factor
            size = radius * 2
            update_rect = QRectF(
                new_pos.x() - radius,
                new_pos.y() - radius,
                size,
                size
            )
        
        # Store the update rectangle for optimized rendering
        self.canvas.active_strand_update_rect = update_rect
        self.last_update_rect = update_rect
        
        # Store affected strands for optimized rendering
        # Ensure affected_strands includes everything needed (main, connected, parents, children)
        self.canvas.affected_strands_for_drawing = list(affected_strands)
        print(f"DEBUG3: TRACKING 1_2 - Final affected_strands_for_drawing: {[s.layer_name for s in self.canvas.affected_strands_for_drawing]}")

        # --- CORRECTED: Re-assert the read-only list from the start of the function --- 
        self.canvas.truly_moving_strands = truly_moving_strands_read_only
        print(f"DEBUG3: TRACKING 1_2 - Set truly_moving_strands to read_only list: {[s.layer_name for s in self.canvas.truly_moving_strands]}")
        # --- END CORRECTION ---
        # logging.info(f"MoveMode (Update Pos): Final truly_moving_strands: {[s.layer_name for s in self.canvas.truly_moving_strands]}, affected_strands_for_drawing: {[s.layer_name for s in self.canvas.affected_strands_for_drawing]}")
        
        # --- NEW: Log positions of all affected strands AFTER updates in this step ---
        #if hasattr(self.canvas, 'affected_strands_for_drawing'):
            # logging.info("--- Positions after update_strand_position step ---")
            # for s in self.canvas.affected_strands_for_drawing:
            #     logging.info(f"  Strand {s.layer_name}: Start={s.start}, End={s.end}")
            # logging.info("--------------------------------------------------")
        # --- END NEW LOGGING ---

        # Check for attached strands that share the same start/end point with the affected strand
        # This is crucial for when moving a shared point between main strand and attached strand
        print(f"DEBUG3: TRACKING 1_2 - About to check attached strands for {self.affected_strand.layer_name if self.affected_strand else 'None'}")
        if self.affected_strand and hasattr(self.affected_strand, 'attached_strands'):
            print(f"DEBUG3: TRACKING 1_2 - {self.affected_strand.layer_name} has attached_strands: {[s.layer_name for s in self.affected_strand.attached_strands]}")
            is_moving_start = (self.moving_side == 0)
            is_moving_end = (self.moving_side == 1)
            moving_point = self.affected_strand.start if is_moving_start else self.affected_strand.end
            
            # Find any attached strands that share this same moving point
            for attached in self.affected_strand.attached_strands:
                # If we're moving the start point of the main strand, check if any attached strand
                # also starts at this same point (or ends at this same point)
                should_add_attached = False
                print(f"DEBUG3: TRACKING 1_2 - Checking attached strand {attached.layer_name}")
                
                # Always check if the attached strand is actually connected at the moving point
                # regardless of the draw_only_affected_strand setting
                if ((is_moving_start and self.points_are_close(attached.start, moving_point)) or \
                   (is_moving_start and self.points_are_close(attached.end, moving_point)) or \
                   (is_moving_end and self.points_are_close(attached.start, moving_point)) or \
                   (is_moving_end and self.points_are_close(attached.end, moving_point))):
                    should_add_attached = True
                    print(f"DEBUG3: TRACKING 1_2 - {attached.layer_name} is connected at moving point, adding to truly_moving_strands")
                else:
                    print(f"DEBUG3: TRACKING 1_2 - {attached.layer_name} is NOT connected at moving point, not adding to truly_moving_strands")
                
                if should_add_attached and attached not in self.canvas.truly_moving_strands:
                    print(f"DEBUG3: TRACKING 1_2 - APPENDING attached strand {attached.layer_name} to truly_moving_strands! draw_only_affected_strand={self.draw_only_affected_strand}")
                    print(f"DEBUG3: TRACKING 1_2 - Attached strand check details: moving_point={moving_point}, attached.start={attached.start}, attached.end={attached.end}")
                    print(f"DEBUG3: TRACKING 1_2 - Points close checks: start_close={self.points_are_close(attached.start, moving_point)}, end_close={self.points_are_close(attached.end, moving_point)}")
                    self.canvas.truly_moving_strands.append(attached)
                        # logging.info(f"MoveMode: Added {attached.layer_name} to truly_moving_strands - shares point with {self.affected_strand.layer_name}")

        # For immediate visual feedback during dragging, invalidate the cache here too
        if hasattr(self.canvas, 'background_cache_valid'):
            self.canvas.background_cache_valid = False
            
        # Force an immediate update for continuous visual feedback
        self.canvas.update()
        
        # Force a redraw while holding to ensure continuous visual feedback
        self.force_redraw_while_holding()

    def move_masked_strand(self, new_pos, moving_side):
        """Move a masked strand's points.

        Args:
            new_pos (QPointF): The new position.
            moving_side (int): Which side of the strand is being moved (0 for start, 1 for end).
        """
        if not self.affected_strand:
            return
            
        if not isinstance(self.affected_strand, MaskedStrand):
            # This should not happen but handle it gracefully
            return
            
        # Record original masked strand endpoints for deletion rectangle translation
        old_masked_start = QPointF(self.affected_strand.start)
        old_masked_end   = QPointF(self.affected_strand.end)

        # Apply minimum distance constraint for masked strands too
        if moving_side == 0:  # Moving start point
            other_point = self.affected_strand.end
            if self.calculate_distance(new_pos, other_point) < self.MIN_STRAND_POINTS_DISTANCE:
                new_pos = self.adjust_position_to_maintain_distance(new_pos, other_point)
        elif moving_side == 1:  # Moving end point
            other_point = self.affected_strand.start
            if self.calculate_distance(new_pos, other_point) < self.MIN_STRAND_POINTS_DISTANCE:
                new_pos = self.adjust_position_to_maintain_distance(new_pos, other_point)
        
        # Store original positions to preserve non-moving endpoints
        original_start = None
        original_end = None
        if moving_side == 0:
            original_end = QPointF(self.affected_strand.end)
        else:
            original_start = QPointF(self.affected_strand.start)
        
        # Update the MaskedStrand's own position using setter
        if moving_side == 0:
            self.affected_strand.start = new_pos
        else:
            self.affected_strand.end = new_pos
        
        # Restore non-moving endpoint
        if moving_side == 0 and original_end:
            self.affected_strand.end = original_end
        elif moving_side == 1 and original_start:
            self.affected_strand.start = original_start
        print ("--------------------------------")
        print ("affected_strand", self.affected_strand.layer_name)
        print ("moving_side", moving_side)
        print ("original_start", original_start)
        print ("original_end", original_end)
        print ("--------------------------------")
        # Update shape
        self.affected_strand.update_shape()
        
        # Update the constituent strands if they exist
        if moving_side == 0:
            if hasattr(self.affected_strand, 'first_selected_strand') and self.affected_strand.first_selected_strand:
                # Store the non-moving endpoint
                first_old_end = QPointF(self.affected_strand.first_selected_strand.end)
                # Use setter to update position
                self.affected_strand.first_selected_strand.start = new_pos
                # Restore non-moving endpoint
                self.affected_strand.first_selected_strand.end = first_old_end
                self.affected_strand.first_selected_strand.update_shape()
                
            if hasattr(self.affected_strand, 'second_selected_strand') and self.affected_strand.second_selected_strand:
                # Store the non-moving endpoint
                second_old_end = QPointF(self.affected_strand.second_selected_strand.end)
                # Use setter to update position  
                self.affected_strand.second_selected_strand.start = new_pos
                # Restore non-moving endpoint
                self.affected_strand.second_selected_strand.end = second_old_end
                self.affected_strand.second_selected_strand.update_shape()
        else:
            if hasattr(self.affected_strand, 'first_selected_strand') and self.affected_strand.first_selected_strand:
                # Store the non-moving endpoint
                first_old_start = QPointF(self.affected_strand.first_selected_strand.start)
                # Use setter to update position
                self.affected_strand.first_selected_strand.end = new_pos
                # Restore non-moving endpoint
                self.affected_strand.first_selected_strand.start = first_old_start
                self.affected_strand.first_selected_strand.update_shape()
                
            if hasattr(self.affected_strand, 'second_selected_strand') and self.affected_strand.second_selected_strand:
                # Store the non-moving endpoint
                second_old_start = QPointF(self.affected_strand.second_selected_strand.start)
                # Use setter to update position
                self.affected_strand.second_selected_strand.end = new_pos
                # Restore non-moving endpoint
                self.affected_strand.second_selected_strand.start = second_old_start
                self.affected_strand.second_selected_strand.update_shape()
        # Translate deletion rectangles along with masked strand movement
        if hasattr(self.affected_strand, 'deletion_rectangles') and self.affected_strand.deletion_rectangles:
                # Compute movement delta
                dx = (self.affected_strand.start.x() - old_masked_start.x()) if moving_side == 0 else (self.affected_strand.end.x() - old_masked_end.x())
                dy = (self.affected_strand.start.y() - old_masked_start.y()) if moving_side == 0 else (self.affected_strand.end.y() - old_masked_end.y())
                for rect in self.affected_strand.deletion_rectangles:
                    rect['top_left'] = (rect['top_left'][0] + dx, rect['top_left'][1] + dy)
                    rect['top_right'] = (rect['top_right'][0] + dx, rect['top_right'][1] + dy)
                    rect['bottom_left'] = (rect['bottom_left'][0] + dx, rect['bottom_left'][1] + dy)
                    rect['bottom_right'] = (rect['bottom_right'][0] + dx, rect['bottom_right'][1] + dy)
        # Use the new comprehensive update method if available
        if hasattr(self.affected_strand, 'force_complete_update'):
            self.affected_strand.force_complete_update()
        else:
            # Fall back to the old update approach
            # Update mask path and recalculate center points
            if hasattr(self.affected_strand, 'update_mask_path'):
                self.affected_strand.update_mask_path()
                
            # Ensure center points are updated
            if hasattr(self.affected_strand, 'calculate_center_point'):
                self.affected_strand.calculate_center_point()
                    
            # Force update of all components - only pass center point if it exists
            if hasattr(self.affected_strand, 'edited_center_point') and self.affected_strand.edited_center_point:
                self.affected_strand.update(self.affected_strand.edited_center_point)
            elif hasattr(self.affected_strand, 'base_center_point') and self.affected_strand.base_center_point:
                self.affected_strand.update(self.affected_strand.base_center_point)
            else:
                # If no center point is available, update without position
                # This will trigger the warning but won't crash
                self.affected_strand.update(None)
        
        # Force a complete redraw of the canvas
        if hasattr(self.canvas, 'background_cache_valid'):
            self.canvas.background_cache_valid = False
        
        # Update canvas bounds to track the new strand positions
        if hasattr(self.canvas, 'update_canvas_bounds'):
            self.canvas.update_canvas_bounds()
        
        # Ensure the canvas is updated
        self.canvas.update()
        
        # Force a redraw while holding to ensure continuous visual feedback
        self.force_redraw_while_holding()

    def move_strand_and_update_attached(self, strand, new_pos, moving_side):
        """Move the strand's point and update attached strands without resetting control points.

        Args:
            strand (Strand): The strand to move.
            new_pos (QPointF): The new position.
            moving_side (int or str): Which side of the strand is being moved.
            
        Returns:
            Strand or None: The parent strand if one exists, otherwise None.
        """
        # --- ADD LOGGING: Before update ---
        # logging.info(f"MoveStrandUpdate: Moving strand {strand.layer_name}, side {moving_side} to {new_pos}")
        # logging.info(f"MoveStrandUpdate: BEFORE - Start: {strand.start}, End: {strand.end}")
        # --- END LOGGING ---
        
        # Store original positions to preserve the non-moving endpoint
        old_start, old_end = QPointF(strand.start), QPointF(strand.end)
        
        # Apply minimum distance constraint
        if moving_side == 0:  # Moving start point
            other_point = strand.end
            if self.calculate_distance(new_pos, other_point) < self.MIN_STRAND_POINTS_DISTANCE:
                new_pos = self.adjust_position_to_maintain_distance(new_pos, other_point)
        elif moving_side == 1:  # Moving end point
            other_point = strand.start
            if self.calculate_distance(new_pos, other_point) < self.MIN_STRAND_POINTS_DISTANCE:
                new_pos = self.adjust_position_to_maintain_distance(new_pos, other_point)
        
        # Keep track of all affected strands for optimized drawing
        affected_strands = set([strand])
        # Track the parent strand if one exists
        parent_strand = None

        if moving_side == 0:
            # Use the strand's setter directly to ensure control points are properly updated
            strand.start = new_pos
        elif moving_side == 1:
            # Use the strand's setter directly to ensure control points are properly updated
            strand.end = new_pos

        strand.update_shape()
        strand.update_side_line()

        # Make sure the non-moving endpoint stays in place
        if moving_side == 0:
            strand.end = old_end
        elif moving_side == 1:
            strand.start = old_start
        
        # Update shape again after preserving the non-moving endpoint
        strand.update_shape()
        strand.update_side_line()

        # Update parent strands recursively
        parent_strands = self.update_parent_strands(strand)
        affected_strands.update(parent_strands)
        
        # Find the immediate parent strand
        if isinstance(strand, AttachedStrand):
            parent_strand = self.find_parent_strand(strand)
            if parent_strand:
                affected_strands.add(parent_strand)

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
                # Store the non-moving endpoint of first selected strand
                if moving_side == 0 and hasattr(strand.first_selected_strand, 'end'):
                    first_old_end = QPointF(strand.first_selected_strand.end)
                elif moving_side == 1 and hasattr(strand.first_selected_strand, 'start'):
                    first_old_start = QPointF(strand.first_selected_strand.start)
                
                strand.first_selected_strand.update(new_pos)
                
                # Restore the non-moving endpoint
                if moving_side == 0 and hasattr(strand.first_selected_strand, 'end'):
                    strand.first_selected_strand.end = first_old_end
                    strand.first_selected_strand.update_shape()
                elif moving_side == 1 and hasattr(strand.first_selected_strand, 'start'):
                    strand.first_selected_strand.start = first_old_start
                    strand.first_selected_strand.update_shape()
                
                affected_strands.add(strand.first_selected_strand)
                
            if strand.second_selected_strand and hasattr(strand.second_selected_strand, 'update'):
                # Store the non-moving endpoint of second selected strand
                if moving_side == 0 and hasattr(strand.second_selected_strand, 'end'):
                    second_old_end = QPointF(strand.second_selected_strand.end)
                elif moving_side == 1 and hasattr(strand.second_selected_strand, 'start'):
                    second_old_start = QPointF(strand.second_selected_strand.start)
                
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
                
                # Restore the non-moving endpoint
                if moving_side == 0 and hasattr(strand.second_selected_strand, 'end'):
                    strand.second_selected_strand.end = second_old_end
                    strand.second_selected_strand.update_shape()
                elif moving_side == 1 and hasattr(strand.second_selected_strand, 'start'):
                    strand.second_selected_strand.start = second_old_start
                    strand.second_selected_strand.update_shape()
                
                affected_strands.add(strand.second_selected_strand)
                
        # Find any connected strands using the OLD position before the move
        old_moving_point = old_start if moving_side == 0 else old_end
        connected_strand = self.find_connected_strand(strand, moving_side, old_moving_point)
        # logging.info(f"MoveStrandUpdate: find_connected_strand for {strand.layer_name} side {moving_side} at {old_moving_point} -> {connected_strand.layer_name if connected_strand else None}")
        
        if connected_strand:
            affected_strands.add(connected_strand)
            
            # Update connected strand's connection point to match the new position
            if moving_side == 0:
                # Moving strand's start -> update connected strand's end
                connected_strand.end = new_pos
                # logging.info(f"MoveStrandUpdate: Updated connected {connected_strand.layer_name} end to {new_pos}")
            else:
                # Moving strand's end -> update connected strand's start
                connected_strand.start = new_pos
                # logging.info(f"MoveStrandUpdate: Updated connected {connected_strand.layer_name} start to {new_pos}")
                
            connected_strand.update_shape()
            connected_strand.update_side_line()
            
        # Store affected strands for optimized rendering
        self.canvas.affected_strands_for_drawing = list(affected_strands)

        # --- ADD LOGGING: After update ---
        # logging.info(f"MoveStrandUpdate: AFTER - Strand {strand.layer_name} - Start: {strand.start}, End: {strand.end}")
        # --- END LOGGING ---

        return parent_strand

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
                # --- FIX: Update only the correct parent endpoint --- 
                # Check which side of the parent the child (strand) is attached to
                if hasattr(strand, 'attachment_side'):
                    if strand.attachment_side == 0:
                        # Child is attached to parent's start, update parent's start
                        parent.start = strand.start
                    elif strand.attachment_side == 1:
                        # Child is attached to parent's end, update parent's end
                        parent.end = strand.start # AttachedStrand.start is always the connection point
                    # else:
                    #     # Handle potential unexpected attachment_side value
                    #     # logging.warning(f"update_parent_strands: Invalid attachment_side {strand.attachment_side} for {strand.layer_name}")
                else:
                    # Fallback or error if attachment_side is missing (shouldn't happen)
                    # logging.error(f"update_parent_strands: Missing attachment_side for {strand.layer_name}")
                    # As a fallback, try the old (potentially problematic) logic
                    if strand.start == parent.start:
                        parent.start = strand.start
                    else:
                        parent.end = strand.start
                # --- END FIX ---

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
            # Store the non-moving endpoint
            attached_old_end = QPointF(attached.end)
            
            if attached.start == old_start:
                attached.start = strand.start
            elif attached.start == old_end:
                attached.start = strand.end
            # Update attached strand without resetting control points
            attached.update(attached.end, reset_control_points=False)
            
            # Ensure the end point stays in place
            attached.end = attached_old_end
            attached.update_shape()
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



    

    def draw_c_shape_for_strand(self, painter, strand):
        """
        Draw C-shape for a specific strand.
        
        Args:
            painter (QPainter): The painter object to draw with.
            strand: The strand to draw the C-shape for.
        """
        # Check if strand is hidden - don't draw C-shape for hidden strands
        if hasattr(strand, 'is_hidden') and strand.is_hidden:
            return
            
        # Extra check to prevent drawing when moving control points
        if self.is_moving_control_point or (self.is_moving and (self.moving_side == 'control_point1' or self.moving_side == 'control_point2')):
            return
            
        painter.save()
        
        # Draw the circles at connection points
        for i, has_circle in enumerate(strand.has_circles):
            # --- REPLACE WITH THIS SIMPLE CHECK ---
            # Only draw if this end should have a circle and the strand is currently selected
            if not has_circle or not strand.is_selected:
                continue
            # --- END REPLACE ---
            
            # Save painter state (Original line)
            painter.save()
            
            center = strand.start if i == 0 else strand.end
            
            # Calculate the proper radius for the highlight
            # The highlighted strand outline uses: QPen(QColor('red'), self.stroke_width + 8)
            # This pen is drawn around the stroke path, so the outer edge is at:
            highlight_pen_thickness = 10  # Fixed thickness instead of strand.stroke_width + 8
            stroke_path_radius = (strand.width + strand.stroke_width * 2) / 2
            outer_radius = stroke_path_radius + highlight_pen_thickness / 2
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
            
            # Now create the stroke and color parts within the C-shape
            # Outer part (stroke area) - from outer_radius to stroke boundary
            stroke_outer_radius = outer_radius
            stroke_inner_radius = strand.width / 2 + strand.stroke_width
            
            stroke_outer_circle = QPainterPath()
            stroke_outer_circle.addEllipse(center, stroke_outer_radius, stroke_outer_radius)
            stroke_inner_circle = QPainterPath()
            stroke_inner_circle.addEllipse(center, stroke_inner_radius, stroke_inner_radius)
            stroke_ring = stroke_outer_circle.subtracted(stroke_inner_circle)
            stroke_c_shape = stroke_ring.subtracted(mask_rect)
            
            # Inner part (color area) - from stroke boundary to inner_radius
            color_outer_radius = strand.width / 2 + strand.stroke_width
            color_inner_radius = inner_radius
            
            color_outer_circle = QPainterPath()
            color_outer_circle.addEllipse(center, color_outer_radius, color_outer_radius)
            color_inner_circle = QPainterPath()
            color_inner_circle.addEllipse(center, color_inner_radius, color_inner_radius)
            color_ring = color_outer_circle.subtracted(color_inner_circle)
            color_c_shape = color_ring.subtracted(mask_rect)
            
            # Draw the stroke part in red
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 0, 0, 255))
            painter.drawPath(stroke_c_shape)
            
            # Draw the color part in black
            painter.setBrush(QColor(0, 0, 0, 255))
            painter.drawPath(color_c_shape)
            
            # Restore painter state
            painter.restore()
        
        painter.restore()

    def build_connection_cache(self):
        """Build a cache of connection relationships for performance optimization."""
        if not hasattr(self.canvas, 'layer_state_manager') or not self.canvas.layer_state_manager:
            return
            
        self.connection_cache.clear()
        connections = self.canvas.layer_state_manager.getConnections()
        
        # Build a mapping of (strand_name, side) -> connected_strand_object
        for strand in self.canvas.strands:
            if isinstance(strand, MaskedStrand):
                continue
                
            strand_connections = connections.get(strand.layer_name, [])
            prefix = strand.layer_name.split('_')[0]
            
            for connected_layer_name in strand_connections:
                if not connected_layer_name.startswith(f"{prefix}_"):
                    continue
                    
                # Find the connected strand object
                connected_strand = next(
                    (s for s in self.canvas.strands 
                     if s.layer_name == connected_layer_name 
                     and not isinstance(s, MaskedStrand)), 
                    None
                )
                
                if connected_strand and connected_strand != strand:
                    # Check which side this connection is on
                    # Side 0 (start) connects to other strand's end
                    # Skip proximity detection if "drag only affected strand" is enabled
                    if not self.draw_only_affected_strand:
                        if self.points_are_close(strand.start, connected_strand.end):
                            cache_key = (strand.layer_name, 0)
                            self.connection_cache[cache_key] = connected_strand
                        # Side 1 (end) connects to other strand's start  
                        elif self.points_are_close(strand.end, connected_strand.start):
                            cache_key = (strand.layer_name, 1)
                            self.connection_cache[cache_key] = connected_strand
        
        self.cache_valid = True

    def invalidate_connection_cache(self):
        """Invalidate the connection cache when strands are modified."""
        self.cache_valid = False
        self.connection_cache.clear()

    def get_cached_connected_strand(self, strand, side):
        """Get connected strand from cache if available."""
        if not self.cache_valid:
            self.build_connection_cache()
            
        cache_key = (strand.layer_name, side)
        return self.connection_cache.get(cache_key, None)

    def find_connected_strand(self, strand, side, moving_point):
        """Find a strand connected to the given strand at the specified side."""
        if not hasattr(self.canvas, 'layer_state_manager') or not self.canvas.layer_state_manager:
            return None

        # Use cached connection if available for better performance    
        cached_strand = self.get_cached_connected_strand(strand, side)
        if cached_strand:
            # Verify the cached connection is still valid by checking the moving point
            # Skip proximity detection if "drag only affected strand" is enabled
            if not self.draw_only_affected_strand:
                if side == 0 and self.points_are_close(cached_strand.end, moving_point):
                    return cached_strand
                elif side == 1 and self.points_are_close(cached_strand.start, moving_point):
                    return cached_strand
            # If cached connection is invalid, fall back to original search
            
        # Fallback to original search method if cache miss or invalid
        connections = self.canvas.layer_state_manager.getConnections()
        strand_connections = connections.get(strand.layer_name, [])
        prefix = strand.layer_name.split('_')[0]

        for connected_layer_name in strand_connections:
            if not connected_layer_name.startswith(f"{prefix}_"):
                continue

            connected_strand = next(
                (s for s in self.canvas.strands 
                if s.layer_name == connected_layer_name 
                and not isinstance(s, MaskedStrand)), 
                None
            )

            if connected_strand and connected_strand != strand:
                # Skip proximity detection if "drag only affected strand" is enabled
                if not self.draw_only_affected_strand and ((side == 0 and self.points_are_close(connected_strand.end, moving_point)) or \
                (side == 1 and self.points_are_close(connected_strand.start, moving_point))):
                    return connected_strand

        return None

    def draw(self, painter):
        """
        Draw method called by the canvas during paintEvent.
        
        Args:
            painter (QPainter): The painter object to draw with.
        """
        # When optimized drawing is enabled and we're moving, drawing is handled
        # by the optimized paint handler, so we skip drawing here.
        if self.is_moving and self.draw_only_affected_strand:
            return
            
        # In normal drawing mode (or when not moving), draw C-shaped highlights for all selected strands.
   

    # Add a new method to reset selection state
    def reset_selection(self):
        """Reset the selection state when deselect all is requested."""
        # Remove the problematic logging that causes recursion
        # logging.info(f"Reset selection called. is_moving_control_point: {self.is_moving_control_point}, is_moving_strand_point: {self.is_moving_strand_point}")
        
        # --- Persist Selection Start ---
        # DO NOT clear originally_selected_strand here. It should persist until mouseReleaseEvent.
        # # Only clear originally_selected_strand if we're not in control point or strand endpoint movement
        # if not (self.is_moving_control_point or self.is_moving_strand_point):
        #     logging.info(f"Clearing originally_selected_strand (was: {self.originally_selected_strand})")
        #     self.originally_selected_strand = None
        # else:
        #     logging.info(f"Preserving originally_selected_strand: {self.originally_selected_strand}")
        # --- Persist Selection End ---

        self.highlighted_strand = None # Clear legacy highlight reference
        self.temp_selected_strand = None
        self.user_deselected_all = True # Still useful to know if a deselect *signal* occurred



    def force_continuous_redraw(self):
        """Force continuous redraw to keep grid and strands visible even when not moving the mouse."""
        import logging
        
        # Only stop if we're definitely not moving anything
        if not self.is_moving and not self.affected_strand:
            # Stop the timer when completely done
            self.redraw_timer.stop()
            return
            
        # Always invalidate the background cache to ensure grid and other strands are visible
        if hasattr(self.canvas, 'background_cache_valid'):
            self.canvas.background_cache_valid = False
                
        # Force a full redraw of the canvas
        self.canvas.update()
        
        # Ensure we get another update on the next UI cycle for smoother rendering
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, self.canvas.update)

    def mouseMoveEvent(self, event):
        """
        Handle mouse move events.
        
        Args:
            event (QMouseEvent): The mouse event.
        """
        # --- ADDED: Log current state on move (only if not suppressing) ---
        import logging
        if self.is_moving and not perf_logger.suppress_move_logging:
            logging.info(f"MouseMove Check: Affected={self.affected_strand.layer_name if self.affected_strand else 'None'}, Side={self.moving_side}")
        # --- END ADDED ---

        # If we're not in a moving state, do nothing
        if not self.is_moving:
            return
            
        # Get the current position (already converted to canvas coordinates by canvas)
        pos = event.pos()
        
        # Apply the mouse offset to maintain smooth movement from initial click position
        if (hasattr(self, 'mouse_offset') and self.mouse_offset and 
            (self.mouse_offset.x() != 0 or self.mouse_offset.y() != 0)):
            adjusted_pos = QPointF(pos.x() + self.mouse_offset.x(), 
                                  pos.y() + self.mouse_offset.y())
            # Debug logging for zoom-out issues
            if hasattr(self.canvas, 'zoom_factor') and self.canvas.zoom_factor < 0.8:
                logging.info(f"ZOOM_MOVE: zoom={self.canvas.zoom_factor:.2f}, raw_pos={pos}, offset={self.mouse_offset}, adjusted={adjusted_pos}")
        else:
            # No offset needed (cursor was moved to strand position) or offset is zero
            adjusted_pos = pos
        
        # Smart grid snapping based on zoom level and modifiers
        # Check if Ctrl key is pressed for forced grid snapping
        from PyQt5.QtWidgets import QApplication
        force_grid_snap = QApplication.keyboardModifiers() & Qt.ControlModifier
        
        # Extra logging for zoom-out debugging
        if hasattr(self.canvas, 'zoom_factor') and self.canvas.zoom_factor < 0.8:
            logging.info(f"ZOOM_SNAP: Before snapping - adjusted_pos={adjusted_pos}, zoom={self.canvas.zoom_factor:.2f}")
        
        if self.canvas.zoom_factor >= 0.8 or force_grid_snap:
            # Near normal zoom OR Ctrl held - use full grid snapping
            snapped_pos = self.canvas.snap_to_grid(adjusted_pos)
        elif self.canvas.zoom_factor >= 0.5:
            # Moderately zoomed out - use very gentle snapping
            snapped_pos = adjusted_pos
            
            # Only snap when EXTREMELY close to grid lines
            grid_size = self.canvas.grid_size
            # Scale threshold with zoom - smaller threshold when zoomed out
            snap_threshold = (grid_size / 8) * self.canvas.zoom_factor
            
            # Check if close to grid lines
            grid_x = round(adjusted_pos.x() / grid_size) * grid_size
            grid_y = round(adjusted_pos.y() / grid_size) * grid_size
            
            # Snap only if very close to grid intersection
            if (abs(adjusted_pos.x() - grid_x) < snap_threshold and 
                abs(adjusted_pos.y() - grid_y) < snap_threshold):
                snapped_pos = QPointF(grid_x, grid_y)
        else:
            # Very zoomed out (< 0.5) - NO grid snapping at all
            snapped_pos = adjusted_pos
        
        # Extra logging for zoom-out debugging
        if hasattr(self.canvas, 'zoom_factor') and self.canvas.zoom_factor < 0.8:
            logging.info(f"ZOOM_SNAP: After snapping - snapped_pos={snapped_pos}, zoom={self.canvas.zoom_factor:.2f}")
        
        # Update target position for gradual movement
        self.target_pos = snapped_pos
        
        # Update last snapped position for next movement
        self.last_snapped_pos = snapped_pos
        
        # Ensure the background cache is invalidated for continuous refresh
        if hasattr(self.canvas, 'background_cache_valid'):
            self.canvas.background_cache_valid = False
        
        # Update strand position directly for immediate feedback
        self.update_strand_position(snapped_pos)
        
        # Even if the mouse doesn't move, keep refreshing
        # Start/restart both timers to ensure continuous updates
        if hasattr(self, 'hold_timer') and not self.hold_timer.isActive():
            self.hold_timer.start()
            
        if hasattr(self, 'redraw_timer') and not self.redraw_timer.isActive():
            self.redraw_timer.start()
            
        # Force an immediate update
        self.canvas.update()

    def calculate_distance(self, point1, point2):
        """Calculate the Euclidean distance between two points."""
        return ((point1.x() - point2.x())**2 + (point1.y() - point2.y())**2)**0.5
        
    def adjust_position_to_maintain_distance(self, new_pos, fixed_point):
        """Adjust a position to maintain minimum distance from a fixed point."""
        # Calculate the vector from fixed point to new position
        dx = new_pos.x() - fixed_point.x()
        dy = new_pos.y() - fixed_point.y()
        
        # Calculate the current distance
        current_distance = self.calculate_distance(new_pos, fixed_point)
        
        if current_distance < self.MIN_STRAND_POINTS_DISTANCE and current_distance > 0:
            # Calculate the scaling factor to reach minimum distance
            scale = self.MIN_STRAND_POINTS_DISTANCE / current_distance
            
            # Apply the scaling to the vector
            adjusted_x = fixed_point.x() + dx * scale
            adjusted_y = fixed_point.y() + dy * scale
            
            # Return the adjusted position
            return QPointF(adjusted_x, adjusted_y)
        
        # If points are exactly on top of each other, move in an arbitrary direction
        if current_distance == 0:
            return QPointF(fixed_point.x() + self.MIN_STRAND_POINTS_DISTANCE, fixed_point.y())
            
        # Return the original position if distance is already sufficient
        return new_pos