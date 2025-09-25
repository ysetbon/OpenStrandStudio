# src/strand.py

from PyQt5.QtCore import QPointF, Qt, QRectF
from PyQt5.QtGui import (
    QColor, QPainter, QPen, QBrush, QPainterPath, QPainterPathStroker,  QTransform,QImage, QRadialGradient
)
from render_utils import RenderUtils
import math
from PyQt5.QtGui import QPolygonF  # Ensure this is included among your imports
from PyQt5.QtGui import QPainterPath, QPainterPathStroker
class Strand:
    """
    Represents a basic strand in the application with two Bezier control points.
    """
    def __init__(
        self, start, end, width,
        color=QColor(200, 170, 230, 255) , stroke_color=QColor(0, 0, 0, 255), stroke_width=4,
        set_number=None, layer_name=""
    ):
        self._start = start
        self._end = end
        self.width = width
        self.color = color
        self.shadow_color = QColor(0, 0, 0, 150)  # Semi-transparent black shadow for overlaps
        self._stroke_color = stroke_color  # Use private attribute for property
        self.stroke_width = stroke_width
        self.side_line_color = QColor(0, 0, 0, 255)
        self.attached_strands = []  # List to store attached strands
        self.has_circles = [False, False]  # Flags for circles at start and end
        self.is_start_side = True
        self._is_selected = False  # Indicates if the strand is selected (use private attribute for property)
        self.is_hidden = False # Indicates if the strand is hidden
        self.shadow_only = False # Indicates if the strand is in shadow-only mode
        # Control point influence parameters - will be overridden by canvas settings if available
        self.curve_response_exponent = 1.5  # Default: Exponential response (1.0=linear, 1.5=mild quadratic, 2.0=quadratic)
        self.control_point_base_fraction = 0.4  # Default: Base fraction for control point influence
        self.distance_multiplier = 1.2  # Default: Distance multiplication factor (1.0-10.0 range)
        self.endpoint_tension = 1.15  # Extra tension for start/end control points (1.0=normal, 1.15=15% tighter)

        # Initialize attachment statuses
        self.start_attached = False
        self.end_attached = False

        # Initialize control points at proper positions along the strand
        dx = 0
        dy = 0
        
        self.control_point1 = QPointF(
            self._start.x(),
            self._start.y()
        )
        self.control_point2 = QPointF(
            self._start.x(),
            self._start.y()
        )
        
        # Add the center control point (midpoint between control_point1 and control_point2)
        self.control_point_center = QPointF(
            self._start.x(),
            self._start.y()
        )
        # Flag to track if the center control point has been manually positioned
        self.control_point_center_locked = False
        
        # Flag to track if the triangle control point has been moved
        self.triangle_has_moved = False

        # Add canvas reference
        self._canvas = None
        
        # Initialize bias control (will be properly set when canvas is assigned)
        self.bias_control = None

        # Add line visibility flags
        self.start_line_visible = True
        self.end_line_visible = True
        # Add dashed extension visibility flags
        self.start_extension_visible = False
        self.end_extension_visible = False

        # --- NEW: Arrow visibility flags ---
        self.start_arrow_visible = False
        self.end_arrow_visible = False
        # --- END NEW ---
        # --- NEW: Full arrow visibility flag ---
        self.full_arrow_visible = False
        # Arrow customization properties
        self.arrow_color = None  # Will use stroke_color if None
        self.arrow_transparency = 100  # 100% = fully opaque
        self.arrow_texture = 'none'  # Options: 'none', 'stripes', 'dots', 'crosshatch'
        self.arrow_shaft_style = 'solid'  # Options: 'solid', 'stripes', 'dots'
        self.arrow_head_visible = True  # Whether to show arrow head
        # --- END NEW ---

        self.layer_name = layer_name
        self.set_number = set_number
        self._circle_stroke_color = None  # Keep for backward compatibility
        self._start_circle_stroke_color = None
        self._end_circle_stroke_color = None
        
        # Initialize knot connections
        self.knot_connections = {}
        
        self.update_attachable()
        self.update_shape()
        self.attachable = True  # Initialize as True, will be updated based on has_circles

    @property
    def canvas(self):
        """Getter for the canvas reference."""
        return self._canvas
    
    @canvas.setter
    def canvas(self, value):
        """Setter for the canvas reference."""
        self._canvas = value
        # Initialize bias control when canvas is set
        if value and hasattr(value, 'enable_curvature_bias_control'):
            from curvature_bias_control import CurvatureBiasControl
            if self.bias_control is None:
                self.bias_control = CurvatureBiasControl(value)
    
    @property
    def start(self):
        """Getter for the start point."""
        return self._start

    @start.setter
    def start(self, value):
        """Setter for the start point."""
        # Update control points if they coincide with the current start point
        if self.control_point1 == self._start:
            self.control_point1 = value
        if self.control_point2 == self._start:
            self.control_point2 = value
        self._start = value
        self.update_shape()

    @property
    def end(self):
        """Getter for the end point."""
        return self._end

    @end.setter
    def end(self, value):
        """Setter for the end point."""
        self._end = value
        self.update_shape()

    @property
    def stroke_color(self):
        """Getter for the stroke color."""
        return self._stroke_color

    @stroke_color.setter
    def stroke_color(self, value):
        """Setter for the stroke color that also updates circle_stroke_color."""
        self._stroke_color = value

    @property
    def is_selected(self):
        """Getter for the is_selected property."""
        return self._is_selected

    @is_selected.setter
    def is_selected(self, value):
        """Setter for the is_selected property with protection for moving strands."""
        # CRITICAL FIX: Never allow is_selected to be set to False for strands in truly_moving_strands
        if value is False and hasattr(self, 'canvas') and self.canvas:
            truly_moving_strands = getattr(self.canvas, 'truly_moving_strands', [])
            if self in truly_moving_strands:
                pass
                return  # Don't set to False if strand is in truly_moving_strands
        
        self._is_selected = value
        
        # For AttachedStrand instances, also update circle_stroke_color
        # Check class name to avoid circular import issues
        if self.__class__.__name__ == 'AttachedStrand':
            # Only update circle_stroke_color if it's not transparent (alpha > 0)
            # This preserves intentionally transparent circle strokes
            if hasattr(self, '_circle_stroke_color') and self._circle_stroke_color and self._circle_stroke_color.alpha() > 0:
                new_color = QColor(self.stroke_color) if hasattr(self, 'stroke_color') and self.stroke_color else QColor(0, 0, 0, 255)
                self.circle_stroke_color = new_color
                pass

    @property
    def circle_stroke_color(self):
        # Keep for backward compatibility - return start circle color
        return self.start_circle_stroke_color

    @circle_stroke_color.setter
    def circle_stroke_color(self, value):
        # Keep for backward compatibility - set both start and end colors
        self.start_circle_stroke_color = value
        self.end_circle_stroke_color = value

    @property
    def start_circle_stroke_color(self):
        # If separate start color is set, use it
        if self._start_circle_stroke_color is not None:
            return self._start_circle_stroke_color
        # Otherwise fall back to general circle_stroke_color
        if self._circle_stroke_color is not None:
            return self._circle_stroke_color
        # Default to black
        return QColor(0, 0, 0, 255)

    @start_circle_stroke_color.setter
    def start_circle_stroke_color(self, value):
        if value is not None and isinstance(value, (Qt.GlobalColor, int)):
            value = QColor(value)
        
        self._setting_circle_transparency = True
        
        if value is None:
            pass
            self._start_circle_stroke_color = QColor(0, 0, 0, 255)
        else:
            pass
            self._start_circle_stroke_color = value
        
        self._setting_circle_transparency = False

    @property
    def end_circle_stroke_color(self):
        # If separate end color is set, use it
        if self._end_circle_stroke_color is not None:
            return self._end_circle_stroke_color
        # Otherwise fall back to general circle_stroke_color
        if self._circle_stroke_color is not None:
            return self._circle_stroke_color
        # Default to black
        return QColor(0, 0, 0, 255)

    @end_circle_stroke_color.setter
    def end_circle_stroke_color(self, value):
        if value is not None and isinstance(value, (Qt.GlobalColor, int)):
            value = QColor(value)
        
        self._setting_circle_transparency = True
        
        if value is None:
            pass
            self._end_circle_stroke_color = QColor(0, 0, 0, 255)
        else:
            pass
            self._end_circle_stroke_color = value
        
        self._setting_circle_transparency = False

    def draw_selection_path(self, painter):
        """Draws the selection area of the strand."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        selection_pen = QPen(QColor('blue'), 1, Qt.DashLine)
        painter.setPen(selection_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.get_selection_path())

        painter.restore()


    def get_start_selection_path(self):
        """Get a selection path for the exact start point of the strand."""
        # Create a small circle at the start point that matches the strand's start
        start_path = QPainterPath()
        
        # Base radius using strand width, but adjust for zoom to maintain consistent click targets
        base_radius = max(self.width / 2, 15)  # Minimum radius for clickability
        
        # Adjust radius based on zoom level to maintain consistent screen-space click targets
        if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'zoom_factor'):
            # When zoomed out, make radius larger in canvas coordinates
            # When zoomed in, make radius smaller in canvas coordinates  
            # This maintains consistent screen-space click target size
            zoom_factor = self.canvas.zoom_factor
            radius = base_radius / zoom_factor
        else:
            radius = base_radius
            
        start_path.addEllipse(self.start, radius, radius)
        return start_path
    def draw_path(self, painter):
        """Draw the path of the strand without filling."""
        path = self.get_path()
        painter.drawPath(path)
    def get_end_selection_path(self):
        """Get a selection path for the exact end point of the strand."""
        # Create a small circle at the end point that matches the strand's end
        end_path = QPainterPath()
        
        # Base radius using strand width, but adjust for zoom to maintain consistent click targets
        base_radius = max(self.width / 2, 15)  # Minimum radius for clickability
        
        # Adjust radius based on zoom level to maintain consistent screen-space click targets
        if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'zoom_factor'):
            # When zoomed out, make radius larger in canvas coordinates
            # When zoomed in, make radius smaller in canvas coordinates  
            # This maintains consistent screen-space click target size
            zoom_factor = self.canvas.zoom_factor
            radius = base_radius / zoom_factor
        else:
            radius = base_radius
            
        end_path.addEllipse(self.end, radius, radius)
        return end_path
 

    def is_straight_line(self):
        """Check if the strand is a straight line."""
        return (self.start == self.control_point1 == self.control_point2 == self.end) or \
               self.are_points_colinear(self.start, self.control_point1, self.control_point2, self.end)

    def are_points_colinear(self, *points):
        """Check if given points are colinear."""
        if len(points) < 2:
            return True
        x0, y0 = points[0].x(), points[0].y()
        dx, dy = points[-1].x() - x0, points[-1].y() - y0
        for point in points[1:-1]:
            x, y = point.x() - x0, point.y() - y0
            # Cross product should be zero for colinear points
            if abs(dx * y - dy * x) > 1e-6:
                return False
        return True

    def create_selection_rectangle(self, stroke_width):
        """Create a rectangular selection path around a straight line."""
        # Calculate the vector from start to end
        dx = self.end.x() - self.start.x()
        dy = self.end.y() - self.start.y()
        length = math.hypot(dx, dy)

        if length == 0:
            # Start and end are the same point, create a circle around the point
            radius = stroke_width / 2
            rect_path = QPainterPath()
            rect_path.addEllipse(self.start, radius, radius)
            return rect_path
        else:
            # Normalize direction vector
            dir_x = dx / length
            dir_y = dy / length

            # Perpendicular vector
            perp_x = -dir_y
            perp_y = dir_x

            # Half of the stroke width
            half_width = stroke_width / 2

            # Calculate the offsets
            offset_x = perp_x * half_width
            offset_y = perp_y * half_width

            # Calculate the four corners of the rectangle
            p1 = QPointF(self.start.x() + offset_x, self.start.y() + offset_y)
            p2 = QPointF(self.start.x() - offset_x, self.start.y() - offset_y)
            p3 = QPointF(self.end.x() - offset_x, self.end.y() - offset_y)
            p4 = QPointF(self.end.x() + offset_x, self.end.y() + offset_y)

            # Create the rectangular path
            rect_path = QPainterPath()
            rect_path.moveTo(p1)
            rect_path.lineTo(p2)
            rect_path.lineTo(p3)
            rect_path.lineTo(p4)
            rect_path.closeSubpath()

            return rect_path

    def update_attachable(self):
        """Update the attachable property based on has_circles."""
        self.attachable = not all(self.has_circles)
        
    def maintain_knot_connections(self):
        """Maintain coordinate synchronization for knot connections."""
        if not hasattr(self, 'knot_connections'):
            return
            
        # Skip synchronization if we're in the middle of a move operation
        if hasattr(self, 'updating_position') and self.updating_position:
            return
            
        # Skip synchronization if this strand is currently being moved
        if hasattr(self, '_is_being_moved') and self._is_being_moved:
            return
            
        # Skip synchronization if this strand is currently being rotated as part of a group
        if hasattr(self, '_is_being_rotated') and self._is_being_rotated:
            return
            
        for end_type, connection_info in self.knot_connections.items():
            connected_strand = connection_info['connected_strand']
            connected_end = connection_info['connected_end']
            
            # Skip if the connected strand is being moved
            if hasattr(connected_strand, '_is_being_moved') and connected_strand._is_being_moved:
                return
            
            # Get current coordinates
            if end_type == 'start':
                my_point = self.start
            else:
                my_point = self.end
                
            if connected_end == 'start':
                connected_point = connected_strand.start
            else:
                connected_point = connected_strand.end
                
            # Only synchronize if coordinates have drifted significantly (more than 1 pixel)
            # This prevents interference with intentional movements
            distance = ((my_point.x() - connected_point.x()) ** 2 + 
                       (my_point.y() - connected_point.y()) ** 2) ** 0.5
            if distance > 1.0:
                # Use the connected strand's coordinate as the reference
                if end_type == 'start':
                    self.start = connected_point
                else:
                    self.end = connected_point

    def set_has_circles(self, start_circle, end_circle):
        """Set the has_circles attribute and update attachable."""
        self.has_circles = [start_circle, end_circle]
        self.update_attachable()

    @property
    def set_number(self):
        """Getter for set_number, always returns an integer."""
        return self._set_number

    @set_number.setter
    def set_number(self, value):
        """Setter for set_number, stores the value as an integer."""
        self._set_number = int(value) if value is not None else None

    def set_color(self, new_color):
        """Set the color of the strand and its side line."""
        self.color = new_color
        self.side_line_color = self.stroke_color

    def update_shape(self):
        """Update the shape of the strand based on its start, end, and control points."""
        # Check if we're in the middle of a group move
        if hasattr(self, 'updating_position') and self.updating_position:
            # Only update the side lines without modifying control points
            self.update_side_line()
            return
            
        # Maintain knot connections - ensure connected endpoints stay synchronized
        self.maintain_knot_connections()

        # Store original control points if they exist
        original_cp1 = getattr(self, 'control_point1', None)
        original_cp2 = getattr(self, 'control_point2', None)
        original_cp_center = getattr(self, 'control_point_center', None)
        original_cp_center_locked = getattr(self, 'control_point_center_locked', False)

        # Calculate the default center position (midpoint between control points 1 and 2)
        default_center = QPointF(
            (self.control_point1.x() + self.control_point2.x()) / 2,
            (self.control_point1.y() + self.control_point2.y()) / 2
        )
        
        # Check if the center point is at its default position
        if hasattr(self, 'control_point_center_locked') and self.control_point_center_locked:
            # Calculate distance between current center and default center
            dx = self.control_point_center.x() - default_center.x()
            dy = self.control_point_center.y() - default_center.y()
            distance = math.sqrt(dx*dx + dy*dy)
            
            # If the center point is very close to its default position, unlock it
            if distance < 0.5:  # Within half a pixel
                self.control_point_center_locked = False

        # Only recalculate control_point_center if it's not locked (not manually positioned)
        if not hasattr(self, 'control_point_center_locked') or not self.control_point_center_locked:
            # Recalculate the center control point
            self.control_point_center = default_center
        
        # Restore original control points if they were manually positioned and modified
        if original_cp1 and original_cp2 and original_cp_center:
            # Detect if we're setting transparent circle which would maintain locked state
            maintain_control_points = (hasattr(self, '_setting_circle_transparency') and 
                                      getattr(self, '_setting_circle_transparency', False))
            
            # If we're explicitly setting transparency, restore the original control points
            if maintain_control_points:
                self.control_point1 = original_cp1
                self.control_point2 = original_cp2
                self.control_point_center = original_cp_center
                self.control_point_center_locked = original_cp_center_locked

        # Store the current path
        self._path = self.get_path()
        
        # Update side lines
        self.update_side_line()

    def draw_arrow_shaft_with_pattern(self, painter, shaft_path, shaft_color, line_width):
        """Draw arrow shaft with optional pattern (stripes or dots)."""
        shaft_style = getattr(self, 'arrow_shaft_style', 'solid')

        # Always draw the base shaft as a solid line first
        base_pen = QPen(shaft_color, line_width)
        base_pen.setCapStyle(Qt.FlatCap)  # Flat caps on both ends
        base_pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(base_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(shaft_path)

        if shaft_style == 'tiles':
            # Tiles pattern using a tiled brush to guarantee full coverage inside the stroke
            painter.save()

            # Build stroke shape to paint inside
            stroker = QPainterPathStroker()
            stroker.setWidth(line_width)
            stroker.setCapStyle(Qt.FlatCap)
            stroker.setJoinStyle(Qt.RoundJoin)
            stroke_path = stroker.createStroke(shaft_path)

            # Create a diagonal tiles pixmap tile
            from PyQt5.QtGui import QPixmap
            tile_size = 12
            pixmap = QPixmap(tile_size, tile_size)
            pixmap.fill(Qt.transparent)
            tile_painter = QPainter(pixmap)
            stripe_color = QColor(255, 255, 255, 80)
            stripe_pen = QPen(stripe_color, 3)
            stripe_pen.setCapStyle(Qt.FlatCap)
            tile_painter.setPen(stripe_pen)
            # Draw two diagonals to ensure seamless tiling
            tile_painter.drawLine(0, tile_size, tile_size, 0)
            tile_painter.drawLine(-tile_size//2, tile_size, tile_size//2, 0)
            tile_painter.end()

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(pixmap))
            painter.drawPath(stroke_path)
            painter.restore()


        elif shaft_style == 'stripes':
            # Alternating brighter/darker diagonal stripes using a tiled brush
            painter.save()

            # Build stroke shape to paint inside
            stroker = QPainterPathStroker()
            stroker.setWidth(line_width)
            stroker.setCapStyle(Qt.FlatCap)
            stroker.setJoinStyle(Qt.RoundJoin)
            stroke_path = stroker.createStroke(shaft_path)

            from PyQt5.QtGui import QPixmap
            # Compact, thin slashes: tighter spacing and slimmer strokes
            stripe_width = max(2, min(6, int(line_width * 0.22)))
            spacing = max(int(stripe_width * 1.6), 5)  # closer distance for more /// density
            tile_size = spacing * 2  # guarantee perfect tiling period
            pixmap = QPixmap(tile_size, tile_size)
            pixmap.fill(Qt.transparent)
            tile_painter = QPainter(pixmap)
            tile_painter.setRenderHint(QPainter.Antialiasing, True)

            # Two pens: brighter (white) and darker (black) overlays
            bright_pen = QPen(QColor(255, 255, 255, 80), stripe_width)
            dark_pen = QPen(QColor(0, 0, 0, 80), stripe_width)
            bright_pen.setCapStyle(Qt.FlatCap)
            dark_pen.setCapStyle(Qt.FlatCap)

            # Draw bright lines (every 2*spacing so alternating with dark)
            tile_painter.setPen(bright_pen)
            margin = stripe_width
            for i in range(-tile_size - margin, tile_size * 2 + margin, spacing * 2):
                tile_painter.drawLine(QPointF(i - margin, tile_size + margin), QPointF(i + tile_size + margin, -margin))

            # Draw dark lines offset by half spacing
            tile_painter.setPen(dark_pen)
            half = spacing
            for i in range(-tile_size + half - margin, tile_size * 2 + half + margin, spacing * 2):
                tile_painter.drawLine(QPointF(i - margin, tile_size + margin), QPointF(i + tile_size + margin, -margin))

            tile_painter.end()

            painter.setPen(Qt.NoPen)
            brush = QBrush(pixmap)
            painter.setBrushOrigin(0, 0)
            painter.setBrush(brush)
            painter.drawPath(stroke_path)
            painter.restore()

        elif shaft_style == 'dots':
            # Dots pattern using a tiled brush to guarantee full coverage inside the stroke
            painter.save()

            # Build stroke shape to paint inside
            stroker = QPainterPathStroker()
            stroker.setWidth(line_width)
            stroker.setCapStyle(Qt.FlatCap)
            stroker.setJoinStyle(Qt.RoundJoin)
            stroke_path = stroker.createStroke(shaft_path)

            # Create a dot pixmap tile
            from PyQt5.QtGui import QPixmap
            tile_size = 12
            pixmap = QPixmap(tile_size, tile_size)
            pixmap.fill(Qt.transparent)
            tile_painter = QPainter(pixmap)
            dot_color = QColor(255, 255, 255, 80)
            tile_painter.setPen(Qt.NoPen)
            tile_painter.setBrush(dot_color)
            radius = 2
            # Hex-like staggered dots for nicer pattern
            for x in range(2, tile_size, 6):
                for y in range(2, tile_size, 6):
                    offset = 3 if ((y // 6) % 2 == 1) else 0
                    tile_painter.drawEllipse(x + offset, y, radius*2, radius*2)
            tile_painter.end()

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(pixmap))
            painter.drawPath(stroke_path)
            painter.restore()

    def apply_arrow_texture_brush(self, painter, fill_color):
        """Apply texture to arrow based on arrow_texture setting."""
        from PyQt5.QtGui import QBrush, QPixmap

        arrow_texture = getattr(self, 'arrow_texture', 'none')
        if arrow_texture == 'stripes':
            # Create a striped brush pattern
            pixmap = QPixmap(10, 10)
            pixmap.fill(Qt.transparent)
            pixmap_painter = QPainter(pixmap)
            pixmap_painter.setPen(QPen(fill_color, 2))
            for i in range(0, 10, 3):
                pixmap_painter.drawLine(i, 0, i, 10)
            pixmap_painter.end()
            painter.setBrush(QBrush(pixmap))
        elif arrow_texture == 'dots':
            # Create a dotted brush pattern
            pixmap = QPixmap(10, 10)
            pixmap.fill(Qt.transparent)
            pixmap_painter = QPainter(pixmap)
            pixmap_painter.setPen(Qt.NoPen)
            pixmap_painter.setBrush(fill_color)
            for x in range(2, 10, 4):
                for y in range(2, 10, 4):
                    pixmap_painter.drawEllipse(x-1, y-1, 2, 2)
            pixmap_painter.end()
            painter.setBrush(QBrush(pixmap))
        elif arrow_texture == 'crosshatch':
            # Create a crosshatch pattern
            pixmap = QPixmap(10, 10)
            pixmap.fill(Qt.transparent)
            pixmap_painter = QPainter(pixmap)
            pixmap_painter.setPen(QPen(fill_color, 1))
            for i in range(0, 10, 3):
                pixmap_painter.drawLine(i, 0, i, 10)
                pixmap_painter.drawLine(0, i, 10, i)
            pixmap_painter.end()
            painter.setBrush(QBrush(pixmap))
        else:
            # No texture, solid fill
            painter.setBrush(fill_color)

    def get_arrow_path(self, for_receiving_shadows=False):
        """Get the arrow path (shaft + head) for shadow rendering.

        Args:
            for_receiving_shadows: If True, returns arrow path regardless of arrow_casts_shadow setting
                                 (for receiving shadows ON the arrow)
        """
        if not getattr(self, 'full_arrow_visible', False):
            return QPainterPath()

        # Only check arrow_casts_shadow if not for receiving shadows
        if not for_receiving_shadows and not getattr(self, 'arrow_casts_shadow', False):
            return QPainterPath()

        arrow_path = QPainterPath()

        try:
            # Get the shaft path (entire strand path)
            shaft_path = self.get_path()

            # Create stroked version of shaft with arrow line width
            full_arrow_shaft_line_width = getattr(self.canvas, 'arrow_line_width', 10)
            stroker = QPainterPathStroker()
            stroker.setWidth(full_arrow_shaft_line_width)
            stroker.setJoinStyle(Qt.MiterJoin)
            stroker.setCapStyle(Qt.FlatCap)
            arrow_path = stroker.createStroke(shaft_path)

            # Add arrow head if visible
            if getattr(self, 'arrow_head_visible', True):
                # Calculate arrow head geometry
                arrow_head_len = getattr(self.canvas, 'arrow_head_length', 20)
                arrow_head_width = getattr(self.canvas, 'arrow_head_width', 10)

                # Calculate the tangent at the endpoint
                tangent_at_end = self.calculate_cubic_tangent(0.999)
                len_at_end = math.hypot(tangent_at_end.x(), tangent_at_end.y())

                if len_at_end > 0:
                    # Unit vector pointing along the curve at the endpoint
                    unit_vector_shaft = QPointF(tangent_at_end.x() / len_at_end, tangent_at_end.y() / len_at_end)

                    # Perpendicular vector to the shaft direction (for arrow width)
                    perp_vector = QPointF(-unit_vector_shaft.y(), unit_vector_shaft.x())

                    # Calculate the two base corners at the endpoint
                    left_point = self.end + perp_vector * (arrow_head_width / 2)
                    right_point = self.end - perp_vector * (arrow_head_width / 2)

                    # Calculate tip position extending outward from the endpoint
                    tip = self.end + unit_vector_shaft * arrow_head_len

                    # Create arrow head polygon path
                    head_path = QPainterPath()
                    head_path.moveTo(tip)
                    head_path.lineTo(left_point)
                    head_path.lineTo(right_point)
                    head_path.closeSubpath()

                    # Unite with arrow shaft
                    arrow_path = arrow_path.united(head_path)
        except Exception as e:
            pass
            return QPainterPath()

        return arrow_path

    def get_arrow_shadow_path(self):
        """Get the arrow path (shaft + head) for shadow rendering when arrow_casts_shadow is enabled."""
        if not getattr(self, 'full_arrow_visible', False) or not getattr(self, 'arrow_casts_shadow', False):
            return QPainterPath()

        arrow_path = QPainterPath()

        try:
            # Get the shaft path (entire strand path)
            shaft_path = self.get_path()

            # Create stroked version of shaft with arrow line width
            full_arrow_shaft_line_width = getattr(self.canvas, 'arrow_line_width', 10)
            stroker = QPainterPathStroker()
            stroker.setWidth(full_arrow_shaft_line_width)
            stroker.setJoinStyle(Qt.MiterJoin)
            stroker.setCapStyle(Qt.FlatCap)
            arrow_path = stroker.createStroke(shaft_path)

            # Add arrow head if visible
            if getattr(self, 'arrow_head_visible', True):
                # Calculate arrow head geometry
                arrow_head_len = getattr(self.canvas, 'arrow_head_length', 20)
                arrow_head_width = getattr(self.canvas, 'arrow_head_width', 10)

                # Calculate the tangent at the endpoint
                tangent_at_end = self.calculate_cubic_tangent(0.999)
                len_at_end = math.hypot(tangent_at_end.x(), tangent_at_end.y())

                if len_at_end > 0:
                    # Unit vector pointing along the curve at the endpoint
                    unit_vector_shaft = QPointF(tangent_at_end.x() / len_at_end, tangent_at_end.y() / len_at_end)

                    # Perpendicular vector to the shaft direction (for arrow width)
                    perp_vector = QPointF(-unit_vector_shaft.y(), unit_vector_shaft.x())

                    # Calculate the two base corners at the endpoint
                    left_point = self.end + perp_vector * (arrow_head_width / 2)
                    right_point = self.end - perp_vector * (arrow_head_width / 2)

                    # Calculate tip position extending outward from the endpoint
                    tip = self.end + unit_vector_shaft * arrow_head_len

                    # Create arrow head polygon path
                    head_path = QPainterPath()
                    head_path.moveTo(tip)
                    head_path.lineTo(left_point)
                    head_path.lineTo(right_point)
                    head_path.closeSubpath()

                    # Unite with arrow shaft
                    arrow_path = arrow_path.united(head_path)
        except Exception as e:
            pass
            return QPainterPath()

        return arrow_path

    def get_shadow_path(self):
        """Get the path with extensions for shadow rendering, extending 10px beyond start/end."""
        path = QPainterPath()

        # Check if this is a strand with transparent start or end circles
        is_transparent_start = False
        is_transparent_end = False
        
        # Check for transparent start circle
        start_circle_color = self.start_circle_stroke_color
        if start_circle_color and start_circle_color.alpha() == 0:
            is_transparent_start = True
            pass
        
        # Check for transparent end circle
        end_circle_color = self.end_circle_stroke_color
        if end_circle_color and end_circle_color.alpha() == 0:
            is_transparent_end = True
            pass

        if is_transparent_start:
            # If transparent start circle on AttachedStrand, don't extend
            extended_start = self.start
        else:
            # Original extension logic for other strands or non-transparent attached strands
            # Calculate vectors for direction at start and end
            # For start point, use the tangent direction from the start towards control_point1
            start_vector = self.control_point1 - self.start
            if start_vector.manhattanLength() > 0:
                # Normalize and extend by exactly 10 pixels using Euclidean length
                start_vector_length = math.sqrt(start_vector.x()**2 + start_vector.y()**2)
                # Avoid division by zero if length is extremely small
                if start_vector_length > 1e-6:
                    normalized_start_vector = start_vector / start_vector_length
                    extended_start = self.start - (normalized_start_vector * 10)
                else:
                    extended_start = QPointF(self.start.x() - 0, self.start.y()) # Default horizontal
            else:
                # Fallback if control point is at same position as start
                # Use direction from start to end instead
                fallback_vector = self.end - self.start
                if fallback_vector.manhattanLength() > 0:
                    fallback_length = math.sqrt(fallback_vector.x()**2 + fallback_vector.y()**2)
                    # Avoid division by zero if length is extremely small
                    if fallback_length > 1e-6:
                        normalized_fallback = fallback_vector / fallback_length
                        extended_start = self.start - (normalized_fallback * 10)
                    else:
                         extended_start = QPointF(self.start.x() - 0, self.start.y()) # Default horizontal
                else:
                    # If start and end are the same, use a default horizontal direction
                    extended_start = QPointF(self.start.x() - 0, self.start.y())

        # For end point, check if transparent end circle should skip shadow extension
        if is_transparent_end:
            # If transparent end circle, don't extend
            extended_end = self.end
        else:
            # Original extension logic for non-transparent end
            # For end point, use the tangent direction from control_point2 towards the end
            end_vector = self.end - self.control_point2
            if end_vector.manhattanLength() > 0:
                # Normalize and extend by exactly 10 pixels using Euclidean length
                end_vector_length = math.sqrt(end_vector.x()**2 + end_vector.y()**2)
                normalized_end_vector = end_vector / end_vector_length
                extended_end = self.end + (normalized_end_vector * 10)
            else:
                # Fallback if control point is at same position as end
                # Use direction from end to start instead
                fallback_vector = self.end - self.start
                if fallback_vector.manhattanLength() > 0:
                    fallback_length = math.sqrt(fallback_vector.x()**2 + fallback_vector.y()**2)
                    normalized_fallback = fallback_vector / fallback_length
                    extended_end = self.end + (normalized_fallback * 10)
                else:
                    # If start and end are the same, use a default horizontal direction
                    extended_end = QPointF(self.end.x() + 0, self.end.y())
            
        # Create the path with the extended points
        path.moveTo(self.start)

        # Only use the third control point if:
        # 1. The feature is enabled AND
        # 2. The control_point_center has been manually positioned
        if (hasattr(self, 'canvas') and self.canvas and 
            hasattr(self.canvas, 'enable_third_control_point') and 
            self.canvas.enable_third_control_point and
            hasattr(self, 'control_point_center_locked') and 
            self.control_point_center_locked):
            
            # Create a smooth spline incorporating all control points
            # Use the user's control points to guide the curve shape
            
            # Extract the key points we're working with
            p0 = self.start
            p1 = self.control_point1
            p2 = self.control_point_center
            p3 = self.control_point2
            p4 = self.end
            
            # For a smooth curve through 5 points, calculate intermediate control points
            # that ensure C1 continuity (smooth tangents) at the center point
            
            # Calculate tangent at the center point for smooth transition
            # This is the average direction between incoming and outgoing segments
            in_vector = p2 - p1
            out_vector = p3 - p2
            
            # Normalize and average for center tangent
            def normalize_vector(v):
                length = math.sqrt(v.x() * v.x() + v.y() * v.y())
                if length < 0.001:
                    return QPointF(0, 0)
                return QPointF(v.x() / length, v.y() / length)
            
            in_norm = normalize_vector(in_vector)
            out_norm = normalize_vector(out_vector)
            center_tangent = QPointF(
                (in_norm.x() + out_norm.x()) * 0.5,
                (in_norm.y() + out_norm.y()) * 0.5
            )
            
            # Calculate distances for scaling
            dist1 = math.sqrt((p1.x() - p0.x())**2 + (p1.y() - p0.y())**2)
            dist2 = math.sqrt((p2.x() - p1.x())**2 + (p2.y() - p1.y())**2)
            dist3 = math.sqrt((p3.x() - p2.x())**2 + (p3.y() - p2.y())**2)
            dist4 = math.sqrt((p4.x() - p3.x())**2 + (p4.y() - p3.y())**2)
            
            # Get curvature parameters to influence the curve
            base_fraction = getattr(self, 'control_point_base_fraction', 0.4)
            dist_multiplier = getattr(self, 'distance_multiplier', 1.2)
            exponent = getattr(self, 'curve_response_exponent', 1.5)
            
            # Each parameter has 100% independent influence on the curve
            # Use values directly from spinboxes without normalization
            # base_fraction range: 0.25-3.0 (use directly for influence)
            # Map to control point influence fractions
            frac1 = min(0.1 + (base_fraction * 0.3), 8.33)  # Direct scaling
            frac2 = min(0.05 + (base_fraction * 0.15), 3.77)  # Direct scaling
            
            # Distance boost: 1.0-10.0 range (use full range)
            # Apply distance multiplier directly
            frac1 = min(frac1 * dist_multiplier, 8.33)
            frac2 = min(frac2 * dist_multiplier, 8.33)
            
            # Apply exponent to shape the curve (1.0-3.0 range)
            # Direct power application for curve shaping
            if exponent != 1.0:
                # Direct exponential shaping: higher values = sharper curves
                frac1 = pow(frac1, 1.0 / exponent)  # Inverse power for more intuitive control
                frac2 = pow(frac2, 1.0 / exponent)
            
            # Apply bias control weights if enabled
            bias_triangle = 0.5  # Default neutral bias
            bias_circle = 0.5    # Default neutral bias
            
            if (hasattr(self, 'bias_control') and self.bias_control and
                hasattr(self.canvas, 'enable_curvature_bias_control') and 
                self.canvas.enable_curvature_bias_control):
                # Get the current bias values
                bias_triangle = self.bias_control.triangle_bias
                bias_circle = self.bias_control.circle_bias
            
            # Apply bias to control point positions
            # Bias affects how much influence each control point has on the curve
            # Triangle bias affects the first half, circle bias affects the second half
            
            # Modify frac1 and frac2 based on bias values
            # Bias range is 0.0 to 1.0, where 0.5 is neutral
            # Scale the fractions based on bias (0.0 = less influence, 1.0 = more influence)
            frac1_biased = frac1 * (0.5 + bias_triangle)  # Scale from 0.5x to 1.5x
            frac2_biased = frac2 * (0.5 + bias_circle)     # Scale from 0.5x to 1.5x
            
            # Create control points for smooth bezier segments
            # These ensure the curve passes smoothly through all 5 control points
            cp1 = QPointF(
                p0.x() + (p1.x() - p0.x()) * frac1_biased,
                p0.y() + (p1.y() - p0.y()) * frac1_biased
            )
            cp2 = QPointF(
                p2.x() - center_tangent.x() * dist2 * frac2 * (0.5 + bias_triangle),
                p2.y() - center_tangent.y() * dist2 * frac2 * (0.5 + bias_triangle)
            )
            cp3 = QPointF(
                p2.x() + center_tangent.x() * dist3 * frac2 * (0.5 + bias_circle),
                p2.y() + center_tangent.y() * dist3 * frac2 * (0.5 + bias_circle)
            )
            cp4 = QPointF(
                p4.x() + (p3.x() - p4.x()) * frac2_biased,
                p4.y() + (p3.y() - p4.y()) * frac2_biased
            )
            
            # First segment: start to center
            path.cubicTo(cp1, cp2, p2)
            
            # Second segment: center to end
            path.cubicTo(cp3, cp4, p4)
        else:
            # Standard cubic Bezier curve when third control point is disabled or not manually positioned
            # Match the logic from get_path() - check if control points are at default positions
            
            # Check if control points are at their default positions (both at start - not moved)
            cp1_at_start = (abs(self.control_point1.x() - self.start.x()) < 1.0 and 
                           abs(self.control_point1.y() - self.start.y()) < 1.0)
            cp2_at_start = (abs(self.control_point2.x() - self.start.x()) < 1.0 and 
                           abs(self.control_point2.y() - self.start.y()) < 1.0)
            
            if cp1_at_start and cp2_at_start:
                # Control points haven't been moved (both still at start) - draw a straight line
                path.lineTo(self.end)
            else:
                # Control points have been moved - treat as if there's a virtual 3rd control point
                # at the center between the two control points
                
                # Extract the key points
                p0 = self.start
                p1 = self.control_point1
                # Virtual center point between the two control points
                p2 = QPointF(
                    (self.control_point1.x() + self.control_point2.x()) / 2,
                    (self.control_point1.y() + self.control_point2.y()) / 2
                )
                p3 = self.control_point2
                p4 = self.end
                
                # Use the same logic as 3rd control point
                # Calculate tangent at the center point for smooth transition
                in_vector = p2 - p1
                out_vector = p3 - p2
                
                # Normalize and average for center tangent
                def normalize_vector(v):
                    length = math.sqrt(v.x() * v.x() + v.y() * v.y())
                    if length < 0.001:
                        return QPointF(0, 0)
                    return QPointF(v.x() / length, v.y() / length)
                
                in_norm = normalize_vector(in_vector)
                out_norm = normalize_vector(out_vector)
                center_tangent = QPointF(
                    (in_norm.x() + out_norm.x()) * 0.5,
                    (in_norm.y() + out_norm.y()) * 0.5
                )
                
                # Calculate distances for scaling
                dist1 = math.sqrt((p1.x() - p0.x())**2 + (p1.y() - p0.y())**2)
                dist2 = math.sqrt((p2.x() - p1.x())**2 + (p2.y() - p1.y())**2)
                dist3 = math.sqrt((p3.x() - p2.x())**2 + (p3.y() - p2.y())**2)
                dist4 = math.sqrt((p4.x() - p3.x())**2 + (p4.y() - p3.y())**2)
                
                # Get curvature parameters to influence the curve
                base_fraction = getattr(self, 'control_point_base_fraction', 0.4)
                dist_multiplier = getattr(self, 'distance_multiplier', 1.2)
                exponent = getattr(self, 'curve_response_exponent', 1.5)
                
                
                # Each parameter has 100% independent influence on the curve
                # Use values directly from spinboxes
                # base_fraction range: 0.25-10.0 (use directly)
                base_frac1 = min(0.1 + (base_fraction * 0.2), 2.34)  # Direct scaling
                base_frac2 = min(0.05 + (base_fraction * 0.1), 1.17)  # Direct scaling
                
                # Apply distance multiplier (1.0-10.0) directly
                frac1 = min(base_frac1 * dist_multiplier, 8.33)
                frac2 = min(base_frac2 * dist_multiplier, 8.33)
                
                # Apply exponent (1.0-3.0) to shape the curve
                if exponent != 1.0:
                    frac1 = pow(frac1, 1.0 / exponent)
                    frac2 = pow(frac2, 1.0 / exponent)
                
                # Create control points for smooth bezier segments
                # These ensure the curve passes smoothly through all 5 control points
                cp1 = QPointF(
                    p0.x() + (p1.x() - p0.x()) * frac1,
                    p0.y() + (p1.y() - p0.y()) * frac1
                )
                cp2 = QPointF(
                    p2.x() - center_tangent.x() * dist2 * frac2,
                    p2.y() - center_tangent.y() * dist2 * frac2
                )
                cp3 = QPointF(
                    p2.x() + center_tangent.x() * dist3 * frac2,
                    p2.y() + center_tangent.y() * dist3 * frac2
                )
                cp4 = QPointF(
                    p4.x() + (p3.x() - p4.x()) * frac2,
                    p4.y() + (p3.y() - p4.y()) * frac2
                )
                
                # First segment: start to center
                path.cubicTo(cp1, cp2, p2)
                
                # Second segment: center to end
                path.cubicTo(cp3, cp4, p4)
        
        # Path already ends at the correct point
            
        return path

    def get_path(self):
        """Get the path representing the strand as a cubic Bézier curve."""
        path = QPainterPath()
        path.moveTo(self.start)
        # Calculate the center point between two points

        
        # Only use the third control point if:
        # 1. The feature is enabled AND
        # 2. The control_point_center has been manually positioned
        if (hasattr(self, 'canvas') and self.canvas and 
            hasattr(self.canvas, 'enable_third_control_point') and 
            self.canvas.enable_third_control_point and
            hasattr(self, 'control_point_center_locked') and 
            self.control_point_center_locked):
            
            # Create a smooth spline incorporating all control points
            # Use the user's control points to guide the curve shape
            
            # Extract the key points we're working with
            p0 = self.start
            p1 = self.control_point1
            p2 = self.control_point_center
            p3 = self.control_point2
            p4 = self.end
            
            # For a smooth curve through 5 points, calculate intermediate control points
            # that ensure C1 continuity (smooth tangents) at the center point
            
            # Calculate tangent at the center point for smooth transition
            # This is the average direction between incoming and outgoing segments
            in_vector = p2 - p1
            out_vector = p3 - p2
            
            # Normalize and average for center tangent
            def normalize_vector(v):
                length = math.sqrt(v.x() * v.x() + v.y() * v.y())
                if length < 0.001:
                    return QPointF(0, 0)
                return QPointF(v.x() / length, v.y() / length)
            
            in_norm = normalize_vector(in_vector)
            out_norm = normalize_vector(out_vector)
            center_tangent = QPointF(
                (in_norm.x() + out_norm.x()) * 0.5,
                (in_norm.y() + out_norm.y()) * 0.5
            )
            
            # Calculate distances for scaling
            dist1 = math.sqrt((p1.x() - p0.x())**2 + (p1.y() - p0.y())**2)
            dist2 = math.sqrt((p2.x() - p1.x())**2 + (p2.y() - p1.y())**2)
            dist3 = math.sqrt((p3.x() - p2.x())**2 + (p3.y() - p2.y())**2)
            dist4 = math.sqrt((p4.x() - p3.x())**2 + (p4.y() - p3.y())**2)
            
            # Get curvature parameters to influence the curve
            base_fraction = getattr(self, 'control_point_base_fraction', 0.4)
            dist_multiplier = getattr(self, 'distance_multiplier', 1.2)
            exponent = getattr(self, 'curve_response_exponent', 1.5)
            
            # Each parameter has 100% independent influence on the curve
            # Use values directly from spinboxes without normalization
            # base_fraction range: 0.25-3.0 (use directly for influence)
            # Map to control point influence fractions
            frac1 = min(0.1 + (base_fraction * 0.3), 8.33)  # Direct scaling
            frac2 = min(0.05 + (base_fraction * 0.15), 3.77)  # Direct scaling
            
            # Distance boost: 1.0-10.0 range (use full range)
            # Apply distance multiplier directly
            frac1 = min(frac1 * dist_multiplier, 8.33)
            frac2 = min(frac2 * dist_multiplier, 8.33)
            
            # Apply exponent to shape the curve (1.0-3.0 range)
            # Direct power application for curve shaping
            if exponent != 1.0:
                # Direct exponential shaping: higher values = sharper curves
                frac1 = pow(frac1, 1.0 / exponent)  # Inverse power for more intuitive control
                frac2 = pow(frac2, 1.0 / exponent)
            
            # Apply bias control weights if enabled
            bias_triangle = 0.5  # Default neutral bias
            bias_circle = 0.5    # Default neutral bias
            
            if (hasattr(self, 'bias_control') and self.bias_control and
                hasattr(self.canvas, 'enable_curvature_bias_control') and 
                self.canvas.enable_curvature_bias_control):
                # Get the current bias values
                bias_triangle = self.bias_control.triangle_bias
                bias_circle = self.bias_control.circle_bias
            
            # Apply bias to control point positions
            # Bias affects how much influence each control point has on the curve
            # Triangle bias affects the first half, circle bias affects the second half
            
            # Modify frac1 and frac2 based on bias values
            # Bias range is 0.0 to 1.0, where 0.5 is neutral
            # Scale the fractions based on bias (0.0 = less influence, 1.0 = more influence)
            frac1_biased = frac1 * (0.5 + bias_triangle)  # Scale from 0.5x to 1.5x
            frac2_biased = frac2 * (0.5 + bias_circle)     # Scale from 0.5x to 1.5x
            
            # Create control points for smooth bezier segments
            # These ensure the curve passes smoothly through all 5 control points
            cp1 = QPointF(
                p0.x() + (p1.x() - p0.x()) * frac1_biased,
                p0.y() + (p1.y() - p0.y()) * frac1_biased
            )
            cp2 = QPointF(
                p2.x() - center_tangent.x() * dist2 * frac2 * (0.5 + bias_triangle),
                p2.y() - center_tangent.y() * dist2 * frac2 * (0.5 + bias_triangle)
            )
            cp3 = QPointF(
                p2.x() + center_tangent.x() * dist3 * frac2 * (0.5 + bias_circle),
                p2.y() + center_tangent.y() * dist3 * frac2 * (0.5 + bias_circle)
            )
            cp4 = QPointF(
                p4.x() + (p3.x() - p4.x()) * frac2_biased,
                p4.y() + (p3.y() - p4.y()) * frac2_biased
            )
            
            # First segment: start to center
            path.cubicTo(cp1, cp2, p2)
            
            # Second segment: center to end
            path.cubicTo(cp3, cp4, p4)
        else:
            # Standard cubic Bezier curve when third control point is disabled or not manually positioned
            
            # Check if control points are at their default positions (both at start - not moved)
            cp1_at_start = (abs(self.control_point1.x() - self.start.x()) < 1.0 and 
                           abs(self.control_point1.y() - self.start.y()) < 1.0)
            cp2_at_start = (abs(self.control_point2.x() - self.start.x()) < 1.0 and 
                           abs(self.control_point2.y() - self.start.y()) < 1.0)
            
            if cp1_at_start and cp2_at_start:
                # Control points haven't been moved (both still at start) - draw a straight line
                path.lineTo(self.end)
            else:
                # Control points have been moved - treat as if there's a virtual 3rd control point
                # at the center between the two control points
                
                # Extract the key points
                p0 = self.start
                p1 = self.control_point1
                # Virtual center point between the two control points
                p2 = QPointF(
                    (self.control_point1.x() + self.control_point2.x()) / 2,
                    (self.control_point1.y() + self.control_point2.y()) / 2
                )
                p3 = self.control_point2
                p4 = self.end
                
                # Use the same logic as 3rd control point
                # Calculate tangent at the center point for smooth transition
                in_vector = p2 - p1
                out_vector = p3 - p2
                
                # Normalize and average for center tangent
                def normalize_vector(v):
                    length = math.sqrt(v.x() * v.x() + v.y() * v.y())
                    if length < 0.001:
                        return QPointF(0, 0)
                    return QPointF(v.x() / length, v.y() / length)
                
                in_norm = normalize_vector(in_vector)
                out_norm = normalize_vector(out_vector)
                center_tangent = QPointF(
                    (in_norm.x() + out_norm.x()) * 0.5,
                    (in_norm.y() + out_norm.y()) * 0.5
                )
                
                # Calculate distances for scaling
                dist1 = math.sqrt((p1.x() - p0.x())**2 + (p1.y() - p0.y())**2)
                dist2 = math.sqrt((p2.x() - p1.x())**2 + (p2.y() - p1.y())**2)
                dist3 = math.sqrt((p3.x() - p2.x())**2 + (p3.y() - p2.y())**2)
                dist4 = math.sqrt((p4.x() - p3.x())**2 + (p4.y() - p3.y())**2)
                
                # Get curvature parameters to influence the curve
                base_fraction = getattr(self, 'control_point_base_fraction', 0.4)
                dist_multiplier = getattr(self, 'distance_multiplier', 1.2)
                exponent = getattr(self, 'curve_response_exponent', 1.5)
                
                
                # Each parameter has 100% independent influence on the curve
                # Use values directly from spinboxes
                # base_fraction range: 0.25-10.0 (use directly)
                base_frac1 = min(0.1 + (base_fraction * 0.2), 2.34)  # Direct scaling
                base_frac2 = min(0.05 + (base_fraction * 0.1), 1.17)  # Direct scaling
                
                # Apply distance multiplier (1.0-10.0) directly
                frac1 = min(base_frac1 * dist_multiplier, 8.33)
                frac2 = min(base_frac2 * dist_multiplier, 8.33)
                
                # Apply exponent (1.0-3.0) to shape the curve
                if exponent != 1.0:
                    frac1 = pow(frac1, 1.0 / exponent)
                    frac2 = pow(frac2, 1.0 / exponent)
                
                # Create control points for smooth bezier segments
                # These ensure the curve passes smoothly through all 5 control points
                cp1 = QPointF(
                    p0.x() + (p1.x() - p0.x()) * frac1,
                    p0.y() + (p1.y() - p0.y()) * frac1
                )
                cp2 = QPointF(
                    p2.x() - center_tangent.x() * dist2 * frac2,
                    p2.y() - center_tangent.y() * dist2 * frac2
                )
                cp3 = QPointF(
                    p2.x() + center_tangent.x() * dist3 * frac2,
                    p2.y() + center_tangent.y() * dist3 * frac2
                )
                cp4 = QPointF(
                    p4.x() + (p3.x() - p4.x()) * frac2,
                    p4.y() + (p3.y() - p4.y()) * frac2
                )
                
                # First segment: start to center
                path.cubicTo(cp1, cp2, p2)
                
                # Second segment: center to end
                path.cubicTo(cp3, cp4, p4)
        
        return path

    def get_selection_path(self):
        """Get the selection path for the entire strand body."""
        # Use a wider path for easier selection, adjusted for zoom level
        base_width = max(self.width, 20)  # Minimum width for clickability
        
        # Adjust selection width based on zoom level to maintain consistent click targets
        if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'zoom_factor'):
            zoom_factor = self.canvas.zoom_factor
            selection_width = base_width / zoom_factor
        else:
            selection_width = base_width
            
        return self.get_stroked_path(selection_width)

    def get_stroked_path(self, width: float) -> QPainterPath:
        """
        Get the path representing the strand as a stroked path with the given width.

        Args:
            width (float): The width of the strand.

        Returns:
            QPainterPath: The stroked path representing the strand with the specified width.
        """
        original_path = self.get_path()
        stroker = QPainterPathStroker()
        stroker.setWidth(width)
        stroked_path = stroker.createStroke(original_path)
        return stroked_path



    def boundingRect(self):
        """Return the bounding rectangle of the strand."""
        path = self.get_path()

        # Create a stroker for the stroke path with squared ends
        stroke_stroker = QPainterPathStroker()
        stroke_stroker.setWidth(self.width + self.stroke_width * 2)
        stroke_stroker.setJoinStyle(Qt.MiterJoin)
        stroke_stroker.setCapStyle(Qt.FlatCap)
        stroke_path = stroke_stroker.createStroke(path)

        # Start with the bounding rect of the stroke path
        bounding_rect = stroke_path.boundingRect()

        # Include side lines in the bounding rect if they exist
        if hasattr(self, 'start_line_start') and hasattr(self, 'start_line_end'):
            start_line_rect = QRectF(self.start_line_start, self.start_line_end)
            bounding_rect = bounding_rect.united(start_line_rect)

        if hasattr(self, 'end_line_start') and hasattr(self, 'end_line_end'):
            end_line_rect = QRectF(self.end_line_start, self.end_line_end)
            bounding_rect = bounding_rect.united(end_line_rect)

        # Return the combined bounding rectangle
        return bounding_rect

    def point_at(self, t):
        """Compute a point on the Bézier curve at parameter t."""
        # If third control point is enabled, use a composite curve with two segments
        if (hasattr(self, 'canvas') and self.canvas and 
            hasattr(self.canvas, 'enable_third_control_point') and 
            self.canvas.enable_third_control_point and
            hasattr(self, 'control_point_center_locked') and 
            self.control_point_center_locked):
            
            # Use the same sophisticated curve construction as get_path
            p0 = self.start
            p1 = self.control_point1
            p2 = self.control_point_center
            p3 = self.control_point2
            p4 = self.end
            
            # Calculate tangents (same as in get_path)
            start_tangent = QPointF(p1.x() - p0.x(), p1.y() - p0.y())
            in_tangent = QPointF(p2.x() - p1.x(), p2.y() - p1.y())
            out_tangent = QPointF(p3.x() - p2.x(), p3.y() - p2.y())
            
            def normalize_vector(v):
                length = math.sqrt(v.x() * v.x() + v.y() * v.y())
                if length < 0.001:
                    return QPointF(0, 0)
                return QPointF(v.x() / length, v.y() / length)
            
            start_tangent_normalized = normalize_vector(start_tangent)
            in_tangent_normalized = normalize_vector(in_tangent)
            out_tangent_normalized = normalize_vector(out_tangent)
            
            center_tangent = QPointF(
                0.5 * in_tangent_normalized.x() + 0.5 * out_tangent_normalized.x(), 
                0.5 * in_tangent_normalized.y() + 0.5 * out_tangent_normalized.y()
            )
            center_tangent_normalized = normalize_vector(center_tangent)
            
            end_tangent = QPointF(p4.x() - p3.x(), p4.y() - p3.y())
            end_tangent_normalized = normalize_vector(end_tangent)
            
            # Calculate distances
            dist_p0_p1 = math.sqrt((p1.x() - p0.x())**2 + (p1.y() - p0.y())**2)
            dist_p1_p2 = math.sqrt((p2.x() - p1.x())**2 + (p2.y() - p1.y())**2)
            dist_p2_p3 = math.sqrt((p3.x() - p2.x())**2 + (p3.y() - p2.y())**2)
            dist_p3_p4 = math.sqrt((p4.x() - p3.x())**2 + (p4.y() - p3.y())**2)
            
            # Get control point influence parameters
            exponent = getattr(self, 'curve_response_exponent', 1.5)
            base_fraction = getattr(self, 'control_point_base_fraction', 0.4)
            dist_multiplier = getattr(self, 'distance_multiplier', 1.2)
            
            # Apply distance multiplier and exponential scaling
            boosted_dist_p0_p1 = dist_p0_p1 * dist_multiplier
            boosted_dist_p1_p2 = dist_p1_p2 * dist_multiplier
            boosted_dist_p2_p3 = dist_p2_p3 * dist_multiplier
            boosted_dist_p3_p4 = dist_p3_p4 * dist_multiplier
            
            max_dist = max(boosted_dist_p0_p1, boosted_dist_p1_p2, boosted_dist_p2_p3, boosted_dist_p3_p4, 1.0)
            scaled_dist_p0_p1 = (boosted_dist_p0_p1 / max_dist) ** exponent * boosted_dist_p0_p1
            scaled_dist_p1_p2 = (boosted_dist_p1_p2 / max_dist) ** exponent * boosted_dist_p1_p2
            scaled_dist_p2_p3 = (boosted_dist_p2_p3 / max_dist) ** exponent * boosted_dist_p2_p3
            scaled_dist_p3_p4 = (boosted_dist_p3_p4 / max_dist) ** exponent * boosted_dist_p3_p4
            
            # Calculate intermediate control points with combined influence
            cp1 = p0 + start_tangent_normalized * (scaled_dist_p0_p1 * base_fraction) if start_tangent_normalized.manhattanLength() > 1e-6 else p1
            cp2 = p2 - center_tangent_normalized * (scaled_dist_p1_p2 * base_fraction) if center_tangent_normalized.manhattanLength() > 1e-6 else p1
            cp3 = p2 + center_tangent_normalized * (scaled_dist_p2_p3 * base_fraction) if center_tangent_normalized.manhattanLength() > 1e-6 else p3
            cp4 = p4 - end_tangent_normalized * (scaled_dist_p3_p4 * base_fraction) if end_tangent_normalized.manhattanLength() > 1e-6 else p3
            
            if t <= 0.5:
                # First segment: start to center
                scaled_t = t * 2
                x = (
                    (1 - scaled_t) ** 3 * p0.x() +
                    3 * (1 - scaled_t) ** 2 * scaled_t * cp1.x() +
                    3 * (1 - scaled_t) * scaled_t ** 2 * cp2.x() +
                    scaled_t ** 3 * p2.x()
                )
                y = (
                    (1 - scaled_t) ** 3 * p0.y() +
                    3 * (1 - scaled_t) ** 2 * scaled_t * cp1.y() +
                    3 * (1 - scaled_t) * scaled_t ** 2 * cp2.y() +
                    scaled_t ** 3 * p2.y()
                )
            else:
                # Second segment: center to end
                scaled_t = (t - 0.5) * 2
                x = (
                    (1 - scaled_t) ** 3 * p2.x() +
                    3 * (1 - scaled_t) ** 2 * scaled_t * cp3.x() +
                    3 * (1 - scaled_t) * scaled_t ** 2 * cp4.x() +
                    scaled_t ** 3 * p4.x()
                )
                y = (
                    (1 - scaled_t) ** 3 * p2.y() +
                    3 * (1 - scaled_t) ** 2 * scaled_t * cp3.y() +
                    3 * (1 - scaled_t) * scaled_t ** 2 * cp4.y() +
                    scaled_t ** 3 * p4.y()
                )
            
            return QPointF(x, y)
        else:
            # Standard cubic Bézier with 2 control points
            p0, p1, p2, p3 = self.start, self.control_point1, self.control_point2, self.end

            # Ensure points are valid before calculation
            if p0 is None or p1 is None or p2 is None or p3 is None:
                 pass
                 return QPointF(0, 0) # Or handle error appropriately

            x = (
                (1 - t) ** 3 * p0.x() +
                3 * (1 - t) ** 2 * t * p1.x() +
                3 * (1 - t) * t ** 2 * p2.x() +
                t ** 3 * p3.x()
            )
            y = (
                (1 - t) ** 3 * p0.y() +
                3 * (1 - t) ** 2 * t * p1.y() +
                3 * (1 - t) * t ** 2 * p2.y() +
                t ** 3 * p3.y()
            )
            return QPointF(x, y)

    def calculate_cubic_tangent(self, t):
        """Calculate the tangent vector at a given t value of the Bézier curve."""
        # Check if third control point is enabled and manually positioned
        if (hasattr(self, 'canvas') and self.canvas and 
            hasattr(self.canvas, 'enable_third_control_point') and 
            self.canvas.enable_third_control_point and
            hasattr(self, 'control_point_center_locked') and 
            self.control_point_center_locked):
            
            # Use the same sophisticated curve construction as get_path
            p0 = self.start
            p1 = self.control_point1
            p2 = self.control_point_center
            p3 = self.control_point2
            p4 = self.end
            
            # Calculate tangents (same as in get_path)
            start_tangent = QPointF(p1.x() - p0.x(), p1.y() - p0.y())
            in_tangent = QPointF(p2.x() - p1.x(), p2.y() - p1.y())
            out_tangent = QPointF(p3.x() - p2.x(), p3.y() - p2.y())
            
            def normalize_vector(v):
                length = math.sqrt(v.x() * v.x() + v.y() * v.y())
                if length < 0.001:
                    return QPointF(0, 0)
                return QPointF(v.x() / length, v.y() / length)
            
            start_tangent_normalized = normalize_vector(start_tangent)
            in_tangent_normalized = normalize_vector(in_tangent)
            out_tangent_normalized = normalize_vector(out_tangent)
            
            center_tangent = QPointF(
                0.5 * in_tangent_normalized.x() + 0.5 * out_tangent_normalized.x(), 
                0.5 * in_tangent_normalized.y() + 0.5 * out_tangent_normalized.y()
            )
            center_tangent_normalized = normalize_vector(center_tangent)
            
            end_tangent = QPointF(p4.x() - p3.x(), p4.y() - p3.y())
            end_tangent_normalized = normalize_vector(end_tangent)
            
            # Calculate distances
            dist_p0_p1 = math.sqrt((p1.x() - p0.x())**2 + (p1.y() - p0.y())**2)
            dist_p1_p2 = math.sqrt((p2.x() - p1.x())**2 + (p2.y() - p1.y())**2)
            dist_p2_p3 = math.sqrt((p3.x() - p2.x())**2 + (p3.y() - p2.y())**2)
            dist_p3_p4 = math.sqrt((p4.x() - p3.x())**2 + (p4.y() - p3.y())**2)
            
            # Get control point influence parameters
            exponent = getattr(self, 'curve_response_exponent', 1.5)
            base_fraction = getattr(self, 'control_point_base_fraction', 0.4)
            dist_multiplier = getattr(self, 'distance_multiplier', 1.2)
            
            # Apply distance multiplier and exponential scaling
            boosted_dist_p0_p1 = dist_p0_p1 * dist_multiplier
            boosted_dist_p1_p2 = dist_p1_p2 * dist_multiplier
            boosted_dist_p2_p3 = dist_p2_p3 * dist_multiplier
            boosted_dist_p3_p4 = dist_p3_p4 * dist_multiplier
            
            max_dist = max(boosted_dist_p0_p1, boosted_dist_p1_p2, boosted_dist_p2_p3, boosted_dist_p3_p4, 1.0)
            scaled_dist_p0_p1 = (boosted_dist_p0_p1 / max_dist) ** exponent * boosted_dist_p0_p1
            scaled_dist_p1_p2 = (boosted_dist_p1_p2 / max_dist) ** exponent * boosted_dist_p1_p2
            scaled_dist_p2_p3 = (boosted_dist_p2_p3 / max_dist) ** exponent * boosted_dist_p2_p3
            scaled_dist_p3_p4 = (boosted_dist_p3_p4 / max_dist) ** exponent * boosted_dist_p3_p4
            
            # Calculate intermediate control points with combined influence
            cp1 = p0 + start_tangent_normalized * (scaled_dist_p0_p1 * base_fraction) if start_tangent_normalized.manhattanLength() > 1e-6 else p1
            cp2 = p2 - center_tangent_normalized * (scaled_dist_p1_p2 * base_fraction) if center_tangent_normalized.manhattanLength() > 1e-6 else p1
            cp3 = p2 + center_tangent_normalized * (scaled_dist_p2_p3 * base_fraction) if center_tangent_normalized.manhattanLength() > 1e-6 else p3
            cp4 = p4 - end_tangent_normalized * (scaled_dist_p3_p4 * base_fraction) if end_tangent_normalized.manhattanLength() > 1e-6 else p3
            
            if t <= 0.5:
                # First segment: start to center
                scaled_t = t * 2
                # Tangent for the first segment
                tangent = (
                    3 * (1 - scaled_t) ** 2 * (cp1 - p0) +
                    6 * (1 - scaled_t) * scaled_t * (cp2 - cp1) +
                    3 * scaled_t ** 2 * (p2 - cp2)
                )
            else:
                # Second segment: center to end
                scaled_t = (t - 0.5) * 2
                # Tangent for the second segment
                tangent = (
                    3 * (1 - scaled_t) ** 2 * (cp3 - p2) +
                    6 * (1 - scaled_t) * scaled_t * (cp4 - cp3) +
                    3 * scaled_t ** 2 * (p4 - cp4)
                )
            
            # Handle zero-length tangent vector
            if tangent.manhattanLength() == 0:
                if t <= 0.5:
                    tangent = p2 - p0
                else:
                    tangent = p4 - p2
                
        else:
            # Standard cubic Bézier with 2 control points
            p0, p1, p2, p3 = self.start, self.control_point1, self.control_point2, self.end

            # Ensure points are valid before calculation
            if p0 is None or p1 is None or p2 is None or p3 is None:
                pass
                # Return a default zero vector or handle appropriately
                return QPointF(0, 0) 

            # Compute the derivative at parameter t
            tangent = (
                3 * (1 - t) ** 2 * (p1 - p0) +
                6 * (1 - t) * t * (p2 - p1) +
                3 * t ** 2 * (p3 - p2)
            )

            # Handle zero-length tangent vector
            if tangent.manhattanLength() == 0:
                tangent = p3 - p0

        return tangent

    def force_path_update(self):
        """Force the path to be recalculated without modifying control points."""
        # Clear any cached path
        if hasattr(self, '_path'):
            delattr(self, '_path')
        
        # Special handling for 3rd control point strands
        if (hasattr(self, 'canvas') and self.canvas and 
            hasattr(self.canvas, 'enable_third_control_point') and 
            self.canvas.enable_third_control_point and
            hasattr(self, 'control_point_center_locked') and 
            self.control_point_center_locked):
            # For 3rd control point strands, we need to ensure the curvature parameters
            # are properly applied to the curve calculation
            # The get_path() method will use these parameters when recalculating
            # Also call update_shape() to ensure all aspects are updated
            self.update_shape()
        else:
            # For regular strands, just recalculate the path
            self._path = self.get_path()
            # Update side lines
            self.update_side_line()
        
        # Force canvas redraw if we have a canvas reference
        if hasattr(self, 'canvas') and self.canvas:
            # Invalidate any cached bounding rects
            if hasattr(self, '_bounding_rect_cache'):
                delattr(self, '_bounding_rect_cache')
            # Force canvas update to redraw with new curvature settings
            self.canvas.update()
    
    def update_side_line(self):
        """Update side lines considering the curve's shape near the ends."""
        # IMPROVED: Smart tangent calculation for proper side line angles
        
        # For start side line: Check if control point is at default/coincident position
        tangent_start = self.control_point1 - self.start
        if tangent_start.manhattanLength() < 0.001:
            # Control point coincides with start - need to look ahead on the curve
            # Use the actual curve tangent at a small t value to get proper direction
            # This gives us the true curve direction even when control points are at defaults
            t_lookahead = 0.01  # Look slightly ahead on the curve
            point_ahead = self.point_at(t_lookahead)
            tangent_start = point_ahead - self.start
            
            if tangent_start.manhattanLength() < 0.001:
                # Still no direction - use direction to second control point or end
                if (self.control_point2 - self.start).manhattanLength() > 0.001:
                    tangent_start = self.control_point2 - self.start
                else:
                    tangent_start = self.end - self.start
            
        # For end side line: Check if control point is at default/coincident position
        tangent_end = self.end - self.control_point2
        if tangent_end.manhattanLength() < 0.001:
            # Control point coincides with end - need to look back on the curve
            # Use the actual curve tangent at a small t value from the end
            t_lookback = 0.99  # Look slightly back from the end
            point_before = self.point_at(t_lookback)
            tangent_end = self.end - point_before
            
            if tangent_end.manhattanLength() < 0.001:
                # Still no direction - use direction from first control point or start
                if (self.end - self.control_point1).manhattanLength() > 0.001:
                    tangent_end = self.end - self.control_point1
                else:
                    tangent_end = self.end - self.start

        # Additional safety check for zero tangents
        if tangent_start.manhattanLength() < 0.001:
            tangent_start = QPointF(1, 0)  # Default to horizontal
        if tangent_end.manhattanLength() < 0.001:
            tangent_end = QPointF(1, 0)  # Default to horizontal

        # Calculate angles of tangents
        angle_start = math.atan2(tangent_start.y(), tangent_start.x())
        angle_end = math.atan2(tangent_end.y(), tangent_end.x())

        # Perpendicular angles at start and end
        perp_angle_start = angle_start + math.pi / 2
        perp_angle_end = angle_end + math.pi / 2

        # Calculate the offset for the side lines
        half_total_width = (self.width + self.stroke_width * 2) / 2
        dx_start = half_total_width * math.cos(perp_angle_start)
        dy_start = half_total_width * math.sin(perp_angle_start)
        dx_end = half_total_width * math.cos(perp_angle_end)
        dy_end = half_total_width * math.sin(perp_angle_end)

        # Start side line positions
        self.start_line_start = QPointF(self.start.x() - dx_start, self.start.y() - dy_start)
        self.start_line_end = QPointF(self.start.x() + dx_start, self.start.y() + dy_start)

        # End side line positions
        self.end_line_start = QPointF(self.end.x() - dx_end, self.end.y() - dy_end)
        self.end_line_end = QPointF(self.end.x() + dx_end, self.end.y() + dy_end)

    def set_attachable(self, attachable):
        self.attachable = attachable
        self.update_shape()  # Assuming you have this method to update the strand's appearance
    def calculate_start_tangent(self):
        """
        Calculate the tangent angle at the start point of the Bézier curve.
        Returns the angle in radians.
        """
        # Get tangent vector at t=0 for cubic bezier
        # For a cubic Bézier curve, the tangent at t=0 is proportional to P1 - P0
        tangent = (self.control_point1 - self.start) * 3
        
        # If control point coincides with start, use alternative direction
        if tangent.manhattanLength() == 0:
            # Try using the second control point
            tangent = (self.control_point2 - self.start) * 3
            
            # If second control point also coincides, fall back to end point direction
            if tangent.manhattanLength() == 0:
                tangent = self.end - self.start
                
                # If end point also coincides (degenerate case), use default angle
                if tangent.manhattanLength() == 0:
                    return 0.0
        
        return math.atan2(tangent.y(), tangent.x())
    
    def draw(self, painter, skip_painter_setup=False):
        painter.save() # <<<< SAVE 1 (Top Level)
        if not skip_painter_setup:
            RenderUtils.setup_painter(painter, enable_high_quality=True)

        # Check zoom factor and use direct drawing when zoomed
        zoom_factor = getattr(self.canvas, 'zoom_factor', 1.0) if hasattr(self, 'canvas') else 1.0
        
        # When zoomed (either in or out) OR panned, use direct drawing without temporary
        # image optimization to avoid clipping issues that can occur with bounds calculations
        is_panned = False
        if hasattr(self, 'canvas') and self.canvas:
            pan_x = getattr(self.canvas, 'pan_offset_x', 0)
            pan_y = getattr(self.canvas, 'pan_offset_y', 0)
            is_panned = (pan_x != 0 or pan_y != 0)
        if zoom_factor != 1.0 or is_panned:
            # logging.info(f"[Strand.draw] Zoomed ({zoom_factor}), using direct drawing without temp image optimization")
            self._draw_direct(painter)
            painter.restore() # Top Level Restore
            return

        # --- START: Handle hidden state ---
        if self.is_hidden:
            # Draw arrow shadow first if arrow casts shadow is enabled
            if getattr(self, 'full_arrow_visible', False) and getattr(self, 'arrow_casts_shadow', False):
                painter.save()
                try:
                    from shader_utils import draw_strand_shadow
                    # Draw arrow shadow even when strand is hidden
                    shadow_color = None
                    if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'default_shadow_color'):
                        shadow_color = self.canvas.default_shadow_color
                        self.shadow_color = QColor(shadow_color)

                    draw_strand_shadow(painter, self, shadow_color,
                                      num_steps=self.canvas.num_steps if hasattr(self.canvas, 'num_steps') else 3,
                                      max_blur_radius=self.canvas.max_blur_radius if hasattr(self.canvas, 'max_blur_radius') else 29.99)
                except Exception as e:
                    pass
                finally:
                    painter.restore()

            # --- NEW: Draw full strand arrow when strand is hidden ---
            if getattr(self, 'full_arrow_visible', False):
                painter.save()

                # --- Draw Arrowhead extending outward from the endpoint ---
                arrow_head_len = getattr(self.canvas, 'arrow_head_length', 20)
                arrow_head_width = getattr(self.canvas, 'arrow_head_width', 10)

                # Use custom arrow color if set, otherwise default to strand color
                default_arrow_head_fill_color = self.color if self.color else QColor(Qt.black)
                if hasattr(self, 'arrow_color'):
                    arrow_head_fill_color = self.arrow_color
                else:
                    arrow_head_fill_color = self.canvas.default_arrow_fill_color if hasattr(self.canvas, 'use_default_arrow_color') and not self.canvas.use_default_arrow_color else default_arrow_head_fill_color

                # Apply transparency if set
                if hasattr(self, 'arrow_transparency'):
                    transparency = self.arrow_transparency / 100.0  # Convert from percentage to 0-1
                    arrow_head_fill_color = QColor(arrow_head_fill_color)
                    arrow_head_fill_color.setAlphaF(transparency)
                
                arrow_head_border_pen = QPen(self.stroke_color, getattr(self.canvas, 'arrow_head_stroke_width', 4))
                arrow_head_border_pen.setJoinStyle(Qt.MiterJoin)
                arrow_head_border_pen.setCapStyle(Qt.FlatCap)

                # Calculate the tangent at the endpoint to determine arrow direction
                # Use a point very close to the end to get the tangent
                tangent_at_end = self.calculate_cubic_tangent(0.999)
                len_at_end = math.hypot(tangent_at_end.x(), tangent_at_end.y())
                
                if len_at_end > 0:
                    # Unit vector pointing along the curve at the endpoint
                    unit_vector_shaft = QPointF(tangent_at_end.x() / len_at_end, tangent_at_end.y() / len_at_end)
                    
                    # Perpendicular vector to the shaft direction (for arrow width)
                    perp_vector = QPointF(-unit_vector_shaft.y(), unit_vector_shaft.x())

                    # Calculate the two base corners at the endpoint
                    left_point = self.end + perp_vector * (arrow_head_width / 2)
                    right_point = self.end - perp_vector * (arrow_head_width / 2)

                    # Calculate tip position extending outward from the endpoint
                    # The tip should be arrow_head_len away from the endpoint along the shaft direction
                    tip = self.end + unit_vector_shaft * arrow_head_len
                    
                    # --- Draw Shaft (the entire strand path) ---
                    full_arrow_shaft_line_width = getattr(self.canvas, 'arrow_line_width', 10)
                    # Use custom arrow color for shaft if set
                    shaft_color = getattr(self, 'arrow_color', self.stroke_color)
                    if hasattr(self, 'arrow_transparency'):
                        shaft_color = QColor(shaft_color)
                        shaft_color.setAlphaF(self.arrow_transparency / 100.0)

                    # Use the exact strand path as the shaft
                    shaft_path = self.get_path()  # This uses all the control points and bias settings

                    # Draw the shaft with pattern (entire strand path)
                    self.draw_arrow_shaft_with_pattern(painter, shaft_path, shaft_color, full_arrow_shaft_line_width)
                    # --- End Shaft ---
                    
                    # Create the arrow polygon
                    arrow_head_poly = QPolygonF([tip, left_point, right_point])

                    # Fill the arrow with optional texture (only if arrow head is visible)
                    if getattr(self, 'arrow_head_visible', True):
                        painter.setPen(Qt.NoPen)
                        self.apply_arrow_texture_brush(painter, arrow_head_fill_color)
                        painter.drawPolygon(arrow_head_poly)

                    # Draw the border (only if arrow head is visible)
                    if getattr(self, 'arrow_head_visible', True):
                        painter.setPen(arrow_head_border_pen)
                        painter.setBrush(Qt.NoBrush)
                        painter.drawPolygon(arrow_head_poly)
                painter.restore()

            # --- NEW: Draw dashed extension lines when hidden ---
            ext_len_hidden = getattr(self.canvas, 'extension_length', 100)
            dash_count_hidden = getattr(self.canvas, 'extension_dash_count', 10)
            dash_width_hidden = getattr(self.canvas, 'extension_dash_width', self.stroke_width)
            dash_seg_hidden = ext_len_hidden / (2 * dash_count_hidden) if dash_count_hidden > 0 else ext_len_hidden
            dash_gap_hidden = getattr(self.canvas, 'extension_dash_gap_length', dash_seg_hidden)
            dash_gap_hidden = -dash_gap_hidden
            
            side_color_hidden_dash = QColor(self.stroke_color)
            if self.color:
                side_color_hidden_dash.setAlpha(self.color.alpha())
            else:
                side_color_hidden_dash.setAlpha(255)

            dash_pen_hidden_ext = QPen(side_color_hidden_dash, dash_width_hidden, Qt.CustomDashLine)
            pattern_len_hidden_ext = dash_seg_hidden / dash_width_hidden if dash_width_hidden > 0 else dash_seg_hidden
            dash_pen_hidden_ext.setDashPattern([pattern_len_hidden_ext, pattern_len_hidden_ext])
            dash_pen_hidden_ext.setCapStyle(Qt.FlatCap)

            # Check shadow-only mode
            shadow_only_mode = getattr(self, 'shadow_only', False)

            if getattr(self, 'start_extension_visible', False) or getattr(self, 'end_extension_visible', False):
                painter.save()
                painter.setPen(dash_pen_hidden_ext)
                if getattr(self, 'start_extension_visible', False) and not shadow_only_mode:
                    tangent_hidden_start_ext = self.calculate_cubic_tangent(0.0)
                    length_hidden_start_ext = math.hypot(tangent_hidden_start_ext.x(), tangent_hidden_start_ext.y())
                    if length_hidden_start_ext:
                        unit_hidden_start_ext = QPointF(tangent_hidden_start_ext.x()/length_hidden_start_ext, tangent_hidden_start_ext.y()/length_hidden_start_ext)
                        raw_end_hidden_start_ext = QPointF(self.start.x() - unit_hidden_start_ext.x()*ext_len_hidden, self.start.y() - unit_hidden_start_ext.y()*ext_len_hidden)
                        start_pt_hidden_start_ext = QPointF(self.start.x() + unit_hidden_start_ext.x()*dash_gap_hidden, self.start.y() + unit_hidden_start_ext.y()*dash_gap_hidden)
                        end_pt_hidden_start_ext = QPointF(raw_end_hidden_start_ext.x() + unit_hidden_start_ext.x()*dash_gap_hidden, raw_end_hidden_start_ext.y() + unit_hidden_start_ext.y()*dash_gap_hidden)
                        painter.drawLine(start_pt_hidden_start_ext, end_pt_hidden_start_ext)
                if getattr(self, 'end_extension_visible', False) and not shadow_only_mode:
                    tangent_hidden_end_ext = self.calculate_cubic_tangent(1.0)
                    length_hidden_end_ext = math.hypot(tangent_hidden_end_ext.x(), tangent_hidden_end_ext.y())
                    if length_hidden_end_ext:
                        unit_hidden_end_ext = QPointF(tangent_hidden_end_ext.x()/length_hidden_end_ext, tangent_hidden_end_ext.y()/length_hidden_end_ext)
                        raw_end_hidden_end_ext = QPointF(self.end.x() + unit_hidden_end_ext.x()*ext_len_hidden, self.end.y() + unit_hidden_end_ext.y()*ext_len_hidden)
                        start_pt_hidden_end_ext = QPointF(self.end.x() - unit_hidden_end_ext.x()*dash_gap_hidden, self.end.y() - unit_hidden_end_ext.y()*dash_gap_hidden)
                        end_pt_hidden_end_ext = QPointF(raw_end_hidden_end_ext.x() - unit_hidden_end_ext.x()*dash_gap_hidden, raw_end_hidden_end_ext.y() - unit_hidden_end_ext.y()*dash_gap_hidden)
                        painter.drawLine(start_pt_hidden_end_ext, end_pt_hidden_end_ext)
                painter.restore()

            # --- NEW: Draw individual start/end arrows when hidden ---
            arrow_len_hidden_indiv = getattr(self.canvas, 'arrow_head_length', 20)
            arrow_width_hidden_indiv = getattr(self.canvas, 'arrow_head_width', 10)
            arrow_gap_length_hidden_indiv = getattr(self.canvas, 'arrow_gap_length', 10)
            arrow_line_length_hidden_indiv = getattr(self.canvas, 'arrow_line_length', 20)
            arrow_line_width_hidden_indiv = getattr(self.canvas, 'arrow_line_width', 10)
            
            default_fill_color_hidden_indiv = self.color if self.color else QColor(Qt.black)
            fill_color_hidden_indiv = self.canvas.default_arrow_fill_color if hasattr(self.canvas, 'use_default_arrow_color') and not self.canvas.use_default_arrow_color else default_fill_color_hidden_indiv
            
            border_pen_hidden_indiv = QPen(self.stroke_color, getattr(self.canvas, 'arrow_head_stroke_width', 4))
            border_pen_hidden_indiv.setJoinStyle(Qt.MiterJoin)
            border_pen_hidden_indiv.setCapStyle(Qt.FlatCap)

            if getattr(self, 'start_arrow_visible', False) or getattr(self, 'end_arrow_visible', False):
                painter.save()
                if getattr(self, 'start_arrow_visible', False):
                    tangent_s_hidden_indiv = self.calculate_cubic_tangent(0.0)
                    len_s_hidden_indiv = math.hypot(tangent_s_hidden_indiv.x(), tangent_s_hidden_indiv.y())
                    if len_s_hidden_indiv:
                        unit_s_hidden_indiv = QPointF(tangent_s_hidden_indiv.x() / len_s_hidden_indiv, tangent_s_hidden_indiv.y() / len_s_hidden_indiv)
                        arrow_dir_s_hidden_indiv = QPointF(-unit_s_hidden_indiv.x(), -unit_s_hidden_indiv.y())
                        shaft_start_s_hidden_indiv = QPointF(self.start.x() + arrow_dir_s_hidden_indiv.x() * arrow_gap_length_hidden_indiv, self.start.y() + arrow_dir_s_hidden_indiv.y() * arrow_gap_length_hidden_indiv)
                        shaft_end_s_hidden_indiv = QPointF(shaft_start_s_hidden_indiv.x() + arrow_dir_s_hidden_indiv.x() * arrow_line_length_hidden_indiv, shaft_start_s_hidden_indiv.y() + arrow_dir_s_hidden_indiv.y() * arrow_line_length_hidden_indiv)
                        line_pen_s_hidden_indiv = QPen(self.stroke_color, arrow_line_width_hidden_indiv)
                        line_pen_s_hidden_indiv.setCapStyle(Qt.FlatCap)
                        painter.setPen(line_pen_s_hidden_indiv)
                        painter.setBrush(Qt.NoBrush)
                        painter.drawLine(shaft_start_s_hidden_indiv, shaft_end_s_hidden_indiv)
                        base_center_s_hidden_indiv = shaft_end_s_hidden_indiv
                        tip_s_hidden_indiv = QPointF(base_center_s_hidden_indiv.x() + arrow_dir_s_hidden_indiv.x() * arrow_len_hidden_indiv, base_center_s_hidden_indiv.y() + arrow_dir_s_hidden_indiv.y() * arrow_len_hidden_indiv)
                        perp_s_hidden_indiv = QPointF(-arrow_dir_s_hidden_indiv.y(), arrow_dir_s_hidden_indiv.x())
                        left_s_hidden_indiv = QPointF(base_center_s_hidden_indiv.x() + perp_s_hidden_indiv.x() * arrow_width_hidden_indiv / 2, base_center_s_hidden_indiv.y() + perp_s_hidden_indiv.y() * arrow_width_hidden_indiv / 2)
                        right_s_hidden_indiv = QPointF(base_center_s_hidden_indiv.x() - perp_s_hidden_indiv.x() * arrow_width_hidden_indiv / 2, base_center_s_hidden_indiv.y() - perp_s_hidden_indiv.y() * arrow_width_hidden_indiv / 2)
                        arrow_poly_s_hidden_indiv = QPolygonF([tip_s_hidden_indiv, left_s_hidden_indiv, right_s_hidden_indiv])
                        painter.setPen(Qt.NoPen)
                        painter.setBrush(fill_color_hidden_indiv)
                        painter.drawPolygon(arrow_poly_s_hidden_indiv)
                        painter.setPen(border_pen_hidden_indiv)
                        painter.setBrush(Qt.NoBrush)
                        painter.drawPolygon(arrow_poly_s_hidden_indiv)
                if getattr(self, 'end_arrow_visible', False):
                    tangent_e_hidden_indiv = self.calculate_cubic_tangent(1.0)
                    len_e_hidden_indiv = math.hypot(tangent_e_hidden_indiv.x(), tangent_e_hidden_indiv.y())
                    if len_e_hidden_indiv:
                        unit_e_hidden_indiv = QPointF(tangent_e_hidden_indiv.x() / len_e_hidden_indiv, tangent_e_hidden_indiv.y() / len_e_hidden_indiv)
                        arrow_dir_e_hidden_indiv = QPointF(unit_e_hidden_indiv.x(), unit_e_hidden_indiv.y())
                        shaft_start_e_hidden_indiv = QPointF(self.end.x() + arrow_dir_e_hidden_indiv.x() * arrow_gap_length_hidden_indiv, self.end.y() + arrow_dir_e_hidden_indiv.y() * arrow_gap_length_hidden_indiv)
                        shaft_end_e_hidden_indiv = QPointF(shaft_start_e_hidden_indiv.x() + arrow_dir_e_hidden_indiv.x() * arrow_line_length_hidden_indiv, shaft_start_e_hidden_indiv.y() + arrow_dir_e_hidden_indiv.y() * arrow_line_length_hidden_indiv)
                        line_pen_e_hidden_indiv = QPen(self.stroke_color, arrow_line_width_hidden_indiv)
                        line_pen_e_hidden_indiv.setCapStyle(Qt.FlatCap)
                        painter.setPen(line_pen_e_hidden_indiv)
                        painter.setBrush(Qt.NoBrush)
                        painter.drawLine(shaft_start_e_hidden_indiv, shaft_end_e_hidden_indiv)
                        base_center_e_hidden_indiv = shaft_end_e_hidden_indiv
                        tip_e_hidden_indiv = QPointF(base_center_e_hidden_indiv.x() + arrow_dir_e_hidden_indiv.x() * arrow_len_hidden_indiv, base_center_e_hidden_indiv.y() + arrow_dir_e_hidden_indiv.y() * arrow_len_hidden_indiv)
                        perp_e_hidden_indiv = QPointF(-arrow_dir_e_hidden_indiv.y(), arrow_dir_e_hidden_indiv.x())
                        left_e_hidden_indiv = QPointF(base_center_e_hidden_indiv.x() + perp_e_hidden_indiv.x() * arrow_width_hidden_indiv / 2, base_center_e_hidden_indiv.y() + perp_e_hidden_indiv.y() * arrow_width_hidden_indiv / 2)
                        right_e_hidden_indiv = QPointF(base_center_e_hidden_indiv.x() - perp_e_hidden_indiv.x() * arrow_width_hidden_indiv / 2, base_center_e_hidden_indiv.y() - perp_e_hidden_indiv.y() * arrow_width_hidden_indiv / 2)
                        arrow_poly_e_hidden_indiv = QPolygonF([tip_e_hidden_indiv, left_e_hidden_indiv, right_e_hidden_indiv])
                        painter.setPen(Qt.NoPen)
                        painter.setBrush(fill_color_hidden_indiv)
                        painter.drawPolygon(arrow_poly_e_hidden_indiv)
                        painter.setPen(border_pen_hidden_indiv)
                        painter.setBrush(Qt.NoBrush)
                        painter.drawPolygon(arrow_poly_e_hidden_indiv)
                painter.restore()

            painter.restore() # RESTORE 1 (Top Level)
            return # Arrow and extensions drawn (if requested); skip drawing strand body
        # --- END: Handle hidden state ---

        # Note: Shadow-only mode handled later - need to cast shadows first

        # Check shadow-only mode for non-hidden strands as well
        shadow_only_mode = getattr(self, 'shadow_only', False)

        # Import necessary classes locally to avoid potential circular imports
        from masked_strand import MaskedStrand
        from attached_strand import AttachedStrand # Added import

        # Get the path representing the strand as a cubic Bézier curve
        path = self.get_path()

        # Create a stroker for the stroke path with squared ends
        stroke_stroker = QPainterPathStroker()
        stroke_stroker.setWidth(self.width + self.stroke_width * 2)
        stroke_stroker.setJoinStyle(Qt.MiterJoin)
        stroke_stroker.setCapStyle(Qt.FlatCap)  # Use FlatCap for squared ends
        stroke_path = stroke_stroker.createStroke(path)

        # Draw shadow for overlapping strands - using the utility function
        # Reduced high-frequency logging for performance
        # logging.info(f"Strand {self.layer_name}: Before shadow save()")
        painter.save() # SAVE 2
        try:
            # Import is inside try block to handle potential import errors
            from shader_utils import draw_strand_shadow, draw_circle_shadow

            # Only draw shadows if this strand should draw its own shadow
            if not hasattr(self, 'should_draw_shadow') or self.should_draw_shadow:
                # Use canvas's shadow color if available
                shadow_color = None
                if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'default_shadow_color'):
                    shadow_color = self.canvas.default_shadow_color
                    # Ensure the strand's shadow color is also updated for future reference
                    self.shadow_color = QColor(shadow_color)

                draw_strand_shadow(painter, self, shadow_color,
                                  num_steps=self.canvas.num_steps if hasattr(self.canvas, 'num_steps') else 3,
                                  max_blur_radius=self.canvas.max_blur_radius if hasattr(self.canvas, 'max_blur_radius') else 29.99)

                # Draw circle shadows if this strand has circles
                if hasattr(self, 'has_circles') and any(self.has_circles):
                    draw_circle_shadow(painter, self, shadow_color)
        except Exception as e:
            # Log the error but continue with the rendering
            pass
        finally:
            painter.restore() # RESTORE 2
            # Reduced high-frequency logging for performance
        # logging.info(f"Strand {self.layer_name}: After shadow restore()")
            # Draw dashed extension lines under the strand (below base paths)
            painter.save()
            # Setup extension parameters from canvas or defaults
            ext_len = getattr(self.canvas, 'extension_length', 100)
            dash_count = getattr(self.canvas, 'extension_dash_count', 10)
            line_w = getattr(self.canvas, 'extension_dash_width', self.stroke_width)
            dash_seg = ext_len / (2 * dash_count) if dash_count > 0 else ext_len
            # Extension color same as side color with original alpha
            ext_color = QColor(self.stroke_color)
            ext_color.setAlpha(self.color.alpha())
            
            # Create path for dashed line
            dash_path = QPainterPath()
            dash_path.setFillRule(Qt.WindingFill)
            
            # Create stroker to give the path width
            stroker = QPainterPathStroker()
            stroker.setWidth(line_w)
            stroker.setCapStyle(Qt.FlatCap)
            
            # Get configured gap length between dashes or default to dash segment, invert for offset
            dash_gap = getattr(self.canvas, 'extension_dash_gap_length', dash_seg)
            dash_gap = -dash_gap
            # Setup pen for dashed line
            dash_pen = QPen(ext_color, line_w, Qt.CustomDashLine)
            # Uniform dash pattern: equal on/off lengths based on dash_seg
            pattern_len = dash_seg / line_w if line_w > 0 else dash_seg
            dash_pen.setDashPattern([pattern_len, pattern_len])
            painter.setPen(dash_pen)
     
            painter.restore()

        # Only draw highlight if this is not a MaskedStrand
        if self.is_selected and not isinstance(self, MaskedStrand):
            # Create a shortened path for the highlight (10 pixels from each end)
            # Use percentAtLength to get accurate t values for pixel offsets
            total_length = path.length()
            if self.start_circle_stroke_color.alpha() == 0:
                t_start_point = 5.0
            else:
                t_start_point = 0.0
            if self.end_circle_stroke_color.alpha() == 0:
                t_end_point = 5.0
            else:
                t_end_point = 0.0
            if self.start_circle_stroke_color.alpha() == 0 or self.end_circle_stroke_color.alpha() == 0:            
                if total_length > 10:  # Only shorten if path is longer than 20 pixels
                    # Get t values at exactly 10 pixels from start and 10 pixels from end
                    t_start = path.percentAtLength(t_start_point)
                    t_end = path.percentAtLength(total_length - t_end_point)
                    
                    # Create a new path for the shortened highlight
                    highlight_path = QPainterPath()
                    
                    # Sample points along the actual path using pointAtPercent
                    # This correctly handles both 2 and 3 control point configurations
                    num_samples = 50
                    points = []
                    for i in range(num_samples + 1):
                        t = t_start + (t_end - t_start) * (i / num_samples)
                        # Use pointAtPercent to get the actual point on the path
                        # This works correctly for any path configuration (2 or 3 control points)
                        point = path.pointAtPercent(t)
                        points.append(point)
                    
                    # Build the shortened path
                    if points:
                        highlight_path.moveTo(points[0])
                        for point in points[1:]:
                            highlight_path.lineTo(point)
                    
                    # Create stroker for the shortened highlight path
                    highlight_stroker = QPainterPathStroker()
                    highlight_stroker.setWidth(self.width + self.stroke_width * 2)
                    highlight_stroker.setJoinStyle(Qt.RoundJoin)
                    highlight_stroker.setCapStyle(Qt.FlatCap)
                    shortened_stroke_path = highlight_stroker.createStroke(highlight_path)
                    
                    # Draw the shortened highlight
                    highlight_pen = QPen(QColor('red'), 10)  # Fixed width instead of self.stroke_width + 8
                    highlight_pen.setJoinStyle(Qt.RoundJoin)
                    highlight_pen.setCapStyle(Qt.FlatCap)
                    painter.setPen(highlight_pen)
                    painter.setBrush(Qt.NoBrush)
                    painter.drawPath(shortened_stroke_path)
            else:
                # If path is too short, draw normal highlight
                highlight_pen = QPen(QColor('red'), 10)  # Fixed width instead of self.stroke_width + 8
                highlight_pen.setJoinStyle(Qt.MiterJoin)
                highlight_pen.setCapStyle(Qt.FlatCap)
                painter.setPen(highlight_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(stroke_path)
            
            # Add side line highlighting for regular strands (not attached strands)
            # Only highlight sides that don't have attached strands
            if not hasattr(self, 'parent'):  # This is a regular strand, not an attached strand
           
                
                painter.save()
                
                # Calculate the half-width for side line highlighting
                highlight_pen_thickness = 10
                black_half_width = (self.width + self.stroke_width * 2) / 2
                highlight_half_width = black_half_width + (highlight_pen_thickness / 2)
                
                # Calculate angles of tangents
                tangent_start = self.calculate_cubic_tangent(0.0)
                tangent_end = self.calculate_cubic_tangent(1.0)
                
                # Handle zero-length tangent vectors
                if tangent_start.manhattanLength() == 0:
                    tangent_start = self.end - self.start
                if tangent_end.manhattanLength() == 0:
                    tangent_end = self.start - self.end
                
                # Calculate angles
                angle_start = math.atan2(tangent_start.y(), tangent_start.x())
                angle_end = math.atan2(tangent_end.y(), tangent_end.x())
                
                # Perpendicular angles
                perp_angle_start = angle_start + math.pi / 2
                perp_angle_end = angle_end + math.pi / 2
                
                # Calculate extended positions for start line
                dx_start_extended = highlight_half_width * math.cos(perp_angle_start)
                dy_start_extended = highlight_half_width * math.sin(perp_angle_start)
                start_line_start_extended = QPointF(self.start.x() - dx_start_extended, self.start.y() - dy_start_extended)
                start_line_end_extended = QPointF(self.start.x() + dx_start_extended, self.start.y() + dy_start_extended)
                
                # Calculate extended positions for end line
                dx_end_extended = highlight_half_width * math.cos(perp_angle_end)
                dy_end_extended = highlight_half_width * math.sin(perp_angle_end)
                end_line_start_extended = QPointF(self.end.x() - dx_end_extended, self.end.y() - dy_end_extended)
                end_line_end_extended = QPointF(self.end.x() + dx_end_extended, self.end.y() + dy_end_extended)
                
                # Create highlight pen for side lines
                highlight_pen = QPen(QColor(255, 0, 0, 255), self.stroke_width + 10 , Qt.SolidLine)
                highlight_pen.setCapStyle(Qt.FlatCap)
                highlight_pen.setJoinStyle(Qt.MiterJoin)
                
                painter.setPen(highlight_pen)
                painter.setBrush(Qt.NoBrush)
                
                # Only draw side lines where there are no attached strands
                # has_circles[0] = True means start has attached strand, has_circles[1] = True means end has attached strand
                if self.start_line_visible and not self.has_circles[0] and not self.start_circle_stroke_color.alpha() == 0:
                    pass
                    painter.drawLine(start_line_start_extended, start_line_end_extended)
                
                if self.end_line_visible and not self.has_circles[1] and not self.end_circle_stroke_color.alpha() == 0:
                    pass
                    painter.drawLine(end_line_start_extended, end_line_end_extended)
                
                painter.restore()
            else:
                pass

        # Create a stroker for the fill path with squared ends
        fill_stroker = QPainterPathStroker()
        fill_stroker.setWidth(self.width)
        fill_stroker.setJoinStyle(Qt.MiterJoin)
        fill_stroker.setCapStyle(Qt.FlatCap)  # Use FlatCap for squared ends
        fill_path = fill_stroker.createStroke(path)

        # --- START: Skip strand body drawing in shadow-only mode ---
        if not getattr(self, 'shadow_only', False):
            # Draw the stroke path with the stroke color
            # Reduced high-frequency logging for performance
            # logging.info(f"Strand {self.layer_name}: Before drawing stroke_path")
            painter.setPen(Qt.NoPen)
            painter.setBrush(self.stroke_color)
            painter.drawPath(stroke_path)

            # Draw the fill path with the strand's color
            # Reduced high-frequency logging for performance
            # logging.info(f"Strand {self.layer_name}: Before drawing fill_path")
            painter.setBrush(self.color)
            painter.drawPath(fill_path)

            # Draw the side lines
            side_pen = QPen(self.stroke_color, self.stroke_width)
            side_pen.setCapStyle(Qt.FlatCap)

            # Create a new color with the same alpha as the strand's color
            side_color = QColor(self.stroke_color)
            side_color.setAlpha(self.stroke_color.alpha())
            side_pen.setColor(side_color)

            painter.setPen(side_pen)
            # Conditionally draw start line
            if self.start_line_visible:
                painter.drawLine(self.start_line_start, self.start_line_end)
            # Conditionally draw end line
            if self.end_line_visible:
                painter.drawLine(self.end_line_start, self.end_line_end)
        # --- END: Skip strand body drawing in shadow-only mode ---

        # Shadow-only mode was already checked earlier
        
        # Define side_color for extension lines (needed even in shadow-only mode for pen setup)
        side_color = QColor(self.stroke_color)
        side_color.setAlpha(self.color.alpha())
        
        # Draw dashed extension lines with configured dash count and width (skip in shadow-only)
        if not shadow_only_mode:
            ext_len = getattr(self.canvas, 'extension_length', 100)
            dash_count = getattr(self.canvas, 'extension_dash_count', 10)
            # Determine dash width (thickness)
            dash_width = getattr(self.canvas, 'extension_dash_width', self.stroke_width)
            # Compute segment length so that there are dash_count dashes over ext_len
            dash_seg = ext_len / (2 * dash_count) if dash_count > 0 else ext_len
            # Get configured gap length between dashes or default to dash segment, invert for offset
            dash_gap = getattr(self.canvas, 'extension_dash_gap_length', dash_seg)
            dash_gap = -dash_gap
            # Setup pen for dashed line
            dash_pen = QPen(side_color, dash_width, Qt.CustomDashLine)
            # Uniform dash pattern: equal on/off lengths based on dash_seg
            pattern_len = dash_seg / dash_width if dash_width > 0 else dash_seg
            dash_pen.setDashPattern([pattern_len, pattern_len])
            dash_pen.setCapStyle(Qt.FlatCap)
            painter.setPen(dash_pen)
        # Start extension with gap offset at both ends
        if getattr(self, 'start_extension_visible', False) and not shadow_only_mode:
            tangent = self.calculate_cubic_tangent(0.0)
            length = math.hypot(tangent.x(), tangent.y())
            if length:
                unit = QPointF(tangent.x()/length, tangent.y()/length)
                raw_end = QPointF(self.start.x() - unit.x()*ext_len, self.start.y() - unit.y()*ext_len)
                start_pt = QPointF(self.start.x() + unit.x()*dash_gap, self.start.y() + unit.y()*dash_gap)
                end_pt = QPointF(raw_end.x() + unit.x()*dash_gap, raw_end.y() + unit.y()*dash_gap)
                painter.drawLine(start_pt, end_pt)
        # End extension with gap offset at both ends
        if getattr(self, 'end_extension_visible', False) and not shadow_only_mode:
            tangent_end = self.calculate_cubic_tangent(1.0)
            length_end = math.hypot(tangent_end.x(), tangent_end.y())
            if length_end:
                unit = QPointF(tangent_end.x()/length_end, tangent_end.y()/length_end)
                raw_end = QPointF(self.end.x() + unit.x()*ext_len, self.end.y() + unit.y()*ext_len)
                start_pt = QPointF(self.end.x() - unit.x()*dash_gap, self.end.y() - unit.y()*dash_gap)
                end_pt = QPointF(raw_end.x() - unit.x()*dash_gap, raw_end.y() - unit.y()*dash_gap)
                painter.drawLine(start_pt, end_pt)
        # --- NEW: Draw arrow heads ---
        arrow_len = getattr(self.canvas, 'arrow_head_length', 20)
        arrow_width = getattr(self.canvas, 'arrow_head_width', 10)
        # Arrow gap and shaft parameters
        # Distance between the strand end and the start of the arrow shaft (gap)
        arrow_gap_length = getattr(self.canvas, 'arrow_gap_length', 10)
        # Length of the arrow shaft itself
        arrow_line_length = getattr(self.canvas, 'arrow_line_length', 20)
        arrow_line_width = getattr(self.canvas, 'arrow_line_width', 10)
        # Fill and border styling
        if hasattr(self.canvas, 'use_default_arrow_color') and not self.canvas.use_default_arrow_color:
            fill_color = self.canvas.default_arrow_fill_color
        else:
            fill_color = self.color
        border_pen = QPen(self.stroke_color, getattr(self.canvas, 'arrow_head_stroke_width', 4))
        border_pen.setJoinStyle(Qt.MiterJoin)
        border_pen.setCapStyle(Qt.FlatCap)

        # Draw start arrow if visible (gap → shaft → head) - skip in shadow-only mode
        if getattr(self, 'start_arrow_visible', False) and not shadow_only_mode:
            tangent_start = self.calculate_cubic_tangent(0.0)
            len_start = math.hypot(tangent_start.x(), tangent_start.y())
            if len_start:
                unit = QPointF(tangent_start.x() / len_start, tangent_start.y() / len_start)
                arrow_dir = QPointF(-unit.x(), -unit.y())
                # Compute shaft start and end positions (skip gap first)
                shaft_start = QPointF(
                    self.start.x() + arrow_dir.x() * arrow_gap_length,
                    self.start.y() + arrow_dir.y() * arrow_gap_length
                )
                shaft_end = QPointF(
                    shaft_start.x() + arrow_dir.x() * arrow_line_length,
                    shaft_start.y() + arrow_dir.y() * arrow_line_length
                )
                # Draw the arrow shaft
                line_pen = QPen(self.stroke_color, arrow_line_width)
                line_pen.setCapStyle(Qt.FlatCap)
                painter.setPen(line_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawLine(shaft_start, shaft_end)
                # Compute arrow head base at end of shaft and tip at head length
                base_center = shaft_end
                tip = QPointF(
                    base_center.x() + arrow_dir.x() * arrow_len,
                    base_center.y() + arrow_dir.y() * arrow_len
                )
                # Build arrow polygon before drawing
                perp = QPointF(-arrow_dir.y(), arrow_dir.x())
                left = QPointF(base_center.x() + perp.x() * arrow_width / 2,
                               base_center.y() + perp.y() * arrow_width / 2)
                right = QPointF(base_center.x() - perp.x() * arrow_width / 2,
                                base_center.y() - perp.y() * arrow_width / 2)
                arrow_poly = QPolygonF([tip, left, right])
                # Fill the arrow head
                painter.setPen(Qt.NoPen)
                painter.setBrush(fill_color)
                painter.drawPolygon(arrow_poly)
                # Draw an outline around the arrow head so it matches the strand border
                painter.setPen(border_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPolygon(arrow_poly)

        # Draw end arrow if visible (gap → shaft → head) - skip in shadow-only mode
        if getattr(self, 'end_arrow_visible', False) and not shadow_only_mode:
            tangent_end = self.calculate_cubic_tangent(1.0)
            len_end = math.hypot(tangent_end.x(), tangent_end.y())
            if len_end:
                unit = QPointF(tangent_end.x() / len_end, tangent_end.y() / len_end)
                arrow_dir = QPointF(unit.x(), unit.y())
                # Compute shaft start and end positions (skip gap first)
                shaft_start = QPointF(
                    self.end.x() + arrow_dir.x() * arrow_gap_length,
                    self.end.y() + arrow_dir.y() * arrow_gap_length
                )
                shaft_end = QPointF(
                    shaft_start.x() + arrow_dir.x() * arrow_line_length,
                    shaft_start.y() + arrow_dir.y() * arrow_line_length
                )
                # Draw the arrow shaft
                line_pen = QPen(self.stroke_color, arrow_line_width)
                line_pen.setCapStyle(Qt.FlatCap)
                painter.setPen(line_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawLine(shaft_start, shaft_end)
                # Compute arrow head base at end of shaft and tip at head length
                base_center = shaft_end
                tip = QPointF(
                    base_center.x() + arrow_dir.x() * arrow_len,
                    base_center.y() + arrow_dir.y() * arrow_len
                )
                # Build arrow polygon before drawing
                perp = QPointF(-arrow_dir.y(), arrow_dir.x())
                left = QPointF(base_center.x() + perp.x() * arrow_width / 2,
                               base_center.y() + perp.y() * arrow_width / 2)
                right = QPointF(base_center.x() - perp.x() * arrow_width / 2,
                                base_center.y() - perp.y() * arrow_width / 2)
                arrow_poly = QPolygonF([tip, left, right])
                # Fill the arrow head
                painter.setPen(Qt.NoPen)
                painter.setBrush(fill_color)
                painter.drawPolygon(arrow_poly)
                # Draw an outline around the arrow head so it matches the strand border
                painter.setPen(border_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPolygon(arrow_poly)
        # --- END NEW ---

        # Draw the selection path
        painter.save() # SAVE 3
        selection_pen = QPen(QColor('transparent'), 0, Qt.DashLine)
        painter.setPen(selection_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.get_selection_path())  # Use get_selection_path to show selection area
        painter.drawPath(path)
        painter.restore() # RESTORE 3

        # Draw the selection path for debugging
        painter.save() # SAVE 4
        debug_pen = QPen(QColor('transparent'), 0, Qt.DashLine)
        painter.setPen(debug_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.get_selection_path())
        painter.restore() # RESTORE 4

        # Control points are now only drawn by StrandDrawingCanvas.draw_control_points
        # This prevents duplicate drawing of control points
        # By keeping the try-except for compatibility but disabling the actual drawing
        try:
            # Control point drawing code removed to avoid conflicts with canvas drawing
            pass
        except Exception as e:
            pass
            # Continue drawing even if control points fail
        # NEW: Draw half-circle attachments at endpoints where there are AttachedStrand children
        from attached_strand import AttachedStrand
        # Start endpoint half-circle (only if circle is enabled, visible, and child is not in shadow-only mode)
        if (self.has_circles[0]
            and self.start_circle_stroke_color.alpha() > 0
            and any(isinstance(child, AttachedStrand) and child.start == self.start and not getattr(child, 'shadow_only', False) for child in self.attached_strands)):
            tangent = self.calculate_cubic_tangent(0.0)
            angle = math.atan2(tangent.y(), tangent.x())
            total_d = self.width + self.stroke_width * 2
            radius = total_d / 2

            # Creating Outer Circle Half-Circle
            mask = QPainterPath()
            rect_width = total_d * 2
            rect_height = total_d * 2
            mask.addRect(0, -rect_height / 2, rect_width, rect_height)
            tr = QTransform().translate(self.start.x(), self.start.y())
            tr.rotate(math.degrees(angle))
            mask = tr.map(mask)
            outer = QPainterPath()
            outer.addEllipse(self.start, radius, radius)
            clip = outer.subtracted(mask)
            painter.setPen(Qt.NoPen)
            painter.setBrush(self.stroke_color)
            painter.drawPath(clip)

            # Draw the inner circle (fill) only if stroke is visible
            # When stroke is transparent, don't draw any part of the circle
            if self.start_circle_stroke_color.alpha() > 0:
                inner = QPainterPath()
                inner.addEllipse(self.start, self.width * 0.5, self.width * 0.5)
                painter.setBrush(self.color)
                painter.drawPath(inner)

            # Draw side line that covers the inner circle (only when stroke is visible)
            if self.start_circle_stroke_color.alpha() > 0:
                painter.setPen(Qt.NoPen)
                painter.setBrush(self.color)
                just_inner = QPainterPath()
                just_inner.addRect(-self.stroke_width,  -self.width*0.5, self.stroke_width , self.width)
                tr_inner = QTransform().translate(self.start.x(), self.start.y())
                tr_inner.rotate(math.degrees(angle))
                just_inner = tr_inner.map(just_inner)
                painter.drawPath(just_inner)

        # End endpoint half-circle (only if circle is enabled, visible, and child is not in shadow-only mode)
        if (self.has_circles[1]
            and self.end_circle_stroke_color.alpha() > 0
            and any(isinstance(child, AttachedStrand) and child.start == self.end and not getattr(child, 'shadow_only', False) for child in self.attached_strands)):
            tangent = self.calculate_cubic_tangent(1.0)
            angle = math.atan2(tangent.y(), tangent.x())
            total_d = self.width + self.stroke_width * 2
            radius = total_d / 2

            # Creating Outer Circle Half-Circle
            mask = QPainterPath()
            rect_width = total_d * 2
            rect_height = total_d * 2
            mask.addRect(-rect_width, -rect_height/2, rect_width, rect_height)
            tr = QTransform().translate(self.end.x(), self.end.y())
            tr.rotate(math.degrees(angle))
            mask = tr.map(mask)
            outer = QPainterPath()
            outer.addEllipse(self.end, radius, radius)
            clip = outer.subtracted(mask)
            painter.setPen(Qt.NoPen)
            painter.setBrush(self.stroke_color)
            painter.drawPath(clip)

            # Draw the inner circle (fill) only if stroke is visible
            # When stroke is transparent, don't draw any part of the circle
            if self.end_circle_stroke_color.alpha() > 0:
                inner = QPainterPath()
                inner.addEllipse(self.end, self.width * 0.5, self.width * 0.5)
                painter.setBrush(self.color)
                painter.drawPath(inner)

            # Draw side line that covers the inner circle (only when stroke is visible)
            if self.end_circle_stroke_color.alpha() > 0:
                painter.setPen(Qt.NoPen)
                painter.setBrush(self.color) 
                just_inner = QPainterPath()
                just_inner.addRect(-self.stroke_width,  -self.width*0.5, self.stroke_width, self.width)
                tr_inner = QTransform().translate(self.end.x(), self.end.y())
                tr_inner.rotate(math.degrees(angle))
                just_inner = tr_inner.map(just_inner)
                painter.drawPath(just_inner)

        # --- NEW: Draw semi-circles on top for closed connections ---
        # Draw semi-circle on top when start connection is closed (only if visible)
        if (hasattr(self, 'closed_connections') and self.closed_connections[0]
            and self.start_circle_stroke_color.alpha() > 0 and not shadow_only_mode):
            tangent = self.calculate_cubic_tangent(0.0)
            angle = math.atan2(tangent.y(), tangent.x())
            total_d = self.width + self.stroke_width * 2
            radius = total_d / 2

            # Create ring-shaped half-circle for stroke so it doesn't fill the interior
            mask = QPainterPath()
            rect_width = total_d * 2
            rect_height = total_d * 2
            mask.addRect(0, -rect_height / 2, rect_width, rect_height)
            tr = QTransform().translate(self.start.x(), self.start.y())
            tr.rotate(math.degrees(angle))
            mask = tr.map(mask)

            outer = QPainterPath()
            outer.addEllipse(self.start, radius, radius)
            outer_half = outer.subtracted(mask)

            inner_full = QPainterPath()
            inner_full.addEllipse(self.start, self.width * 0.5, self.width * 0.5)
            ring_half = outer_half.subtracted(inner_full)

            # Draw the stroke ring only if it's visible
            if self.start_circle_stroke_color.alpha() > 0:
                painter.setPen(Qt.NoPen)
                painter.setBrush(self.stroke_color)
                painter.drawPath(ring_half)

            # Draw the inner circle (fill) over everything only if visible
            if self.start_circle_stroke_color.alpha() > 0:
                painter.setBrush(self.color)
                painter.drawPath(inner_full)

            # Draw side line that covers the inner circle (only when stroke is visible)
            if self.start_circle_stroke_color.alpha() > 0:
                painter.setPen(Qt.NoPen)
                painter.setBrush(self.color)
                just_inner = QPainterPath()
                just_inner.addRect(-self.stroke_width,  -self.width*0.5, self.stroke_width , self.width)
                tr_inner = QTransform().translate(self.start.x(), self.start.y())
                tr_inner.rotate(math.degrees(angle))
                just_inner = tr_inner.map(just_inner)
                painter.drawPath(just_inner)

        # Draw semi-circle on top when end connection is closed (only if visible)
        if (hasattr(self, 'closed_connections') and self.closed_connections[1]
            and self.end_circle_stroke_color.alpha() > 0 and not shadow_only_mode):
            tangent = self.calculate_cubic_tangent(1.0)
            angle = math.atan2(tangent.y(), tangent.x())
            total_d = self.width + self.stroke_width * 2
            radius = total_d / 2

            # Create ring-shaped half-circle for stroke so it doesn't fill the interior
            mask = QPainterPath()
            rect_width = total_d * 2
            rect_height = total_d * 2
            mask.addRect(-rect_width, -rect_height/2, rect_width, rect_height)
            tr = QTransform().translate(self.end.x(), self.end.y())
            tr.rotate(math.degrees(angle))
            mask = tr.map(mask)

            outer = QPainterPath()
            outer.addEllipse(self.end, radius, radius)
            outer_half = outer.subtracted(mask)

            inner_full = QPainterPath()
            inner_full.addEllipse(self.end, self.width * 0.5, self.width * 0.5)
            ring_half = outer_half.subtracted(inner_full)

            # Draw the stroke ring only if it's visible
            if self.end_circle_stroke_color.alpha() > 0:
                painter.setPen(Qt.NoPen)
                painter.setBrush(self.stroke_color)
                painter.drawPath(ring_half)

            # Draw the inner circle (fill) over everything only if visible
            if self.end_circle_stroke_color.alpha() > 0:
                painter.setBrush(self.color)
                painter.drawPath(inner_full)

            # Draw side line that covers the inner circle (only when stroke is visible)
            if self.end_circle_stroke_color.alpha() > 0:
                painter.setPen(Qt.NoPen)
                painter.setBrush(self.color) 
                just_inner = QPainterPath()
                just_inner.addRect(-self.stroke_width,  -self.width*0.5, self.stroke_width, self.width)
                tr_inner = QTransform().translate(self.end.x(), self.end.y())
                tr_inner.rotate(math.degrees(angle))
                just_inner = tr_inner.map(just_inner)
                painter.drawPath(just_inner)
        # --- END NEW ---

        # --- Draw full strand arrow on TOP of strand body (if not hidden) ---
        if getattr(self, 'full_arrow_visible', False) and not shadow_only_mode: # 'not self.is_hidden' is implicit due to earlier return
            painter.save()
            
            # --- Draw Arrowhead first to calculate base position ---
            arrow_head_len = getattr(self.canvas, 'arrow_head_length', 20)
            arrow_head_width = getattr(self.canvas, 'arrow_head_width', 10)

            # Use custom arrow color if set, otherwise default to strand color
            default_arrow_head_fill_color = self.color if self.color else QColor(Qt.black)
            if hasattr(self, 'arrow_color'):
                arrow_head_fill_color = self.arrow_color
            else:
                arrow_head_fill_color = self.canvas.default_arrow_fill_color if hasattr(self.canvas, 'use_default_arrow_color') and not self.canvas.use_default_arrow_color else default_arrow_head_fill_color

            # Apply transparency if set
            if hasattr(self, 'arrow_transparency'):
                transparency = self.arrow_transparency / 100.0  # Convert from percentage to 0-1
                arrow_head_fill_color = QColor(arrow_head_fill_color)
                arrow_head_fill_color.setAlphaF(transparency)
            
            arrow_head_border_pen = QPen(self.stroke_color, getattr(self.canvas, 'arrow_head_stroke_width', 4))
            arrow_head_border_pen.setJoinStyle(Qt.MiterJoin)
            arrow_head_border_pen.setCapStyle(Qt.FlatCap)

            # Calculate the tangent at the endpoint to determine arrow direction
            # Use a point very close to the end to get the tangent
            tangent_at_end = self.calculate_cubic_tangent(0.999)
            len_at_end = math.hypot(tangent_at_end.x(), tangent_at_end.y())

            if len_at_end > 0:
                # Unit vector pointing along the curve at the endpoint
                unit_vector_shaft = QPointF(tangent_at_end.x() / len_at_end, tangent_at_end.y() / len_at_end)

                # Perpendicular vector to the shaft direction (for arrow width)
                perp_vector = QPointF(-unit_vector_shaft.y(), unit_vector_shaft.x())

                # Calculate the two base corners at the endpoint
                left_point = self.end + perp_vector * (arrow_head_width / 2)
                right_point = self.end - perp_vector * (arrow_head_width / 2)

                # Calculate tip position extending outward from the endpoint
                # The tip should be arrow_head_len away from the endpoint along the shaft direction
                tip = self.end + unit_vector_shaft * arrow_head_len

                # --- Draw Shaft (the entire strand path) ---
                full_arrow_shaft_line_width = getattr(self.canvas, 'arrow_line_width', 10)
                # Use custom arrow color for shaft if set
                shaft_color = getattr(self, 'arrow_color', self.stroke_color)
                if hasattr(self, 'arrow_transparency'):
                    shaft_color = QColor(shaft_color)
                    shaft_color.setAlphaF(self.arrow_transparency / 100.0)

                # Use the exact strand path as the shaft
                shaft_path = self.get_path()  # This uses all the control points and bias settings

                # Draw the shaft with pattern (entire strand path)
                self.draw_arrow_shaft_with_pattern(painter, shaft_path, shaft_color, full_arrow_shaft_line_width)
                # --- End Shaft ---
                
                # Create the arrow polygon
                arrow_head_poly = QPolygonF([tip, left_point, right_point])

                # Fill the arrow with optional texture (only if arrow head is visible)
                if getattr(self, 'arrow_head_visible', True):
                    painter.setPen(Qt.NoPen)
                    self.apply_arrow_texture_brush(painter, arrow_head_fill_color)
                    painter.drawPolygon(arrow_head_poly)

                    # Draw the border
                    painter.setPen(arrow_head_border_pen)
                    painter.setBrush(Qt.NoBrush)
                    painter.drawPolygon(arrow_head_poly)
            painter.restore()
        # --- END Draw full strand arrow on TOP ---

        # Ensure the initial save is restored
        painter.restore() # RESTORE 1
    def _draw_direct(self, painter):
        """Draw the attached strand directly to the painter without temporary image optimization.
        This method is used when zoomed to avoid clipping issues with bounds calculations."""
        from attached_strand import AttachedStrand
        from masked_strand import MaskedStrand          
        
        # Ensure high-quality rendering for direct drawing
        RenderUtils.setup_painter(painter, enable_high_quality=True)
        
        # --- Handle hidden state comprehensively ---
        if self.is_hidden:
            # Draw arrow shadow first if arrow casts shadow is enabled
            if getattr(self, 'full_arrow_visible', False) and getattr(self, 'arrow_casts_shadow', False):
                painter.save()
                try:
                    from shader_utils import draw_strand_shadow
                    # Draw arrow shadow even when strand is hidden
                    shadow_color = None
                    if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'default_shadow_color'):
                        shadow_color = self.canvas.default_shadow_color
                        self.shadow_color = QColor(shadow_color)

                    draw_strand_shadow(painter, self, shadow_color,
                                      num_steps=self.canvas.num_steps if hasattr(self.canvas, 'num_steps') else 3,
                                      max_blur_radius=self.canvas.max_blur_radius if hasattr(self.canvas, 'max_blur_radius') else 29.99)
                except Exception as e:
                    pass
                finally:
                    painter.restore()

            # Draw full arrow if requested
            if getattr(self, 'full_arrow_visible', False):
                painter.save() # Specific save for this drawing operation
                
                # --- Draw Arrowhead extending outward from the endpoint ---
                arrow_head_len = getattr(self.canvas, 'arrow_head_length', 20)
                arrow_head_width = getattr(self.canvas, 'arrow_head_width', 10)

                # Use custom arrow color if set, otherwise default to strand color
                default_arrow_head_fill_color = self.color if self.color else QColor(Qt.black)
                if hasattr(self, 'arrow_color'):
                    arrow_head_fill_color = self.arrow_color
                else:
                    arrow_head_fill_color = self.canvas.default_arrow_fill_color if hasattr(self.canvas, 'use_default_arrow_color') and not self.canvas.use_default_arrow_color else default_arrow_head_fill_color

                # Apply transparency if set
                if hasattr(self, 'arrow_transparency'):
                    transparency = self.arrow_transparency / 100.0  # Convert from percentage to 0-1
                    arrow_head_fill_color = QColor(arrow_head_fill_color)
                    arrow_head_fill_color.setAlphaF(transparency)
                
                arrow_head_border_pen = QPen(self.stroke_color, getattr(self.canvas, 'arrow_head_stroke_width', 4))
                arrow_head_border_pen.setJoinStyle(Qt.MiterJoin)
                arrow_head_border_pen.setCapStyle(Qt.FlatCap)

                # Calculate the tangent at the endpoint to determine arrow direction
                # Use a point very close to the end to get the tangent
                tangent_at_end = self.calculate_cubic_tangent(0.999)
                len_at_end = math.hypot(tangent_at_end.x(), tangent_at_end.y())
                
                if len_at_end > 0:
                    # Unit vector pointing along the curve at the endpoint
                    unit_vector_shaft = QPointF(tangent_at_end.x() / len_at_end, tangent_at_end.y() / len_at_end)
                    
                    # Perpendicular vector to the shaft direction (for arrow width)
                    perp_vector = QPointF(-unit_vector_shaft.y(), unit_vector_shaft.x())

                    # Calculate the two base corners at the endpoint
                    left_point = self.end + perp_vector * (arrow_head_width / 2)
                    right_point = self.end - perp_vector * (arrow_head_width / 2)

                    # Calculate tip position extending outward from the endpoint
                    # The tip should be arrow_head_len away from the endpoint along the shaft direction
                    tip = self.end + unit_vector_shaft * arrow_head_len
                    
                    # --- Draw Shaft (the entire strand path) ---
                    full_arrow_shaft_line_width = getattr(self.canvas, 'arrow_line_width', 10)
                    # Use custom arrow color for shaft if set
                    shaft_color = getattr(self, 'arrow_color', self.stroke_color)
                    if hasattr(self, 'arrow_transparency'):
                        shaft_color = QColor(shaft_color)
                        shaft_color.setAlphaF(self.arrow_transparency / 100.0)

                    # Use the exact strand path as the shaft
                    shaft_path = self.get_path()  # This uses all the control points and bias settings

                    # Draw the shaft with pattern (entire strand path)
                    self.draw_arrow_shaft_with_pattern(painter, shaft_path, shaft_color, full_arrow_shaft_line_width)
                    # --- End Shaft ---
                    
                    # Create the arrow polygon
                    arrow_head_poly = QPolygonF([tip, left_point, right_point])
                    
                    # Fill the arrow (only if arrow head is visible)
                    if getattr(self, 'arrow_head_visible', True):
                        painter.setPen(Qt.NoPen)
                        self.apply_arrow_texture_brush(painter, arrow_head_fill_color)
                        painter.drawPolygon(arrow_head_poly)

                        # Draw the border
                        painter.setPen(arrow_head_border_pen)
                        painter.setBrush(Qt.NoBrush)
                        painter.drawPolygon(arrow_head_poly)
                painter.restore() # Specific restore for full arrow

            # Draw dashed extension lines if requested when hidden
            ext_len_hidden = getattr(self.canvas, 'extension_length', 100)
            dash_count_hidden = getattr(self.canvas, 'extension_dash_count', 10)
            dash_width_hidden = getattr(self.canvas, 'extension_dash_width', self.stroke_width)
            dash_seg_hidden = ext_len_hidden / (2 * dash_count_hidden) if dash_count_hidden > 0 else ext_len_hidden
            dash_gap_hidden = getattr(self.canvas, 'extension_dash_gap_length', dash_seg_hidden); dash_gap_hidden = -dash_gap_hidden
            
            side_color_hidden_dash = QColor(self.stroke_color)
            if self.color: side_color_hidden_dash.setAlpha(self.color.alpha())
            else: side_color_hidden_dash.setAlpha(255)
            
            dash_pen_hidden_ext = QPen(side_color_hidden_dash, dash_width_hidden, Qt.CustomDashLine)
            pattern_len_hidden_ext = dash_seg_hidden / dash_width_hidden if dash_width_hidden > 0 else dash_seg_hidden
            dash_pen_hidden_ext.setDashPattern([pattern_len_hidden_ext, pattern_len_hidden_ext])
            dash_pen_hidden_ext.setCapStyle(Qt.FlatCap)

            if getattr(self, 'start_extension_visible', False) or getattr(self, 'end_extension_visible', False):
                painter.save()
                painter.setPen(dash_pen_hidden_ext)
                if getattr(self, 'start_extension_visible', False):
                    tangent_hidden_start_ext = self.calculate_cubic_tangent(0.0); length_hidden_start_ext = math.hypot(tangent_hidden_start_ext.x(), tangent_hidden_start_ext.y())
                    if length_hidden_start_ext: unit_hidden_start_ext = QPointF(tangent_hidden_start_ext.x()/length_hidden_start_ext, tangent_hidden_start_ext.y()/length_hidden_start_ext); raw_end_hidden_start_ext = QPointF(self.start.x() - unit_hidden_start_ext.x()*ext_len_hidden, self.start.y() - unit_hidden_start_ext.y()*ext_len_hidden); start_pt_hidden_start_ext = QPointF(self.start.x() + unit_hidden_start_ext.x()*dash_gap_hidden, self.start.y() + unit_hidden_start_ext.y()*dash_gap_hidden); end_pt_hidden_start_ext = QPointF(raw_end_hidden_start_ext.x() + unit_hidden_start_ext.x()*dash_gap_hidden, raw_end_hidden_start_ext.y() + unit_hidden_start_ext.y()*dash_gap_hidden); painter.drawLine(start_pt_hidden_start_ext, end_pt_hidden_start_ext)
                if getattr(self, 'end_extension_visible', False):
                    tangent_hidden_end_ext = self.calculate_cubic_tangent(1.0); length_hidden_end_ext = math.hypot(tangent_hidden_end_ext.x(), tangent_hidden_end_ext.y())
                    if length_hidden_end_ext: unit_end_hidden_ext = QPointF(tangent_hidden_end_ext.x()/length_hidden_end_ext, tangent_hidden_end_ext.y()/length_hidden_end_ext); raw_end_hidden_end_ext = QPointF(self.end.x() + unit_end_hidden_ext.x()*ext_len_hidden, self.end.y() + unit_end_hidden_ext.y()*ext_len_hidden); start_pt_hidden_end_ext = QPointF(self.end.x() - unit_end_hidden_ext.x()*dash_gap_hidden, self.end.y() - unit_end_hidden_ext.y()*dash_gap_hidden); end_pt_hidden_end_ext = QPointF(raw_end_hidden_end_ext.x() - unit_end_hidden_ext.x()*dash_gap_hidden, raw_end_hidden_end_ext.y() - unit_end_hidden_ext.y()*dash_gap_hidden); painter.drawLine(start_pt_hidden_end_ext, end_pt_hidden_end_ext)
                painter.restore()

            # Draw individual start/end arrows if requested when hidden
            arrow_len_hidden_indiv = getattr(self.canvas, 'arrow_head_length', 20)
            arrow_width_hidden_indiv = getattr(self.canvas, 'arrow_head_width', 10)
            arrow_gap_length_hidden_indiv = getattr(self.canvas, 'arrow_gap_length', 10)
            arrow_line_length_hidden_indiv = getattr(self.canvas, 'arrow_line_length', 20)
            arrow_line_width_hidden_indiv = getattr(self.canvas, 'arrow_line_width', 10)
            
            default_fill_color_hidden_indiv = self.color if self.color else QColor(Qt.black)
            fill_color_hidden_indiv = self.canvas.default_arrow_fill_color if hasattr(self.canvas, 'use_default_arrow_color') and not self.canvas.use_default_arrow_color else default_fill_color_hidden_indiv
            
            border_pen_hidden_indiv = QPen(self.stroke_color, getattr(self.canvas, 'arrow_head_stroke_width', 4))
            border_pen_hidden_indiv.setJoinStyle(Qt.MiterJoin)
            border_pen_hidden_indiv.setCapStyle(Qt.FlatCap)

            if getattr(self, 'start_arrow_visible', False) or getattr(self, 'end_arrow_visible', False):
                painter.save()
                
                # Draw start arrow if visible
                if getattr(self, 'start_arrow_visible', False):
                    # Calculate tangent and unit vector
                    tangent_s = self.calculate_cubic_tangent(0.0)
                    len_s = math.hypot(tangent_s.x(), tangent_s.y())
                    if len_s:
                        unit_s = QPointF(tangent_s.x() / len_s, tangent_s.y() / len_s)
                        arrow_dir_s = QPointF(-unit_s.x(), -unit_s.y())
                        
                        # Calculate shaft points
                        shaft_start_s = QPointF(
                            self.start.x() + arrow_dir_s.x() * arrow_gap_length_hidden_indiv,
                            self.start.y() + arrow_dir_s.y() * arrow_gap_length_hidden_indiv
                        )
                        shaft_end_s = QPointF(
                            shaft_start_s.x() + arrow_dir_s.x() * arrow_line_length_hidden_indiv,
                            shaft_start_s.y() + arrow_dir_s.y() * arrow_line_length_hidden_indiv
                        )
                        
                        # Draw shaft line
                        line_pen_s = QPen(self.stroke_color, arrow_line_width_hidden_indiv)
                        line_pen_s.setCapStyle(Qt.FlatCap)
                        painter.setPen(line_pen_s)
                        painter.setBrush(Qt.NoBrush)
                        painter.drawLine(shaft_start_s, shaft_end_s)
                        
                        # Calculate arrow head points
                        base_center_s = shaft_end_s
                        tip_s = QPointF(
                            base_center_s.x() + arrow_dir_s.x() * arrow_len_hidden_indiv,
                            base_center_s.y() + arrow_dir_s.y() * arrow_len_hidden_indiv
                        )
                        perp_s = QPointF(-arrow_dir_s.y(), arrow_dir_s.x())
                        left_s = QPointF(
                            base_center_s.x() + perp_s.x() * arrow_width_hidden_indiv / 2,
                            base_center_s.y() + perp_s.y() * arrow_width_hidden_indiv / 2
                        )
                        right_s = QPointF(
                            base_center_s.x() - perp_s.x() * arrow_width_hidden_indiv / 2,
                            base_center_s.y() - perp_s.y() * arrow_width_hidden_indiv / 2
                        )
                        
                        # Draw arrow head
                        arrow_poly_s = QPolygonF([tip_s, left_s, right_s])
                        painter.setPen(Qt.NoPen)
                        painter.setBrush(fill_color_hidden_indiv)
                        painter.drawPolygon(arrow_poly_s)
                        painter.setPen(border_pen_hidden_indiv)
                        painter.setBrush(Qt.NoBrush)
                        painter.drawPolygon(arrow_poly_s)
                
                # Draw end arrow if visible
                if getattr(self, 'end_arrow_visible', False):
                    # Calculate tangent and unit vector
                    tangent_e = self.calculate_cubic_tangent(1.0)
                    len_e = math.hypot(tangent_e.x(), tangent_e.y())
                    if len_e:
                        unit_e = QPointF(tangent_e.x() / len_e, tangent_e.y() / len_e)
                        arrow_dir_e = QPointF(unit_e.x(), unit_e.y())
                        
                        # Calculate shaft points
                        shaft_start_e = QPointF(
                            self.end.x() + arrow_dir_e.x() * arrow_gap_length_hidden_indiv,
                            self.end.y() + arrow_dir_e.y() * arrow_gap_length_hidden_indiv
                        )
                        shaft_end_e = QPointF(
                            shaft_start_e.x() + arrow_dir_e.x() * arrow_line_length_hidden_indiv,
                            shaft_start_e.y() + arrow_dir_e.y() * arrow_line_length_hidden_indiv
                        )
                        
                        # Draw shaft line
                        line_pen_e = QPen(self.stroke_color, arrow_line_width_hidden_indiv)
                        line_pen_e.setCapStyle(Qt.FlatCap)
                        painter.setPen(line_pen_e)
                        painter.setBrush(Qt.NoBrush)
                        painter.drawLine(shaft_start_e, shaft_end_e)
                        
                        # Calculate arrow head points
                        base_center_e = shaft_end_e
                        tip_e = QPointF(
                            base_center_e.x() + arrow_dir_e.x() * arrow_len_hidden_indiv,
                            base_center_e.y() + arrow_dir_e.y() * arrow_len_hidden_indiv
                        )
                        perp_e = QPointF(-arrow_dir_e.y(), arrow_dir_e.x())
                        left_e = QPointF(
                            base_center_e.x() + perp_e.x() * arrow_width_hidden_indiv / 2,
                            base_center_e.y() + perp_e.y() * arrow_width_hidden_indiv / 2
                        )
                        right_e = QPointF(
                            base_center_e.x() - perp_e.x() * arrow_width_hidden_indiv / 2,
                            base_center_e.y() - perp_e.y() * arrow_width_hidden_indiv / 2
                        )
                        
                        # Draw arrow head
                        arrow_poly_e = QPolygonF([tip_e, left_e, right_e])
                        painter.setPen(Qt.NoPen)
                        painter.setBrush(fill_color_hidden_indiv)
                        painter.drawPolygon(arrow_poly_e)
                        painter.setPen(border_pen_hidden_indiv)
                        painter.setBrush(Qt.NoBrush)
                        painter.drawPolygon(arrow_poly_e)
                
                painter.restore()

            return # Skip drawing strand body etc.
        # --- END Handle hidden state ---

        # Get the path representing the strand as a cubic Bézier curve
        path = self.get_path()

        # Create a stroker for the stroke path
        stroke_stroker = QPainterPathStroker()
        stroke_stroker.setWidth(self.width + self.stroke_width * 2)
        stroke_stroker.setJoinStyle(Qt.MiterJoin)
        stroke_stroker.setCapStyle(Qt.FlatCap)
        stroke_path = stroke_stroker.createStroke(path)

        # Draw shadow for overlapping strands - using the utility function
        try:
            # Import is inside try block to handle potential import errors
            from shader_utils import draw_strand_shadow, draw_circle_shadow
            
            # Only draw shadows if this strand should draw its own shadow
            if not hasattr(self, 'should_draw_shadow') or self.should_draw_shadow:
                # Use canvas's shadow color if available
                shadow_color = None
                if hasattr(self.canvas, 'default_shadow_color'):
                    shadow_color = self.canvas.default_shadow_color
                    # Ensure the strand's shadow color is also updated for future reference
                    self.shadow_color = QColor(shadow_color)
                
                # Draw strand body shadow with explicit shadow color
                draw_strand_shadow(painter, self, shadow_color,
                                  num_steps=self.canvas.num_steps if hasattr(self.canvas, 'num_steps') else 3,
                                  max_blur_radius=self.canvas.max_blur_radius if hasattr(self.canvas, 'max_blur_radius') else 29.99)
                
                # Draw circle shadows if this strand has circles
                if hasattr(self, 'has_circles') and any(self.has_circles):
                    draw_circle_shadow(painter, self, shadow_color)
        except Exception as e:
            # Log the error but continue with the rendering
            pass
      
        # Draw highlight if selected (before shadow-only check so highlights show even in shadow-only mode)
        if self.is_selected and not isinstance(self, MaskedStrand):
            # Create a shortened path for the highlight (10 pixels from each end)
            # Use percentAtLength to get accurate t values for pixel offsets
            total_length = path.length()
            if self.start_circle_stroke_color.alpha() == 0:
                t_start_point = 5.0
            else:
                t_start_point = 0.0
            if self.end_circle_stroke_color.alpha() == 0:
                t_end_point = 5.0
            else:
                t_end_point = 0.0
            if self.start_circle_stroke_color.alpha() == 0 or self.end_circle_stroke_color.alpha() == 0:              
                if total_length > 10:  # Only shorten if path is longer than 20 pixels
                    # Get t values at exactly 10 pixels from start and 10 pixels from end
                    t_start = path.percentAtLength(t_start_point)
                    t_end = path.percentAtLength(total_length - t_end_point)
                    
                    # Create a new path for the shortened highlight
                    highlight_path = QPainterPath()
                    
                    # Sample points along the actual path using pointAtPercent
                    # This correctly handles both 2 and 3 control point configurations
                    num_samples = 50
                    points = []
                    for i in range(num_samples + 1):
                        t = t_start + (t_end - t_start) * (i / num_samples)
                        # Use pointAtPercent to get the actual point on the path
                        # This works correctly for any path configuration (2 or 3 control points)
                        point = path.pointAtPercent(t)
                        points.append(point)
                    
                    # Build the shortened path
                    if points:
                        highlight_path.moveTo(points[0])
                        for point in points[1:]:
                            highlight_path.lineTo(point)
                    
                    # Create stroker for the shortened highlight path
                    highlight_stroker = QPainterPathStroker()
                    highlight_stroker.setWidth(self.width + self.stroke_width * 2)
                    highlight_stroker.setJoinStyle(Qt.MiterJoin)
                    highlight_stroker.setCapStyle(Qt.FlatCap)
                    shortened_stroke_path = highlight_stroker.createStroke(highlight_path)
                    
                    # Draw the shortened highlight
                    highlight_pen = QPen(QColor('red'), 10)
                    highlight_pen.setJoinStyle(Qt.MiterJoin)
                    highlight_pen.setCapStyle(Qt.FlatCap)
                    painter.setPen(highlight_pen)
                    painter.setBrush(Qt.NoBrush)
                    painter.drawPath(shortened_stroke_path)
            else:
                # If path is too short, draw normal highlight
                highlight_pen = QPen(QColor('red'), 10)
                highlight_pen.setJoinStyle(Qt.MiterJoin)
                highlight_pen.setCapStyle(Qt.FlatCap)
                
                painter.setPen(highlight_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(stroke_path)
            # Draw highlight for Strand's side line
            painter.save()
            
            highlight_pen_thickness = 10
            black_half_width = (self.width + self.stroke_width * 2) / 2
            highlight_half_width = black_half_width + (highlight_pen_thickness / 2)

            # Calculate angles of tangents
            tangent_start = self.calculate_cubic_tangent(0.0)
            tangent_end = self.calculate_cubic_tangent(1.0)
            
            # Handle zero-length tangent vectors
            if tangent_start.manhattanLength() == 0:
                tangent_start = self.end - self.start
            if tangent_end.manhattanLength() == 0:
                tangent_end = self.start - self.end

            angle_start = math.atan2(tangent_start.y(), tangent_start.x())
            angle_end = math.atan2(tangent_end.y(), tangent_end.x())
            
            # Perpendicular angles at start and end
            perp_angle_start = angle_start + math.pi / 2
            perp_angle_end = angle_end + math.pi / 2
            
            # Calculate extended positions for end line
            dx_end_extended = highlight_half_width * math.cos(perp_angle_end)
            dy_end_extended = highlight_half_width * math.sin(perp_angle_end)
            dx_start_extended = highlight_half_width * math.cos(perp_angle_start)
            dy_start_extended = highlight_half_width * math.sin(perp_angle_start)
            end_line_start_extended = QPointF(self.end.x() - dx_end_extended, self.end.y() - dy_end_extended)
            end_line_end_extended = QPointF(self.end.x() + dx_end_extended, self.end.y() + dy_end_extended)
            start_line_start_extended = QPointF(self.start.x() - dx_start_extended, self.start.y() - dy_start_extended)
            start_line_end_extended = QPointF(self.start.x() + dx_start_extended, self.start.y() + dy_start_extended)
            # Create a pen for the red sideline highlight
            highlight_pen = QPen(QColor(255, 0, 0, 255), self.stroke_width + 10, Qt.SolidLine)
            highlight_pen.setCapStyle(Qt.FlatCap)
            highlight_pen.setJoinStyle(Qt.MiterJoin)
            
            painter.setPen(highlight_pen)
            painter.setBrush(Qt.NoBrush)
            if self.start_line_visible and not self.has_circles[0] and not self.start_circle_stroke_color.alpha() == 0:
                painter.drawLine(start_line_start_extended, start_line_end_extended)
            # Only draw end line if there's no attached strand on the end
            if self.end_line_visible and not self.has_circles[1] and not self.end_circle_stroke_color.alpha() == 0:
                painter.drawLine(end_line_start_extended, end_line_end_extended)
            
            painter.restore()            


        # --- START: Skip visual rendering in shadow-only mode ---
        if getattr(self, 'shadow_only', False):
            # In shadow-only mode, skip all visual drawing but preserve shadows and highlights
            return
        # --- END: Skip visual rendering in shadow-only mode ---

        # Draw dashed extension lines
        ext_len = getattr(self.canvas, 'extension_length', 100)
        dash_count = getattr(self.canvas, 'extension_dash_count', 10)
        dash_width = getattr(self.canvas, 'extension_dash_width', self.stroke_width)
        # Compute base dash segment length
        dash_seg = ext_len / (2 * dash_count) if dash_count > 0 else ext_len
        # Get configured gap length or default to dash segment
        dash_gap = getattr(self.canvas, 'extension_dash_gap_length', dash_seg)
        dash_gap = -dash_gap 
        # Setup pen for dashed line using side color
        side_color = QColor(self.stroke_color)
        side_color.setAlpha(self.color.alpha())
        dash_pen = QPen(side_color, dash_width, Qt.CustomDashLine)
        # Uniform dash pattern: equal on/off lengths based on dash segment
        pattern_len = dash_seg / dash_width if dash_width > 0 else dash_seg
        dash_pen.setDashPattern([pattern_len, pattern_len])
        dash_pen.setCapStyle(Qt.FlatCap)
        painter.setPen(dash_pen)
        # Draw start extension with gap offsets
        if getattr(self, 'start_extension_visible', False):
            tangent = self.calculate_cubic_tangent(0.0)
            length = math.hypot(tangent.x(), tangent.y())
            if length:
                unit = QPointF(tangent.x()/length, tangent.y()/length)
                raw_end = QPointF(self.start.x() - unit.x()*ext_len, self.start.y() - unit.y()*ext_len)
                start_pt = QPointF(self.start.x() + unit.x()*dash_gap, self.start.y() + unit.y()*dash_gap)
                end_pt = QPointF(raw_end.x() + unit.x()*dash_gap, raw_end.y() + unit.y()*dash_gap)
                painter.drawLine(start_pt, end_pt)
        # Draw end extension with gap offsets
        if getattr(self, 'end_extension_visible', False):
            tangent_end = self.calculate_cubic_tangent(1.0)
            length_end = math.hypot(tangent_end.x(), tangent_end.y())
            if length_end:
                unit_end = QPointF(tangent_end.x()/length_end, tangent_end.y()/length_end)
                raw_end = QPointF(self.end.x() + unit_end.x()*ext_len, self.end.y() + unit_end.y()*ext_len)
                start_pt = QPointF(self.end.x() - unit_end.x()*dash_gap, self.end.y() - unit_end.y()*dash_gap)
                end_pt = QPointF(raw_end.x() - unit_end.x()*dash_gap, raw_end.y() - unit_end.y()*dash_gap)
                painter.drawLine(start_pt, end_pt)

        # Draw arrow heads for attached strands
        arrow_len = getattr(self.canvas, 'arrow_head_length', 20)
        arrow_width = getattr(self.canvas, 'arrow_head_width', 10)
        # Arrow gap and shaft parameters
        arrow_gap_length = getattr(self.canvas, 'arrow_gap_length', 10)
        arrow_line_length = getattr(self.canvas, 'arrow_line_length', 20)
        arrow_line_width = getattr(self.canvas, 'arrow_line_width', 10)
        # Fill and border styling
        if hasattr(self.canvas, 'use_default_arrow_color') and not self.canvas.use_default_arrow_color:
            fill_color = self.canvas.default_arrow_fill_color
        else:
            fill_color = self.color
        border_pen = QPen(self.stroke_color, getattr(self.canvas, 'arrow_head_stroke_width', 4))
        border_pen.setJoinStyle(Qt.MiterJoin)
        border_pen.setCapStyle(Qt.FlatCap)

        # Draw start arrow if visible (gap → shaft → head)
        if getattr(self, 'start_arrow_visible', False):
            tangent_start = self.calculate_cubic_tangent(0.0)
            len_start = math.hypot(tangent_start.x(), tangent_start.y())
            if len_start:
                unit = QPointF(tangent_start.x() / len_start, tangent_start.y() / len_start)
                arrow_dir = QPointF(-unit.x(), -unit.y())
                shaft_start = QPointF(
                    self.start.x() + arrow_dir.x() * arrow_gap_length,
                    self.start.y() + arrow_dir.y() * arrow_gap_length
                )
                shaft_end = QPointF(
                    shaft_start.x() + arrow_dir.x() * arrow_line_length,
                    shaft_start.y() + arrow_dir.y() * arrow_line_length
                )
                line_pen = QPen(self.stroke_color, arrow_line_width)
                line_pen.setCapStyle(Qt.FlatCap)
                painter.setPen(line_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawLine(shaft_start, shaft_end)
                base_center = shaft_end
                tip = QPointF(
                    base_center.x() + arrow_dir.x() * arrow_len,
                    base_center.y() + arrow_dir.y() * arrow_len
                )
                perp = QPointF(-arrow_dir.y(), arrow_dir.x())
                left = QPointF(base_center.x() + perp.x() * arrow_width / 2,
                               base_center.y() + perp.y() * arrow_width / 2)
                right = QPointF(base_center.x() - perp.x() * arrow_width / 2,
                                base_center.y() - perp.y() * arrow_width / 2)
                arrow_poly = QPolygonF([tip, left, right])
                painter.setPen(Qt.NoPen)
                painter.setBrush(fill_color)
                painter.drawPolygon(arrow_poly)
                painter.setPen(border_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPolygon(arrow_poly)

        # Draw end arrow if visible (gap → shaft → head)
        if getattr(self, 'end_arrow_visible', False):
            tangent_end = self.calculate_cubic_tangent(1.0)
            len_end = math.hypot(tangent_end.x(), tangent_end.y())
            if len_end:
                unit = QPointF(tangent_end.x() / len_end, tangent_end.y() / len_end)
                arrow_dir = QPointF(unit.x(), unit.y())
                shaft_start = QPointF(
                    self.end.x() + arrow_dir.x() * arrow_gap_length,
                    self.end.y() + arrow_dir.y() * arrow_gap_length
                )
                shaft_end = QPointF(
                    shaft_start.x() + arrow_dir.x() * arrow_line_length,
                    shaft_start.y() + arrow_dir.y() * arrow_line_length
                )
                line_pen = QPen(self.stroke_color, arrow_line_width)
                line_pen.setCapStyle(Qt.FlatCap)
                painter.setPen(line_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawLine(shaft_start, shaft_end)
                base_center = shaft_end
                tip = QPointF(
                    base_center.x() + arrow_dir.x() * arrow_len,
                    base_center.y() + arrow_dir.y() * arrow_len
                )
                perp = QPointF(-arrow_dir.y(), arrow_dir.x())
                left = QPointF(base_center.x() + perp.x() * arrow_width / 2,
                               base_center.y() + perp.y() * arrow_width / 2)
                right = QPointF(base_center.x() - perp.x() * arrow_width / 2,
                                base_center.y() - perp.y() * arrow_width / 2)
                arrow_poly = QPolygonF([tip, left, right])
                painter.setPen(Qt.NoPen)
                painter.setBrush(fill_color)
                painter.drawPolygon(arrow_poly)
                painter.setPen(border_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPolygon(arrow_poly)


        # Draw the main strand directly to the painter
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.stroke_color)
        painter.drawPath(stroke_path)

        # Draw the fill
        fill_stroker = QPainterPathStroker()
        fill_stroker.setWidth(self.width)
        fill_stroker.setJoinStyle(Qt.MiterJoin)
        fill_stroker.setCapStyle(Qt.FlatCap)
        fill_path = fill_stroker.createStroke(path)
        painter.setBrush(self.color)
        painter.drawPath(fill_path)

        # Draw the end line conditionally
        side_pen = QPen(self.stroke_color, self.stroke_width)
        side_pen.setCapStyle(Qt.FlatCap)

        # Create a new color with the same alpha as the strand's color
        side_color = QColor(self.stroke_color)
        side_color.setAlpha(self.stroke_color.alpha())
        side_pen.setColor(side_color)
        painter.setPen(side_pen)
            # Conditionally draw start line
        if self.start_line_visible:
            painter.drawLine(self.start_line_start, self.start_line_end)
        if self.end_line_visible: # Only draw end line if visible
            painter.drawLine(self.end_line_start, self.end_line_end)

        # Draw circles directly without temporary images
        # Only draw the start circle if explicitly enabled (has_circles[0] == True)
        pass
        if self.has_circles[0]:
            total_diameter = self.width + self.stroke_width * 2
            circle_radius = total_diameter / 2

            # Calculate the angle based on the tangent at the start point
            angle = self.calculate_start_tangent()

            # Check if this is a closed connection (should draw full circle)
            is_closed_connection = hasattr(self, 'closed_connections') and self.closed_connections[0]
            
            # Initialize variables that will be used in highlight drawing
            mask_rect = None
            outer_circle = QPainterPath()
            outer_circle.addEllipse(self.start, circle_radius, circle_radius)
            
            if is_closed_connection:
                # Draw full circle for closed connections
                # Draw the outer circle (stroke) only if visible
                if self.start_circle_stroke_color.alpha() > 0:
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(self.start_circle_stroke_color)
                    #painter.drawPath(outer_circle)
                
                # Draw the inner circle (fill) for closed connections only if visible
                if self.start_circle_stroke_color.alpha() > 0:
                    inner_circle = QPainterPath()
                    inner_circle.addEllipse(self.start, self.width * 0.5, self.width * 0.5)
                    painter.setBrush(self.color)
                    painter.drawPath(inner_circle)
            else:
                # Create the masking rectangle for half circle
                mask_rect = QPainterPath()
                rect_width = total_diameter * 2
                rect_height = total_diameter * 2
                mask_rect.addRect(0, -rect_height / 2, rect_width, rect_height)
                transform = QTransform()
                transform.translate(self.start.x(), self.start.y())
                transform.rotate(math.degrees(angle))  # Rotate based on tangent angle
                mask_rect = transform.map(mask_rect)
                outer_mask = outer_circle.subtracted(mask_rect)

                # Draw the outer circle (stroke)
                # Draw the stroke only if it's visible
                if self.start_circle_stroke_color.alpha() > 0:
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(self.stroke_color)
                    painter.drawPath(outer_mask)

                # Draw the inner semi-circle (fill)
                inner = QPainterPath()
                inner.addEllipse(self.start, self.width * 0.5, self.width * 0.5)
                inner_mask = inner.subtracted(mask_rect)
                painter.setBrush(self.color)
                painter.drawPath(inner_mask)

                # Draw side line that covers the inner circle
                painter.setPen(Qt.NoPen)
                painter.setBrush(self.color)
                just_inner = QPainterPath()
                just_inner.addRect(-self.stroke_width, -self.width*0.5, self.stroke_width , self.width)
                tr_inner = QTransform().translate(self.start.x(), self.start.y())
                tr_inner.rotate(math.degrees(angle))
                just_inner = tr_inner.map(just_inner)
                painter.drawPath(just_inner)
            
            
            
        # Draw ending circle if has_circles == [True, True]
        pass
        if (self.has_circles == [False, True]):
            # Check for attached children that would skip circle drawing
            # Only check parent's attached strands if this strand has a parent (i.e., it's an AttachedStrand)
            parent_children = getattr(self, 'parent', None)
            parent_attached_strands = getattr(parent_children, 'attached_strands', []) if parent_children else []
            


            skip_end_circle = any(
                isinstance(child, AttachedStrand) and child.start == self.end
                for child in parent_attached_strands
            ) or any(
                isinstance(child, AttachedStrand) and child.start == self.end
                for child in getattr(self, 'attached_strands', [])
            )

            total_diameter = self.width + self.stroke_width * 2
            circle_radius = total_diameter / 2



            # Draw End Circle (if not skipped)
            if not skip_end_circle:
                tangent_end = self.calculate_cubic_tangent(1.0)
                angle_end = math.atan2(tangent_end.y(), tangent_end.x())

                # Check if this is a closed connection (should draw full circle)
                is_closed_connection = hasattr(self, 'closed_connections') and self.closed_connections[1]
                
                if is_closed_connection:
                    # Draw full circle for closed connections
                    outer_circle_end = QPainterPath()
                    outer_circle_end.addEllipse(self.end, circle_radius, circle_radius)
                    
                    # Draw the outer circle (stroke) only if visible
                    if self.end_circle_stroke_color.alpha() > 0:
                        painter.setPen(Qt.NoPen)
                        painter.setBrush(self.end_circle_stroke_color)
                        painter.drawPath(outer_circle_end)
                    
                    # Draw the inner circle (fill) for closed connections only if visible
                    if self.end_circle_stroke_color.alpha() > 0:
                        inner_circle_end = QPainterPath()
                        inner_circle_end.addEllipse(self.end, self.width * 0.5, self.width * 0.5)
                        painter.setBrush(self.color)
                        painter.drawPath(inner_circle_end)
                else:
                    # Creating Outer Circle Half-Circle
                    mask_rect_end = QPainterPath()
                    rect_width_end = total_diameter * 2
                    rect_height_end = total_diameter * 2
                    mask_rect_end.addRect(-rect_width_end, -rect_height_end / 2, rect_width_end, rect_height_end)
                    transform_end = QTransform()
                    transform_end.translate(self.end.x(), self.end.y())
                    transform_end.rotate(math.degrees(angle_end))
                    mask_rect_end = transform_end.map(mask_rect_end)
                    outer_circle_end = QPainterPath()
                    outer_circle_end.addEllipse(self.end, circle_radius, circle_radius)
                    outer_mask_end = outer_circle_end.subtracted(mask_rect_end)

                    # Debug: draw the outer semi-circle stroke in red (regardless of alpha)
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(self.stroke_color)
                    painter.drawPath(outer_mask_end)
                    # Draw the inner semi-circle fill
                    inner = QPainterPath()
                    inner.addEllipse(self.end, self.width * 0.5, self.width * 0.5)
                    inner_mask_end = inner.subtracted(mask_rect_end)
                    painter.setBrush(self.color)
                    painter.drawPath(inner_mask_end)

                    # Draw side line that covers the inner circle
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(self.color)
                    just_inner = QPainterPath()
                    just_inner.addRect(-self.stroke_width,  -self.width*0.5, self.stroke_width, self.width)
                    tr_inner = QTransform().translate(self.end.x(), self.end.y())
                    tr_inner.rotate(math.degrees(angle_end))
                    just_inner = tr_inner.map(just_inner)
                    painter.drawPath(just_inner)
        # Draw ending circle if has_circles == [True, True]
        pass
        if (self.has_circles == [True, True]):
            # Check for attached children that would skip circle drawing
            # Only check parent's attached strands if this strand has a parent (i.e., it's an AttachedStrand)
            parent_children = getattr(self, 'parent', None)
            parent_attached_strands = getattr(parent_children, 'attached_strands', []) if parent_children else []
            
            skip_start_circle = any(
                isinstance(child, AttachedStrand) and child.start == self.start
                for child in parent_attached_strands
            ) or any(
                isinstance(child, AttachedStrand) and child.start == self.start
                for child in getattr(self, 'attached_strands', [])
            )

            skip_end_circle = any(
                isinstance(child, AttachedStrand) and child.start == self.end
                for child in parent_attached_strands
            ) or any(
                isinstance(child, AttachedStrand) and child.start == self.end
                for child in getattr(self, 'attached_strands', [])
            )

            total_diameter = self.width + self.stroke_width * 2
            circle_radius = total_diameter / 2

            # Draw Start Circle (if not skipped)
            if not skip_start_circle:
                angle_start = self.calculate_start_tangent()

                # Creating Outer Circle Half-Circle
                mask_rect_start = QPainterPath()
                rect_width_start = total_diameter * 2
                rect_height_start = total_diameter * 2
                mask_rect_start.addRect(0, -rect_height_start / 2, rect_width_start, rect_height_start)
                transform_start = QTransform()
                transform_start.translate(self.start.x(), self.start.y())
                transform_start.rotate(math.degrees(angle_start))
                mask_rect_start = transform_start.map(mask_rect_start)
                outer_circle_start = QPainterPath()
                outer_circle_start.addEllipse(self.start, circle_radius, circle_radius)
                outer_mask_start = outer_circle_start.subtracted(mask_rect_start)

                # Draw stroke (debug red for outer semi-circle)
                painter.setPen(Qt.NoPen)
                painter.setBrush(self.stroke_color)
                painter.drawPath(outer_mask_start)
                
                # Draw inner semi-circle using main color
                inner = QPainterPath()
                inner.addEllipse(self.start, self.width * 0.5, self.width * 0.5)
                inner_mask_start = inner.subtracted(mask_rect_start)
                painter.setBrush(self.color)
                painter.drawPath(inner_mask_start)

                # Draw side line that covers the inner circle
                painter.setPen(Qt.NoPen)
                painter.setBrush(self.color)
                just_inner = QPainterPath()
                just_inner.addRect(-self.stroke_width,  -self.width*0.5, self.stroke_width , self.width)
                tr_inner = QTransform().translate(self.start.x(), self.start.y())
                tr_inner.rotate(math.degrees(angle_start))
                just_inner = tr_inner.map(just_inner)
                painter.drawPath(just_inner)

            # Draw End Circle (if not skipped)
            if not skip_end_circle:
                tangent_end = self.calculate_cubic_tangent(1.0)
                angle_end = math.atan2(tangent_end.y(), tangent_end.x())

                # Check if this is a closed connection (should draw full circle)
                is_closed_connection = hasattr(self, 'closed_connections') and self.closed_connections[1]
                
                if is_closed_connection:
                    # Draw full circle for closed connections
                    outer_circle_end = QPainterPath()
                    outer_circle_end.addEllipse(self.end, circle_radius, circle_radius)
                    
                    # Draw the outer circle (stroke) only if visible
                    if self.end_circle_stroke_color.alpha() > 0:
                        painter.setPen(Qt.NoPen)
                        painter.setBrush(self.end_circle_stroke_color)
                        painter.drawPath(outer_circle_end)
                    
                    # Draw the inner circle (fill) for closed connections only if visible
                    if self.end_circle_stroke_color.alpha() > 0:
                        inner_circle_end = QPainterPath()
                        inner_circle_end.addEllipse(self.end, self.width * 0.5, self.width * 0.5)
                        painter.setBrush(self.color)
                        painter.drawPath(inner_circle_end)
                else:
                    # Creating Outer Circle Half-Circle
                    mask_rect_end = QPainterPath()
                    rect_width_end = total_diameter * 2
                    rect_height_end = total_diameter * 2
                    mask_rect_end.addRect(-rect_width_end, -rect_height_end / 2, rect_width_end, rect_height_end)
                    transform_end = QTransform()
                    transform_end.translate(self.end.x(), self.end.y())
                    transform_end.rotate(math.degrees(angle_end))
                    mask_rect_end = transform_end.map(mask_rect_end)
                    outer_circle_end = QPainterPath()
                    outer_circle_end.addEllipse(self.end, circle_radius, circle_radius)
                    outer_mask_end = outer_circle_end.subtracted(mask_rect_end)

                    # Draw the outer circle stroke only if visible (debug red for outer semi-circle)
                    if self.end_circle_stroke_color.alpha() > 0:
                        painter.setPen(Qt.NoPen)
                        painter.setBrush(self.stroke_color)
                        painter.drawPath(outer_mask_end)
                    
                    # Draw the inner semi-circle fill
                    inner = QPainterPath()
                    inner.addEllipse(self.end, self.width * 0.5, self.width * 0.5)
                    inner_mask_end = inner.subtracted(mask_rect_end)
                    painter.setBrush(self.color)
                    painter.drawPath(inner_mask_end)

                    # Draw side line that covers the inner circle
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(self.color)
                    just_inner = QPainterPath()
                    just_inner.addRect(-self.stroke_width,  -self.width*0.5, self.stroke_width , self.width)
                    tr_inner = QTransform().translate(self.end.x(), self.end.y())
                    tr_inner.rotate(math.degrees(angle_end))
                    just_inner = tr_inner.map(just_inner)
                    painter.drawPath(just_inner)

        # --- NEW: Draw semi-circles on top for closed connections (direct drawing) ---
        # Draw semi-circle on top when start connection is closed
        if hasattr(self, 'closed_connections') and self.closed_connections[0]:
            tangent = self.calculate_cubic_tangent(0.0)
            angle = math.atan2(tangent.y(), tangent.x())
            total_d = self.width + self.stroke_width * 2
            radius = total_d / 2

            # Creating Outer Circle Half-Circle (same as AttachedStrand logic)
            mask = QPainterPath()
            rect_width = total_d * 2
            rect_height = total_d * 2
            mask.addRect(0, -rect_height / 2, rect_width, rect_height)
            tr = QTransform().translate(self.start.x(), self.start.y())
            tr.rotate(math.degrees(angle))
            mask = tr.map(mask)
            outer = QPainterPath()
            outer.addEllipse(self.start, radius, radius)
            clip = outer.subtracted(mask)
            # Draw the stroke only if it's visible
            if self.start_circle_stroke_color.alpha() > 0:
                painter.setPen(Qt.NoPen)
                painter.setBrush(self.stroke_color)
                painter.drawPath(clip)

            # Draw the inner circle (fill) only if stroke is visible
            # When stroke is transparent, don't draw any part of the circle
            if self.start_circle_stroke_color.alpha() > 0:
                inner = QPainterPath()
                inner.addEllipse(self.start, self.width * 0.5, self.width * 0.5)
                painter.setBrush(self.color)
                painter.drawPath(inner)

            # Draw side line that covers the inner circle (only when stroke is visible)
            if self.start_circle_stroke_color.alpha() > 0:
                painter.setPen(Qt.NoPen)
                painter.setBrush(self.color)
                just_inner = QPainterPath()
                just_inner.addRect(-self.stroke_width,  -self.width*0.5, self.stroke_width , self.width)
                tr_inner = QTransform().translate(self.start.x(), self.start.y())
                tr_inner.rotate(math.degrees(angle))
                just_inner = tr_inner.map(just_inner)
                painter.drawPath(just_inner)

        # Draw semi-circle on top when end connection is closed
        if hasattr(self, 'closed_connections') and self.closed_connections[1]:
            tangent = self.calculate_cubic_tangent(1.0)
            angle = math.atan2(tangent.y(), tangent.x())
            total_d = self.width + self.stroke_width * 2
            radius = total_d / 2

            # Creating Outer Circle Half-Circle (same as AttachedStrand logic)
            mask = QPainterPath()
            rect_width = total_d * 2
            rect_height = total_d * 2
            mask.addRect(-rect_width, -rect_height/2, rect_width, rect_height)
            tr = QTransform().translate(self.end.x(), self.end.y())
            tr.rotate(math.degrees(angle))
            mask = tr.map(mask)
            outer = QPainterPath()
            outer.addEllipse(self.end, radius, radius)
            clip = outer.subtracted(mask)
            # Draw the stroke only if it's visible
            if self.end_circle_stroke_color.alpha() > 0:
                painter.setPen(Qt.NoPen)
                painter.setBrush(self.stroke_color)
                painter.drawPath(clip)

            # Draw the inner circle (fill) only if stroke is visible
            # When stroke is transparent, don't draw any part of the circle
            if self.end_circle_stroke_color.alpha() > 0:
                inner = QPainterPath()
                inner.addEllipse(self.end, self.width * 0.5, self.width * 0.5)
                painter.setBrush(self.color)
                painter.drawPath(inner)

            # Draw side line that covers the inner circle (only when stroke is visible)
            if self.end_circle_stroke_color.alpha() > 0:
                painter.setPen(Qt.NoPen)
                painter.setBrush(self.color) 
                just_inner = QPainterPath()
                just_inner.addRect(-self.stroke_width,  -self.width*0.5, self.stroke_width, self.width)
                tr_inner = QTransform().translate(self.end.x(), self.end.y())
                tr_inner.rotate(math.degrees(angle))
                just_inner = tr_inner.map(just_inner)
                painter.drawPath(just_inner)
        # --- END NEW ---

        # Draw half-circle attachments at endpoints where there are AttachedStrand children
        # (This would use the same logic as in the original draw method, but directly to painter)
        # Start endpoint half-circle
        if self.has_circles[0] and any(isinstance(child, AttachedStrand) and child.start == self.start for child in self.attached_strands):
            tangent = self.calculate_cubic_tangent(0.0)
            angle = math.atan2(tangent.y(), tangent.x())
            total_d = self.width + self.stroke_width * 2
            radius = total_d / 2

            # Creating Outer Circle Half-Circle
            mask = QPainterPath()
            rect_width = total_d * 2
            rect_height = total_d * 2
            mask.addRect(0, -rect_height / 2, rect_width, rect_height)
            tr = QTransform().translate(self.start.x(), self.start.y())
            tr.rotate(math.degrees(angle))
            mask = tr.map(mask)
            outer = QPainterPath()
            outer.addEllipse(self.start, radius, radius)
            clip = outer.subtracted(mask)
            painter.setPen(Qt.NoPen)
            painter.setBrush(self.stroke_color)
            painter.drawPath(clip)

            # Draw the inner circle (fill) only if stroke is visible
            # When stroke is transparent, don't draw any part of the circle
            if self.start_circle_stroke_color.alpha() > 0:
                inner = QPainterPath()
                inner.addEllipse(self.start, self.width * 0.5, self.width * 0.5)
                painter.setBrush(self.color)
                painter.drawPath(inner)

            # Draw side line that covers the inner circle (only when stroke is visible)
            if self.start_circle_stroke_color.alpha() > 0:
                painter.setPen(Qt.NoPen)
                painter.setBrush(self.color)
                just_inner = QPainterPath()
                just_inner.addRect(-self.stroke_width,  -self.width*0.5, self.stroke_width , self.width)
                tr_inner = QTransform().translate(self.start.x(), self.start.y())
                tr_inner.rotate(math.degrees(angle))
                just_inner = tr_inner.map(just_inner)
                painter.drawPath(just_inner)

        # End endpoint half-circle (only if circle is enabled and child is not in shadow-only mode)
        if self.has_circles[1] and any(isinstance(child, AttachedStrand) and child.start == self.end and not getattr(child, 'shadow_only', False) for child in self.attached_strands):
            tangent = self.calculate_cubic_tangent(1.0)
            angle = math.atan2(tangent.y(), tangent.x())
            total_d = self.width + self.stroke_width * 2
            radius = total_d / 2

            # Creating Outer Circle Half-Circle
            mask = QPainterPath()
            rect_width = total_d * 2
            rect_height = total_d * 2
            mask.addRect(-rect_width, -rect_height/2, rect_width, rect_height)
            tr = QTransform().translate(self.end.x(), self.end.y())
            tr.rotate(math.degrees(angle))
            mask = tr.map(mask)
            outer = QPainterPath()
            outer.addEllipse(self.end, radius, radius)
            clip = outer.subtracted(mask)
            painter.setPen(Qt.NoPen)
            painter.setBrush(self.stroke_color)
            painter.drawPath(clip)

            # Draw the inner circle (fill) only if stroke is visible
            # When stroke is transparent, don't draw any part of the circle
            if self.end_circle_stroke_color.alpha() > 0:
                inner = QPainterPath()
                inner.addEllipse(self.end, self.width * 0.5, self.width * 0.5)
                painter.setBrush(self.color)
                painter.drawPath(inner)

            # Draw side line that covers the inner circle (only when stroke is visible)
            if self.end_circle_stroke_color.alpha() > 0:
                painter.setPen(Qt.NoPen)
                painter.setBrush(self.color) 
                just_inner = QPainterPath()
                just_inner.addRect(-self.stroke_width,  -self.width*0.5, self.stroke_width, self.width)
                tr_inner = QTransform().translate(self.end.x(), self.end.y())
                tr_inner.rotate(math.degrees(angle))
                just_inner = tr_inner.map(just_inner)
                painter.drawPath(just_inner)

        # --- Draw full strand arrow on TOP of strand body (if not hidden) ---
        if getattr(self, 'full_arrow_visible', False): # 'not self.is_hidden' is implicit due to earlier return
            painter.save()

            # --- Draw Arrowhead extending outward from the endpoint ---
            arrow_head_len = getattr(self.canvas, 'arrow_head_length', 20)
            arrow_head_width = getattr(self.canvas, 'arrow_head_width', 10)

            # Use custom arrow color if set, otherwise default to strand color
            default_arrow_head_fill_color = self.color if self.color else QColor(Qt.black)
            if hasattr(self, 'arrow_color'):
                arrow_head_fill_color = self.arrow_color
            else:
                arrow_head_fill_color = self.canvas.default_arrow_fill_color if hasattr(self.canvas, 'use_default_arrow_color') and not self.canvas.use_default_arrow_color else default_arrow_head_fill_color

            # Apply transparency if set
            if hasattr(self, 'arrow_transparency'):
                transparency = self.arrow_transparency / 100.0  # Convert from percentage to 0-1
                arrow_head_fill_color = QColor(arrow_head_fill_color)
                arrow_head_fill_color.setAlphaF(transparency)

            arrow_head_border_pen = QPen(self.stroke_color, getattr(self.canvas, 'arrow_head_stroke_width', 4))
            arrow_head_border_pen.setJoinStyle(Qt.MiterJoin)
            arrow_head_border_pen.setCapStyle(Qt.FlatCap)

            # Calculate the tangent at the endpoint to determine arrow direction
            # Use a point very close to the end to get the tangent
            tangent_at_end = self.calculate_cubic_tangent(0.999)
            len_at_end = math.hypot(tangent_at_end.x(), tangent_at_end.y())

            if len_at_end > 0:
                # Unit vector pointing along the curve at the endpoint
                unit_vector_shaft = QPointF(tangent_at_end.x() / len_at_end, tangent_at_end.y() / len_at_end)

                # Perpendicular vector to the shaft direction (for arrow width)
                perp_vector = QPointF(-unit_vector_shaft.y(), unit_vector_shaft.x())

                # Calculate the two base corners at the endpoint
                left_point = self.end + perp_vector * (arrow_head_width / 2)
                right_point = self.end - perp_vector * (arrow_head_width / 2)

                # Calculate tip position extending outward from the endpoint
                # The tip should be arrow_head_len away from the endpoint along the shaft direction
                tip = self.end + unit_vector_shaft * arrow_head_len

                # --- Draw Shaft (the entire strand path) ---
                full_arrow_shaft_line_width = getattr(self.canvas, 'arrow_line_width', 10)
                # Use custom arrow color for shaft if set
                shaft_color = getattr(self, 'arrow_color', self.stroke_color)
                if hasattr(self, 'arrow_transparency'):
                    shaft_color = QColor(shaft_color)
                    shaft_color.setAlphaF(self.arrow_transparency / 100.0)

                # Use the exact strand path as the shaft
                shaft_path = self.get_path()  # This uses all the control points and bias settings

                # Draw the shaft with pattern (entire strand path)
                self.draw_arrow_shaft_with_pattern(painter, shaft_path, shaft_color, full_arrow_shaft_line_width)
                # --- End Shaft ---

                # Create the arrow polygon
                arrow_head_poly = QPolygonF([tip, left_point, right_point])

                # Fill the arrow (only if arrow head is visible)
                if getattr(self, 'arrow_head_visible', True):
                    painter.setPen(Qt.NoPen)
                    self.apply_arrow_texture_brush(painter, arrow_head_fill_color)
                    painter.drawPolygon(arrow_head_poly)

                    # Draw the border
                    painter.setPen(arrow_head_border_pen)
                    painter.setBrush(Qt.NoBrush)
                    painter.drawPolygon(arrow_head_poly)
            painter.restore() # Specific restore for full arrow

    def remove_attached_strands(self):
        """Recursively remove all attached strands."""
        for attached_strand in self.attached_strands:
            attached_strand.remove_attached_strands()
        self.attached_strands.clear()

    def is_attachable(self):
        """
        Determine if the strand is attachable.
        Returns True if the strand is attachable, False otherwise.
        """
        # A strand is not attachable if both ends have circles (i.e., has_circles is [True, True])
        return not all(self.has_circles)


    def is_point_near(self, pos):
        """Check if a point is within the start or end selection path."""
        contains_start = self.get_start_selection_path().contains(pos)
        contains_end = self.get_end_selection_path().contains(pos)
        return contains_start or contains_end
    def update_control_points_from_geometry(self):
        """Update control points based on current start and end positions."""
        # Calculate control points at 1/3 and 2/3 along the line
        dx = self.end.x() - self.start.x()
        dy = self.end.y() - self.start.y()
        
        self.control_point1 = QPointF(
            self.start.x() + dx / 3,
            self.start.y() + dy / 3
        )
        self.control_point2 = QPointF(
            self.start.x() + 2 * dx / 3,
            self.start.y() + 2 * dy / 3
        )   
        
        # Update the center control point as the midpoint between control_point1 and control_point2
        # Reset the lock status since we're recalculating from geometry
        self.control_point_center = QPointF(
            (self.control_point1.x() + self.control_point2.x()) / 2,
            (self.control_point1.y() + self.control_point2.y()) / 2
        )
        # Reset the lock when recalculating from geometry
        self.control_point_center_locked = False

    def update_control_points(self, reset_control_points=True):
        """
        If reset_control_points=False, do not recalculate them from geometry,
        only re-run update_shape() so we keep the loaded control points.
        """
        if reset_control_points:
            self.update_control_points_from_geometry()
        self.update_shape()
