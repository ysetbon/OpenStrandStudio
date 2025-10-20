import math
import time
from datetime import datetime
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
    """No-op performance logger placeholder to retain interface without logging."""

    def __init__(self):
        # Retain the flag in case any conditional checks reference it
        self.suppress_move_logging = True

    def suppress_during_move(self, suppress: bool = True) -> None:
        # No-op: we simply store the flag; no interaction with Python logging
        self.suppress_move_logging = suppress

    def log_if_allowed(self, level, message) -> None:
        # No-op: logging removed
        return

# Global performance logger instance
perf_logger = PerformanceLogger()

def _write_selection_debug(canvas, message: str) -> None:
    """
    Append move-mode debug details to the shared selection log when enabled.
    """
    enabled = getattr(canvas, 'selection_debug_logging_enabled', False) if canvas else False
    if not enabled:
        return
    log_path = getattr(canvas, 'selection_debug_log_path', None)
    if not log_path:
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'selection_debug.log')
    try:
        with open(log_path, 'a', encoding='utf-8') as log_file:
            log_file.write(f"{datetime.now().isoformat()} - MOVE_MODE - {message}\n")
    except Exception:
        pass

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
        self.frame_limit_ms = 1  # Min time between updates (~ 60 fps)

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
        
        # Always setup efficient paint handler during movement for consistent behavior
        # The toggle setting will control what gets drawn, not which paint handler to use
        has_original = hasattr(self.canvas, 'original_paintEvent')
        if not has_original:
            self._setup_optimized_paint_handler()
        else:
            pass
        
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
            
            # Always log at WARNING level to ensure we see this
            
            # Access the MoveMode instance through the stored reference
            move_mode = move_mode_ref
            
            # --- MODIFIED ENTRY CONDITION ---
            # Check if we should use the optimized path
            use_optimized_path = False
            
            # Check if we have any selected strands that need highlighting
            has_selected_strands = False
            truly_moving_strands = getattr(self_canvas, 'truly_moving_strands', [])
            for strand in self_canvas.strands:
                if getattr(strand, 'is_selected', False):
                    has_selected_strands = True
                    break
            
            # Always use optimized path when:
            # 1. MoveMode is set up AND
            # 2. Either we're actively moving OR we have selected strands that need highlighting
            has_canvas = hasattr(move_mode_ref, 'canvas')
            canvas_match = move_mode_ref.canvas == self_canvas if has_canvas else False
            is_moving = getattr(move_mode_ref, 'is_moving', False)
            
            
            if has_canvas and canvas_match and (is_moving or has_selected_strands or truly_moving_strands):
                use_optimized_path = True
            else:
                pass
            
            if not use_optimized_path:
                # If the original event exists, call it. Otherwise, maybe log an error or do nothing.
                if hasattr(self_canvas, 'original_paintEvent'):
                    self_canvas.original_paintEvent(event)
                else:
                    # This case should ideally not happen if setup is correct
                    pass
                return
            # --- END MODIFIED ENTRY CONDITION ---

            # If we reach here, we are using the optimized path.
            # Get the lists needed for drawing.
            active_strand = getattr(self_canvas, 'active_strand_for_drawing', None) # Still useful for some logic/logging
            truly_moving_strands = getattr(self_canvas, 'truly_moving_strands', []) # This is the key list
            affected_strands = getattr(self_canvas, 'affected_strands_for_drawing', truly_moving_strands) # Default to truly_moving if affected not set

        

            # Store original order of all strands for proper z-ordering
            # We need to collect ALL strands including attached strands
            original_strands_order = []
            
            # First, collect all main strands
            for strand in self_canvas.strands:
                original_strands_order.append(strand)
            
            # Then recursively add all attached strands
            for strand in self_canvas.strands:
                def collect_attached_strands(parent_strand):
                    for attached in parent_strand.attached_strands:
                        if attached not in original_strands_order:  # Avoid duplicates
                            original_strands_order.append(attached)
                        collect_attached_strands(attached)
                collect_attached_strands(strand)
                
            # Debug logging
            if not perf_logger.suppress_move_logging:
                pass
            
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
            
            
            # Special handling for the very first paint during movement to ensure consistent rendering
            first_movement = hasattr(self_canvas, 'movement_first_draw') and self_canvas.movement_first_draw == False
            
            # Debug: Check if this is the very first paint
            if first_movement and not perf_logger.suppress_move_logging:
                all_strand_names = []
                for s in self_canvas.strands:
                    all_strand_names.append(s.layer_name)
                    if hasattr(s, 'attached_strands'):
                        for att in s.attached_strands:
                            all_strand_names.append(att.layer_name)
            
            # Create a background cache first time or if it's invalidated
            background_cache_needed = (not hasattr(self_canvas, 'background_cache') or 
                                    not getattr(self_canvas, 'background_cache_valid', False) or
                                    first_movement)
            
            # Always regenerate cache when handling MaskedStrand
            if isinstance(active_strand, MaskedStrand):
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
                    # Force recreation with proper dimensions and device pixel ratio
                    viewport_rect = self_canvas.viewport().rect() if hasattr(self_canvas, 'viewport') else self_canvas.rect()
                    dpr = self_canvas.devicePixelRatioF() if hasattr(self_canvas, 'devicePixelRatioF') else 1.0
                    width = max(1, int(viewport_rect.width() * dpr))
                    height = max(1, int(viewport_rect.height() * dpr))
                    self_canvas.background_cache = QtGui.QPixmap(width, height)
                    if hasattr(self_canvas.background_cache, 'setDevicePixelRatio'):
                        self_canvas.background_cache.setDevicePixelRatio(dpr)
                    self_canvas.background_cache.fill(Qt.transparent)
            
            # Get truly moving strands from the canvas attribute if available, otherwise create it
            truly_moving_strands = getattr(self_canvas, 'truly_moving_strands', [])
            
            # Ensure truly_moving_strands is populated even when not actively moving
            # This is crucial for proper highlighting when toggle is OFF
            if not truly_moving_strands:
                # If we have an affected strand, use it
                if hasattr(move_mode, 'affected_strand') and move_mode.affected_strand:
                    truly_moving_strands = [move_mode.affected_strand]
                    # For attached strands, we want to also move immediate children but keep parents in original order
                    if isinstance(move_mode.affected_strand, AttachedStrand) and hasattr(move_mode.affected_strand, 'attached_strands'):
                        # Include the attached strands of the moving strand
                        truly_moving_strands.extend(move_mode.affected_strand.attached_strands)
                # If no affected strand but we have selected strands, use those for highlighting
                elif not getattr(move_mode, 'is_moving', False):
                    # When not actively moving, collect all selected strands for highlighting
                    for strand in self_canvas.strands:
                        if getattr(strand, 'is_selected', False):
                            truly_moving_strands.append(strand)
                        # Also check attached strands
                        if hasattr(strand, 'attached_strands'):
                            for attached in strand.attached_strands:
                                if getattr(attached, 'is_selected', False):
                                    truly_moving_strands.append(attached)
                    # Also check canvas selection references
                    if self_canvas.selected_strand and self_canvas.selected_strand not in truly_moving_strands:
                        truly_moving_strands.append(self_canvas.selected_strand)
                    if self_canvas.selected_attached_strand and self_canvas.selected_attached_strand not in truly_moving_strands:
                        truly_moving_strands.append(self_canvas.selected_attached_strand)
                        
            # CRITICAL FIX: When toggle is OFF, ensure ALL strands with is_selected=True are in truly_moving_strands
            # This ensures proper highlighting for connected strands
            if not move_mode.draw_only_affected_strand:
                # Collect all strands that have is_selected=True
                selected_strands = []
                for strand in original_strands_order:
                    if getattr(strand, 'is_selected', False):
                        if strand not in truly_moving_strands:
                            truly_moving_strands.append(strand)
                            
                    
            # Important: Ensure all truly moving strands are actually present in the original_strands_order
            # This handles the case where strands were just attached and might not be fully synchronized
            for moving_strand in truly_moving_strands[:]:  # Use slice to avoid modifying list while iterating
                if moving_strand not in original_strands_order:
                    # Try to find it in the canvas strands or attached strands
                    found = False
                    for canvas_strand in self_canvas.strands:
                        if canvas_strand == moving_strand:
                            original_strands_order.append(moving_strand)
                            found = True
                            break
                        elif hasattr(canvas_strand, 'attached_strands'):
                            for attached in canvas_strand.attached_strands:
                                if attached == moving_strand:
                                    original_strands_order.append(moving_strand)
                                    found = True
                                    break
                            if found:
                                break
                    if not found:
                        pass
                
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
                        viewport_rect = self_canvas.viewport().rect() if hasattr(self_canvas, 'viewport') else self_canvas.rect()
                        dpr = self_canvas.devicePixelRatioF() if hasattr(self_canvas, 'devicePixelRatioF') else 1.0
                        width = max(1, int(viewport_rect.width() * dpr))
                        height = max(1, int(viewport_rect.height() * dpr))
                        self_canvas.background_cache = QtGui.QPixmap(width, height)
                        if hasattr(self_canvas.background_cache, 'setDevicePixelRatio'):
                            self_canvas.background_cache.setDevicePixelRatio(dpr)
                        self_canvas.background_cache.fill(Qt.transparent)
                    
                    # Save the original strands list
                    original_strands = list(self_canvas.strands)
                    
                    # Respect the toggle:
                    # - When draw_only_affected_strand is True: do NOT draw any strands in the background cache
                    #   (cache only background/grid). Moving strands will be drawn on top, so only affected appear.
                    # - When False: include all non-moving strands in the cache for performance; moving are drawn on top.
                    if move_mode.draw_only_affected_strand:
                        static_strands = []
                    else:
                        static_strands = [s for s in original_strands if s not in truly_moving_strands]
                    
                    # For MaskedStrand, ensure both constituent strands are handled properly
                    if isinstance(active_strand, MaskedStrand):
                        # Add this check to ensure proper handling of edited masks
                        if hasattr(active_strand, 'first_selected_strand') and active_strand.first_selected_strand:
                            if active_strand.first_selected_strand in static_strands:
                                static_strands.remove(active_strand.first_selected_strand)
                        if hasattr(active_strand, 'second_selected_strand') and active_strand.second_selected_strand:
                            if active_strand.second_selected_strand in static_strands:
                                static_strands.remove(active_strand.second_selected_strand)
                    
                    # Log strand counts
                    
                    # Temporarily replace the strands list with only static strands
                    self_canvas.strands = static_strands
                    
                    # Draw the entire canvas (background, grid, static strands) to the cache
                    cache_painter = QtGui.QPainter(self_canvas.background_cache)
                    RenderUtils.setup_painter(cache_painter, enable_high_quality=True)
                    
                    # First clear the cache
                    cache_painter.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
                    cache_painter.fillRect(self_canvas.background_cache.rect(), Qt.transparent)
                    cache_painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
                    
                    # End the cache painter before calling original paintEvent
                    cache_painter.end()
                    
                    # Now draw the entire canvas without truly moving strands
                    # Create a paint event for the background cache
                    cache_event = QtGui.QPaintEvent(self_canvas.background_cache.rect())
                    
                    # Temporarily redirect painting to the background cache
                    original_paint_device = None
                    if hasattr(self_canvas, 'paintEvent'):
                        # Save the original paint method and create a wrapper
                        def paint_to_cache(evt):
                            bg_painter = QtGui.QPainter(self_canvas.background_cache)
                            RenderUtils.setup_painter(bg_painter, enable_high_quality=True)

                            # Mirror the exact transform order used in StrandDrawingCanvas.paintEvent
                            bg_painter.save()
                            canvas_center = QPointF(self_canvas.width() / 2, self_canvas.height() / 2)
                            bg_painter.translate(canvas_center)
                            bg_painter.translate(self_canvas.pan_offset_x, self_canvas.pan_offset_y)
                            bg_painter.scale(self_canvas.zoom_factor, self_canvas.zoom_factor)
                            bg_painter.translate(-canvas_center)

                            # Draw in the exact same sequence as the normal paint path
                            if hasattr(self_canvas, 'draw_background'):
                                self_canvas.draw_background(bg_painter)
                            if hasattr(self_canvas, 'show_grid') and self_canvas.show_grid and hasattr(self_canvas, 'draw_grid'):
                                # Ensure grid uses the full strand list, just like normal paint
                                previous_strands = self_canvas.strands
                                try:
                                    self_canvas.strands = original_strands
                                    self_canvas.draw_grid(bg_painter)
                                finally:
                                    self_canvas.strands = previous_strands
                            for strand in static_strands:
                                if hasattr(strand, 'draw'):
                                    strand.draw(bg_painter, skip_painter_setup=True)

                            bg_painter.restore()
                            bg_painter.end()
                        
                        paint_to_cache(cache_event)
                    
                    # Mark the cache as valid
                    self_canvas.background_cache_valid = True
                    
                    # Restore original strands
                    self_canvas.strands = original_strands
                        
                except Exception as e:
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
                        pass
                    # Background cache already contains the transformed content; draw it 1:1
                    painter.save()
                    painter.resetTransform()
                    painter.drawPixmap(0, 0, self_canvas.background_cache)
                    painter.restore()
                else:
                    pass

                # Get the truly moving strands list prepared by update_strand_position
                truly_moving_strands = getattr(self_canvas, 'truly_moving_strands', [])

                # --- ADD LOGGING HERE ---
                if not perf_logger.suppress_move_logging:
                    pass
                # --- END LOGGING ---

                # --- DRAW C-SHAPE EARLY --- 
                is_moving_strand_point = getattr(move_mode, 'is_moving_strand_point', False)
                affected_strand = getattr(move_mode, 'affected_strand', None)
                if is_moving_strand_point and affected_strand and affected_strand.is_selected:
                    if not perf_logger.suppress_move_logging:
                        pass
                # --- END DRAW C-SHAPE EARLY ---

                # Draw strands on top based on toggle state:
                # - When toggle ON: draw only truly moving strands  
                # - When toggle OFF: draw ALL strands with proper highlighting
                if move_mode.draw_only_affected_strand:
                    # Original behavior: draw only the truly moving strands on top
                    sorted_moving_strands = [s for s in original_strands_order if s in truly_moving_strands]
                else:
                    # New behavior: draw ALL strands on top, maintaining original order
                    # BUT also ensure any selected strands not in original order are included
                    sorted_moving_strands = list(original_strands_order)  # Start with original order
                    
                    # Add any selected strands that aren't in original order but are in truly_moving_strands
                    for strand in truly_moving_strands:
                        if strand not in sorted_moving_strands:
                            sorted_moving_strands.append(strand)
                    
                # Debug: Check if strands marked with is_selected are in sorted_moving_strands
                for strand in original_strands_order:
                    if getattr(strand, 'is_selected', False) and strand not in sorted_moving_strands:
                        pass
                    if getattr(strand, 'is_selected', False):
                        pass
                
                # Debug logging for strand filtering - use WARNING to ensure visibility
                if move_mode.draw_only_affected_strand:
                    pass
                else:
                    
                    # Check if any strands are missing (only relevant when toggle is ON)
                    if move_mode.draw_only_affected_strand:
                        for strand in truly_moving_strands:
                            if strand not in sorted_moving_strands:
                                if strand not in original_strands_order:
                                    pass

                # --- DRAW STRAND BODIES WITH PROPER HIGHLIGHTING --- 
                if not perf_logger.suppress_move_logging:
                    if move_mode.draw_only_affected_strand:
                        pass
                    else:
                        pass
                        
                for strand in sorted_moving_strands:
                    painter.save() # Ensure clean state for each strand
                    try:
                        if hasattr(strand, 'draw'):
                            # Always log at WARNING to ensure visibility
                            
                            # Debug output removed
                                
                            # Determine if this strand should be highlighted
                            should_highlight = False
                            if move_mode.draw_only_affected_strand:
                                # Toggle ON: only highlight if strand is selected and moving
                                should_highlight = strand.is_selected and strand in truly_moving_strands
                            else:
                                # Toggle OFF: highlight ALL strands that have is_selected=True
                                # This ensures connected strands are highlighted properly
                                should_highlight = getattr(strand, 'is_selected', False)
                                if not should_highlight:
                                    # Also check other highlighting conditions
                                    # Check if strand is in truly_moving_strands or is the selected strand
                                    should_highlight = (strand in truly_moving_strands or 
                                                      strand == self_canvas.selected_strand or 
                                                      strand == self_canvas.selected_attached_strand)
                                    # If still not highlighted and it's in truly_moving_strands, force highlight
                                    if not should_highlight and strand in truly_moving_strands:
                                        should_highlight = True
                                
                            # CRITICAL FIX: If strand is in truly_moving_strands, always highlight it
                            # This ensures that connected strands are always highlighted during movement
                            if strand in truly_moving_strands:
                                should_highlight = True
                                
                            if should_highlight:
                                pass
                            
                            # Draw the strand with or without highlighting
                            if should_highlight:
                                # Draw with highlighting using the canvas's highlight method
                                if hasattr(self_canvas, 'draw_highlighted_strand'):
                                    self_canvas.draw_highlighted_strand(painter, strand)
                                else:
                                    # Fallback: draw normally and add C-shape
                                    strand.draw(painter, skip_painter_setup=True)
                                    if strand.is_selected:
                                        move_mode_ref.draw_c_shape_for_strand(painter, strand)
                            else:
                                # Draw normally without highlighting
                                strand.draw(painter, skip_painter_setup=True)
                                if not perf_logger.suppress_move_logging:
                                    pass
                    finally:
                        painter.restore() # Restore state after drawing strand
                # --- END DRAWING STRAND BODIES WITH HIGHLIGHTING ---
                
                # --- ADD POST-BODY C-SHAPE DRAW ---
                is_moving_strand_point = getattr(move_mode, 'is_moving_strand_point', False)
                affected_strand = getattr(move_mode, 'affected_strand', None)
                if is_moving_strand_point and affected_strand and affected_strand.is_selected:
                    if not perf_logger.suppress_move_logging:
                        pass
                # --- END POST-BODY C-SHAPE DRAW ---
                
                # Special handling for MaskedStrand - only needed when toggle is ON
                if isinstance(active_strand, MaskedStrand) and move_mode.draw_only_affected_strand:
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
                        pass
                    move_mode.draw_selection_square(painter)
                
                # Draw any interaction elements
                if hasattr(self_canvas, 'draw_interaction_elements'):
                    self_canvas.draw_interaction_elements(painter)
                
                # Draw control points based on move state and settings
                if hasattr(self_canvas, 'show_control_points') and self_canvas.show_control_points:
                    if hasattr(self_canvas, 'draw_control_points'):
                        if not perf_logger.suppress_move_logging:
                            pass
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
                pass
        
        # Replace with our optimized paint event
        self.canvas.paintEvent = optimized_paint_event.__get__(self.canvas, type(self.canvas))

    def draw_selection_square(self, painter):
        """Draw the yellow selection square for the currently selected point."""
        if not self.is_moving or not self.selected_rectangle or not self.affected_strand:
            return
        
        # Check if highlights are disabled in settings
        if hasattr(self.canvas, 'show_move_highlights') and not self.canvas.show_move_highlights:
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
        # Smaller rectangle for bias controls
        bias_square_size = 50  # Same size as regular control points
        half_bias_size = bias_square_size / 2
        
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
        elif self.moving_side == 'control_point_center' and hasattr(self.affected_strand, 'control_point_center'):
            # Use control point size for the center control point
            yellow_rect = QRectF(
                self.affected_strand.control_point_center.x() - half_control_size,
                self.affected_strand.control_point_center.y() - half_control_size,
                square_control_size,
                square_control_size
            )
            painter.drawRect(yellow_rect)
        elif self.moving_side == 'bias_triangle' and hasattr(self.affected_strand, 'bias_control') and self.affected_strand.bias_control:
            tp, cp = self.affected_strand.bias_control.get_bias_control_positions(self.affected_strand)
            if tp:
                yellow_rect = QRectF(
                    tp.x() - half_bias_size,
                    tp.y() - half_bias_size,
                    bias_square_size,
                    bias_square_size
                )
                painter.drawRect(yellow_rect)
        elif self.moving_side == 'bias_circle' and hasattr(self.affected_strand, 'bias_control') and self.affected_strand.bias_control:
            tp, cp = self.affected_strand.bias_control.get_bias_control_positions(self.affected_strand)
            if cp:
                yellow_rect = QRectF(
                    cp.x() - half_bias_size,
                    cp.y() - half_bias_size,
                    bias_square_size,
                    bias_square_size
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
        
        if not self.draw_only_affected_strand:
            return
            
        
        # Make sure we have a setup_background_cache method
        if not hasattr(self, '_setup_background_cache'):
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

    def mousePressEvent(self, event):
        """
        Handle mouse press events.
        
        Args:
            event (QMouseEvent): The mouse event.
        """
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
            # Use the same logic as start_movement for consistency
            if self.canvas.selected_strand is not None:
                self.originally_selected_strand = self.canvas.selected_strand
            elif self.canvas.selected_attached_strand is not None:
                self.originally_selected_strand = self.canvas.selected_attached_strand
            # --- REMOVE ELSE BLOCK --- It is handled by current_selection logic and mouseReleaseEvent
            # else:
            #     # If there's no selection, make sure we clear our stored selection
            #     self.originally_selected_strand = None
            #     logging.info("MoveMode: No selected strand, clearing originally_selected_strand")
            # --- END REMOVE ---

            # Start movement operation in LayerStateManager EARLY to prevent premature cleanup
            if hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
                self.canvas.layer_state_manager.start_movement_operation()
            else:
                pass
            
            # Update LayerStateManager connections before building cache (ensure connections are current)
            if hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
                self.canvas.layer_state_manager.save_current_state()
            else:
                pass
            
            # Build connection cache for performance optimization (same as start_movement)
            self.build_connection_cache()
            
            # Suppress verbose logging during movement for better performance (same as start_movement)
            perf_logger.suppress_during_move(True)
            
            # Store a reference to the undo_redo_manager if it exists (same as start_movement)
            if hasattr(self.canvas, 'undo_redo_manager') and not hasattr(self, 'undo_redo_manager'):
                self.undo_redo_manager = self.canvas.undo_redo_manager
            
            # Start movement operation in LayerStateManager to prevent connection confusion (same as start_movement)
            if hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
                self.canvas.layer_state_manager.start_movement_operation()

            self.in_move_mode = True
            # Reset time limiter at the start of move mode
            self.last_update_time = 0
            
            # Continue with the rest of the mousePressEvent logic

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
                if self.try_move_control_points(strand, pos, event):
                    control_point_moved = True
                    
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
                    

        # If we're not moving a control point, proceed with normal strand movement
        # Store current selection state before handling movement
        current_selection_states = {}
        for strand in self.canvas.strands:
            current_selection_states[strand] = strand.is_selected
            if isinstance(strand, AttachedStrand):
                for attached in strand.attached_strands:
                    current_selection_states[attached] = attached.is_selected
        
        # Handle strand selection and movement
        self.handle_strand_movement(pos, event)
        
        # If no movement was initiated, restore selection states
        # BUT only if we're not in the middle of setting up movement highlighting
        if not self.is_moving and not self.in_move_mode:
            for strand, was_selected in current_selection_states.items():
                strand.is_selected = was_selected
        
        
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
            # --- End capture ---

            self.last_update_pos = pos
            self.accumulated_delta = QPointF(0, 0)
            self.last_snapped_pos = self.canvas.snap_to_grid(pos)
            self.target_pos = self.last_snapped_pos
            
            # Special handling for MaskedStrand
            if isinstance(self.affected_strand, MaskedStrand):
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
                
            # Always setup efficient paint handler during movement for consistent behavior
            if not hasattr(self.canvas, 'original_paintEvent'):
                self._setup_optimized_paint_handler()
                
            # Ensure background cache is properly invalidated on first movement
            if hasattr(self.canvas, 'background_cache_valid'):
                self.canvas.background_cache_valid = False

        else: # No move initiated (blank space click)
            # Keep the selection from the start of the press
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
        
        if not self.is_moving:
            # If not in moving state, stop the timer
            self.hold_timer.stop()
            return
            
        
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
        if self.is_moving:
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

        affected_name = getattr(self.affected_strand, 'layer_name', None) if self.affected_strand else None
        prev_cp = self.is_moving_control_point
        prev_sp = self.is_moving_strand_point
        _write_selection_debug(
            self.canvas,
            (
                f"reset_movement_state begin affected={affected_name or 'None'} "
                f"is_moving={self.is_moving} "
                f"is_moving_control_point={prev_cp} "
                f"is_moving_strand_point={prev_sp}"
            )
        )

        # --- 1. Stop Timers ---
        if hasattr(self, 'hold_timer'):
            self.hold_timer.stop()
        if hasattr(self, 'redraw_timer'):
            self.redraw_timer.stop()
 
        # --- 2. Reset MoveMode State COMPLETELY ---
        self.is_moving = False
        self.moving_point = None
        
        # Clear the _is_being_moved flag from the affected strand and any connected strands
        if self.affected_strand:
            self.affected_strand._is_being_moved = False
            # Also clear the flag on any connected strands
            if hasattr(self.affected_strand, 'knot_connections') and self.affected_strand.knot_connections:
                for end_type, connection_info in self.affected_strand.knot_connections.items():
                    connected_strand = connection_info['connected_strand']
                    connected_strand._is_being_moved = False
        
        self.affected_strand = None
        self.moving_side = None
        self.selected_rectangle = None
        self.last_update_pos = None
        self.accumulated_delta = QPointF(0, 0)
        self.last_snapped_pos = None
        self.target_pos = None
        
        # Invalidate connection cache when movement ends
        self.invalidate_connection_cache()
        
        # End movement operation in LayerStateManager to allow connection recalculation
        if hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
            self.canvas.layer_state_manager.end_movement_operation()
        
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
        _write_selection_debug(
            self.canvas,
            "reset_movement_state end flags cleared"
        )

        # --- 3. Clean up Canvas Temp Attributes & Restore Paint Event ---
        if hasattr(self.canvas, 'original_paintEvent'):
            self.canvas.paintEvent = self.canvas.original_paintEvent
            delattr(self.canvas, 'original_paintEvent')
        attrs_to_clean = ['active_strand_for_drawing', 'active_strand_update_rect',
                          'last_strand_rect', 'background_cache', 'background_cache_valid',
                          'movement_first_draw', 'affected_strands_for_drawing',
                          'truly_moving_strands', '_frames_since_click', '_logged_force_highlight',
                          '_logged_parent_force_highlight', '_logged_strands_list']
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
        from PyQt5.QtCore import QPointF, QTimer

        # Handle bias control release if active, but allow common selection restore below
        if hasattr(self, 'is_moving_bias_control') and self.is_moving_bias_control:
            if hasattr(self, 'bias_control_strand') and self.bias_control_strand:
                # Finalize drag on the bias control itself
                self.bias_control_strand.bias_control.handle_mouse_release(event)
            # Clear bias flags and continue to selection restoration logic
            self.is_moving_bias_control = False
            self.bias_control_strand = None
            # Do not return; fall through to common restore
        
        # Store relevant state before resetting
        was_moving = self.is_moving
        final_pos = event.pos()
        # Capture selection state *before* reset
        selection_at_release_start = self.canvas.selected_strand or self.canvas.selected_attached_strand
        original_selection_ref = self.originally_selected_strand # Keep reference used during move
        
        self.reset_movement_state()
        
        # --- 4. Restore Selection State --- 
        # Determine the final selection based on whether it was a click or a move
        final_selected_strand = None
        if was_moving:
            # Restore the selection from *before* the move started
            final_selected_strand = original_selection_ref
        else: # It was a click (either on blank space or an element without dragging)
            # Restore the selection that was active *just before* this release event started
            final_selected_strand = selection_at_release_start

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

        # Clear the originally_selected_strand reference ONLY AFTER the release event is fully processed
        self.originally_selected_strand = None

        # --- 5. Removed duplicate control point save ---
        # Control point saves are now handled by undo_redo_manager's enhanced_mouse_release
        # to ensure consistent behavior with start/end point movements

        # --- 6. Force Updates ---
        self.canvas.update() # Force immediate redraw with restored state
        QTimer.singleShot(0, self.canvas.update) # Schedule another for next cycle

    def update_strand_geometry_only(self, new_pos):
        """ Update strand geometry without triggering drawing optimizations or selection changes."""
        if not self.affected_strand: return

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

    def handle_strand_movement(self, pos, event=None):
        """
        Handle the movement of strands.

        Args:
            pos (QPointF): The position of the mouse click.
            event (QMouseEvent): The mouse event (optional, for bias controls).
        """
        self.is_moving = False  # Reset this flag at the start
        

        # First pass: Check all control points for all strands (excluding masked strands)
        for strand in self.canvas.strands:
            if not getattr(strand, 'deleted', False) and not isinstance(strand, MaskedStrand):
                if self.try_move_control_points(strand, pos, event):
                    return
                if self.try_move_attached_strands_control_points(strand.attached_strands, pos):
                    return

        # Second pass: Check start and end points for all strands (excluding masked strands)
        # First, check if we're clicking on a connection point
        connection_point_strands = []
        
        # Check all strands to see if the click position matches any connection points
        for i, strand in enumerate(self.canvas.strands):
            if not getattr(strand, 'deleted', False) and not isinstance(strand, MaskedStrand) and (not self.lock_mode_active or i not in self.locked_layers):
                start_area = self.get_start_area(strand)
                end_area = self.get_end_area(strand)
                
                if start_area.contains(pos) and self.can_move_side(strand, 0, i):
                    # Always add this strand if we clicked on it
                    if not any(s[0] == strand for s in connection_point_strands):
                        connection_point_strands.append((strand, 0, start_area))
                    # Check if this is a connection point with other strands
                    connected_strands = self.get_connected_strands(strand.layer_name, 0)
                    if connected_strands:
                        # Add all connected strands at this point
                        for conn_strand, conn_side in connected_strands:
                            if not any(s[0] == conn_strand for s in connection_point_strands):
                                conn_area = self.get_end_area(conn_strand) if conn_side == 1 else self.get_start_area(conn_strand)
                                connection_point_strands.append((conn_strand, conn_side, conn_area))
                                
                if end_area.contains(pos) and self.can_move_side(strand, 1, i):
                    # Always add this strand if we clicked on it
                    if not any(s[0] == strand for s in connection_point_strands):
                        connection_point_strands.append((strand, 1, end_area))
                    # Check if this is a connection point with other strands
                    connected_strands = self.get_connected_strands(strand.layer_name, 1)
                    if connected_strands:
                        # Add all connected strands at this point
                        for conn_strand, conn_side in connected_strands:
                            if not any(s[0] == conn_strand for s in connection_point_strands):
                                conn_area = self.get_end_area(conn_strand) if conn_side == 1 else self.get_start_area(conn_strand)
                                connection_point_strands.append((conn_strand, conn_side, conn_area))
        
        # If we found strands at a connection point, handle them specially
        if connection_point_strands:
            for s, side, area in connection_point_strands:
                pass
            
            # If we have multiple strands at a connection point, prefer the main strand over attached
            # This ensures we start movement with the parent strand when possible
            main_strand_entry = None
            for entry in connection_point_strands:
                strand, side, area = entry
                if not isinstance(strand, AttachedStrand):
                    main_strand_entry = entry
                    break
            
            # Use main strand if found, otherwise use first strand
            if main_strand_entry:
                first_strand, first_side, first_area = main_strand_entry
            else:
                first_strand, first_side, first_area = connection_point_strands[0]
                
            self.start_movement(first_strand, first_side, first_area, pos)
            return
        
        # Otherwise, iterate in reverse to check topmost strands first (excluding masked strands)
        for i, strand in reversed(list(enumerate(self.canvas.strands))):
            if not getattr(strand, 'deleted', False) and not isinstance(strand, MaskedStrand) and (not self.lock_mode_active or i not in self.locked_layers):
                # Debug: Check if this strand has knot connections
                if hasattr(strand, 'knot_connections') and strand.knot_connections:
                    pass
                if self.try_move_strand(strand, pos, i):
                    return
                else:
                    pass
        

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

    def try_move_control_points(self, strand, pos, event=None):
        """
        Try to move a strand's control points if the position is within their selection areas.

        Args:
            strand (Strand): The strand to try moving.
            pos (QPointF): The position to check.
            event (QMouseEvent): The mouse event (optional, for bias controls).

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

        # Check if control points exist
        if not hasattr(strand, 'control_point1') or not hasattr(strand, 'control_point2'):
            return False
        
        # Check bias controls first if they're enabled and event is provided
        if (event and hasattr(strand, 'bias_control') and strand.bias_control and 
            hasattr(self.canvas, 'enable_curvature_bias_control') and 
            self.canvas.enable_curvature_bias_control):
            
            # Let the bias control handle the mouse press and see if it accepts it
            if strand.bias_control.handle_mouse_press(event, strand):
                # The bias control is now handling the drag
                # Determine which bias control is being dragged
                if strand.bias_control.dragging_triangle:
                    side_name = 'bias_triangle'
                elif strand.bias_control.dragging_circle:
                    side_name = 'bias_circle'
                else:
                    side_name = 'bias_control'
                # Build a selection rectangle for the specific bias control so yellow highlight draws
                bias_square_size = 50
                half_bias = bias_square_size / 2
                rect = None
                try:
                    tp, cp = strand.bias_control.get_bias_control_positions(strand)
                    if side_name == 'bias_triangle' and tp:
                        rect = QRectF(tp.x() - half_bias, tp.y() - half_bias, bias_square_size, bias_square_size)
                    elif side_name == 'bias_circle' and cp:
                        rect = QRectF(cp.x() - half_bias, cp.y() - half_bias, bias_square_size, bias_square_size)
                except Exception:
                    rect = None

                self.start_movement(strand, side_name, rect, event.pos())
                self.is_moving_control_point = True
                self.is_moving_bias_control = True
                self.bias_control_strand = strand
                if hasattr(self.canvas, 'truly_moving_strands'):
                    self.canvas.truly_moving_strands = [strand]
                return True
        
        # Check if third control point is enabled
        third_cp_enabled = hasattr(self.canvas, 'enable_third_control_point') and self.canvas.enable_third_control_point
        center_is_locked = getattr(strand, 'control_point_center_locked', False)
        
        # Control point movement logic:
        # 1. When third CP is disabled: Always allow moving end control points (classic mode)
        # 2. When third CP is enabled:
        #    - Initially (center_is_locked = False): Only end control points are movable, center is NOT selectable
        #    - After moving an end control point: Center becomes locked and movable
        #    - Both end and center control points remain movable after that
        
        # ALWAYS check end control points first - they should be the primary way to control the curve
        # Allow override with Shift to force-select a small control point
        shift_held = False
        try:
            from PyQt5.QtWidgets import QApplication
            shift_held = QApplication.keyboardModifiers() & Qt.ShiftModifier
        except Exception:
            shift_held = False
            
        cp1_at_start = (abs(strand.control_point1.x() - strand.start.x()) < 1.0 and
                        abs(strand.control_point1.y() - strand.start.y()) < 1.0)
        cp2_at_start = (abs(strand.control_point2.x() - strand.start.x()) < 1.0 and
                        abs(strand.control_point2.y() - strand.start.y()) < 1.0)

        # Check end control points - these are always the priority
        # Always allow moving control points, regardless of their position
        if True:  # Always check control points
            control_point1_rect = self.get_control_point_rectangle(strand, 1)
            control_point2_rect = self.get_control_point_rectangle(strand, 2)

            if control_point1_rect.contains(pos):
                self.start_movement(strand, 'control_point1', control_point1_rect, pos)
                self.is_moving_control_point = True
                # Mark that the triangle has been moved
                strand.triangle_has_moved = True
                # Do NOT lock the center when moving end control points
                # Let it update automatically to stay at the midpoint
                if hasattr(self.canvas, 'truly_moving_strands'):
                    self.canvas.truly_moving_strands = [strand]
                else:
                    self.canvas.truly_moving_strands = [strand]
                self.highlighted_strand = None
                return True
            elif control_point2_rect.contains(pos):
                self.start_movement(strand, 'control_point2', control_point2_rect, pos)
                self.is_moving_control_point = True
                # Do NOT lock the center when moving end control points
                # Let it update automatically to stay at the midpoint
                if hasattr(self.canvas, 'truly_moving_strands'):
                    self.canvas.truly_moving_strands = [strand]
                else:
                    self.canvas.truly_moving_strands = [strand]
                self.highlighted_strand = None
                return True
        
        # Check center control point - it can be selected whether locked or not
        # When not locked: selecting it locks it for manual control
        # When locked: allows re-moving it
        if third_cp_enabled:
            control_point_center_rect = self.get_control_point_rectangle(strand, 3)
            
            if control_point_center_rect is not None and control_point_center_rect.contains(pos):
                self.start_movement(strand, 'control_point_center', control_point_center_rect, pos)
                # Mark that we're moving a control point
                self.is_moving_control_point = True
                # Lock the center when it's manually moved
                if not center_is_locked:
                    strand.control_point_center_locked = True
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
        
        # Check if strand has closed connections
        if hasattr(strand, 'closed_connections'):
            pass

        if start_area.contains(pos) and self.can_move_side(strand, 0, strand_index):
            self.start_movement(strand, 0, start_area, pos)
            # start_movement already handles selection of all connected strands
            return True
        elif end_area.contains(pos) and self.can_move_side(strand, 1, strand_index):
            self.start_movement(strand, 1, end_area, pos)
            # start_movement already handles selection of all connected strands
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
        
        # Ensure canvas is fully updated before starting movement
        # This is important when movement starts immediately after creating an attached strand
        self.canvas.update()
        
        # Save the currently selected strand before starting a new movement operation
        if self.canvas.selected_strand is not None:
            self.originally_selected_strand = self.canvas.selected_strand
        elif self.canvas.selected_attached_strand is not None:
            self.originally_selected_strand = self.canvas.selected_attached_strand

        # Set the _is_being_moved flag to prevent knot connection synchronization during movement
        strand._is_being_moved = True
        
        # Also set the flag on any connected strands to prevent mutual synchronization
        if hasattr(strand, 'knot_connections') and strand.knot_connections:
            for end_type, connection_info in strand.knot_connections.items():
                connected_strand = connection_info['connected_strand']
                connected_strand._is_being_moved = True

        # Store a reference to the undo_redo_manager if it exists
        if hasattr(self.canvas, 'undo_redo_manager') and not hasattr(self, 'undo_redo_manager'):
            self.undo_redo_manager = self.canvas.undo_redo_manager

        # Build connection cache for performance optimization
        self.build_connection_cache()
        
        # DON'T suppress logging yet - move this after selection setup
        # perf_logger.suppress_during_move(True)  # MOVED TO AFTER SELECTION SETUP

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
        elif side == 'bias_control':
            # For bias controls, use the click position directly since the bias control handles its own movement
            strand_pos = QPointF(actual_click_pos) if actual_click_pos else QPointF(0, 0)
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
            zoom_info = f", zoom={self.canvas.zoom_factor:.2f}" if hasattr(self.canvas, 'zoom_factor') else ""
            
            # Additional logging for zoom-out debugging
            if hasattr(self.canvas, 'zoom_factor') and self.canvas.zoom_factor < 0.8:
                pass
        else:
            # Fallback: assume click was directly on the strand
            self.initial_mouse_pos = QPointF(strand_pos)
            self.mouse_offset = QPointF(0, 0)
            # Do not move cursor in fallback case to prevent jumps
            
        # Store the moving point as the strand position
        self.moving_point = strand_pos

        self.affected_strand = strand
        self.selected_rectangle = area
        self.is_moving = True
        # Set the flag if we're moving a control point (include bias controls)
        self.is_moving_control_point = side in ['control_point1', 'control_point2', 'control_point_center', 'bias_control', 'bias_triangle', 'bias_circle']
        # Set the flag if we're moving a strand endpoint
        self.is_moving_strand_point = side in [0, 1]
        strand_name = getattr(strand, 'layer_name', None) or getattr(strand, 'set_number', None) or getattr(strand, 'layer', None)
        _write_selection_debug(
            self.canvas,
            (
                f"start_movement strand={strand_name or 'unknown'} id={hex(id(strand))} side={side} "
                f"is_moving_control_point={self.is_moving_control_point} "
                f"is_moving_strand_point={self.is_moving_strand_point} "
                f"draw_only_affected={getattr(self, 'draw_only_affected_strand', False)}"
            )
        )
        
        # AUTO-ADJUST CONTROL POINTS: Only when initially moving control_point1,
        # check if control points are at their initial position (both at start, forming a triangle).
        # If so, automatically move the circle control point (control_point2) near the ending point.
        # Apply this only for the main strand (attached children are handled recursively inside).
        
        # Helper function to auto-adjust control points for a strand
        def auto_adjust_control_points(s):
            if hasattr(s, 'control_point1') and hasattr(s, 'control_point2'):
                cp1_at_start = (abs(s.control_point1.x() - s.start.x()) < 1.0 and
                               abs(s.control_point1.y() - s.start.y()) < 1.0)
                cp2_at_start = (abs(s.control_point2.x() - s.start.x()) < 1.0 and
                               abs(s.control_point2.y() - s.start.y()) < 1.0)
                
                # If both control points are at start (initial triangle state), auto-adjust them
                if cp1_at_start and cp2_at_start:
                    # Position control_point2 at 0.1 units before the end point along the tangent direction
                    # Calculate the tangent direction from start to end
                    dx = s.end.x() - s.start.x()
                    dy = s.end.y() - s.start.y()
                    length = math.hypot(dx, dy)

                    if length > 1e-6:
                        # Normalize the direction vector
                        dir_x = dx / length
                        dir_y = dy / length
                        # Move 0.1 units backward from end along the tangent
                        s.control_point2 = QPointF(s.end.x() - dir_x * 0.01, s.end.y() - dir_y * 0.1)
                    else:
                        # Fallback: if start and end are too close, just use end point
                        s.control_point2 = QPointF(s.end.x(), s.end.y())
                    
                    # If third control point (rectangle) is enabled and active, move it to center
                    if (hasattr(self.canvas, 'enable_third_control_point') and 
                        self.canvas.enable_third_control_point and
                        hasattr(s, 'control_point_center')):
                        # Calculate midpoint between the two control points
                        midpoint = QPointF(
                            (s.control_point1.x() + s.control_point2.x()) / 2,
                            (s.control_point1.y() + s.control_point2.y()) / 2
                        )
                        s.control_point_center = midpoint
                        # Mark that the center has been manually positioned (locked)
                        s.control_point_center_locked = True
                    
                    # Update the strand's shape to reflect the new control point positions
                    s.update_shape()
                    
                    # IMPORTANT: Update side lines and ensure they get properly highlighted
                    if hasattr(s, 'update_side_line'):
                        s.update_side_line()
                    
                    # Also update any attached strands' side lines recursively
                if not self.is_moving_control_point:
                    if hasattr(s, 'attached_strands'):
                        for attached in s.attached_strands:
                            if attached and not getattr(attached, 'deleted', False):
                                # Auto-adjust the attached strand as well
                                auto_adjust_control_points(attached)
                    
                    return True  # Indicates adjustment was made
            return False  # No adjustment needed
        
        # Apply auto-adjustment only when initially moving control_point1
        if side == 'control_point1':
            main_adjustment_made = auto_adjust_control_points(strand)
        else:
            main_adjustment_made = False
        
        # Force canvas update if any adjustments were made
        if main_adjustment_made:
            self.canvas.update()
        
        # Set initial positions to the strand position
        self.last_snapped_pos = strand_pos
        self.target_pos = strand_pos
        
        # Keep the mouse offset to maintain accurate positioning without cursor jumps
        # The offset represents the difference between where user clicked and strand position
        # This prevents visual jumps while maintaining precise control
        
        # Do not move cursor or reset offset - this prevents the visual jump
        # The offset will be applied during mouse movement to maintain correct positioning

        # Find any other strands connected to this point using layer_state_manager
        moving_point = strand.start if side == 0 else strand.end
        connected_strand = self.find_connected_strand(strand, side, moving_point)
        
        # --- NEW CODE: Use LayerStateManager to gather all moving strands ---
        # Initialize truly_moving_strands using the new connection-based logic
        if side in [0, 1]:  # Only for endpoint movement, not control points
            truly_moving_strands = self.gather_moving_strands(strand, side)
        else:
            # For control point movement, only move the affected strand
            truly_moving_strands = [strand]
        
        # Log the strands that will move together
        strand_names = [s.layer_name for s in truly_moving_strands]
        
        # Debug: Check if connection cache is built
        if hasattr(self, 'connection_cache'):
            pass
        else:
            pass
            
        # Debug: Check LayerStateManager
        if hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
            connections = self.canvas.layer_state_manager.getConnections()
        else:
            pass
        
        # Special handling for MaskedStrand components
        if isinstance(strand, MaskedStrand) and hasattr(strand, 'first_selected_strand') and hasattr(strand, 'second_selected_strand'):
            # Add the component strands
            if strand.first_selected_strand and strand.first_selected_strand not in truly_moving_strands:
                truly_moving_strands.append(strand.first_selected_strand)
            if strand.second_selected_strand and strand.second_selected_strand not in truly_moving_strands:
                truly_moving_strands.append(strand.second_selected_strand)
        
        # Store the list on the canvas for use in optimized_paint_event
        self.canvas.truly_moving_strands = truly_moving_strands
        # Explicitly set is_selected for all moving strands to ensure highlighting
        for s in truly_moving_strands:
            s.is_selected = True
        
        # Ensure affected_strands_for_drawing also contains all truly moving strands initially
        self.canvas.affected_strands_for_drawing = list(truly_moving_strands)
        
        # CRITICAL FIX: Set up optimized paint handler BEFORE calling canvas.update()
        # This ensures highlighting works correctly on the first move
        if not hasattr(self.canvas, 'original_paintEvent'):
            self._setup_optimized_paint_handler()
        
        # Force an immediate update to ensure highlighting is applied right away
        # This is important when draw_only_affected_strand is False
        self.canvas.update()
        
        # Force a paint event update to ensure the optimized paint handler gets the correct strands
        if hasattr(self.canvas, 'movement_first_draw'):
            self.canvas.movement_first_draw = False  # Reset to ensure first draw happens with correct strands

        # Control point movement specific handling
        if self.is_moving_control_point:
            # Ensure control point moves are limited strictly to the affected strand
            self.canvas.truly_moving_strands = [self.affected_strand] if self.affected_strand else [strand]
            self.canvas.affected_strands_for_drawing = [self.affected_strand] if self.affected_strand else [strand]
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
                # CRITICAL FIX: Never clear is_selected for strands that are in truly_moving_strands
                if s in truly_moving_strands:
                    continue
                s.is_selected = False
                # Also clear selections in attached strands
                if hasattr(s, 'attached_strands'):
                    for attached in s.attached_strands:
                        # CRITICAL FIX: Never clear is_selected for attached strands that are in truly_moving_strands
                        if attached in truly_moving_strands:
                            continue
                        attached.is_selected = False
                        
            # Temporarily clear selected attached strand
            self.canvas.selected_attached_strand = None
            self.temp_selected_strand = None
            # Clear highlighted strand to ensure no highlighting during control point movement
            self.highlighted_strand = None
            # Ensure the affected strand itself is not visibly selected during control point movement
            if self.affected_strand:
                # CRITICAL FIX: Never clear is_selected for the affected strand if it's in truly_moving_strands
                if self.affected_strand not in truly_moving_strands:
                    self.affected_strand.is_selected = False
        else:
            # For normal strand movement, ensure all truly moving strands are selected
            if self.affected_strand:
                # Set is_selected = True for ALL truly moving strands to ensure proper highlighting
                for moving_strand in truly_moving_strands:
                    moving_strand.is_selected = True
                
                # Verify the selection states were set correctly
                for moving_strand in truly_moving_strands:
                    pass
                
                # CRITICAL: Move the canvas selection AFTER setting is_selected flags
                # This prevents any canvas selection logic from interfering with our flags
                if isinstance(self.affected_strand, MaskedStrand):
                    self.canvas.selected_strand = self.affected_strand
                    self.canvas.selected_attached_strand = None
                elif isinstance(self.affected_strand, AttachedStrand):
                    self.canvas.selected_attached_strand = self.affected_strand
                    self.canvas.selected_strand = None
                else:
                    # Regular strand - set as selected_strand (not attached)
                    self.canvas.selected_strand = self.affected_strand
                    self.canvas.selected_attached_strand = None
                
                # Verify flags are still correct after canvas selection changes
                for moving_strand in truly_moving_strands:
                    pass
                
                # CRITICAL: Set up optimized paint handler immediately after selection to ensure highlighting works
                self.canvas.active_strand_for_drawing = self.affected_strand
                self.canvas.truly_moving_strands = truly_moving_strands
                has_original = hasattr(self.canvas, 'original_paintEvent')
                if not has_original:
                    self._setup_optimized_paint_handler()
                else:
                    pass
                
                # CRITICAL: Invalidate background cache to ensure proper redraw with highlighting
                if hasattr(self.canvas, 'background_cache_valid'):
                    self.canvas.background_cache_valid = False
                
                # CRITICAL: Force canvas update to trigger optimized paint handler with selected strands
                # This ensures the highlighting is visible immediately when clicking on strands
                self.canvas.update()
                
                # NOW suppress verbose logging after selection is set up
                perf_logger.suppress_during_move(True)
                
                # Also handle the connected strand for backward compatibility
                if connected_strand:
                    if isinstance(connected_strand, AttachedStrand):
                        self.temp_selected_strand = connected_strand
        # --- REPLACE print with logging.info ---
        # We need to check if original_start and original_end are defined before logging
        # These were defined in the context of the previous move_masked_strand or update_strand_position
        # They are NOT directly available here. We should log the current start/end instead.
        # --- END REPLACE ---
        
        # Start movement operation in LayerStateManager to prevent connection confusion
        if hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
            self.canvas.layer_state_manager.start_movement_operation()
        
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
        # Control point moves don't need this restriction
        
        # Keep track of what strands are affected for optimization
        affected_strands = set([self.affected_strand])
        
        # Identify truly moving strands (ones being dragged by user, not just connected)
        # --- CORRECTED: Preserve truly_moving_strands from start_movement --- 
        # truly_moving_strands = [self.affected_strand] # OLD LOGIC
        # Retrieve the list set by start_movement and ensure it's treated as read-only here
        truly_moving_strands_read_only = getattr(self.canvas, 'truly_moving_strands', [self.affected_strand])
        # --- END CORRECTION ---
        
        # --- Find and include connected strands using LayerStateManager ---
        connected_strands_at_moving_point = set()
        is_moving_endpoint = self.moving_side == 0 or self.moving_side == 1

        if is_moving_endpoint:
            # Get all strands connected to the moving point from LayerStateManager
            connected_info = self.get_connected_strands(self.affected_strand.layer_name, self.moving_side)
            
            for connected_strand, connected_end in connected_info:
                connected_strands_at_moving_point.add(connected_strand)
                affected_strands.add(connected_strand)
        # --- End finding and including connected strands ---

        # --- Include attached strands based on LayerStateManager connections ---
        # The connected_strands_at_moving_point already includes all properly connected strands
        # No need for additional proximity checks
        # --- End inclusion of attached strands ---

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
            # Force canvas update to redraw shadows with new control point position
            self.canvas.update()
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
            # Force canvas update to redraw shadows with new control point position
            self.canvas.update()
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
            # Force canvas update to redraw shadows with new control point position
            self.canvas.update()
            # Update the selection rectangle to the new position
            self.selected_rectangle = self.get_control_point_rectangle(self.affected_strand, 3)
            # Keep the strand deselected to prevent highlighting during control point movement
            self.affected_strand.is_selected = False
            self.canvas.selected_attached_strand = None
            self.highlighted_strand = None
            
        elif self.moving_side == 'bias_triangle' or self.moving_side == 'bias_circle':
            # Handle bias control movement
            if hasattr(self.affected_strand, 'bias_control') and self.affected_strand.bias_control:
                # Calculate horizontal movement from original position
                if hasattr(self, 'initial_pos'):
                    dx = new_pos.x() - self.initial_pos.x()
                    # Convert to bias change (scale for sensitivity)
                    bias_change = dx / 200.0
                    
                    if self.moving_side == 'bias_triangle':
                        # Update triangle bias
                        if hasattr(self, 'bias_start_value'):
                            new_bias = self.bias_start_value + bias_change
                        else:
                            new_bias = self.affected_strand.bias_control.triangle_bias + bias_change
                        self.affected_strand.bias_control.triangle_bias = max(0.0, min(1.0, new_bias))
                    else:  # bias_circle
                        # Update circle bias
                        if hasattr(self, 'bias_start_value'):
                            new_bias = self.bias_start_value + bias_change
                        else:
                            new_bias = self.affected_strand.bias_control.circle_bias + bias_change
                        self.affected_strand.bias_control.circle_bias = max(0.0, min(1.0, new_bias))
                    
                    # Update the strand shape to reflect the bias change
                    self.affected_strand.update_shape()
                    # Keep the yellow selection rectangle in sync with the moving bias control
                    try:
                        bias_square_size = 50
                        half_bias = bias_square_size / 2
                        tp, cp = self.affected_strand.bias_control.get_bias_control_positions(self.affected_strand)
                        if self.moving_side == 'bias_triangle' and tp:
                            self.selected_rectangle = QRectF(tp.x() - half_bias, tp.y() - half_bias, bias_square_size, bias_square_size)
                        elif self.moving_side == 'bias_circle' and cp:
                            self.selected_rectangle = QRectF(cp.x() - half_bias, cp.y() - half_bias, bias_square_size, bias_square_size)
                    except Exception:
                        pass

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
                # Move the primary strand directly - let the new logic handle connected strands
                if self.moving_side == 0:
                    self.affected_strand.start = new_pos
                else:  # self.moving_side == 1
                    self.affected_strand.end = new_pos

                # Update the strand shape to reflect the change
                self.affected_strand.update_shape()
                self.affected_strand.update_side_line()

                # Handle parent strand if this is an AttachedStrand
                if isinstance(self.affected_strand, AttachedStrand) and self.affected_strand.parent:
                    parent_strand = self.affected_strand.parent
                    affected_strands.add(parent_strand)

                # --- FIXED: Move all other truly moving strands to the same position ---
                # All truly moving strands should move their connected points to the same absolute position
                for moving_strand in truly_moving_strands_read_only:
                    if moving_strand != self.affected_strand:  # Skip the primary strand that was already moved
                        # Find which point of this strand is connected to the SPECIFIC moving point of the primary strand
                        connected_info = self.get_connected_strands(moving_strand.layer_name, 0)  # Check start
                        move_start = any(conn_strand == self.affected_strand and conn_end == self.moving_side 
                                       for conn_strand, conn_end in connected_info)
                        
                        connected_info = self.get_connected_strands(moving_strand.layer_name, 1)  # Check end  
                        move_end = any(conn_strand == self.affected_strand and conn_end == self.moving_side 
                                     for conn_strand, conn_end in connected_info)
                        
                        # Move the connected point to the same position as the primary strand's moved point
                        if move_start:
                            moving_strand.start = new_pos
                        if move_end:
                            moving_strand.end = new_pos
                        
                        moving_strand.update_shape()
                        moving_strand.update_side_line()
                # --- End fixed movement logic ---

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
        # --- CORRECTED: Re-assert the read-only list from the start of the function --- 
        self.canvas.truly_moving_strands = truly_moving_strands_read_only
        # --- END CORRECTION ---
        # logging.info(f"MoveMode (Update Pos): Final truly_moving_strands: {[s.layer_name for s in self.canvas.truly_moving_strands]}, affected_strands_for_drawing: {[s.layer_name for s in self.canvas.affected_strands_for_drawing]}")
        
        # --- NEW: Log positions of all affected strands AFTER updates in this step ---
        #if hasattr(self.canvas, 'affected_strands_for_drawing'):
            # logging.info("--- Positions after update_strand_position step ---")
            # for s in self.canvas.affected_strands_for_drawing:
            #     logging.info(f"  Strand {s.layer_name}: Start={s.start}, End={s.end}")
            # logging.info("--------------------------------------------------")
        # --- END NEW LOGGING ---

        # All connected strands are already handled by LayerStateManager connections
        # No need for additional proximity-based checks

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

    def get_connected_strands(self, strand_name, connection_point):
        """
        Get all strands connected to a specific point of a strand using LayerStateManager.
        
        Args:
            strand_name (str): The name of the strand (e.g., '1_1')
            connection_point (int or str): 0 for start point, 1 for end point, or control point name
            
        Returns:
            list: List of tuples (strand_object, connection_end) for all connected strands
        """
        
        if not hasattr(self.canvas, 'layer_state_manager') or not self.canvas.layer_state_manager:
            return []
            
        # Control points don't have connections in LayerStateManager
        if isinstance(connection_point, str) or connection_point not in [0, 1]:
            return []
            
        connections = self.canvas.layer_state_manager.getConnections()
        strand_connections = connections.get(strand_name, ['null', 'null'])
        
        # Get the connection at the specified point
        connection_str = strand_connections[connection_point]
        
        if connection_str == 'null':
            return []
            
        connected_strands = []
        
        # Parse connection string format: 'strand_name(end_point)'
        if '(' in connection_str and ')' in connection_str:
            connected_name = connection_str[:connection_str.index('(')]
            connected_end = int(connection_str[connection_str.index('(') + 1:connection_str.index(')')])
            
            # Find the strand object by name
            for strand in self.canvas.strands:
                if strand.layer_name == connected_name:
                    connected_strands.append((strand, connected_end))
                    break
            else:
                pass
                    
        return connected_strands

    def gather_moving_strands(self, initial_strand, moving_point):
        """
        Recursively gather all strands that should move together based on LayerStateManager connections.
        
        Args:
            initial_strand: The strand being directly moved
            moving_point: 0 for start point, 1 for end point, or control point name
            
        Returns:
            list: List of all strands that should move together
        """
        
        # Debug: Check LayerStateManager connections
        if hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
            connections = self.canvas.layer_state_manager.getConnections()
        else:
            pass
        
        if not hasattr(self.canvas, 'layer_state_manager') or not self.canvas.layer_state_manager:
            # Fallback to just the initial strand
            return [initial_strand]
            
        # Control points only move their own strand
        if isinstance(moving_point, str) or moving_point not in [0, 1]:
            return [initial_strand]
            
        moving_strands = []
        visited = set()
        to_process = [(initial_strand, moving_point)]
        
        while to_process:
            current_strand, current_point = to_process.pop(0)
            
            # Skip if already processed
            strand_key = (current_strand.layer_name, current_point)
            if strand_key in visited:
                continue
                
            visited.add(strand_key)
            moving_strands.append(current_strand)
            
            # Get all strands connected to this point
            connected = self.get_connected_strands(current_strand.layer_name, current_point)
            
            # Debug: Log the actual connection info
            if hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
                connections = self.canvas.layer_state_manager.getConnections()
                current_connections = connections.get(current_strand.layer_name, ['null', 'null'])
            
            for conn_strand, conn_point in connected:
                # The connected strand moves at the point where it connects
                # For example, if 1_1's end connects to 1_2's start, 
                # when moving 1_1's end, 1_2 moves at its start
                new_key = (conn_strand.layer_name, conn_point)
                if new_key not in visited:
                    to_process.append((conn_strand, conn_point))
                    
        # Remove duplicates while preserving order
        seen = set()
        unique_strands = []
        for strand in moving_strands:
            if strand not in seen:
                seen.add(strand)
                unique_strands.append(strand)
                
        return unique_strands

    def get_strand_by_name(self, strand_name):
        """Get a strand object by its layer name."""
        for strand in self.canvas.strands:
            if strand.layer_name == strand_name:
                return strand
        return None

    def parse_connection_string(self, connection_str):
        """
        Parse a connection string like '1_2(0)' into strand name and endpoint.
        
        Args:
            connection_str (str): Connection string in format 'strand_name(endpoint)'
            
        Returns:
            tuple: (strand_name, endpoint) or (None, None) if invalid
        """
        if connection_str == 'null' or not connection_str:
            return None, None
            
        if '(' in connection_str and ')' in connection_str:
            strand_name = connection_str[:connection_str.index('(')]
            endpoint = int(connection_str[connection_str.index('(') + 1:connection_str.index(')')])
            return strand_name, endpoint
            
        return None, None

    def build_connection_cache(self):
        """Build a cache of connections for performance optimization."""
        if not hasattr(self.canvas, 'layer_state_manager') or not self.canvas.layer_state_manager:
            self.connection_cache = {}
            self.cache_valid = False
            return
            
        self.connection_cache = self.canvas.layer_state_manager.getConnections()
        self.cache_valid = True
        
    def invalidate_connection_cache(self):
        """Invalidate the connection cache when connections change."""
        self.cache_valid = False
        self.connection_cache = {}
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
            # Only draw if this end should have a circle and the strand is currently selected OR in truly_moving_strands
            truly_moving_strands = getattr(self.canvas, 'truly_moving_strands', [])
            if not has_circle or (not strand.is_selected and strand not in truly_moving_strands):
                continue
            
            # Debug logging for highlighting fix
            if strand in truly_moving_strands and not strand.is_selected:
                pass
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
            
            # Draw the stroke part in red (or transparent red if circle stroke is transparent)
            painter.setPen(Qt.NoPen)
            
            # Check if this circle has transparent stroke
            if hasattr(strand, 'start_circle_stroke_color') and hasattr(strand, 'end_circle_stroke_color'):
                circle_stroke_color = strand.start_circle_stroke_color if i == 0 else strand.end_circle_stroke_color
                if circle_stroke_color and circle_stroke_color.alpha() == 0:
                    # Use transparent red for transparent circles
                    painter.setBrush(QColor(255, 0, 0, 0))
                else:
                    # Use solid red for normal circles
                    painter.setBrush(QColor(255, 0, 0, 255))
            else:
                # Default to solid red if properties don't exist
                painter.setBrush(QColor(255, 0, 0, 255))
                
            painter.drawPath(stroke_c_shape)
            
            # Draw the color part using the strand's fill color to avoid black artifacts
            try:
                strand_fill = QColor(strand.color) if hasattr(strand, 'color') and strand.color is not None else QColor(0, 0, 0, 0)
                painter.setBrush(strand_fill)
                #painter.drawPath(color_c_shape)
            except Exception:
                # Fallback: don't draw the color segment if color is unavailable
                pass
            
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
                
            strand_connections = connections.get(strand.layer_name, ['null', 'null'])
            
            # Process start point (side 0) connection
            start_connection = strand_connections[0]
            if start_connection != 'null':
                connected_name, connected_end = self.parse_connection_string(start_connection)
                if connected_name:
                    # Find the connected strand object
                    connected_strand = self.get_strand_by_name(connected_name)
                    if connected_strand and connected_strand != strand:
                        cache_key = (strand.layer_name, 0)
                        self.connection_cache[cache_key] = connected_strand
            
            # Process end point (side 1) connection  
            end_connection = strand_connections[1]
            if end_connection != 'null':
                connected_name, connected_end = self.parse_connection_string(end_connection)
                if connected_name:
                    # Find the connected strand object
                    connected_strand = self.get_strand_by_name(connected_name)
                    if connected_strand and connected_strand != strand:
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
        """Find a strand connected to the given strand at the specified side using LayerStateManager."""
        if not hasattr(self.canvas, 'layer_state_manager') or not self.canvas.layer_state_manager:
            return None

        # Control points don't have connected strands
        if isinstance(side, str) or side not in [0, 1]:
            return None

        # Get connected strands from LayerStateManager
        connected_info = self.get_connected_strands(strand.layer_name, side)
        
        # Return the first connected strand if any
        if connected_info:
            return connected_info[0][0]  # Return the strand object
            
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
        
        # Stop the timer if we're not in an active movement
        if not self.is_moving or not self.affected_strand:
            self.redraw_timer.stop()
            return
            
        # Always invalidate the background cache to ensure grid and other strands are visible
        if hasattr(self.canvas, 'background_cache_valid'):
            self.canvas.background_cache_valid = False
                
        # Force a single redraw of the canvas - no additional timers to prevent infinite loops
        self.canvas.update()

    def mouseMoveEvent(self, event):
        """
        Handle mouse move events.
        
        Args:
            event (QMouseEvent): The mouse event.
        """
        # --- ADDED: Log current state on move (only if not suppressing) ---
        if self.is_moving and not perf_logger.suppress_move_logging:
            pass
        # --- END ADDED ---

        # Handle bias control movement if active
        if hasattr(self, 'is_moving_bias_control') and self.is_moving_bias_control:
            if hasattr(self, 'bias_control_strand') and self.bias_control_strand:
                if self.bias_control_strand.bias_control.handle_mouse_move(event, self.bias_control_strand):
                    # Update strand geometry so the curve reflects bias changes in real-time
                    self.bias_control_strand.update_shape()
                    if hasattr(self.bias_control_strand, 'update_side_line'):
                        self.bias_control_strand.update_side_line()
                    self.canvas.update()
                    return
        
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
                pass
        else:
            # No offset needed (cursor was moved to strand position) or offset is zero
            adjusted_pos = pos
        
        # Smart grid snapping based on zoom level and modifiers
        # Check if Ctrl key is pressed for forced grid snapping
        from PyQt5.QtWidgets import QApplication
        force_grid_snap = QApplication.keyboardModifiers() & Qt.ControlModifier

        # Extra logging for zoom-out debugging
        if hasattr(self.canvas, 'zoom_factor') and self.canvas.zoom_factor < 0.8:
            pass

        # Check if user has enabled snap to grid (bias controls should never snap)
        user_snap_enabled = (hasattr(self.canvas, 'snap_to_grid_enabled') and
                            self.canvas.snap_to_grid_enabled and
                            self.moving_side not in ['bias_triangle', 'bias_circle'])

        # At very high zoom out (300% = zoom_factor ~0.33), disable snapping unless Ctrl is pressed
        if self.canvas.zoom_factor < 0.35 and not force_grid_snap:
            # Very zoomed out - NO grid snapping
            snapped_pos = adjusted_pos
        elif (self.canvas.zoom_factor >= 0.8 or force_grid_snap) and user_snap_enabled:
            # Near normal zoom OR Ctrl held - use full grid snapping if enabled
            snapped_pos = self.canvas.snap_to_grid(adjusted_pos)
        elif self.canvas.zoom_factor >= 0.5 and user_snap_enabled:
            # Moderately zoomed out - use very gentle snapping if enabled
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
        elif force_grid_snap:
            # Ctrl held but snap disabled in settings - still allow Ctrl override
            snapped_pos = self.canvas.snap_to_grid(adjusted_pos)
        else:
            # Snap disabled by user or zoom level between 0.35-0.8 without snap enabled
            snapped_pos = adjusted_pos
        
        # Extra logging for zoom-out debugging
        if hasattr(self.canvas, 'zoom_factor') and self.canvas.zoom_factor < 0.8:
            pass
        
        # Update target position for gradual movement
        self.target_pos = snapped_pos
        
        # Update last snapped position for next movement
        self.last_snapped_pos = snapped_pos
        
        # Ensure the background cache is invalidated for continuous refresh
        if hasattr(self.canvas, 'background_cache_valid'):
            self.canvas.background_cache_valid = False
        
        # Update strand position directly for immediate feedback
        self.update_strand_position(snapped_pos)
        
        # Mouse movement provides continuous updates - no need for additional timers
        # Only force a single immediate update
        self.canvas.update()
