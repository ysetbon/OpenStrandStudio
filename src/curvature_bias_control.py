from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath, QPolygonF
import math

class CurvatureBiasControl:
    """
    Manages the curvature bias control points for asymmetric curve control.
    These controls appear near the 3rd control point when enabled.
    """
    
    def __init__(self, canvas):
        self.canvas = canvas
        
        # Bias values: 0.5 = neutral, 0.0 = full bias toward triangle, 1.0 = full bias toward circle
        self.triangle_bias = 0.5  # How much the curve biases toward the triangle control point
        self.circle_bias = 0.5    # How much the curve biases toward the circle control point
        
        # Store the actual positions of bias controls (they follow the mouse when dragged)
        self.triangle_position = None  # Will be set to actual position
        self.circle_position = None     # Will be set to actual position
        
        # Visual properties
        self.control_size = 16  # Smaller bias control squares to match subtle highlight
        self.icon_size = 9      # Size of triangle/circle icons inside squares
        self.selection_size = 50  # Larger clickable area for easier selection (same as green highlight square)
        
        # Active drag state
        self.dragging_triangle = False
        self.dragging_circle = False
        self.drag_start_pos = None
        self.drag_start_bias = None
        # Store the offset between mouse click and control center
        self.drag_offset = QPointF(0, 0)
        # Visual drag offsets so squares visibly move while dragging
        self.triangle_drag_offset = QPointF(0, 0)
        self.circle_drag_offset = QPointF(0, 0)
        # Persistent visual offset derived from bias values (so squares stay after release)
        self.max_visual_offset = 40  # pixels from neutral per control
        
    def get_bias_control_positions(self, strand):
        """
        Calculate the positions of the bias control points based on the strand's control points.
        Returns (triangle_pos, circle_pos) as QPointF objects.
        """
        # Don't update during dragging
        if self.dragging_triangle or self.dragging_circle:
            # Return current positions without modification
            return self.triangle_position, self.circle_position
            
        # If positions haven't been initialized, initialize them based on bias values
        if self.triangle_position is None or self.circle_position is None:
            self.update_positions_from_biases(strand)
            if self.triangle_position is None or self.circle_position is None:
                return None, None
        
        # Check if any of the main control points have moved
        # and update bias control positions accordingly
        needs_update = False
        
        if hasattr(self, '_last_center') and hasattr(strand, 'control_point_center'):
            if self._last_center != strand.control_point_center:
                needs_update = True
        
        if hasattr(self, '_last_control1') and hasattr(strand, 'control_point1'):
            if self._last_control1 != strand.control_point1:
                needs_update = True
                
        if hasattr(self, '_last_control2') and hasattr(strand, 'control_point2'):
            if self._last_control2 != strand.control_point2:
                needs_update = True
        
        # Update positions if any control point has moved
        if needs_update:
            self.update_positions_from_biases(strand)
        
        # Store current control point positions for next comparison
        if hasattr(strand, 'control_point_center'):
            self._last_center = QPointF(strand.control_point_center)
        if hasattr(strand, 'control_point1'):
            self._last_control1 = QPointF(strand.control_point1)
        if hasattr(strand, 'control_point2'):
            self._last_control2 = QPointF(strand.control_point2)
        
        # Return stored positions
        return self.triangle_position, self.circle_position
        
    def draw_bias_controls(self, painter, strand):
        """
        Draw the bias control squares with their icons.
        """
        if not self.should_show_controls(strand):
            return
        
        # Don't reinitialize if we're dragging
        if self.dragging_triangle or self.dragging_circle:
            # Use current positions directly during drag
            triangle_pos = self.triangle_position
            circle_pos = self.circle_position
        else:
            # Only initialize if needed when not dragging
            if self.triangle_position is None or self.circle_position is None:
                # Use update_positions_from_biases to set positions based on actual bias values
                self.update_positions_from_biases(strand)
                
            triangle_pos, circle_pos = self.get_bias_control_positions(strand)
            
        if not triangle_pos or not circle_pos:
            return
            
        # Save painter state
        painter.save()
        
        # Draw triangle bias control
        self.draw_control_square(painter, triangle_pos, True, self.triangle_bias, strand.color if hasattr(strand, 'color') else QColor(50, 50, 50))
        
        # Draw circle bias control
        self.draw_control_square(painter, circle_pos, False, self.circle_bias, strand.color if hasattr(strand, 'color') else QColor(50, 50, 50))
        
        # Draw connection lines to show bias influence
        if self.triangle_bias != 0.5 or self.circle_bias != 0.5:
            self.draw_bias_influence_lines(painter, strand, triangle_pos, circle_pos)
        
        # Restore painter state
        painter.restore()
        
    def draw_control_square(self, painter, pos, is_triangle, bias_value, strand_color):
        """
        Draw a single control square with its icon.
        """
        # Create rectangle for control square
        rect = QRectF(
            pos.x() - self.control_size / 2,
            pos.y() - self.control_size / 2,
            self.control_size,
            self.control_size
        )
        
        # Draw order: outer black border -> green filled square -> strand-colored icon

        # 1) Outer black border (slightly larger)
        outer_size = self.control_size + 2
        outer_rect = QRectF(
            pos.x() - outer_size / 2,
            pos.y() - outer_size / 2,
            outer_size,
            outer_size
        )
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor('black'), 2))
        painter.drawRect(outer_rect)

        # 2) Inner green filled square (covers the section)
        painter.setPen(QPen(QColor('green'), 1.5))
        painter.setBrush(QBrush(QColor('green')))
        painter.drawRect(rect)
        
        # 3) Icon inside (filled with strand color)
        icon_color = QColor(strand_color) if isinstance(strand_color, QColor) else QColor(50, 50, 50)
        icon_pen = QPen(icon_color, 1.5)
        painter.setPen(icon_pen)
        painter.setBrush(QBrush(icon_color))
        
        if is_triangle:
            # Draw triangle icon
            triangle = QPolygonF([
                QPointF(pos.x(), pos.y() - self.icon_size / 2),
                QPointF(pos.x() - self.icon_size / 2, pos.y() + self.icon_size / 2),
                QPointF(pos.x() + self.icon_size / 2, pos.y() + self.icon_size / 2)
            ])
            painter.drawPolygon(triangle)
        else:
            # Draw circle icon
            painter.drawEllipse(pos, self.icon_size / 2, self.icon_size / 2)
        # (Borders already drawn above in steps 1 and 2)
            
    def draw_bias_influence_lines(self, painter, strand, triangle_pos, circle_pos):
        """
        Draw visual indicators showing how bias affects the curve.
        """
        pen = QPen(QColor(150, 150, 150, 100), 1, Qt.DashLine)
        painter.setPen(pen)
        
        center = strand.control_point_center
        
        # Draw influence lines with opacity based on bias
        if self.triangle_bias != 0.5:
            opacity = int(100 * abs(self.triangle_bias - 0.5) * 2)
            pen.setColor(QColor(255, 0, 0, opacity))
            painter.setPen(pen)
            painter.drawLine(center, strand.control_point1)
            
        if self.circle_bias != 0.5:
            opacity = int(100 * abs(self.circle_bias - 0.5) * 2)
            pen.setColor(QColor(0, 0, 255, opacity))
            painter.setPen(pen)
            painter.drawLine(center, strand.control_point2)
            
    def should_show_controls(self, strand):
        """
        Check if bias controls should be shown for this strand.
        """
        # Basic requirements:
        # 1. Curvature bias control is enabled
        # 2. Third control point is enabled  
        # 3. Control points are being shown (which means strand is relevant for editing)
        # 4. The center control point must be locked (manually positioned)
        
        if not hasattr(self.canvas, 'enable_curvature_bias_control'):
            return False
            
        if not self.canvas.enable_curvature_bias_control:
            return False
            
        if not hasattr(self.canvas, 'enable_third_control_point'):
            return False
            
        if not self.canvas.enable_third_control_point:
            return False
        
        # Check if the center control point is locked (required for bias controls to work)
        if not hasattr(strand, 'control_point_center_locked') or not strand.control_point_center_locked:
            return False
        
        # Always show if control points are visible OR if we're in test mode
        # This is the simplest and most consistent approach
        if hasattr(self.canvas, 'show_control_points') and self.canvas.show_control_points:
            return True
        
        # Also always show in test mode (when there's only one strand)
        if hasattr(self.canvas, 'strands') and len(self.canvas.strands) == 1:
            return True
            
        return False
        
    def get_control_rect(self, pos):
        """
        Get the rectangle for a control point at the given position.
        Uses selection_size for the clickable area, not the visual control_size.
        """
        return QRectF(
            pos.x() - self.selection_size / 2,
            pos.y() - self.selection_size / 2,
            self.selection_size,
            self.selection_size
        )
        
    def handle_mouse_press(self, event, strand):
        """
        Handle mouse press events for bias controls.
        Returns True if a control was clicked, False otherwise.
        """
        if not self.should_show_controls(strand):
            return False
            
        pos = event.pos()
        
        # Make sure positions are initialized and properly updated before checking
        if self.triangle_position is None or self.circle_position is None:
            # Initialize with proper positions based on current bias values
            self.update_positions_from_biases(strand)
        
        # Ensure positions are synced with current bias values
        # This is important if bias values were changed programmatically
        if not (self.dragging_triangle or self.dragging_circle):
            self.update_positions_from_biases(strand)
        
        triangle_pos = self.triangle_position
        circle_pos = self.circle_position
        
        if not triangle_pos or not circle_pos:
            return False
            
        # Check triangle control
        triangle_rect = self.get_control_rect(triangle_pos)
        if triangle_rect.contains(pos):
            self.dragging_triangle = True
            self.drag_start_pos = pos
            self.drag_start_bias = self.triangle_bias
            # Don't store offset for line-constrained movement
            self.drag_offset = QPointF(0, 0)
            # Mark that triangle has been moved to show other control points
            if hasattr(strand, 'triangle_has_moved'):
                strand.triangle_has_moved = True
            return True
            
        # Check circle control
        circle_rect = self.get_control_rect(circle_pos)
        if circle_rect.contains(pos):
            self.dragging_circle = True
            self.drag_start_pos = pos
            self.drag_start_bias = self.circle_bias
            # Don't store offset for line-constrained movement
            self.drag_offset = QPointF(0, 0)
            return True
            
        return False
        
    def handle_mouse_move(self, event, strand):
        """
        Handle mouse move events for bias controls.
        Returns True if a control is being dragged, False otherwise.
        """
        if not self.dragging_triangle and not self.dragging_circle:
            return False
            
        pos = event.pos()
        center = strand.control_point_center
        
        if self.dragging_triangle:
            # Constrain movement along the line from center to control_point1
            control1 = strand.control_point1
            
            # Project mouse position onto the line from center to control1
            line_vec = control1 - center
            line_length = math.sqrt(line_vec.x()**2 + line_vec.y()**2)
            
            if line_length > 0:
                # Normalize the line vector
                line_vec_norm = QPointF(line_vec.x() / line_length, line_vec.y() / line_length)
                
                # Get vector from center to mouse position
                mouse_vec = pos - center
                
                # Project mouse position onto the line (dot product)
                projection_length = mouse_vec.x() * line_vec_norm.x() + mouse_vec.y() * line_vec_norm.y()
                
                # Clamp the projection to be between center (0) and control point (line_length)
                projection_length = max(0, min(line_length, projection_length))
                
                # Calculate the new position on the line
                self.triangle_position = center + line_vec_norm * projection_length
                
                # Calculate bias based on position along the line (0 at center, 1 at control point)
                self.triangle_bias = projection_length / line_length
                
        elif self.dragging_circle:
            # Constrain movement along the line from center to control_point2
            control2 = strand.control_point2
            
            # Project mouse position onto the line from center to control2
            line_vec = control2 - center
            line_length = math.sqrt(line_vec.x()**2 + line_vec.y()**2)
            
            if line_length > 0:
                # Normalize the line vector
                line_vec_norm = QPointF(line_vec.x() / line_length, line_vec.y() / line_length)
                
                # Get vector from center to mouse position
                mouse_vec = pos - center
                
                # Project mouse position onto the line (dot product)
                projection_length = mouse_vec.x() * line_vec_norm.x() + mouse_vec.y() * line_vec_norm.y()
                
                # Clamp the projection to be between center (0) and control point (line_length)
                projection_length = max(0, min(line_length, projection_length))
                
                # Calculate the new position on the line
                self.circle_position = center + line_vec_norm * projection_length
                
                # Calculate bias based on position along the line (0 at center, 1 at control point)
                self.circle_bias = projection_length / line_length
                
        return True
    
    def get_base_positions(self, strand):
        """
        Get the base positions of bias controls on the lines between center and control points.
        """
        if not hasattr(strand, 'control_point_center'):
            return None, None
            
        center = strand.control_point_center
        control1 = strand.control_point1
        control2 = strand.control_point2
        
        # Position triangle bias control on the line from center to control_point1
        # Start at 50% of the distance (neutral position)
        triangle_vec = control1 - center
        triangle_base = center + triangle_vec * 0.5  # 50% along the line for neutral bias
        
        # Position circle bias control on the line from center to control_point2
        # Start at 50% of the distance (neutral position)
        circle_vec = control2 - center
        circle_base = center + circle_vec * 0.5  # 50% along the line for neutral bias
        
        return triangle_base, circle_base
        
    def handle_mouse_release(self, event):
        """
        Handle mouse release events for bias controls.
        """
        was_dragging = self.dragging_triangle or self.dragging_circle
        
        # The positions are already saved in triangle_position and circle_position
        # The bias values are already updated based on those positions
        # Just clear the dragging state
        self.dragging_triangle = False
        self.dragging_circle = False
        self.drag_start_pos = None
        self.drag_start_bias = None
        self.drag_offset = QPointF(0, 0)  # Reset the drag offset
        
        return was_dragging
        
    def get_bias_weights(self):
        """
        Get the current bias weights for curve calculation.
        Returns (triangle_weight, circle_weight) where weights sum to 1.0
        """
        # Normalize biases to weights
        total = self.triangle_bias + self.circle_bias
        if total == 0:
            return 0.5, 0.5
            
        triangle_weight = self.triangle_bias / total
        circle_weight = self.circle_bias / total
        
        return triangle_weight, circle_weight
        
    def reset_biases(self):
        """
        Reset biases to neutral (0.5 each) and positions to default.
        """
        self.triangle_bias = 0.5
        self.circle_bias = 0.5
        # Reset positions to None so they'll be recalculated
        self.triangle_position = None
        self.circle_position = None
    
    def update_positions_from_biases(self, strand):
        """
        Update the positions of bias controls based on their bias values.
        This is used when bias values are changed programmatically.
        """
        if not hasattr(strand, 'control_point_center'):
            return
        
        if not hasattr(strand, 'control_point1') or not hasattr(strand, 'control_point2'):
            return
            
        center = strand.control_point_center
        control1 = strand.control_point1
        control2 = strand.control_point2
        
        # Update triangle position based on triangle_bias
        triangle_vec = control1 - center
        self.triangle_position = center + triangle_vec * self.triangle_bias
        
        # Update circle position based on circle_bias
        circle_vec = control2 - center
        self.circle_position = center + circle_vec * self.circle_bias