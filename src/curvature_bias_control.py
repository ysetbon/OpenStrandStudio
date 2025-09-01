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
        self.control_size = 12  # Smaller bias control squares to match subtle highlight
        self.icon_size = 8      # Size of triangle/circle icons inside squares
        
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
        # Don't reinitialize during dragging
        if self.dragging_triangle or self.dragging_circle:
            # Return current positions without modification
            return self.triangle_position, self.circle_position
            
        # If positions haven't been initialized, set them to base positions
        if self.triangle_position is None or self.circle_position is None:
            triangle_base, circle_base = self.get_base_positions(strand)
            if triangle_base is None or circle_base is None:
                print(f"[ERROR] Could not calculate base positions!")
                return None, None
            self.triangle_position = triangle_base
            self.circle_position = circle_base
        
        # Check if we need to update positions (e.g., if center point moved)
        # This is important to keep bias controls relative to the center point
        if hasattr(self, '_last_center') and hasattr(strand, 'control_point_center'):
            if self._last_center != strand.control_point_center:
                # Center moved, update positions relatively
                delta = strand.control_point_center - self._last_center
                if self.triangle_position:
                    self.triangle_position += delta
                if self.circle_position:
                    self.circle_position += delta
                self._last_center = QPointF(strand.control_point_center)
        elif hasattr(strand, 'control_point_center'):
            self._last_center = QPointF(strand.control_point_center)
        
        # Use stored positions (which get updated when dragging)
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
                print(f"[draw] Initializing positions for first draw")
                triangle_base, circle_base = self.get_base_positions(strand)
                if triangle_base is None or circle_base is None:
                    return
                self.triangle_position = triangle_base
                self.circle_position = circle_base
                
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
        
        if not hasattr(self.canvas, 'enable_curvature_bias_control'):
            return False
            
        if not self.canvas.enable_curvature_bias_control:
            return False
            
        if not hasattr(self.canvas, 'enable_third_control_point'):
            return False
            
        if not self.canvas.enable_third_control_point:
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
        """
        return QRectF(
            pos.x() - self.control_size / 2,
            pos.y() - self.control_size / 2,
            self.control_size,
            self.control_size
        )
        
    def handle_mouse_press(self, event, strand):
        """
        Handle mouse press events for bias controls.
        Returns True if a control was clicked, False otherwise.
        """
        if not self.should_show_controls(strand):
            return False
            
        pos = event.pos()
        
        # Make sure positions are initialized before checking
        if self.triangle_position is None or self.circle_position is None:
            triangle_base, circle_base = self.get_base_positions(strand)
            if triangle_base is None or circle_base is None:
                return False
            self.triangle_position = triangle_base
            self.circle_position = circle_base
            print(f"[INIT] First click - initialized positions")
        
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
            # Store the offset between click position and control center
            self.drag_offset = triangle_pos - pos
            print(f"[START DRAG] TRIANGLE - offset: {self.drag_offset}")
            return True
            
        # Check circle control
        circle_rect = self.get_control_rect(circle_pos)
        if circle_rect.contains(pos):
            self.dragging_circle = True
            self.drag_start_pos = pos
            self.drag_start_bias = self.circle_bias
            # Store the offset between click position and control center
            self.drag_offset = circle_pos - pos
            print(f"[START DRAG] CIRCLE - offset: {self.drag_offset}")
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
        
        # Make the control points follow the mouse with the stored offset
        # This prevents the control from jumping to the mouse position
        new_position = pos + self.drag_offset
        
        if self.dragging_triangle:
            # Update the triangle position to follow the mouse with offset
            self.triangle_position = QPointF(new_position)
            
            # Calculate bias value based on distance from center
            center = strand.control_point_center
            distance = math.sqrt((new_position.x() - center.x())**2 + (new_position.y() - center.y())**2)
            # Map distance to bias (closer = lower bias, farther = higher bias)
            self.triangle_bias = max(0.0, min(1.0, distance / 100.0))
            print(f"[DRAG] Triangle at {self.triangle_position}, bias={self.triangle_bias:.2f}")
                
        elif self.dragging_circle:
            # Update the circle position to follow the mouse with offset
            self.circle_position = QPointF(new_position)
            
            # Calculate bias value based on distance from center
            center = strand.control_point_center
            distance = math.sqrt((new_position.x() - center.x())**2 + (new_position.y() - center.y())**2)
            # Map distance to bias (closer = lower bias, farther = higher bias)
            self.circle_bias = max(0.0, min(1.0, distance / 100.0))
            print(f"[DRAG] Circle at {self.circle_position}, bias={self.circle_bias:.2f}")
                
        return True
    
    def get_base_positions(self, strand):
        """
        Get the base positions of bias controls without any drag offsets.
        """
        if not hasattr(strand, 'control_point_center'):
            return None, None
            
        center = strand.control_point_center
        control1 = strand.control_point1
        control2 = strand.control_point2
        
        # Calculate the angle from control1 to control2
        dx = control2.x() - control1.x()
        dy = control2.y() - control1.y()
        angle = math.atan2(dy, dx)
        
        # Position bias controls perpendicular to the control1-control2 line
        perpendicular_angle = angle + math.pi / 2
        
        # Default distance from center
        distance = 40
        
        # Calculate base positions
        triangle_x = center.x() + distance * math.cos(perpendicular_angle)
        triangle_y = center.y() + distance * math.sin(perpendicular_angle)
        circle_x = center.x() - distance * math.cos(perpendicular_angle)
        circle_y = center.y() - distance * math.sin(perpendicular_angle)
        
        return QPointF(triangle_x, triangle_y), QPointF(circle_x, circle_y)
        
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