# src/strand.py

from PyQt5.QtCore import QPointF, Qt, QRectF
from PyQt5.QtGui import (
    QColor, QPainter, QPen, QBrush, QPainterPath, QPainterPathStroker,  QTransform,QImage, QRadialGradient
)
import math
import logging
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
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width
        self.side_line_color = QColor(0, 0, 0, 255)
        self.attached_strands = []  # List to store attached strands
        self.has_circles = [False, False]  # Flags for circles at start and end
        self.is_first_strand = False
        self.is_start_side = True
        self.is_selected = False  # Indicates if the strand is selected

        # Initialize attachment statuses
        self.start_attached = False
        self.end_attached = False

        self.control_point1 = QPointF(
            self.start.x(),
            self.start.y()
        )
        self.control_point2 = QPointF(
            self.start.x(),
            self.start.y()
        )
        
        # Add the center control point (midpoint between control_point1 and control_point2)
        self.control_point_center = QPointF(
            self.start.x(),
            self.start.y()
        )
        # Flag to track if the center control point has been manually positioned
        self.control_point_center_locked = False

        # Add canvas reference
        self.canvas = None

        self.layer_name = layer_name
        self.set_number = set_number
        self._circle_stroke_color = None
        self.update_attachable()
        self.update_shape()
        self.attachable = True  # Initialize as True, will be updated based on has_circles

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
    def circle_stroke_color(self):
        # If nothing was set or loaded, return black as the default:
        if self._circle_stroke_color is None:
            return QColor(0, 0, 0, 255)
        return self._circle_stroke_color

    @circle_stroke_color.setter
    def circle_stroke_color(self, value):
        if value is not None and isinstance(value, (Qt.GlobalColor, int)):
            value = QColor(value)

        # Set a flag to indicate we're just updating transparency, not geometry
        self._setting_circle_transparency = True
        
        if value is None:
            logging.info(f"Setting default circle_stroke_color for {self.layer_name}")
            # If setter is called with None, revert to default black
            self._circle_stroke_color = QColor(0, 0, 0, 255)
        else:
            logging.info(
                f"Setting circle_stroke_color for {self.layer_name} to "
                f"rgba({value.red()}, {value.green()}, {value.blue()}, {value.alpha()})"
            )
            self._circle_stroke_color = value
        
        # Reset the transparency flag after setting the color
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
        # Use the width of the strand for the selection circle
        radius = self.width / 2
        start_path.addEllipse(self.start, radius, radius)
        return start_path
    def draw_path(self, painter):
        """Draw the path of the strand without filling."""
        path = self.get_path()
        painter.drawPath(path)
    def get_end_selection_path(self):
        """Get a selection path for the exact end point of the strand."""
        # Get the path of the strand
        path = self.get_path()
        # Create a small circle at the end point that matches the strand's end
        end_path = QPainterPath()
        # Use the width of the strand for the selection circle
        radius = self.width / 2
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
        self.side_line_color = self.color

    def update_shape(self):
        """Update the shape of the strand based on its start, end, and control points."""
        # Check if we're in the middle of a group move
        if hasattr(self, 'updating_position') and self.updating_position:
            # Only update the side lines without modifying control points
            self.update_side_line()
            return

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

    def get_shadow_path(self):
        """Get the path with extensions for shadow rendering, extending 10px beyond start/end."""
        path = QPainterPath()

        # Check if this is an AttachedStrand with a transparent start circle
        is_attached_transparent_start = False
        # Use class name check for robustness as AttachedStrand is defined later
        if self.__class__.__name__ == 'AttachedStrand':
            # AttachedStrand always has a start circle (has_circles[0] is True)
            # Check transparency using the circle_stroke_color property
            # Add a check for None before accessing alpha()
            circle_color = self.circle_stroke_color
            if circle_color and circle_color.alpha() == 0:
                is_attached_transparent_start = True
                logging.info(f"AttachedStrand {self.layer_name}: Transparent start circle detected, removing shadow extension.")

        if is_attached_transparent_start:
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
                    extended_start = QPointF(self.start.x() - 10, self.start.y()) # Default horizontal
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
                         extended_start = QPointF(self.start.x() - 10, self.start.y()) # Default horizontal
                else:
                    # If start and end are the same, use a default horizontal direction
                    extended_start = QPointF(self.start.x() - 10, self.start.y())

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
                extended_end = QPointF(self.end.x() + 10, self.end.y())
            
        # Create the path with the extended points
        path.moveTo(extended_start)
        path.lineTo(self.start)

        # Only use the third control point if:
        # 1. The feature is enabled AND
        # 2. The control_point_center has been manually positioned
        if (hasattr(self, 'canvas') and self.canvas and 
            hasattr(self.canvas, 'enable_third_control_point') and 
            self.canvas.enable_third_control_point and
            hasattr(self, 'control_point_center_locked') and 
            self.control_point_center_locked):
            
            # Create a smooth spline incorporating all control points
            # We'll use a sequence of cubic Bézier segments with proper tangent continuity
            
            # Extract the key points we're working with
            p0 = self.start
            p1 = self.control_point1
            p2 = self.control_point_center
            p3 = self.control_point2
            p4 = self.end
            
            # Calculate the tangent at start point (pointing toward control_point1)
            start_tangent = QPointF(p1.x() - p0.x(), p1.y() - p0.y())
            
            # Calculate the tangent at center (average of incoming and outgoing)
            in_tangent = QPointF(p2.x() - p1.x(), p2.y() - p1.y())
            out_tangent = QPointF(p3.x() - p2.x(), p3.y() - p2.y())
            
            # Normalize tangents for better control
            def normalize_vector(v):
                length = math.sqrt(v.x() * v.x() + v.y() * v.y())
                if length < 0.001:  # Avoid division by zero
                    return QPointF(0, 0)
                # Preserve vector magnitude better for small movements
                return QPointF(v.x() / length, v.y() / length)
            
            def distance_vector(v):
                return (math.sqrt(v.x() * v.x() + v.y() * v.y()))/(46*6)
            
            start_tangent_normalized = normalize_vector(start_tangent)
            in_tangent_normalized = normalize_vector(in_tangent)
            out_tangent_normalized = normalize_vector(out_tangent)
            
            # Calculate center tangent as weighted average instead of simple average
            # This makes the curve more responsive to small movements
            center_tangent = QPointF(
                0.5 * in_tangent_normalized.x() + 0.5 * out_tangent_normalized.x(), 
                0.5 * in_tangent_normalized.y() + 0.5 * out_tangent_normalized.y()
            )
            center_tangent_normalized = normalize_vector(center_tangent)
            
            # Calculate end tangent
            end_tangent = QPointF(p4.x() - p3.x(), p4.y() - p3.y())
            end_tangent_normalized = normalize_vector(end_tangent)
            
            # Simple distance calculation based on direct distances between points
            dist_p0_p1 = math.sqrt((p1.x() - p0.x())**2 + (p1.y() - p0.y())**2)
            dist_p1_p2 = math.sqrt((p2.x() - p1.x())**2 + (p2.y() - p1.y())**2)
            dist_p2_p3 = math.sqrt((p3.x() - p2.x())**2 + (p3.y() - p2.y())**2)
            dist_p3_p4 = math.sqrt((p4.x() - p3.x())**2 + (p4.y() - p3.y())**2)

            # Fixed fraction for influence
            fraction = 1.0 / 3.0 # Experiment with this value (e.g., 0.5, 0.4)

            # Calculate intermediate control points, incorporating p1 and p3 influence
            # Ensure tangents are non-zero before using them
            cp1 = p0 + start_tangent_normalized * (dist_p0_p1 * fraction) if start_tangent_normalized.manhattanLength() > 1e-6 else p1
            cp2 = p2 - center_tangent_normalized * (dist_p1_p2 * fraction) if center_tangent_normalized.manhattanLength() > 1e-6 else p1

            cp3 = p2 + center_tangent_normalized * (dist_p2_p3 * fraction) if center_tangent_normalized.manhattanLength() > 1e-6 else p3
            cp4 = p4 - end_tangent_normalized * (dist_p3_p4 * fraction) if end_tangent_normalized.manhattanLength() > 1e-6 else p3
            
            # First segment: start to center
            path.cubicTo(cp1, cp2, p2)
            
            # Second segment: center to end
            path.cubicTo(cp3, cp4, p4)
        else:
            # Standard cubic Bezier curve when third control point is disabled or not manually positioned
            path.cubicTo(self.control_point1, self.control_point2, self.end)
        
        # Add a line to the extended end point
        path.lineTo(extended_end)
            
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
            # We'll use a sequence of cubic Bézier segments with proper tangent continuity
            
            # Create control points that ensure C1 continuity (continuous first derivative)
            
            # Extract the key points we're working with
            p0 = self.start
            p1 = self.control_point1
            p2 = self.control_point_center
            p3 = self.control_point2
            p4 = self.end
            
            # Calculate the tangent at start point (pointing toward control_point1)
            start_tangent = QPointF(p1.x() - p0.x(), p1.y() - p0.y())
            
            # Calculate the tangent at center (average of incoming and outgoing)
            in_tangent = QPointF(p2.x() - p1.x(), p2.y() - p1.y())
            out_tangent = QPointF(p3.x() - p2.x(), p3.y() - p2.y())
            
            # Normalize tangents for better control
            def normalize_vector(v):
                length = math.sqrt(v.x() * v.x() + v.y() * v.y())
                if length < 0.001:  # Avoid division by zero
                    return QPointF(0, 0)
                # Preserve vector magnitude better for small movements
                return QPointF(v.x() / length, v.y() / length)
            def distance_vector(v):
                return (math.sqrt(v.x() * v.x() + v.y() * v.y()))/(46*6)
            start_tangent_normalized = normalize_vector(start_tangent)
            in_tangent_normalized = normalize_vector(in_tangent)
            out_tangent_normalized = normalize_vector(out_tangent)
            
            # Calculate center tangent as weighted average instead of simple average
            # This makes the curve more responsive to small movements
            center_tangent = QPointF(
                0.5 * in_tangent_normalized.x() + 0.5 * out_tangent_normalized.x(), 
                0.5 * in_tangent_normalized.y() + 0.5 * out_tangent_normalized.y()
            )
            center_tangent_normalized = normalize_vector(center_tangent)
            
            # Calculate end tangent
            end_tangent = QPointF(p4.x() - p3.x(), p4.y() - p3.y())
            end_tangent_normalized = normalize_vector(end_tangent)
            
            # Simple distance calculation based on direct distances between points
            dist_p0_p1 = math.sqrt((p1.x() - p0.x())**2 + (p1.y() - p0.y())**2)
            dist_p1_p2 = math.sqrt((p2.x() - p1.x())**2 + (p2.y() - p1.y())**2)
            dist_p2_p3 = math.sqrt((p3.x() - p2.x())**2 + (p3.y() - p2.y())**2)
            dist_p3_p4 = math.sqrt((p4.x() - p3.x())**2 + (p4.y() - p3.y())**2)

            # Fixed fraction for influence
            fraction = 1.0 / 3.0 # Experiment with this value (e.g., 0.5, 0.4)

            # Calculate intermediate control points, incorporating p1 and p3 influence
            # Ensure tangents are non-zero before using them
            cp1 = p0 + start_tangent_normalized * (dist_p0_p1 * fraction) if start_tangent_normalized.manhattanLength() > 1e-6 else p1
            cp2 = p2 - center_tangent_normalized * (dist_p1_p2 * fraction) if center_tangent_normalized.manhattanLength() > 1e-6 else p1

            cp3 = p2 + center_tangent_normalized * (dist_p2_p3 * fraction) if center_tangent_normalized.manhattanLength() > 1e-6 else p3
            cp4 = p4 - end_tangent_normalized * (dist_p3_p4 * fraction) if end_tangent_normalized.manhattanLength() > 1e-6 else p3
            
            # First segment: start to center
            path.cubicTo(cp1, cp2, p2)
            
            # Second segment: center to end
            path.cubicTo(cp3, cp4, p4)
        else:
            # Standard cubic Bezier curve when third control point is disabled or not manually positioned
            path.cubicTo(self.control_point1, self.control_point2, self.end)
        
        return path

    def get_selection_path(self):
        """Combine the start and end selection paths."""
        # Use the exact visual path for selection
        return self.get_stroked_path(self.width)

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
        if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'enable_third_control_point') and self.canvas.enable_third_control_point:
            if t <= 0.5:
                # Scale t to [0,1] for the first segment
                scaled_t = t * 2
                # First cubic segment: start to control_point_center
                p0 = self.start
                p1 = self.control_point1
                # Use a proper control point based on path calculation for smoother results
                p2 = self.control_point1
                p3 = self.control_point_center
            else:
                # Scale t to [0,1] for the second segment
                scaled_t = (t - 0.5) * 2
                # Second cubic segment: control_point_center to end
                p0 = self.control_point_center
                p1 = self.control_point2
                # Use a proper control point based on path calculation for smoother results
                p2 = self.control_point2
                p3 = self.end
            
            # Standard cubic Bézier formula
            x = (
                (1 - scaled_t) ** 3 * p0.x() +
                3 * (1 - scaled_t) ** 2 * scaled_t * p1.x() +
                3 * (1 - scaled_t) * scaled_t ** 2 * p2.x() +
                scaled_t ** 3 * p3.x()
            )
            y = (
                (1 - scaled_t) ** 3 * p0.y() +
                3 * (1 - scaled_t) ** 2 * scaled_t * p1.y() +
                3 * (1 - scaled_t) * scaled_t ** 2 * p2.y() +
                scaled_t ** 3 * p3.y()
            )
            return QPointF(x, y)
        else:
            # Standard cubic Bézier with 2 control points
            p0, p1, p2, p3 = self.start, self.control_point1, self.control_point2, self.end

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
        # Always use the standard cubic Bézier with 2 control points for tangent calculation
        # This ensures consistent C-shape calculations regardless of third control point status
        p0, p1, p2, p3 = self.start, self.control_point1, self.control_point2, self.end

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

    def update_side_line(self):
        """Update side lines considering the curve's shape near the ends."""
        # Small values near 0 and 1 to get tangents that include control points
        t_start = 0.01
        t_end = 0.99

        # Compute tangents near the start and end
        tangent_start = self.calculate_cubic_tangent(t_start)
        tangent_end = self.calculate_cubic_tangent(t_end)

        # Handle zero-length tangent vectors
        if tangent_start.manhattanLength() == 0:
            tangent_start = self.end - self.start
        if tangent_end.manhattanLength() == 0:
            tangent_end = self.start - self.end

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

    def draw(self, painter):
        """Draw the strand with squared ends and highlight if selected."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Get the path representing the strand as a cubic Bézier curve
        path = self.get_path()

        # Create a stroker for the stroke path with squared ends
        stroke_stroker = QPainterPathStroker()
        stroke_stroker.setWidth(self.width + self.stroke_width * 2)
        stroke_stroker.setJoinStyle(Qt.MiterJoin)
        stroke_stroker.setCapStyle(Qt.FlatCap)  # Use FlatCap for squared ends
        stroke_path = stroke_stroker.createStroke(path)

        # Draw shadow for overlapping strands - using the utility function
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
                
                # Draw strand body shadow with explicit shadow color
                draw_strand_shadow(painter, self, shadow_color)
                
                # Draw circle shadows if this strand has circles
                if hasattr(self, 'has_circles') and any(self.has_circles):
                    draw_circle_shadow(painter, self, shadow_color)
        except Exception as e:
            # Log the error but continue with the rendering
            logging.error(f"Error applying strand shadow: {e}")

        # Only draw highlight if this is not a MaskedStrand
        if self.is_selected and not isinstance(self, MaskedStrand):
            highlight_pen = QPen(QColor('red'), self.stroke_width + 8)
            highlight_pen.setJoinStyle(Qt.MiterJoin)
            highlight_pen.setCapStyle(Qt.FlatCap)
            painter.setPen(highlight_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(stroke_path)

        # Create a stroker for the fill path with squared ends
        fill_stroker = QPainterPathStroker()
        fill_stroker.setWidth(self.width)
        fill_stroker.setJoinStyle(Qt.MiterJoin)
        fill_stroker.setCapStyle(Qt.FlatCap)  # Use FlatCap for squared ends
        fill_path = fill_stroker.createStroke(path)

        # Draw the stroke path with the stroke color
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.stroke_color)
        painter.drawPath(stroke_path)

        # Draw the fill path with the strand's color
        painter.setBrush(self.color)
        painter.drawPath(fill_path)

        # Draw the end line
        side_pen = QPen(self.stroke_color, self.stroke_width)
        side_pen.setCapStyle(Qt.FlatCap)

        # Create a new color with the same alpha as the strand's color
        side_color = QColor(self.stroke_color)
        side_color.setAlpha(self.color.alpha())
        side_pen.setColor(side_color)

        painter.setPen(side_pen)
        painter.drawLine(self.start_line_start, self.start_line_end)
        painter.drawLine(self.end_line_start, self.end_line_end)

        painter.restore()

        # Draw the selection path
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        selection_pen = QPen(QColor('transparent'), 0, Qt.DashLine)
        painter.setPen(selection_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.get_selection_path())  # Use get_selection_path to show selection area
        painter.drawPath(path)
        painter.restore()

        # Draw the selection path for debugging
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        debug_pen = QPen(QColor('transparent'), 0, Qt.DashLine)
        painter.setPen(debug_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.get_selection_path())
        painter.restore()
        # Draw the circles at connection points
        for i, has_circle in enumerate(self.has_circles):
            # --- REPLACE WITH THIS SIMPLE CHECK ---
            # Only draw if this end should have a circle and the strand is currently selected
            if not has_circle or not self.is_selected:
                continue
            # --- END REPLACE ---
            
            # Save painter state (Original line)
            painter.save()
            
            center = self.start if i == 0 else self.end
            
            # Calculate the proper radius for the highlight
            outer_radius = self.width / 2 + self.stroke_width + 4
            inner_radius = self.width / 2 + 6
            
            # Create a full circle path for the outer circle
            outer_circle = QPainterPath()
            outer_circle.addEllipse(center, outer_radius, outer_radius)
            
            # Create a path for the inner circle
            inner_circle = QPainterPath()
            inner_circle.addEllipse(center, inner_radius, inner_radius)
            
            # Create a ring path by subtracting the inner circle from the outer circle
            ring_path = outer_circle.subtracted(inner_circle)
            
            # Get the tangent angle at the connection point
            # --- MODIFICATION START ---
            if i == 0 and self.control_point1 == self.start and self.control_point2 == self.start:
                # If control points are at default start position, use start-to-end direction
                direction_vector = self.end - self.start
                if direction_vector.manhattanLength() == 0: # Handle case where start == end
                    angle = 0.0 # Default angle if no direction
                else:
                    angle = math.atan2(direction_vector.y(), direction_vector.x())

            else:
                # Otherwise, use the cubic tangent
                tangent = self.calculate_cubic_tangent(0.0 if i == 0 else 1.0)
                angle = math.atan2(tangent.y(), tangent.x())
            # --- MODIFICATION END ---
            
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
            stroke_pen = QPen(QColor(255, 0, 0, 255), self.stroke_width)
            stroke_pen.setJoinStyle(Qt.MiterJoin)
            stroke_pen.setCapStyle(Qt.FlatCap)
            painter.setPen(stroke_pen)
            # --- CHANGE: Use NoBrush instead of solid red fill ---
            # painter.setBrush(QColor(255, 0, 0, 255))  # Fill with red color
            painter.setBrush(Qt.NoBrush)
            # --- END CHANGE ---
            painter.drawPath(c_shape_path)
            
            # Restore painter state
            painter.restore()
        # Control points are now only drawn by StrandDrawingCanvas.draw_control_points
        # This prevents duplicate drawing of control points
        # By keeping the try-except for compatibility but disabling the actual drawing
        try:
            # Control point drawing code removed to avoid conflicts with canvas drawing
            pass
        except Exception as e:
            logging.error(f"Error with control points: {e}")
            # Continue drawing even if control points fail

        # ----------------------------------------------------------------
        # NEW CODE: also draw an ending circle if self.has_circles == [False, True]
        if self.has_circles == [False, True]:
            # Re-create a temp image so we can blend a half-circle on the end
            temp_image = QImage(painter.device().size(), QImage.Format_ARGB32_Premultiplied)
            temp_image.fill(Qt.transparent)
            temp_painter = QPainter(temp_image)
            temp_painter.setRenderHint(QPainter.Antialiasing)

            # Compute tangent & angle at the end (t=1.0)
            tangent_end = self.calculate_cubic_tangent(1.0)
            angle_end = math.atan2(tangent_end.y(), tangent_end.x())

            # We'll do the same half-circle approach
            total_diameter = self.width + self.stroke_width * 2
            circle_radius = total_diameter / 2

            mask_rect_end = QPainterPath()
            rect_width_end = total_diameter * 2
            rect_height_end = total_diameter * 2
            rect_x_end = self.end.x() - rect_width_end / 2
            rect_y_end = self.end.y()
            mask_rect_end.addRect(rect_x_end + 1, rect_y_end + 1, rect_width_end + 1, rect_height_end + 1)

            transform_end = QTransform()
            transform_end.translate(self.end.x(), self.end.y())
            transform_end.rotate(math.degrees(angle_end - math.pi / 2)+180)
            transform_end.translate(-self.end.x(), -self.end.y())
            mask_rect_end = transform_end.map(mask_rect_end)

            outer_circle_end = QPainterPath()
            outer_circle_end.addEllipse(self.end, circle_radius, circle_radius)
            outer_mask_end = outer_circle_end.subtracted(mask_rect_end)

            # Draw the outer circle stroke with self.circle_stroke_color or self.stroke_color (your preference)
            temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            temp_painter.setPen(Qt.NoPen)
            temp_painter.setBrush(self.stroke_color) # Changed from self.circle_stroke_color
            temp_painter.drawPath(outer_mask_end)

            # Then draw the fill for the inner circle
            inner_circle_end = QPainterPath()
            inner_circle_end.addEllipse(self.end, self.width / 2, self.width / 2)
            inner_mask_end = inner_circle_end.subtracted(mask_rect_end)
            temp_painter.setBrush(self.color)
            temp_painter.drawPath(inner_mask_end)

            # Draw a small inner circle again (no mask) so it doesn't look clipped
            just_inner_end = QPainterPath()
            just_inner_end.addEllipse(self.end, self.width / 2, self.width / 2)
            temp_painter.drawPath(just_inner_end)

            painter.drawImage(0, 0, temp_image)
            temp_painter.end()
        # ----------------------------------------------------------------

        # NEW CODE: Also draw an ending circle if has_circles == [True, True]
        if self.has_circles == [True, True]:            # Re-create a temp image so we can blend a half-circle on the end
            temp_image = QImage(painter.device().size(), QImage.Format_ARGB32_Premultiplied)
            temp_image.fill(Qt.transparent)
            temp_painter = QPainter(temp_image)
            temp_painter.setRenderHint(QPainter.Antialiasing)
            # We'll compute the angle for the end based on the tangent at t=1.0:
            tangent_end = self.calculate_cubic_tangent(1.0)
            angle_end = math.atan2(tangent_end.y(), tangent_end.x())

            # We'll do the same half-circle approach
            total_diameter = self.width + self.stroke_width * 2
            circle_radius = total_diameter / 2

            # Make a fresh path for the end circle's half-mask
            mask_rect_end = QPainterPath()
            rect_width_end = total_diameter * 2
            rect_height_end = total_diameter * 2
            rect_x_end = self.end.x() - rect_width_end / 2
            rect_y_end = self.end.y()
            mask_rect_end.addRect(rect_x_end + 1, rect_y_end + 1, rect_width_end + 1, rect_height_end + 1)

            transform_end = QTransform()
            transform_end.translate(self.end.x(), self.end.y())
            transform_end.rotate(math.degrees(angle_end - math.pi / 2)+180)
            transform_end.translate(-self.end.x(), -self.end.y())
            mask_rect_end = transform_end.map(mask_rect_end)

            outer_circle_end = QPainterPath()
            outer_circle_end.addEllipse(self.end, circle_radius, circle_radius)
            outer_mask_end = outer_circle_end.subtracted(mask_rect_end)
            # Create another temporary painter so we can blend the circle on the end.
            temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            # Draw the outer circle stroke
            temp_painter.setPen(Qt.NoPen)
            temp_painter.setBrush(self.stroke_color)
            temp_painter.drawPath(outer_mask_end)

            # Then draw the fill for the inner circle at the end
            inner_circle_end = QPainterPath()
            inner_circle_end.addEllipse(self.end, self.width / 2, self.width / 2)
            inner_mask_end = inner_circle_end.subtracted(mask_rect_end)
            temp_painter.setBrush(self.color)
            temp_painter.drawPath(inner_mask_end)

            # Draw a small inner circle fill so it doesn't look clipped
            just_inner_end = QPainterPath()
            just_inner_end.addEllipse(self.end, self.width / 2, self.width / 2)
            temp_painter.drawPath(just_inner_end)

            # Overwrite the final image portion
            painter.drawImage(0, 0, temp_image)
            temp_painter.end()
        # ----------------------------------------------------------------

        # ---------------------------------------------------------------
        # NEW CODE: Also draw a start circle if has_circles == [True, True]
        if self.has_circles == [True, True]:
            # Re-create a temp_image for drawing the circles
            temp_image = QImage(painter.device().size(), QImage.Format_ARGB32_Premultiplied)
            temp_image.fill(Qt.transparent)
            temp_painter = QPainter(temp_image)
            temp_painter.setRenderHint(QPainter.Antialiasing)

            # --------------------
            # (1) START CIRCLE
            # --------------------
            tangent_start = self.calculate_cubic_tangent(0.0)
            angle_start = math.atan2(tangent_start.y(), tangent_start.x())

            total_diameter = self.width + self.stroke_width * 2
            circle_radius = total_diameter / 2

            mask_rect_start = QPainterPath()
            rect_width_start = total_diameter * 2
            rect_height_start = total_diameter * 2
            rect_x_start = self.start.x() - rect_width_start / 2
            rect_y_start = self.start.y()
            mask_rect_start.addRect(rect_x_start + 1, rect_y_start + 1, rect_width_start + 1, rect_height_start + 1)

            transform_start = QTransform()
            transform_start.translate(self.start.x(), self.start.y())
            transform_start.rotate(math.degrees(angle_start - math.pi / 2))  # adjust +180 if needed
            transform_start.translate(-self.start.x(), -self.start.y())
            mask_rect_start = transform_start.map(mask_rect_start)

            outer_circle_start = QPainterPath()
            outer_circle_start.addEllipse(self.start, circle_radius, circle_radius)
            outer_mask_start = outer_circle_start.subtracted(mask_rect_start)

            temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            temp_painter.setPen(Qt.NoPen)
            temp_painter.setBrush(self.stroke_color)  # Changed from circle_stroke_color to stroke_color
            temp_painter.drawPath(outer_mask_start)

            # Fill the inner circle
            inner_circle_start = QPainterPath()
            inner_circle_start.addEllipse(self.start, self.width / 2, self.width / 2)
            inner_mask_start = inner_circle_start.subtracted(mask_rect_start)
            temp_painter.setBrush(self.color)
            temp_painter.drawPath(inner_mask_start)

            # Avoid clipping
            just_inner_start = QPainterPath()
            just_inner_start.addEllipse(self.start, self.width / 2, self.width / 2)
            temp_painter.drawPath(just_inner_start)


            # Finalize circles
            painter.drawImage(0, 0, temp_image)
            temp_painter.end()
        # ---------------------------------------------------------------

        painter.restore()

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

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import (
    QColor, QPainter, QPen, QBrush, QPainterPath, QPainterPathStroker
)
import math

# src/strand.py

class AttachedStrand(Strand):
    """
    Represents a strand attached to another strand.
    """

    def __init__(self, parent, start_point):
        super().__init__(
            start_point, start_point, parent.width,
            color=parent.color, stroke_color=parent.stroke_color,
            stroke_width=parent.stroke_width,
            set_number=parent.set_number,
            layer_name=parent.layer_name
        )
        self.parent = parent
        self.angle = 0
        self.length = 0  # Changed from 140 to 0 to prevent initial length
        self.min_length = 40
        self.has_circles = [True, False]
        # Inherit shadow color from parent
        self.shadow_color = parent.shadow_color
        self.update_end()

        # Initialize control points at 1/3 and 2/3 along the strand
        self.control_point1 = QPointF(
            self.start.x(),
            self.start.y()
        )
        self.control_point2 = QPointF(
            self.start.x(),
            self.start.y()
        )
        
        # Add the center control point (midpoint between control_point1 and control_point2)
        self.control_point_center = QPointF(
            self.start.x(),
            self.start.y()
        )
        
        # Initialize attachment statuses
        self.start_attached = True  # Attached at start to parent strand
        self.end_attached = False
        
        # Initialize selection states
        self.is_selected = False  # Indicates if the strand is selected
        self.start_selected = False
        self.end_selected = False

        if hasattr(parent, 'canvas'):
            self.canvas = parent.canvas

        # --------------------------------------------------------------------
        # Removed the force-default to black if circle_stroke_color is None.
        # Instead, keep the color from JSON if it has been deserialized.
        #
        # OLD CODE (removed):
        # if self.circle_stroke_color is None:
        #     self.circle_stroke_color = QColor(0, 0, 0, 255)
        # elif self.circle_stroke_color.alpha() == 0:
        #     logging.info("Circle stroke was loaded with alpha=0, leaving it fully transparent.")
        #
        # NEW CODE to log alpha = 0 if needed:
        if self.circle_stroke_color and self.circle_stroke_color.alpha() == 0:
            logging.info("Circle stroke was loaded with alpha=0, leaving it fully transparent.")
        # --------------------------------------------------------------------

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
        return super().end

    @end.setter
    def end(self, value):
        super(AttachedStrand, self.__class__).end.fset(self, value)
        self.update_shape()

    def get_start_selection_path(self):
        """Get the selection path for the starting point, excluding the inner area for control point selection."""
        path = QPainterPath()

        # Define the outer rectangle (80x80 square)
        outer_size = 120  # Size of the outer selection square for the start edge
        half_outer_size = outer_size / 2
        outer_rect = QRectF(
            self.start.x() - half_outer_size,
            self.start.y() - half_outer_size,
            outer_size,
            outer_size
        )




        # Create the selection path by subtracting the inner rectangle from the outer rectangle
        path.addRect(outer_rect)

        return path

    def get_end_selection_path(self):
        """Get a selection path for the exact end point of the strand."""
        # Get the path of the strand
        path = self.get_path()
        # Create a small circle at the end point that matches the strand's end
        end_path = QPainterPath()
        # Use the width of the strand for the selection circle
        radius = self.width / 2
        end_path.addEllipse(self.end, radius, radius)
        return end_path
 





    def update_side_line(self):
        """Update side lines considering the curve's shape near the ends."""
        # Small values near 0 and 1 to get tangents that include control points
        t_start = 0.01
        t_end = 0.99

        # Compute tangents near the start and end
        tangent_start = self.calculate_cubic_tangent(t_start)
        tangent_end = self.calculate_cubic_tangent(t_end)

        # Handle zero-length tangent vectors
        if tangent_start.manhattanLength() == 0:
            tangent_start = self.end - self.start
        if tangent_end.manhattanLength() == 0:
            tangent_end = self.start - self.end

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

    def update_end(self):
        """Update the end point based on the current angle and length."""
        angle_rad = math.radians(self.angle)
        self.end = QPointF(
            self.start.x() + self.length * math.cos(angle_rad),
            self.start.y() + self.length * math.sin(angle_rad)
        )
        
        # Update control points when the end moves, but preserve their positions relative to start/end
        # when they've been manually adjusted
        if hasattr(self, 'control_point1') and (self.control_point1 == self.start or 
                                          self.control_point1 == QPointF(self.start.x(), self.start.y())):
            # Only reset control_point1 if it's at the default position
            self.control_point1 = QPointF(self.start.x(), self.start.y())
        
        if hasattr(self, 'control_point2') and (self.control_point2 == self.start or 
                                         self.control_point2 == QPointF(self.start.x(), self.start.y())):
            # Only reset control_point2 if it's at the default position
            self.control_point2 = QPointF(self.start.x(), self.start.y())
            
        # Update the center control point only if not locked
        if not hasattr(self, 'control_point_center_locked') or not self.control_point_center_locked:
            self.control_point_center = QPointF(
                (self.control_point1.x() + self.control_point2.x()) / 2,
                (self.control_point1.y() + self.control_point2.y()) / 2
            )
            
        self.update_shape()
        self.update_side_line()

    def update(self, end_point=None, reset_control_points=True):
        """
        Update the end point and optionally reset the control points.

        Args:
            end_point (QPointF): The new end point. If None, use the current end point.
            reset_control_points (bool): Whether to reset the control points.
        """
        # Store original control points to preserve them if needed
        original_control_point1 = QPointF(self.control_point1) if hasattr(self, 'control_point1') else None
        original_control_point2 = QPointF(self.control_point2) if hasattr(self, 'control_point2') else None
        original_control_point_center = QPointF(self.control_point_center) if hasattr(self, 'control_point_center') else None
        original_control_point_center_locked = getattr(self, 'control_point_center_locked', False)

        if end_point is not None:
            self.end = end_point
            
            # Only enforce minimum length when user is actively dragging
            # Calculate current length and angle
            delta_x = self.end.x() - self.start.x()
            delta_y = self.end.y() - self.start.y()
            current_length = math.hypot(delta_x, delta_y)
            
            # If current length < min_length and user is dragging, enforce minimum length
            if current_length > 0 and current_length < self.min_length:
                # Get current angle
                angle = math.atan2(delta_y, delta_x)
                # Set length to minimum while preserving angle
                self.end = QPointF(
                    self.start.x() + self.min_length * math.cos(angle),
                    self.start.y() + self.min_length * math.sin(angle)
                )

        if reset_control_points:
            # When resetting control points, set them to start and end
            self.control_point1 = QPointF(
                self.start.x(),
                self.start.y()
            )
            self.control_point2 = QPointF(
                self.end.x(),
                self.end.y()
            )
            # Also update the center control point when resetting
            self.control_point_center = QPointF(
                (self.control_point1.x() + self.control_point2.x()) / 2,
                (self.control_point1.y() + self.control_point2.y()) / 2
            )
            # Reset control point lock when doing a full update
            if hasattr(self, 'control_point_center_locked'):
                self.control_point_center_locked = False
        else:
            # When not resetting control points, restore the originals to preserve them
            if original_control_point1 is not None:
                self.control_point1 = original_control_point1
            if original_control_point2 is not None:
                self.control_point2 = original_control_point2
            if original_control_point_center is not None:
                self.control_point_center = original_control_point_center
                if hasattr(self, 'control_point_center_locked'):
                    self.control_point_center_locked = original_control_point_center_locked

        self.update_shape()
        self.update_side_line()

    def boundingRect(self):
        """Return the bounding rectangle of the strand."""
        # Get the path representing the strand as a cubic Bézier curve
        path = self.get_path()

        # Create a stroker for the stroke path with squared ends
        stroke_stroker = QPainterPathStroker()
        stroke_stroker.setWidth(self.width + self.stroke_width * 2)
        stroke_stroker.setJoinStyle(Qt.MiterJoin)
        stroke_stroker.setCapStyle(Qt.FlatCap)  # Use FlatCap for squared ends
        stroke_path = stroke_stroker.createStroke(path)

        # Include side lines in the bounding rect
        bounding_rect = stroke_path.boundingRect()
        bounding_rect = bounding_rect.united(QRectF(self.start_line_start, self.start_line_end))
        bounding_rect = bounding_rect.united(QRectF(self.end_line_start, self.end_line_end))

        # Adjust for any pen widths or additional drawing elements if necessary
        return bounding_rect
    # Calculate the angle based on the tangent at the start point
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
    

    def draw(self, painter):
        """Draw the attached strand with a rounded start and squared end."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Get the path representing the strand as a cubic Bézier curve
        path = self.get_path()

        # Create a stroker for the stroke path with squared ends
        stroke_stroker = QPainterPathStroker()
        stroke_stroker.setWidth(self.width + self.stroke_width * 2)
        stroke_stroker.setJoinStyle(Qt.MiterJoin)
        stroke_stroker.setCapStyle(Qt.FlatCap)
        stroke_path = stroke_stroker.createStroke(path)
        
        # Draw shadow for overlapping strands - using the utility function
        # This must be called before drawing the strand itself
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
                
                # Draw strand body shadow with explicit shadow color
                draw_strand_shadow(painter, self, shadow_color)
                
                # Draw circle shadows if this strand has circles
                if hasattr(self, 'has_circles') and any(self.has_circles):
                    draw_circle_shadow(painter, self, shadow_color)
        except Exception as e:
            # Log the error but continue with the rendering
            logging.error(f"Error applying strand shadow: {e}")

        # Draw highlight if selected (only when directly selected)
        if self.is_selected and not isinstance(self.parent, MaskedStrand):
            highlight_pen = QPen(QColor('red'), self.stroke_width + 8)
            highlight_pen.setJoinStyle(Qt.MiterJoin)
            highlight_pen.setCapStyle(Qt.FlatCap)
            
            painter.setPen(highlight_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(stroke_path)

        # Create a temporary image for masking
        temp_image = QImage(
            painter.device().size(),
            QImage.Format_ARGB32_Premultiplied
        )
        temp_image.fill(Qt.transparent)
        temp_painter = QPainter(temp_image)
        temp_painter.setRenderHint(QPainter.Antialiasing)

        # Calculate the angle based on the tangent at the start point
        angle = self.calculate_start_tangent()

        # Draw the main strand
        temp_painter.setPen(Qt.NoPen)
        temp_painter.setBrush(self.stroke_color)
        temp_painter.drawPath(stroke_path)

        # Draw the fill
        fill_stroker = QPainterPathStroker()
        fill_stroker.setWidth(self.width)
        fill_stroker.setJoinStyle(Qt.MiterJoin)
        fill_stroker.setCapStyle(Qt.FlatCap)
        fill_path = fill_stroker.createStroke(path)
        temp_painter.setBrush(self.color)
        temp_painter.drawPath(fill_path)

        # Draw the end line
        side_pen = QPen(self.stroke_color, self.stroke_width)
        side_pen.setCapStyle(Qt.FlatCap)

        # Create a new color with the same alpha as the strand's color
        side_color = QColor(self.stroke_color)
        side_color.setAlpha(self.color.alpha())

        side_pen.setColor(side_color)
        painter.setPen(side_pen)

        temp_painter.setPen(side_pen)
        temp_painter.drawLine(self.end_line_start, self.end_line_end)

        # Create a mask for the circle
        circle_mask = QPainterPath()
        total_diameter = self.width + self.stroke_width * 2
        circle_radius = total_diameter / 2

        # Add the outer circle to the mask
        circle_mask.addEllipse(self.start, circle_radius, circle_radius)

        # Create the masking rectangle for half circle
        mask_rect = QPainterPath()
        rect_width = total_diameter * 2
        rect_height = total_diameter * 2
        rect_x = self.start.x() - rect_width/2
        rect_y = self.start.y()
        mask_rect.addRect(rect_x+1, rect_y+1, rect_width+1, rect_height+1)

        transform = QTransform()
        transform.translate(self.start.x(), self.start.y())
        transform.rotate(math.degrees(angle - math.pi/2))  # Rotate based on tangent angle
        transform.translate(-self.start.x(), -self.start.y())
        mask_rect = transform.map(mask_rect)

        outer_circle = QPainterPath()
        outer_circle.addEllipse(self.start, circle_radius, circle_radius)
        outer_mask = outer_circle.subtracted(mask_rect)

        # -- ADD THIS COMPOSITION MODE SETUP --
        temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        r = self.circle_stroke_color.red()
        g = self.circle_stroke_color.green()
        b = self.circle_stroke_color.blue()
        a = self.circle_stroke_color.alpha()
        logging.info(f"circle_stroke_color: (r={r}, g={g}, b={b}, a={a})")
        temp_painter.setPen(Qt.NoPen)
        temp_painter.setBrush(self.circle_stroke_color)
        temp_painter.drawPath(outer_mask)

        # Then draw the fill for the inner circle:
        inner_circle = QPainterPath()
        inner_circle.addEllipse(self.start, self.width / 2, self.width / 2)
        inner_mask = inner_circle.subtracted(mask_rect)
        temp_painter.setBrush(self.color)
        temp_painter.drawPath(inner_mask)

        # Draw the final image
        # Then draw the inner circle (fill)
        inner_circle = QPainterPath()
        inner_circle.addEllipse(self.start, self.width/2, self.width/2)
        temp_painter.drawPath(inner_circle)
        painter.drawImage(0, 0, temp_image)

        # ----------------------------------------------------------------
        # NEW CODE: Also draw an ending circle if has_circles == [True, True]
        if self.has_circles == [True, True]:
            # We'll compute the angle for the end based on the tangent at t=1.0:
            tangent_end = self.calculate_cubic_tangent(1.0)
            angle_end = math.atan2(tangent_end.y(), tangent_end.x())
            # If you still need to flip by 180°, uncomment or adjust:
            # angle_end += math.pi

            # Create another temporary painter so we can blend the circle on the end.
            temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            # Make a fresh path for the end circle's half-mask
            mask_rect_end = QPainterPath()
            rect_width_end = total_diameter * 2
            rect_height_end = total_diameter * 2
            rect_x_end = self.end.x() - rect_width_end / 2
            rect_y_end = self.end.y()
            mask_rect_end.addRect(rect_x_end + 1, rect_y_end + 1, rect_width_end + 1, rect_height_end + 1)

            transform_end = QTransform()
            transform_end.translate(self.end.x(), self.end.y())
            transform_end.rotate(math.degrees(angle_end - math.pi / 2)+180)
            transform_end.translate(-self.end.x(), -self.end.y())
            mask_rect_end = transform_end.map(mask_rect_end)

            outer_circle_end = QPainterPath()
            outer_circle_end.addEllipse(self.end, circle_radius, circle_radius)
            outer_mask_end = outer_circle_end.subtracted(mask_rect_end)

            # Draw the outer circle stroke
            temp_painter.setPen(Qt.NoPen)
            temp_painter.setBrush(self.stroke_color)
            temp_painter.drawPath(outer_mask_end)

            # Then draw the fill for the inner circle at the end
            inner_circle_end = QPainterPath()
            inner_circle_end.addEllipse(self.end, self.width / 2, self.width / 2)
            inner_mask_end = inner_circle_end.subtracted(mask_rect_end)
            temp_painter.setBrush(self.color)
            temp_painter.drawPath(inner_mask_end)

            # Draw a small inner circle fill so it doesn't look clipped
            just_inner_end = QPainterPath()
            just_inner_end.addEllipse(self.end, self.width / 2, self.width / 2)
            temp_painter.drawPath(just_inner_end)

            # Overwrite the final image portion
            painter.drawImage(0, 0, temp_image)
            temp_painter.end()
        # ----------------------------------------------------------------

        temp_painter.end()
        painter.restore()

        # Control points are now only drawn by StrandDrawingCanvas.draw_control_points
        # This code is removed to avoid duplicate drawing
        """
        # Draw control points if needed
        if hasattr(self, 'canvas') and self.canvas and self.canvas.show_control_points:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw control point lines
            control_line_pen = QPen(QColor('green'), 1, Qt.DashLine)
            painter.setPen(control_line_pen)
            painter.drawLine(self.start, self.control_point1)
            painter.drawLine(self.end, self.control_point2)
            
            # Draw control points
            control_pen = QPen(QColor('green'), 2)
            painter.setPen(control_pen)
            painter.setBrush(QBrush(QColor('green')))
            painter.drawEllipse(self.control_point1, 4, 4)
            painter.drawEllipse(self.control_point2, 4, 4)
            
            painter.restore()
        """


        
    def point_at(self, t):
        """Compute a point on the Bézier curve at parameter t."""
        # If third control point is enabled, use a composite curve with two segments
        if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'enable_third_control_point') and self.canvas.enable_third_control_point:
            if t <= 0.5:
                # Scale t to [0,1] for the first segment
                scaled_t = t * 2
                # First cubic segment: start to control_point_center
                p0 = self.start
                p1 = self.control_point1
                p2 = self.control_point1
                p3 = self.control_point_center
            else:
                # Scale t to [0,1] for the second segment
                scaled_t = (t - 0.5) * 2
                # Second cubic segment: control_point_center to end
                p0 = self.control_point_center
                p1 = self.control_point2
                p2 = self.control_point2
                p3 = self.end
            
            # Standard cubic Bézier formula
            x = (
                (1 - scaled_t) ** 3 * p0.x() +
                3 * (1 - scaled_t) ** 2 * scaled_t * p1.x() +
                3 * (1 - scaled_t) * scaled_t ** 2 * p2.x() +
                scaled_t ** 3 * p3.x()
            )
            y = (
                (1 - scaled_t) ** 3 * p0.y() +
                3 * (1 - scaled_t) ** 2 * scaled_t * p1.y() +
                3 * (1 - scaled_t) * scaled_t ** 2 * p2.y() +
                scaled_t ** 3 * p3.y()
            )
            return QPointF(x, y)
        else:
            # Standard cubic Bézier with 2 control points
            p0, p1, p2, p3 = self.start, self.control_point1, self.control_point2, self.end

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
        # Always use the standard cubic Bézier with 2 control points for tangent calculation
        # This ensures consistent C-shape calculations regardless of third control point status
        p0, p1, p2, p3 = self.start, self.control_point1, self.control_point2, self.end

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

    def update_side_line(self):
        """Update side lines considering the curve's shape near the ends."""
        # Small values near 0 and 1 to get tangents that include control points
        t_start = 0.01
        t_end = 0.99

        # Compute tangents near the start and end
        tangent_start = self.calculate_cubic_tangent(t_start)
        tangent_end = self.calculate_cubic_tangent(t_end)

        # Handle zero-length tangent vectors
        if tangent_start.manhattanLength() == 0:
            tangent_start = self.end - self.start
        if tangent_end.manhattanLength() == 0:
            tangent_end = self.start - self.end

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

    def draw(self, painter):
        """Draw the strand with squared ends and highlight if selected."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Get the path representing the strand as a cubic Bézier curve
        path = self.get_path()

        # Create a stroker for the stroke path with squared ends
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
                if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'default_shadow_color'):
                    shadow_color = self.canvas.default_shadow_color
                    # Ensure the strand's shadow color is also updated for future reference
                    self.shadow_color = QColor(shadow_color)
                
                # Draw strand body shadow with explicit shadow color
                draw_strand_shadow(painter, self, shadow_color)
                
                # Draw circle shadows if this strand has circles
                if hasattr(self, 'has_circles') and any(self.has_circles):
                    draw_circle_shadow(painter, self, shadow_color)
        except Exception as e:
            # Log the error but continue with the rendering
            logging.error(f"Error applying strand shadow: {e}")

        # Only draw highlight if this is not a MaskedStrand
        if self.is_selected and not isinstance(self, MaskedStrand):
            highlight_pen = QPen(QColor('red'), self.stroke_width + 8)
            highlight_pen.setJoinStyle(Qt.MiterJoin)
            highlight_pen.setCapStyle(Qt.FlatCap)
            painter.setPen(highlight_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(stroke_path)

        # Create a temporary image for masking
        temp_image = QImage(
            painter.device().size(),
            QImage.Format_ARGB32_Premultiplied
        )
        temp_image.fill(Qt.transparent)
        temp_painter = QPainter(temp_image)
        temp_painter.setRenderHint(QPainter.Antialiasing)

        # Calculate the angle based on the tangent at the start point
        angle = self.calculate_start_tangent()

        # Draw the main strand
        temp_painter.setPen(Qt.NoPen)
        temp_painter.setBrush(self.stroke_color)
        temp_painter.drawPath(stroke_path)

        # Draw the fill
        fill_stroker = QPainterPathStroker()
        fill_stroker.setWidth(self.width)
        fill_stroker.setJoinStyle(Qt.MiterJoin)
        fill_stroker.setCapStyle(Qt.FlatCap)
        fill_path = fill_stroker.createStroke(path)
        temp_painter.setBrush(self.color)
        temp_painter.drawPath(fill_path)

        # Draw the end line
        side_pen = QPen(self.stroke_color, self.stroke_width)
        side_pen.setCapStyle(Qt.FlatCap)

        # Create a new color with the same alpha as the strand's color
        side_color = QColor(self.stroke_color)
        side_color.setAlpha(self.color.alpha())

        side_pen.setColor(side_color)
        painter.setPen(side_pen)

        temp_painter.setPen(side_pen)
        temp_painter.drawLine(self.end_line_start, self.end_line_end)

        # Create a mask for the circle
        circle_mask = QPainterPath()
        total_diameter = self.width + self.stroke_width * 2
        circle_radius = total_diameter / 2

        # Add the outer circle to the mask
        circle_mask.addEllipse(self.start, circle_radius, circle_radius)

        # Create the masking rectangle for half circle
        mask_rect = QPainterPath()
        rect_width = total_diameter * 2
        rect_height = total_diameter * 2
        rect_x = self.start.x() - rect_width/2
        rect_y = self.start.y()
        mask_rect.addRect(rect_x+1, rect_y+1, rect_width+1, rect_height+1)

        transform = QTransform()
        transform.translate(self.start.x(), self.start.y())
        transform.rotate(math.degrees(angle - math.pi/2))  # Rotate based on tangent angle
        transform.translate(-self.start.x(), -self.start.y())
        mask_rect = transform.map(mask_rect)

        outer_circle = QPainterPath()
        outer_circle.addEllipse(self.start, circle_radius, circle_radius)
        outer_mask = outer_circle.subtracted(mask_rect)

        # -- ADD THIS COMPOSITION MODE SETUP --
        temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        r = self.circle_stroke_color.red()
        g = self.circle_stroke_color.green()
        b = self.circle_stroke_color.blue()
        a = self.circle_stroke_color.alpha()
        logging.info(f"circle_stroke_color: (r={r}, g={g}, b={b}, a={a})")
        temp_painter.setPen(Qt.NoPen)
        temp_painter.setBrush(self.circle_stroke_color)
        temp_painter.drawPath(outer_mask)

        # Then draw the fill for the inner circle:
        inner_circle = QPainterPath()
        inner_circle.addEllipse(self.start, self.width / 2, self.width / 2)
        inner_mask = inner_circle.subtracted(mask_rect)
        temp_painter.setBrush(self.color)
        temp_painter.drawPath(inner_mask)

        # Draw the final image
        # Then draw the inner circle (fill)
        inner_circle = QPainterPath()
        inner_circle.addEllipse(self.start, self.width/2, self.width/2)
        temp_painter.drawPath(inner_circle)
        painter.drawImage(0, 0, temp_image)

        # ----------------------------------------------------------------
        # NEW CODE: Also draw an ending circle if has_circles == [True, True]
        if self.has_circles == [True, True]:
            # We'll compute the angle for the end based on the tangent at t=1.0:
            tangent_end = self.calculate_cubic_tangent(1.0)
            angle_end = math.atan2(tangent_end.y(), tangent_end.x())
            # If you still need to flip by 180°, uncomment or adjust:
            # angle_end += math.pi

            # Create another temporary painter so we can blend the circle on the end.
            temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            # Make a fresh path for the end circle's half-mask
            mask_rect_end = QPainterPath()
            rect_width_end = total_diameter * 2
            rect_height_end = total_diameter * 2
            rect_x_end = self.end.x() - rect_width_end / 2
            rect_y_end = self.end.y()
            mask_rect_end.addRect(rect_x_end + 1, rect_y_end + 1, rect_width_end + 1, rect_height_end + 1)

            transform_end = QTransform()
            transform_end.translate(self.end.x(), self.end.y())
            transform_end.rotate(math.degrees(angle_end - math.pi / 2)+180)
            transform_end.translate(-self.end.x(), -self.end.y())
            mask_rect_end = transform_end.map(mask_rect_end)

            outer_circle_end = QPainterPath()
            outer_circle_end.addEllipse(self.end, circle_radius, circle_radius)
            outer_mask_end = outer_circle_end.subtracted(mask_rect_end)

            # Draw the outer circle stroke
            temp_painter.setPen(Qt.NoPen)
            temp_painter.setBrush(self.stroke_color)
            temp_painter.drawPath(outer_mask_end)

            # Then draw the fill for the inner circle at the end
            inner_circle_end = QPainterPath()
            inner_circle_end.addEllipse(self.end, self.width / 2, self.width / 2)
            inner_mask_end = inner_circle_end.subtracted(mask_rect_end)
            temp_painter.setBrush(self.color)
            temp_painter.drawPath(inner_mask_end)

            # Draw a small inner circle fill so it doesn't look clipped
            just_inner_end = QPainterPath()
            just_inner_end.addEllipse(self.end, self.width / 2, self.width / 2)
            temp_painter.drawPath(just_inner_end)

            # Overwrite the final image portion
            painter.drawImage(0, 0, temp_image)
            temp_painter.end()
        # ----------------------------------------------------------------

        temp_painter.end()
        painter.restore()

        # Control points are now only drawn by StrandDrawingCanvas.draw_control_points
        # This code is removed to avoid duplicate drawing
        """
        # Draw control points if needed
        if hasattr(self, 'canvas') and self.canvas and self.canvas.show_control_points:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw control point lines
            control_line_pen = QPen(QColor('green'), 1, Qt.DashLine)
            painter.setPen(control_line_pen)
            painter.drawLine(self.start, self.control_point1)
            painter.drawLine(self.end, self.control_point2)
            
            # Draw control points
            control_pen = QPen(QColor('green'), 2)
            painter.setPen(control_pen)
            painter.setBrush(QBrush(QColor('green')))
            painter.drawEllipse(self.control_point1, 4, 4)
            painter.drawEllipse(self.control_point2, 4, 4)
            
            painter.restore()
        """


        
    def point_at(self, t):
        """Compute a point on the Bézier curve at parameter t."""
        # If third control point is enabled, use a composite curve with two segments
        if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'enable_third_control_point') and self.canvas.enable_third_control_point:
            if t <= 0.5:
                # Scale t to [0,1] for the first segment
                scaled_t = t * 2
                # First cubic segment: start to control_point_center
                p0 = self.start
                p1 = self.control_point1
                p2 = self.control_point1
                p3 = self.control_point_center
            else:
                # Scale t to [0,1] for the second segment
                scaled_t = (t - 0.5) * 2
                # Second cubic segment: control_point_center to end
                p0 = self.control_point_center
                p1 = self.control_point2
                p2 = self.control_point2
                p3 = self.end
            
            # Standard cubic Bézier formula
            x = (
                (1 - scaled_t) ** 3 * p0.x() +
                3 * (1 - scaled_t) ** 2 * scaled_t * p1.x() +
                3 * (1 - scaled_t) * scaled_t ** 2 * p2.x() +
                scaled_t ** 3 * p3.x()
            )
            y = (
                (1 - scaled_t) ** 3 * p0.y() +
                3 * (1 - scaled_t) ** 2 * scaled_t * p1.y() +
                3 * (1 - scaled_t) * scaled_t ** 2 * p2.y() +
                scaled_t ** 3 * p3.y()
            )
            return QPointF(x, y)
        else:
            # Standard cubic Bézier with 2 control points
            p0, p1, p2, p3 = self.start, self.control_point1, self.control_point2, self.end

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
                


    def update_side_line(self):
        """Update side lines considering the curve's shape near the ends."""
        # Small values near 0 and 1 to get tangents that include control points
        t_start = 0.01
        t_end = 0.99

        # Compute tangents near the start and end
        tangent_start = self.calculate_cubic_tangent(t_start)
        tangent_end = self.calculate_cubic_tangent(t_end)

        # Handle zero-length tangent vectors
        if tangent_start.manhattanLength() == 0:
            tangent_start = self.end - self.start
        if tangent_end.manhattanLength() == 0:
            tangent_end = self.start - self.end

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

    def draw(self, painter):
        """Draw the strand with squared ends and highlight if selected."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Get the path representing the strand as a cubic Bézier curve
        path = self.get_path()

        # Create a stroker for the stroke path with squared ends
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
                if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'default_shadow_color'):
                    shadow_color = self.canvas.default_shadow_color
                    # Ensure the strand's shadow color is also updated for future reference
                    self.shadow_color = QColor(shadow_color)
                
                # Draw strand body shadow with explicit shadow color
                draw_strand_shadow(painter, self, shadow_color)
                
                # Draw circle shadows if this strand has circles
                if hasattr(self, 'has_circles') and any(self.has_circles):
                    draw_circle_shadow(painter, self, shadow_color)
        except Exception as e:
            # Log the error but continue with the rendering
            logging.error(f"Error applying strand shadow: {e}")

        # Only draw highlight if this is not a MaskedStrand
        if self.is_selected and not isinstance(self, MaskedStrand):
            highlight_pen = QPen(QColor('red'), self.stroke_width + 8)
            highlight_pen.setJoinStyle(Qt.MiterJoin)
            highlight_pen.setCapStyle(Qt.FlatCap)
            painter.setPen(highlight_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(stroke_path)

        # Create a temporary image for masking
        temp_image = QImage(
            painter.device().size(),
            QImage.Format_ARGB32_Premultiplied
        )
        temp_image.fill(Qt.transparent)
        temp_painter = QPainter(temp_image)
        temp_painter.setRenderHint(QPainter.Antialiasing)

        # Calculate the angle based on the tangent at the start point
        angle = self.calculate_start_tangent()

        # Draw the main strand
        temp_painter.setPen(Qt.NoPen)
        temp_painter.setBrush(self.stroke_color)
        temp_painter.drawPath(stroke_path)

        # Draw the fill
        fill_stroker = QPainterPathStroker()
        fill_stroker.setWidth(self.width)
        fill_stroker.setJoinStyle(Qt.MiterJoin)
        fill_stroker.setCapStyle(Qt.FlatCap)
        fill_path = fill_stroker.createStroke(path)
        temp_painter.setBrush(self.color)
        temp_painter.drawPath(fill_path)

        # Draw the end line
        side_pen = QPen(self.stroke_color, self.stroke_width)
        side_pen.setCapStyle(Qt.FlatCap)

        # Create a new color with the same alpha as the strand's color
        side_color = QColor(self.stroke_color)
        side_color.setAlpha(self.color.alpha())

        side_pen.setColor(side_color)
        painter.setPen(side_pen)

        temp_painter.setPen(side_pen)
        temp_painter.drawLine(self.end_line_start, self.end_line_end)

        # Create a mask for the circle
        circle_mask = QPainterPath()
        total_diameter = self.width + self.stroke_width * 2
        circle_radius = total_diameter / 2

        # Add the outer circle to the mask
        circle_mask.addEllipse(self.start, circle_radius, circle_radius)

        # Create the masking rectangle for half circle
        mask_rect = QPainterPath()
        rect_width = total_diameter * 2
        rect_height = total_diameter * 2
        rect_x = self.start.x() - rect_width/2
        rect_y = self.start.y()
        mask_rect.addRect(rect_x+1, rect_y+1, rect_width+1, rect_height+1)

        transform = QTransform()
        transform.translate(self.start.x(), self.start.y())
        transform.rotate(math.degrees(angle - math.pi/2))  # Rotate based on tangent angle
        transform.translate(-self.start.x(), -self.start.y())
        mask_rect = transform.map(mask_rect)

        outer_circle = QPainterPath()
        outer_circle.addEllipse(self.start, circle_radius, circle_radius)
        outer_mask = outer_circle.subtracted(mask_rect)

        # -- ADD THIS COMPOSITION MODE SETUP --
        temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        r = self.circle_stroke_color.red()
        g = self.circle_stroke_color.green()
        b = self.circle_stroke_color.blue()
        a = self.circle_stroke_color.alpha()
        logging.info(f"circle_stroke_color: (r={r}, g={g}, b={b}, a={a})")
        temp_painter.setPen(Qt.NoPen)
        temp_painter.setBrush(self.circle_stroke_color)
        temp_painter.drawPath(outer_mask)

        # Then draw the fill for the inner circle:
        inner_circle = QPainterPath()
        inner_circle.addEllipse(self.start, self.width / 2, self.width / 2)
        inner_mask = inner_circle.subtracted(mask_rect)
        temp_painter.setBrush(self.color)
        temp_painter.drawPath(inner_mask)

        # Draw the final image
        # Then draw the inner circle (fill)
        inner_circle = QPainterPath()
        inner_circle.addEllipse(self.start, self.width/2, self.width/2)
        temp_painter.drawPath(inner_circle)
        painter.drawImage(0, 0, temp_image)

        # ----------------------------------------------------------------
        # NEW CODE: Also draw an ending circle if has_circles == [True, True]
        if self.has_circles == [True, True]:
            # We'll compute the angle for the end based on the tangent at t=1.0:
            tangent_end = self.calculate_cubic_tangent(1.0)
            angle_end = math.atan2(tangent_end.y(), tangent_end.x())
            # If you still need to flip by 180°, uncomment or adjust:
            # angle_end += math.pi

            # Create another temporary painter so we can blend the circle on the end.
            temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            # Make a fresh path for the end circle's half-mask
            mask_rect_end = QPainterPath()
            rect_width_end = total_diameter * 2
            rect_height_end = total_diameter * 2
            rect_x_end = self.end.x() - rect_width_end / 2
            rect_y_end = self.end.y()
            mask_rect_end.addRect(rect_x_end + 1, rect_y_end + 1, rect_width_end + 1, rect_height_end + 1)

            transform_end = QTransform()
            transform_end.translate(self.end.x(), self.end.y())
            transform_end.rotate(math.degrees(angle_end - math.pi / 2)+180)
            transform_end.translate(-self.end.x(), -self.end.y())
            mask_rect_end = transform_end.map(mask_rect_end)

            outer_circle_end = QPainterPath()
            outer_circle_end.addEllipse(self.end, circle_radius, circle_radius)
            outer_mask_end = outer_circle_end.subtracted(mask_rect_end)

            # Draw the outer circle stroke
            temp_painter.setPen(Qt.NoPen)
            temp_painter.setBrush(self.stroke_color)
            temp_painter.drawPath(outer_mask_end)

            # Then draw the fill for the inner circle at the end
            inner_circle_end = QPainterPath()
            inner_circle_end.addEllipse(self.end, self.width / 2, self.width / 2)
            inner_mask_end = inner_circle_end.subtracted(mask_rect_end)
            temp_painter.setBrush(self.color)
            temp_painter.drawPath(inner_mask_end)

            # Draw a small inner circle fill so it doesn't look clipped
            just_inner_end = QPainterPath()
            just_inner_end.addEllipse(self.end, self.width / 2, self.width / 2)
            temp_painter.drawPath(just_inner_end)

            # Overwrite the final image portion
            painter.drawImage(0, 0, temp_image)
            temp_painter.end()
        # ----------------------------------------------------------------

        temp_painter.end()
        painter.restore()

        # Control points are now only drawn by StrandDrawingCanvas.draw_control_points
        # This code is removed to avoid duplicate drawing
        """
        # Draw control points if needed
        if hasattr(self, 'canvas') and self.canvas and self.canvas.show_control_points:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw control point lines
            control_line_pen = QPen(QColor('green'), 1, Qt.DashLine)
            painter.setPen(control_line_pen)
            painter.drawLine(self.start, self.control_point1)
            painter.drawLine(self.end, self.control_point2)
            
            # Draw control points
            control_pen = QPen(QColor('green'), 2)
            painter.setPen(control_pen)
            painter.setBrush(QBrush(QColor('green')))
            painter.drawEllipse(self.control_point1, 4, 4)
            painter.drawEllipse(self.control_point2, 4, 4)
            
            painter.restore()
        """


        
    def point_at(self, t):
        """Compute a point on the Bézier curve at parameter t."""
        # If third control point is enabled, use a composite curve with two segments
        if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'enable_third_control_point') and self.canvas.enable_third_control_point:
            if t <= 0.5:
                # Scale t to [0,1] for the first segment
                scaled_t = t * 2
                # First cubic segment: start to control_point_center
                p0 = self.start
                p1 = self.control_point1
                p2 = self.control_point1
                p3 = self.control_point_center
            else:
                # Scale t to [0,1] for the second segment
                scaled_t = (t - 0.5) * 2
                # Second cubic segment: control_point_center to end
                p0 = self.control_point_center
                p1 = self.control_point2
                p2 = self.control_point2
                p3 = self.end
            
            # Standard cubic Bézier formula
            x = (
                (1 - scaled_t) ** 3 * p0.x() +
                3 * (1 - scaled_t) ** 2 * scaled_t * p1.x() +
                3 * (1 - scaled_t) * scaled_t ** 2 * p2.x() +
                scaled_t ** 3 * p3.x()
            )
            y = (
                (1 - scaled_t) ** 3 * p0.y() +
                3 * (1 - scaled_t) ** 2 * scaled_t * p1.y() +
                3 * (1 - scaled_t) * scaled_t ** 2 * p2.y() +
                scaled_t ** 3 * p3.y()
            )
            return QPointF(x, y)
        else:
            # Standard cubic Bézier with 2 control points
            p0, p1, p2, p3 = self.start, self.control_point1, self.control_point2, self.end

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
                


    def update_side_line(self):
        """Update side lines considering the curve's shape near the ends."""
        # Small values near 0 and 1 to get tangents that include control points
        t_start = 0.01
        t_end = 0.99

        # Compute tangents near the start and end
        tangent_start = self.calculate_cubic_tangent(t_start)
        tangent_end = self.calculate_cubic_tangent(t_end)

        # Handle zero-length tangent vectors
        if tangent_start.manhattanLength() == 0:
            tangent_start = self.end - self.start
        if tangent_end.manhattanLength() == 0:
            tangent_end = self.start - self.end

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

    def draw(self, painter):
        """Draw the strand with squared ends and highlight if selected."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Get the path representing the strand as a cubic Bézier curve
        path = self.get_path()

        # Create a stroker for the stroke path with squared ends
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
                if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'default_shadow_color'):
                    shadow_color = self.canvas.default_shadow_color
                    # Ensure the strand's shadow color is also updated for future reference
                    self.shadow_color = QColor(shadow_color)
                
                # Draw strand body shadow with explicit shadow color
                draw_strand_shadow(painter, self, shadow_color)
                
                # Draw circle shadows if this strand has circles
                if hasattr(self, 'has_circles') and any(self.has_circles):
                    draw_circle_shadow(painter, self, shadow_color)
        except Exception as e:
            # Log the error but continue with the rendering
            logging.error(f"Error applying strand shadow: {e}")

        # Only draw highlight if this is not a MaskedStrand
        if self.is_selected and not isinstance(self, MaskedStrand):
            highlight_pen = QPen(QColor('red'), self.stroke_width + 8)
            highlight_pen.setJoinStyle(Qt.MiterJoin)
            highlight_pen.setCapStyle(Qt.FlatCap)
            painter.setPen(highlight_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(stroke_path)

        # Create a temporary image for masking
        temp_image = QImage(
            painter.device().size(),
            QImage.Format_ARGB32_Premultiplied
        )
        temp_image.fill(Qt.transparent)
        temp_painter = QPainter(temp_image)
        temp_painter.setRenderHint(QPainter.Antialiasing)

        # Calculate the angle based on the tangent at the start point
        angle = self.calculate_start_tangent()

        # Draw the main strand
        temp_painter.setPen(Qt.NoPen)
        temp_painter.setBrush(self.stroke_color)
        temp_painter.drawPath(stroke_path)

        # Draw the fill
        fill_stroker = QPainterPathStroker()
        fill_stroker.setWidth(self.width)
        fill_stroker.setJoinStyle(Qt.MiterJoin)
        fill_stroker.setCapStyle(Qt.FlatCap)
        fill_path = fill_stroker.createStroke(path)
        temp_painter.setBrush(self.color)
        temp_painter.drawPath(fill_path)

        # Draw the end line
        side_pen = QPen(self.stroke_color, self.stroke_width)
        side_pen.setCapStyle(Qt.FlatCap)

        # Create a new color with the same alpha as the strand's color
        side_color = QColor(self.stroke_color)
        side_color.setAlpha(self.color.alpha())

        side_pen.setColor(side_color)
        painter.setPen(side_pen)

        temp_painter.setPen(side_pen)
        temp_painter.drawLine(self.end_line_start, self.end_line_end)

        # Create a mask for the circle
        circle_mask = QPainterPath()
        total_diameter = self.width + self.stroke_width * 2
        circle_radius = total_diameter / 2

        # Add the outer circle to the mask
        circle_mask.addEllipse(self.start, circle_radius, circle_radius)

        # Create the masking rectangle for half circle
        mask_rect = QPainterPath()
        rect_width = total_diameter * 2
        rect_height = total_diameter * 2
        rect_x = self.start.x() - rect_width/2
        rect_y = self.start.y()
        mask_rect.addRect(rect_x+1, rect_y+1, rect_width+1, rect_height+1)

        transform = QTransform()
        transform.translate(self.start.x(), self.start.y())
        transform.rotate(math.degrees(angle - math.pi/2))  # Rotate based on tangent angle
        transform.translate(-self.start.x(), -self.start.y())
        mask_rect = transform.map(mask_rect)

        outer_circle = QPainterPath()
        outer_circle.addEllipse(self.start, circle_radius, circle_radius)
        outer_mask = outer_circle.subtracted(mask_rect)

        # -- ADD THIS COMPOSITION MODE SETUP --
        temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        r = self.circle_stroke_color.red()
        g = self.circle_stroke_color.green()
        b = self.circle_stroke_color.blue()
        a = self.circle_stroke_color.alpha()
        logging.info(f"circle_stroke_color: (r={r}, g={g}, b={b}, a={a})")
        temp_painter.setPen(Qt.NoPen)
        temp_painter.setBrush(self.circle_stroke_color)
        temp_painter.drawPath(outer_mask)

        # Then draw the fill for the inner circle:
        inner_circle = QPainterPath()
        inner_circle.addEllipse(self.start, self.width / 2, self.width / 2)
        inner_mask = inner_circle.subtracted(mask_rect)
        temp_painter.setBrush(self.color)
        temp_painter.drawPath(inner_mask)

        # Draw the final image
        # Then draw the inner circle (fill)
        inner_circle = QPainterPath()
        inner_circle.addEllipse(self.start, self.width/2, self.width/2)
        temp_painter.drawPath(inner_circle)
        painter.drawImage(0, 0, temp_image)

        # ----------------------------------------------------------------
        # NEW CODE: Also draw an ending circle if has_circles == [True, True]
        if self.has_circles == [True, True]:
            # We'll compute the angle for the end based on the tangent at t=1.0:
            tangent_end = self.calculate_cubic_tangent(1.0)
            angle_end = math.atan2(tangent_end.y(), tangent_end.x())
            # If you still need to flip by 180°, uncomment or adjust:
            # angle_end += math.pi

            # Create another temporary painter so we can blend the circle on the end.
            temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            # Make a fresh path for the end circle's half-mask
            mask_rect_end = QPainterPath()
            rect_width_end = total_diameter * 2
            rect_height_end = total_diameter * 2
            rect_x_end = self.end.x() - rect_width_end / 2
            rect_y_end = self.end.y()
            mask_rect_end.addRect(rect_x_end + 1, rect_y_end + 1, rect_width_end + 1, rect_height_end + 1)

            transform_end = QTransform()
            transform_end.translate(self.end.x(), self.end.y())
            transform_end.rotate(math.degrees(angle_end - math.pi / 2)+180)
            transform_end.translate(-self.end.x(), -self.end.y())
            mask_rect_end = transform_end.map(mask_rect_end)

            outer_circle_end = QPainterPath()
            outer_circle_end.addEllipse(self.end, circle_radius, circle_radius)
            outer_mask_end = outer_circle_end.subtracted(mask_rect_end)

            # Draw the outer circle stroke
            temp_painter.setPen(Qt.NoPen)
            temp_painter.setBrush(self.stroke_color)
            temp_painter.drawPath(outer_mask_end)

            # Then draw the fill for the inner circle at the end
            inner_circle_end = QPainterPath()
            inner_circle_end.addEllipse(self.end, self.width / 2, self.width / 2)
            inner_mask_end = inner_circle_end.subtracted(mask_rect_end)
            temp_painter.setBrush(self.color)
            temp_painter.drawPath(inner_mask_end)

            # Draw a small inner circle fill so it doesn't look clipped
            just_inner_end = QPainterPath()
            just_inner_end.addEllipse(self.end, self.width / 2, self.width / 2)
            temp_painter.drawPath(just_inner_end)

            # Overwrite the final image portion
            painter.drawImage(0, 0, temp_image)
            temp_painter.end()
        # ----------------------------------------------------------------

        temp_painter.end()
        painter.restore()

        # Control points are now only drawn by StrandDrawingCanvas.draw_control_points
        # This code is removed to avoid duplicate drawing
        """
        # Draw control points if needed
        if hasattr(self, 'canvas') and self.canvas and self.canvas.show_control_points:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw control point lines
            control_line_pen = QPen(QColor('green'), 1, Qt.DashLine)
            painter.setPen(control_line_pen)
            painter.drawLine(self.start, self.control_point1)
            painter.drawLine(self.end, self.control_point2)
            
            # Draw control points
            control_pen = QPen(QColor('green'), 2)
            painter.setPen(control_pen)
            painter.setBrush(QBrush(QColor('green')))
            painter.drawEllipse(self.control_point1, 4, 4)
            painter.drawEllipse(self.control_point2, 4, 4)
            
            painter.restore()
        """


        
    def point_at(self, t):
        """Compute a point on the Bézier curve at parameter t."""
        # If third control point is enabled, use a composite curve with two segments
        if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'enable_third_control_point') and self.canvas.enable_third_control_point:
            if t <= 0.5:
                # Scale t to [0,1] for the first segment
                scaled_t = t * 2
                # First cubic segment: start to control_point_center
                p0 = self.start
                p1 = self.control_point1
                p2 = self.control_point1
                p3 = self.control_point_center
            else:
                # Scale t to [0,1] for the second segment
                scaled_t = (t - 0.5) * 2
                # Second cubic segment: control_point_center to end
                p0 = self.control_point_center
                p1 = self.control_point2
                p2 = self.control_point2
                p3 = self.end
            
            # Standard cubic Bézier formula
            x = (
                (1 - scaled_t) ** 3 * p0.x() +
                3 * (1 - scaled_t) ** 2 * scaled_t * p1.x() +
                3 * (1 - scaled_t) * scaled_t ** 2 * p2.x() +
                scaled_t ** 3 * p3.x()
            )
            y = (
                (1 - scaled_t) ** 3 * p0.y() +
                3 * (1 - scaled_t) ** 2 * scaled_t * p1.y() +
                3 * (1 - scaled_t) * scaled_t ** 2 * p2.y() +
                scaled_t ** 3 * p3.y()
            )
            return QPointF(x, y)
        else:
            # Standard cubic Bézier with 2 control points
            p0, p1, p2, p3 = self.start, self.control_point1, self.control_point2, self.end

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
                


    def update_side_line(self):
        """Update side lines considering the curve's shape near the ends."""
        # Small values near 0 and 1 to get tangents that include control points
        t_start = 0.01
        t_end = 0.99

        # Compute tangents near the start and end
        tangent_start = self.calculate_cubic_tangent(t_start)
        tangent_end = self.calculate_cubic_tangent(t_end)

        # Handle zero-length tangent vectors
        if tangent_start.manhattanLength() == 0:
            tangent_start = self.end - self.start
        if tangent_end.manhattanLength() == 0:
            tangent_end = self.start - self.end

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

    def draw(self, painter):
        """Draw the strand with squared ends and highlight if selected."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Get the path representing the strand as a cubic Bézier curve
        path = self.get_path()

        # Create a stroker for the stroke path with squared ends
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
                if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'default_shadow_color'):
                    shadow_color = self.canvas.default_shadow_color
                    # Ensure the strand's shadow color is also updated for future reference
                    self.shadow_color = QColor(shadow_color)
                
                # Draw strand body shadow with explicit shadow color
                draw_strand_shadow(painter, self, shadow_color)
                
                # Draw circle shadows if this strand has circles
                if hasattr(self, 'has_circles') and any(self.has_circles):
                    draw_circle_shadow(painter, self, shadow_color)
        except Exception as e:
            # Log the error but continue with the rendering
            logging.error(f"Error applying strand shadow: {e}")

        # Only draw highlight if this is not a MaskedStrand
        if self.is_selected and not isinstance(self, MaskedStrand):
            highlight_pen = QPen(QColor('red'), self.stroke_width + 8)
            highlight_pen.setJoinStyle(Qt.MiterJoin)
            highlight_pen.setCapStyle(Qt.FlatCap)
            painter.setPen(highlight_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(stroke_path)

        # Create a temporary image for masking
        temp_image = QImage(
            painter.device().size(),
            QImage.Format_ARGB32_Premultiplied
        )
        temp_image.fill(Qt.transparent)
        temp_painter = QPainter(temp_image)
        temp_painter.setRenderHint(QPainter.Antialiasing)

        # Calculate the angle based on the tangent at the start point
        angle = self.calculate_start_tangent()

        # Draw the main strand
        temp_painter.setPen(Qt.NoPen)
        temp_painter.setBrush(self.stroke_color)
        temp_painter.drawPath(stroke_path)

        # Draw the fill
        fill_stroker = QPainterPathStroker()
        fill_stroker.setWidth(self.width)
        fill_stroker.setJoinStyle(Qt.MiterJoin)
        fill_stroker.setCapStyle(Qt.FlatCap)
        fill_path = fill_stroker.createStroke(path)
        temp_painter.setBrush(self.color)
        temp_painter.drawPath(fill_path)

        # Draw the end line
        side_pen = QPen(self.stroke_color, self.stroke_width)
        side_pen.setCapStyle(Qt.FlatCap)

        # Create a new color with the same alpha as the strand's color
        side_color = QColor(self.stroke_color)
        side_color.setAlpha(self.color.alpha())

        side_pen.setColor(side_color)
        painter.setPen(side_pen)

        temp_painter.setPen(side_pen)
        temp_painter.drawLine(self.end_line_start, self.end_line_end)

        # Create a mask for the circle
        circle_mask = QPainterPath()
        total_diameter = self.width + self.stroke_width * 2
        circle_radius = total_diameter / 2

        # Add the outer circle to the mask
        circle_mask.addEllipse(self.start, circle_radius, circle_radius)

        # Create the masking rectangle for half circle
        mask_rect = QPainterPath()
        rect_width = total_diameter * 2
        rect_height = total_diameter * 2
        rect_x = self.start.x() - rect_width/2
        rect_y = self.start.y()
        mask_rect.addRect(rect_x+1, rect_y+1, rect_width+1, rect_height+1)

        transform = QTransform()
        transform.translate(self.start.x(), self.start.y())
        transform.rotate(math.degrees(angle - math.pi/2))  # Rotate based on tangent angle
        transform.translate(-self.start.x(), -self.start.y())
        mask_rect = transform.map(mask_rect)

        outer_circle = QPainterPath()
        outer_circle.addEllipse(self.start, circle_radius, circle_radius)
        outer_mask = outer_circle.subtracted(mask_rect)

        # -- ADD THIS COMPOSITION MODE SETUP --
        temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        r = self.circle_stroke_color.red()
        g = self.circle_stroke_color.green()
        b = self.circle_stroke_color.blue()
        a = self.circle_stroke_color.alpha()
        logging.info(f"circle_stroke_color: (r={r}, g={g}, b={b}, a={a})")
        temp_painter.setPen(Qt.NoPen)
        temp_painter.setBrush(self.circle_stroke_color)
        temp_painter.drawPath(outer_mask)

        # Then draw the fill for the inner circle:
        inner_circle = QPainterPath()
        inner_circle.addEllipse(self.start, self.width / 2, self.width / 2)
        inner_mask = inner_circle.subtracted(mask_rect)
        temp_painter.setBrush(self.color)
        temp_painter.drawPath(inner_mask)

        # Draw the final image
        # Then draw the inner circle (fill)
        inner_circle = QPainterPath()
        inner_circle.addEllipse(self.start, self.width/2, self.width/2)
        temp_painter.drawPath(inner_circle)
        painter.drawImage(0, 0, temp_image)

        # ----------------------------------------------------------------
        # NEW CODE: Also draw an ending circle if has_circles == [True, True]
        if self.has_circles == [True, True]:
            # We'll compute the angle for the end based on the tangent at t=1.0:
            tangent_end = self.calculate_cubic_tangent(1.0)
            angle_end = math.atan2(tangent_end.y(), tangent_end.x())
            # If you still need to flip by 180°, uncomment or adjust:
            # angle_end += math.pi

            # Create another temporary painter so we can blend the circle on the end.
            temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            # Make a fresh path for the end circle's half-mask
            mask_rect_end = QPainterPath()
            rect_width_end = total_diameter * 2
            rect_height_end = total_diameter * 2
            rect_x_end = self.end.x() - rect_width_end / 2
            rect_y_end = self.end.y()
            mask_rect_end.addRect(rect_x_end + 1, rect_y_end + 1, rect_width_end + 1, rect_height_end + 1)

            transform_end = QTransform()
            transform_end.translate(self.end.x(), self.end.y())
            transform_end.rotate(math.degrees(angle_end - math.pi / 2)+180)
            transform_end.translate(-self.end.x(), -self.end.y())
            mask_rect_end = transform_end.map(mask_rect_end)

            outer_circle_end = QPainterPath()
            outer_circle_end.addEllipse(self.end, circle_radius, circle_radius)
            outer_mask_end = outer_circle_end.subtracted(mask_rect_end)

            # Draw the outer circle stroke
            temp_painter.setPen(Qt.NoPen)
            temp_painter.setBrush(self.stroke_color)
            temp_painter.drawPath(outer_mask_end)

            # Then draw the fill for the inner circle at the end
            inner_circle_end = QPainterPath()
            inner_circle_end.addEllipse(self.end, self.width / 2, self.width / 2)
            inner_mask_end = inner_circle_end.subtracted(mask_rect_end)
            temp_painter.setBrush(self.color)
            temp_painter.drawPath(inner_mask_end)

            # Draw a small inner circle fill so it doesn't look clipped
            just_inner_end = QPainterPath()
            just_inner_end.addEllipse(self.end, self.width / 2, self.width / 2)
            temp_painter.drawPath(just_inner_end)

            # Overwrite the final image portion
            painter.drawImage(0, 0, temp_image)
            temp_painter.end()
        # ----------------------------------------------------------------

        temp_painter.end()
        painter.restore()

        # Control points are now only drawn by StrandDrawingCanvas.draw_control_points
        # This code is removed to avoid duplicate drawing
        """
        # Draw control points if needed
        if hasattr(self, 'canvas') and self.canvas and self.canvas.show_control_points:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw control point lines
            control_line_pen = QPen(QColor('green'), 1, Qt.DashLine)
            painter.setPen(control_line_pen)
            painter.drawLine(self.start, self.control_point1)
            painter.drawLine(self.end, self.control_point2)
            
            # Draw control points
            control_pen = QPen(QColor('green'), 2)
            painter.setPen(control_pen)
            painter.setBrush(QBrush(QColor('green')))
            painter.drawEllipse(self.control_point1, 4, 4)
            painter.drawEllipse(self.control_point2, 4, 4)
            
            painter.restore()
        """


        
    def point_at(self, t):
        """Compute a point on the Bézier curve at parameter t."""
        # If third control point is enabled, use a composite curve with two segments
        if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'enable_third_control_point') and self.canvas.enable_third_control_point:
            if t <= 0.5:
                # Scale t to [0,1] for the first segment
                scaled_t = t * 2
                # First cubic segment: start to control_point_center
                p0 = self.start
                p1 = self.control_point1
                p2 = self.control_point1
                p3 = self.control_point_center
            else:
                # Scale t to [0,1] for the second segment
                scaled_t = (t - 0.5) * 2
                # Second cubic segment: control_point_center to end
                p0 = self.control_point_center
                p1 = self.control_point2
                p2 = self.control_point2
                p3 = self.end
            
            # Standard cubic Bézier formula
            x = (
                (1 - scaled_t) ** 3 * p0.x() +
                3 * (1 - scaled_t) ** 2 * scaled_t * p1.x() +
                3 * (1 - scaled_t) * scaled_t ** 2 * p2.x() +
                scaled_t ** 3 * p3.x()
            )
            y = (
                (1 - scaled_t) ** 3 * p0.y() +
                3 * (1 - scaled_t) ** 2 * scaled_t * p1.y() +
                3 * (1 - scaled_t) * scaled_t ** 2 * p2.y() +
                scaled_t ** 3 * p3.y()
            )
            return QPointF(x, y)
        else:
            # Standard cubic Bézier with 2 control points
            p0, p1, p2, p3 = self.start, self.control_point1, self.control_point2, self.end

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
                


    def update_side_line(self):
        """Update side lines considering the curve's shape near the ends."""
        # Small values near 0 and 1 to get tangents that include control points
        t_start = 0.01
        t_end = 0.99

        # Compute tangents near the start and end
        tangent_start = self.calculate_cubic_tangent(t_start)
        tangent_end = self.calculate_cubic_tangent(t_end)

        # Handle zero-length tangent vectors
        if tangent_start.manhattanLength() == 0:
            tangent_start = self.end - self.start
        if tangent_end.manhattanLength() == 0:
            tangent_end = self.start - self.end

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

    def draw(self, painter):
        """Draw the strand with squared ends and highlight if selected."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Get the path representing the strand as a cubic Bézier curve
        path = self.get_path()

        # Create a stroker for the stroke path with squared ends
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
                if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'default_shadow_color'):
                    shadow_color = self.canvas.default_shadow_color
                    # Ensure the strand's shadow color is also updated for future reference
                    self.shadow_color = QColor(shadow_color)
                
                # Draw strand body shadow with explicit shadow color
                draw_strand_shadow(painter, self, shadow_color)
                
                # Draw circle shadows if this strand has circles
                if hasattr(self, 'has_circles') and any(self.has_circles):
                    draw_circle_shadow(painter, self, shadow_color)
        except Exception as e:
            # Log the error but continue with the rendering
            logging.error(f"Error applying strand shadow: {e}")

        # Only draw highlight if this is not a MaskedStrand
        if self.is_selected and not isinstance(self, MaskedStrand):
            highlight_pen = QPen(QColor('red'), self.stroke_width + 8)
            highlight_pen.setJoinStyle(Qt.MiterJoin)
            highlight_pen.setCapStyle(Qt.FlatCap)
            painter.setPen(highlight_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(stroke_path)

        # Create a temporary image for masking
        temp_image = QImage(
            painter.device().size(),
            QImage.Format_ARGB32_Premultiplied
        )
        temp_image.fill(Qt.transparent)
        temp_painter = QPainter(temp_image)
        temp_painter.setRenderHint(QPainter.Antialiasing)

        # Calculate the angle based on the tangent at the start point
        angle = self.calculate_start_tangent()

        # Draw the main strand
        temp_painter.setPen(Qt.NoPen)
        temp_painter.setBrush(self.stroke_color)
        temp_painter.drawPath(stroke_path)

        # Draw the fill
        fill_stroker = QPainterPathStroker()
        fill_stroker.setWidth(self.width)
        fill_stroker.setJoinStyle(Qt.MiterJoin)
        fill_stroker.setCapStyle(Qt.FlatCap)
        fill_path = fill_stroker.createStroke(path)
        temp_painter.setBrush(self.color)
        temp_painter.drawPath(fill_path)

        # Draw the end line
        side_pen = QPen(self.stroke_color, self.stroke_width)
        side_pen.setCapStyle(Qt.FlatCap)

        # Create a new color with the same alpha as the strand's color
        side_color = QColor(self.stroke_color)
        side_color.setAlpha(self.color.alpha())

        side_pen.setColor(side_color)
        painter.setPen(side_pen)

        temp_painter.setPen(side_pen)
        temp_painter.drawLine(self.end_line_start, self.end_line_end)

        # Create a mask for the circle
        circle_mask = QPainterPath()
        total_diameter = self.width + self.stroke_width * 2
        circle_radius = total_diameter / 2

        # Add the outer circle to the mask
        circle_mask.addEllipse(self.start, circle_radius, circle_radius)

        # Create the masking rectangle for half circle
        mask_rect = QPainterPath()
        rect_width = total_diameter * 2
        rect_height = total_diameter * 2
        rect_x = self.start.x() - rect_width/2
        rect_y = self.start.y()
        mask_rect.addRect(rect_x+1, rect_y+1, rect_width+1, rect_height+1)

        transform = QTransform()
        transform.translate(self.start.x(), self.start.y())
        transform.rotate(math.degrees(angle - math.pi/2))  # Rotate based on tangent angle
        transform.translate(-self.start.x(), -self.start.y())
        mask_rect = transform.map(mask_rect)

        outer_circle = QPainterPath()
        outer_circle.addEllipse(self.start, circle_radius, circle_radius)
        outer_mask = outer_circle.subtracted(mask_rect)

        # -- ADD THIS COMPOSITION MODE SETUP --
        temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        r = self.circle_stroke_color.red()
        g = self.circle_stroke_color.green()
        b = self.circle_stroke_color.blue()
        a = self.circle_stroke_color.alpha()
        logging.info(f"circle_stroke_color: (r={r}, g={g}, b={b}, a={a})")
        temp_painter.setPen(Qt.NoPen)
        temp_painter.setBrush(self.circle_stroke_color)
        temp_painter.drawPath(outer_mask)

        # Then draw the fill for the inner circle:
        inner_circle = QPainterPath()
        inner_circle.addEllipse(self.start, self.width / 2, self.width / 2)
        inner_mask = inner_circle.subtracted(mask_rect)
        temp_painter.setBrush(self.color)
        temp_painter.drawPath(inner_mask)

        # Draw the final image
        # Then draw the inner circle (fill)
        inner_circle = QPainterPath()
        inner_circle.addEllipse(self.start, self.width/2, self.width/2)
        temp_painter.drawPath(inner_circle)
        painter.drawImage(0, 0, temp_image)

        # ----------------------------------------------------------------
        # NEW CODE: Also draw an ending circle if has_circles == [True, True]
        if self.has_circles == [True, True]:
            # We'll compute the angle for the end based on the tangent at t=1.0:
            tangent_end = self.calculate_cubic_tangent(1.0)
            angle_end = math.atan2(tangent_end.y(), tangent_end.x())
            # If you still need to flip by 180°, uncomment or adjust:
            # angle_end += math.pi

            # Create another temporary painter so we can blend the circle on the end.
            temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            # Make a fresh path for the end circle's half-mask
            mask_rect_end = QPainterPath()
            rect_width_end = total_diameter * 2
            rect_height_end = total_diameter * 2
            rect_x_end = self.end.x() - rect_width_end / 2
            rect_y_end = self.end.y()
            mask_rect_end.addRect(rect_x_end + 1, rect_y_end + 1, rect_width_end + 1, rect_height_end + 1)

            transform_end = QTransform()
            transform_end.translate(self.end.x(), self.end.y())
            transform_end.rotate(math.degrees(angle_end - math.pi / 2)+180)
            transform_end.translate(-self.end.x(), -self.end.y())
            mask_rect_end = transform_end.map(mask_rect_end)

            outer_circle_end = QPainterPath()
            outer_circle_end.addEllipse(self.end, circle_radius, circle_radius)
            outer_mask_end = outer_circle_end.subtracted(mask_rect_end)

            # Draw the outer circle stroke
            temp_painter.setPen(Qt.NoPen)
            temp_painter.setBrush(self.stroke_color)
            temp_painter.drawPath(outer_mask_end)

            # Then draw the fill for the inner circle at the end
            inner_circle_end = QPainterPath()
            inner_circle_end.addEllipse(self.end, self.width / 2, self.width / 2)
            inner_mask_end = inner_circle_end.subtracted(mask_rect_end)
            temp_painter.setBrush(self.color)
            temp_painter.drawPath(inner_mask_end)

            # Draw a small inner circle fill so it doesn't look clipped
            just_inner_end = QPainterPath()
            just_inner_end.addEllipse(self.end, self.width / 2, self.width / 2)
            temp_painter.drawPath(just_inner_end)

            # Overwrite the final image portion
            painter.drawImage(0, 0, temp_image)
            temp_painter.end()
        # ----------------------------------------------------------------

        temp_painter.end()
        painter.restore()

        # Control points are now only drawn by StrandDrawingCanvas.draw_control_points
        # This code is removed to avoid duplicate drawing
        """
        # Draw control points if needed
        if hasattr(self, 'canvas') and self.canvas and self.canvas.show_control_points:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw control point lines
            control_line_pen = QPen(QColor('green'), 1, Qt.DashLine)
            painter.setPen(control_line_pen)
            painter.drawLine(self.start, self.control_point1)
            painter.drawLine(self.end, self.control_point2)
            
            # Draw control points
            control_pen = QPen(QColor('green'), 2)
            painter.setPen(control_pen)
            painter.setBrush(QBrush(QColor('green')))
            painter.drawEllipse(self.control_point1, 4, 4)
            painter.drawEllipse(self.control_point2, 4, 4)
            
            painter.restore()
        """


        
    def point_at(self, t):
        """Compute a point on the Bézier curve at parameter t."""
        # If third control point is enabled, use a composite curve with two segments
        if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'enable_third_control_point') and self.canvas.enable_third_control_point:
            if t <= 0.5:
                # Scale t to [0,1] for the first segment
                scaled_t = t * 2
                # First cubic segment: start to control_point_center
                p0 = self.start
                p1 = self.control_point1
                p2 = self.control_point1
                p3 = self.control_point_center
            else:
                # Scale t to [0,1] for the second segment
                scaled_t = (t - 0.5) * 2
                # Second cubic segment: control_point_center to end
                p0 = self.control_point_center
                p1 = self.control_point2
                p2 = self.control_point2
                p3 = self.end
            
            # Standard cubic Bézier formula
            x = (
                (1 - scaled_t) ** 3 * p0.x() +
                3 * (1 - scaled_t) ** 2 * scaled_t * p1.x() +
                3 * (1 - scaled_t) * scaled_t ** 2 * p2.x() +
                scaled_t ** 3 * p3.x()
            )
            y = (
                (1 - scaled_t) ** 3 * p0.y() +
                3 * (1 - scaled_t) ** 2 * scaled_t * p1.y() +
                3 * (1 - scaled_t) * scaled_t ** 2 * p2.y() +
                scaled_t ** 3 * p3.y()
            )
            return QPointF(x, y)
        else:
            # Standard cubic Bézier with 2 control points
            p0, p1, p2, p3 = self.start, self.control_point1, self.control_point2, self.end

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
                


    def update_side_line(self):
        """Update side lines considering the curve's shape near the ends."""
        # Small values near 0 and 1 to get tangents that include control points
        t_start = 0.01
        t_end = 0.99

        # Compute tangents near the start and end
        tangent_start = self.calculate_cubic_tangent(t_start)
        tangent_end = self.calculate_cubic_tangent(t_end)

        # Handle zero-length tangent vectors
        if tangent_start.manhattanLength() == 0:
            tangent_start = self.end - self.start
        if tangent_end.manhattanLength() == 0:
            tangent_end = self.start - self.end

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

    def draw(self, painter):
        """Draw the strand with squared ends and highlight if selected."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Get the path representing the strand as a cubic Bézier curve
        path = self.get_path()

        # Create a stroker for the stroke path with squared ends
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
                if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'default_shadow_color'):
                    shadow_color = self.canvas.default_shadow_color
                    # Ensure the strand's shadow color is also updated for future reference
                    self.shadow_color = QColor(shadow_color)
                
                # Draw strand body shadow with explicit shadow color
                draw_strand_shadow(painter, self, shadow_color)
                
                # Draw circle shadows if this strand has circles
                if hasattr(self, 'has_circles') and any(self.has_circles):
                    draw_circle_shadow(painter, self, shadow_color)
        except Exception as e:
            # Log the error but continue with the rendering
            logging.error(f"Error applying strand shadow: {e}")

        # Only draw highlight if this is not a MaskedStrand
        if self.is_selected and not isinstance(self, MaskedStrand):
            highlight_pen = QPen(QColor('red'), self.stroke_width + 8)
            highlight_pen.setJoinStyle(Qt.MiterJoin)
            highlight_pen.setCapStyle(Qt.FlatCap)
            painter.setPen(highlight_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(stroke_path)

        # Create a temporary image for masking
        temp_image = QImage(
            painter.device().size(),
            QImage.Format_ARGB32_Premultiplied
        )
        temp_image.fill(Qt.transparent)
        temp_painter = QPainter(temp_image)
        temp_painter.setRenderHint(QPainter.Antialiasing)

        # Calculate the angle based on the tangent at the start point
        angle = self.calculate_start_tangent()

        # Draw the main strand
        temp_painter.setPen(Qt.NoPen)
        temp_painter.setBrush(self.stroke_color)
        temp_painter.drawPath(stroke_path)

        # Draw the fill
        fill_stroker = QPainterPathStroker()
        fill_stroker.setWidth(self.width)
        fill_stroker.setJoinStyle(Qt.MiterJoin)
        fill_stroker.setCapStyle(Qt.FlatCap)
        fill_path = fill_stroker.createStroke(path)
        temp_painter.setBrush(self.color)
        temp_painter.drawPath(fill_path)

        # Draw the end line
        side_pen = QPen(self.stroke_color, self.stroke_width)
        side_pen.setCapStyle(Qt.FlatCap)

        # Create a new color with the same alpha as the strand's color
        side_color = QColor(self.stroke_color)
        side_color.setAlpha(self.color.alpha())

        side_pen.setColor(side_color)
        painter.setPen(side_pen)

        temp_painter.setPen(side_pen)
        temp_painter.drawLine(self.end_line_start, self.end_line_end)

        # Create a mask for the circle
        circle_mask = QPainterPath()
        total_diameter = self.width + self.stroke_width * 2
        circle_radius = total_diameter / 2

        # Add the outer circle to the mask
        circle_mask.addEllipse(self.start, circle_radius, circle_radius)

        # Create the masking rectangle for half circle
        mask_rect = QPainterPath()
        rect_width = total_diameter * 2
        rect_height = total_diameter * 2
        rect_x = self.start.x() - rect_width/2
        rect_y = self.start.y()
        mask_rect.addRect(rect_x+1, rect_y+1, rect_width+1, rect_height+1)

        transform = QTransform()
        transform.translate(self.start.x(), self.start.y())
        transform.rotate(math.degrees(angle - math.pi/2))  # Rotate based on tangent angle
        transform.translate(-self.start.x(), -self.start.y())
        mask_rect = transform.map(mask_rect)

        outer_circle = QPainterPath()
        outer_circle.addEllipse(self.start, circle_radius, circle_radius)
        outer_mask = outer_circle.subtracted(mask_rect)

        # -- ADD THIS COMPOSITION MODE SETUP --
        temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        r = self.circle_stroke_color.red()
        g = self.circle_stroke_color.green()
        b = self.circle_stroke_color.blue()
        a = self.circle_stroke_color.alpha()
        logging.info(f"circle_stroke_color: (r={r}, g={g}, b={b}, a={a})")
        temp_painter.setPen(Qt.NoPen)
        temp_painter.setBrush(self.circle_stroke_color)
        temp_painter.drawPath(outer_mask)

        # Then draw the fill for the inner circle:
        inner_circle = QPainterPath()
        inner_circle.addEllipse(self.start, self.width / 2, self.width / 2)
        inner_mask = inner_circle.subtracted(mask_rect)
        temp_painter.setBrush(self.color)
        temp_painter.drawPath(inner_mask)

        # Draw the final image
        # Then draw the inner circle (fill)
        inner_circle = QPainterPath()
        inner_circle.addEllipse(self.start, self.width/2, self.width/2)
        temp_painter.drawPath(inner_circle)
        painter.drawImage(0, 0, temp_image)

        # ----------------------------------------------------------------
        # NEW CODE: Also draw an ending circle if has_circles == [True, True]
        if self.has_circles == [True, True]:
            # We'll compute the angle for the end based on the tangent at t=1.0:
            tangent_end = self.calculate_cubic_tangent(1.0)
            angle_end = math.atan2(tangent_end.y(), tangent_end.x())
            # If you still need to flip by 180°, uncomment or adjust:
            # angle_end += math.pi

            # Create another temporary painter so we can blend the circle on the end.
            temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            # Make a fresh path for the end circle's half-mask
            mask_rect_end = QPainterPath()
            rect_width_end = total_diameter * 2
            rect_height_end = total_diameter * 2
            rect_x_end = self.end.x() - rect_width_end / 2
            rect_y_end = self.end.y()
            mask_rect_end.addRect(rect_x_end + 1, rect_y_end + 1, rect_width_end + 1, rect_height_end + 1)

            transform_end = QTransform()
            transform_end.translate(self.end.x(), self.end.y())
            transform_end.rotate(math.degrees(angle_end - math.pi / 2)+180)
            transform_end.translate(-self.end.x(), -self.end.y())
            mask_rect_end = transform_end.map(mask_rect_end)

            outer_circle_end = QPainterPath()
            outer_circle_end.addEllipse(self.end, circle_radius, circle_radius)
            outer_mask_end = outer_circle_end.subtracted(mask_rect_end)

            # Draw the outer circle stroke
            temp_painter.setPen(Qt.NoPen)
            temp_painter.setBrush(self.stroke_color)
            temp_painter.drawPath(outer_mask_end)

            # Then draw the fill for the inner circle at the end
            inner_circle_end = QPainterPath()
            inner_circle_end.addEllipse(self.end, self.width / 2, self.width / 2)
            inner_mask_end = inner_circle_end.subtracted(mask_rect_end)
            temp_painter.setBrush(self.color)
            temp_painter.drawPath(inner_mask_end)

            # Draw a small inner circle fill so it doesn't look clipped
            just_inner_end = QPainterPath()
            just_inner_end.addEllipse(self.end, self.width / 2, self.width / 2)
            temp_painter.drawPath(just_inner_end)

            # Overwrite the final image portion
            painter.drawImage(0, 0, temp_image)
            temp_painter.end()
        # ----------------------------------------------------------------
        # Draw the circles at connection points
        for i, has_circle in enumerate(self.has_circles):
            # --- REPLACE WITH THIS SIMPLE CHECK ---
            # Only draw if this end should have a circle and the strand is currently selected
            if not has_circle or not self.is_selected:
                continue
            # --- END REPLACE ---
            
            # Save painter state (Original line)
            painter.save()
            
            center = self.start if i == 0 else self.end
            
            # Calculate the proper radius for the highlight
            outer_radius = self.width / 2 + self.stroke_width + 4
            inner_radius = self.width / 2 + 6
            
            # Create a full circle path for the outer circle
            outer_circle = QPainterPath()
            outer_circle.addEllipse(center, outer_radius, outer_radius)
            
            # Create a path for the inner circle
            inner_circle = QPainterPath()
            inner_circle.addEllipse(center, inner_radius, inner_radius)
            
            # Create a ring path by subtracting the inner circle from the outer circle
            ring_path = outer_circle.subtracted(inner_circle)
            
            # Get the tangent angle at the connection point
            tangent = self.calculate_cubic_tangent(0.0 if i == 0 else 1.0)
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
            stroke_pen = QPen(QColor(255, 0, 0, 255), self.stroke_width)
            stroke_pen.setJoinStyle(Qt.MiterJoin)
            stroke_pen.setCapStyle(Qt.FlatCap)
            painter.setPen(stroke_pen)
            # --- CHANGE: Use NoBrush instead of solid red fill ---
            # painter.setBrush(QColor(255, 0, 0, 255))  # Fill with red color
            painter.setBrush(Qt.NoBrush)
            # --- END CHANGE ---
            painter.drawPath(c_shape_path)
            
            # Restore painter state
            painter.restore()
        temp_painter.end()
        painter.restore()

        # Control points are now only drawn by StrandDrawingCanvas.draw_control_points
        # This code is removed to avoid duplicate drawing
        """
        # Draw control points if needed
        if hasattr(self, 'canvas') and self.canvas and self.canvas.show_control_points:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw control point lines
            control_line_pen = QPen(QColor('green'), 1, Qt.DashLine)
            painter.setPen(control_line_pen)
            painter.drawLine(self.start, self.control_point1)
            painter.drawLine(self.end, self.control_point2)
            
            # Draw control points
            control_pen = QPen(QColor('green'), 2)
            painter.setPen(control_pen)
            painter.setBrush(QBrush(QColor('green')))
            painter.drawEllipse(self.control_point1, 4, 4)
            painter.drawEllipse(self.control_point2, 4, 4)
            
            painter.restore()
        """

    def get_shadow_path(self):
        """Get the path with extensions for shadow rendering, extending 10px beyond start/end."""
        path = QPainterPath()

        # Check if this is an AttachedStrand with a transparent start circle
        is_attached_transparent_start = False
        # Use class name check for robustness as AttachedStrand is defined later
        if self.__class__.__name__ == 'AttachedStrand':
            # AttachedStrand always has a start circle (has_circles[0] is True)
            # Check transparency using the circle_stroke_color property
            # Add a check for None before accessing alpha()
            circle_color = self.circle_stroke_color
            if circle_color and circle_color.alpha() == 0:
                is_attached_transparent_start = True
                logging.info(f"AttachedStrand {self.layer_name}: Transparent start circle detected, removing shadow extension.")

        if is_attached_transparent_start:
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
                    extended_start = QPointF(self.start.x() - 10, self.start.y()) # Default horizontal
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
                         extended_start = QPointF(self.start.x() - 10, self.start.y()) # Default horizontal
                else:
                    # If start and end are the same, use a default horizontal direction
                    extended_start = QPointF(self.start.x() - 10, self.start.y())

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
                extended_end = QPointF(self.end.x() + 10, self.end.y())
            
        # Create the path with the extended points
        path.moveTo(extended_start)
        path.lineTo(self.start)

        # Only use the third control point if:
        # 1. The feature is enabled AND
        # 2. The control_point_center has been manually positioned
        if (hasattr(self, 'canvas') and self.canvas and 
            hasattr(self.canvas, 'enable_third_control_point') and 
            self.canvas.enable_third_control_point and
            hasattr(self, 'control_point_center_locked') and 
            self.control_point_center_locked):
            
            # Create a smooth spline incorporating all control points
            # We'll use a sequence of cubic Bézier segments with proper tangent continuity
            
            # Extract the key points we're working with
            p0 = self.start
            p1 = self.control_point1
            p2 = self.control_point_center
            p3 = self.control_point2
            p4 = self.end
            
            # Calculate the tangent at start point (pointing toward control_point1)
            start_tangent = QPointF(p1.x() - p0.x(), p1.y() - p0.y())
            
            # Calculate the tangent at center (average of incoming and outgoing)
            in_tangent = QPointF(p2.x() - p1.x(), p2.y() - p1.y())
            out_tangent = QPointF(p3.x() - p2.x(), p3.y() - p2.y())
            
            # Normalize tangents for better control
            def normalize_vector(v):
                length = math.sqrt(v.x() * v.x() + v.y() * v.y())
                if length < 0.001:  # Avoid division by zero
                    return QPointF(0, 0)
                # Preserve vector magnitude better for small movements
                return QPointF(v.x() / length, v.y() / length)
            
            def distance_vector(v):
                return (math.sqrt(v.x() * v.x() + v.y() * v.y()))/(46*6)
            
            start_tangent_normalized = normalize_vector(start_tangent)
            in_tangent_normalized = normalize_vector(in_tangent)
            out_tangent_normalized = normalize_vector(out_tangent)
            
            # Calculate center tangent as weighted average instead of simple average
            # This makes the curve more responsive to small movements
            center_tangent = QPointF(
                0.5 * in_tangent_normalized.x() + 0.5 * out_tangent_normalized.x(), 
                0.5 * in_tangent_normalized.y() + 0.5 * out_tangent_normalized.y()
            )
            center_tangent_normalized = normalize_vector(center_tangent)
            
            # Calculate end tangent
            end_tangent = QPointF(p4.x() - p3.x(), p4.y() - p3.y())
            end_tangent_normalized = normalize_vector(end_tangent)
            
            # Simple distance calculation based on direct distances between points
            dist_p0_p1 = math.sqrt((p1.x() - p0.x())**2 + (p1.y() - p0.y())**2)
            dist_p1_p2 = math.sqrt((p2.x() - p1.x())**2 + (p2.y() - p1.y())**2)
            dist_p2_p3 = math.sqrt((p3.x() - p2.x())**2 + (p3.y() - p2.y())**2)
            dist_p3_p4 = math.sqrt((p4.x() - p3.x())**2 + (p4.y() - p3.y())**2)

            # Fixed fraction for influence
            fraction = 1.0 / 3.0 # Experiment with this value (e.g., 0.5, 0.4)

            # Calculate intermediate control points, incorporating p1 and p3 influence
            # Ensure tangents are non-zero before using them
            cp1 = p0 + start_tangent_normalized * (dist_p0_p1 * fraction) if start_tangent_normalized.manhattanLength() > 1e-6 else p1
            cp2 = p2 - center_tangent_normalized * (dist_p1_p2 * fraction) if center_tangent_normalized.manhattanLength() > 1e-6 else p1

            cp3 = p2 + center_tangent_normalized * (dist_p2_p3 * fraction) if center_tangent_normalized.manhattanLength() > 1e-6 else p3
            cp4 = p4 - end_tangent_normalized * (dist_p3_p4 * fraction) if end_tangent_normalized.manhattanLength() > 1e-6 else p3
            
            # First segment: start to center
            path.cubicTo(cp1, cp2, p2)
            
            # Second segment: center to end
            path.cubicTo(cp3, cp4, p4)
        else:
            # Standard cubic Bezier curve when third control point is disabled or not manually positioned
            path.cubicTo(self.control_point1, self.control_point2, self.end)
        
        # Add a line to the extended end point
        path.lineTo(extended_end)
            
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
            # We'll use a sequence of cubic Bézier segments with proper tangent continuity
            
            # Create control points that ensure C1 continuity (continuous first derivative)
            
            # Extract the key points we're working with
            p0 = self.start
            p1 = self.control_point1
            p2 = self.control_point_center
            p3 = self.control_point2
            p4 = self.end
            
            # Calculate the tangent at start point (pointing toward control_point1)
            start_tangent = QPointF(p1.x() - p0.x(), p1.y() - p0.y())
            
            # Calculate the tangent at center (average of incoming and outgoing)
            in_tangent = QPointF(p2.x() - p1.x(), p2.y() - p1.y())
            out_tangent = QPointF(p3.x() - p2.x(), p3.y() - p2.y())
            
            # Normalize tangents for better control
            def normalize_vector(v):
                length = math.sqrt(v.x() * v.x() + v.y() * v.y())
                if length < 0.001:  # Avoid division by zero
                    return QPointF(0, 0)
                # Preserve vector magnitude better for small movements
                return QPointF(v.x() / length, v.y() / length)
            def distance_vector(v):
                return (math.sqrt(v.x() * v.x() + v.y() * v.y()))/(46*6)
            start_tangent_normalized = normalize_vector(start_tangent)
            in_tangent_normalized = normalize_vector(in_tangent)
            out_tangent_normalized = normalize_vector(out_tangent)
            
            # Calculate center tangent as weighted average instead of simple average
            # This makes the curve more responsive to small movements
            center_tangent = QPointF(
                0.5 * in_tangent_normalized.x() + 0.5 * out_tangent_normalized.x(), 
                0.5 * in_tangent_normalized.y() + 0.5 * out_tangent_normalized.y()
            )
            center_tangent_normalized = normalize_vector(center_tangent)
            
            # Calculate end tangent
            end_tangent = QPointF(p4.x() - p3.x(), p4.y() - p3.y())
            end_tangent_normalized = normalize_vector(end_tangent)
            
            # Simple distance calculation based on direct distances between points
            dist_p0_p1 = math.sqrt((p1.x() - p0.x())**2 + (p1.y() - p0.y())**2)
            dist_p1_p2 = math.sqrt((p2.x() - p1.x())**2 + (p2.y() - p1.y())**2)
            dist_p2_p3 = math.sqrt((p3.x() - p2.x())**2 + (p3.y() - p2.y())**2)
            dist_p3_p4 = math.sqrt((p4.x() - p3.x())**2 + (p4.y() - p3.y())**2)

            # Fixed fraction for influence
            fraction = 1.0 / 3.0 # Experiment with this value (e.g., 0.5, 0.4)

            # Calculate intermediate control points, incorporating p1 and p3 influence
            # Ensure tangents are non-zero before using them
            cp1 = p0 + start_tangent_normalized * (dist_p0_p1 * fraction) if start_tangent_normalized.manhattanLength() > 1e-6 else p1
            cp2 = p2 - center_tangent_normalized * (dist_p1_p2 * fraction) if center_tangent_normalized.manhattanLength() > 1e-6 else p1

            cp3 = p2 + center_tangent_normalized * (dist_p2_p3 * fraction) if center_tangent_normalized.manhattanLength() > 1e-6 else p3
            cp4 = p4 - end_tangent_normalized * (dist_p3_p4 * fraction) if end_tangent_normalized.manhattanLength() > 1e-6 else p3
            
            # First segment: start to center
            path.cubicTo(cp1, cp2, p2)
            
            # Second segment: center to end
            path.cubicTo(cp3, cp4, p4)
        else:
            # Standard cubic Bezier curve when third control point is disabled or not manually positioned
            path.cubicTo(self.control_point1, self.control_point2, self.end)
        
        return path
    def update_angle_length_from_geometry(self):
        """Update the angle and length of the strand based on current start and end points."""
        delta_x = self.end.x() - self.start.x()
        delta_y = self.end.y() - self.start.y()
        self.length = math.hypot(delta_x, delta_y)
        self.angle = math.degrees(math.atan2(delta_y, delta_x))

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
        Same idea, but for AttachedStrand.
        """
        if reset_control_points:
            self.update_control_points_from_geometry()
        self.update_shape()

class MaskedStrand(Strand):
    """
    Represents a strand that is a result of masking two other strands, without control points.
    """
    def __init__(self, first_selected_strand, second_selected_strand, set_number=None):
        # Initialize without control points
        self.first_selected_strand = first_selected_strand
        self.second_selected_strand = second_selected_strand
        self._attached_strands = []
        self._has_circles = [False, False]
        self.is_selected = False
        self.custom_mask_path = None
        self.deletion_rectangles = []
        self.base_center_point = None
        self.edited_center_point = None
        # Inherit shadow color from first selected strand if available
        self.shadow_color = first_selected_strand.shadow_color if first_selected_strand else QColor(0, 0, 0, 150)
        if first_selected_strand and second_selected_strand:
            super().__init__(
                first_selected_strand.start,
                first_selected_strand.end,
                first_selected_strand.width,
                color=first_selected_strand.color,
                stroke_color=first_selected_strand.stroke_color,
                stroke_width=first_selected_strand.stroke_width,
                set_number=set_number if set_number is not None else int(f"{first_selected_strand.set_number}{second_selected_strand.set_number}"),
                layer_name=f"{first_selected_strand.layer_name}_{second_selected_strand.layer_name}"
            )
            # Override control points to None
            self.control_point1 = None
            self.control_point2 = None
            
            # Calculate initial center point
            self.calculate_center_point()
            
            # Log initialization with safe center point handling
            if self.edited_center_point:
                logging.info(f"Initialized masked strand {self.layer_name} with center point: {self.edited_center_point.x():.2f}, {self.edited_center_point.y():.2f}")
            else:
                logging.info(f"Initialized masked strand {self.layer_name} without overlap (no center point)")
        else:
            super().__init__(QPointF(0, 0), QPointF(1, 1), 1)
            self.set_number = set_number
            self.layer_name = ""
            self.control_point1 = None
            self.control_point2 = None

    @property
    def attached_strands(self):
        """Get only the strands directly attached to this masked strand."""
        # Only return the strands directly attached to this masked strand
        # NOT the attached strands of the component strands
        return self._attached_strands.copy()

    @attached_strands.setter
    def attached_strands(self, value):
        self._attached_strands = value

    @property
    def has_circles(self):
        """Get the circle status from both selected strands."""
        return [False, False]


    @has_circles.setter
    def has_circles(self, value):
        self._has_circles = [False, False]
    def update_shape(self):
 
        pass
    def get_path(self):
        """Get the path representing the masked strand as a straight line."""
        path = QPainterPath()
        path.moveTo(self.start)
        path.lineTo(self.end)
        return path

    def set_custom_mask(self, mask_path):
        """Set a custom mask path for this masked strand."""
        self.custom_mask_path = mask_path
        # Recalculate center point when mask changes
        self.calculate_center_point()
        
        # Add null check before accessing edited_center_point
        if self.edited_center_point:
            logging.info(f"Updated center point after custom mask set for {self.layer_name}: {self.edited_center_point.x():.2f}, {self.edited_center_point.y():.2f}")
        else:
            logging.warning(f"No valid center point calculated for {self.layer_name} after setting custom mask")
            
        # Save the current state of deletion rectangles
        if hasattr(self, 'deletion_rectangles'):
            logging.info(f"Saved {len(self.deletion_rectangles)} deletion rectangles for masked strand {self.layer_name}")

    def reset_mask(self):
        """Reset to the default intersection mask."""
        self.custom_mask_path = None
        self.deletion_rectangles = []  # Clear the deletion rectangles
        logging.info(f"Reset mask and cleared deletion rectangles for masked strand {self.layer_name}")
    def get_masked_shadow_path(self):
        """
        Get the path representing the shadow of the masked area.
        This is used for visual effects like highlighting the intersection.
        Always calculates a fresh shadow path without caching.
        """
        if not self.first_selected_strand or not self.second_selected_strand:
            return QPainterPath()

        # Get the base paths for both strands - always fresh calculation
        shadow_width_offset = 10  # Use consistent shadow size

        # Get fresh paths from both strands
        path1 = self.first_selected_strand.get_path()
        shadow_stroker = QPainterPathStroker()
        shadow_stroker.setWidth(self.first_selected_strand.width + self.first_selected_strand.stroke_width * 2 + shadow_width_offset)
        shadow_stroker.setJoinStyle(Qt.MiterJoin)
        shadow_stroker.setCapStyle(Qt.RoundCap)  # Use RoundCap for smoother shadows
        shadow_path1 = shadow_stroker.createStroke(path1)

        path2 = self.second_selected_strand.get_path()
        shadow_stroker = QPainterPathStroker()
        shadow_stroker.setWidth(self.second_selected_strand.width + self.second_selected_strand.stroke_width * 2)
        shadow_stroker.setJoinStyle(Qt.MiterJoin)
        shadow_stroker.setCapStyle(Qt.RoundCap)  # Use RoundCap for smoother shadows
        shadow_path2 = shadow_stroker.createStroke(path2)

        # Calculate fresh intersection
        intersection_path = shadow_path1.intersected(shadow_path2)
        path_shadow = intersection_path

        # Apply any deletion rectangles to the shadow path
        if hasattr(self, 'deletion_rectangles') and self.deletion_rectangles:
            for rect in self.deletion_rectangles:
                # Use corner-based data for precise deletion
                top_left = QPointF(*rect['top_left'])
                top_right = QPointF(*rect['top_right'])
                bottom_left = QPointF(*rect['bottom_left'])
                bottom_right = QPointF(*rect['bottom_right'])
                deletion_path = QPainterPath()

                deletion_path.moveTo(top_left)
                deletion_path.lineTo(top_right)
                deletion_path.lineTo(bottom_right)
                deletion_path.lineTo(bottom_left)
                deletion_path.closeSubpath()

                path_shadow = path_shadow.subtracted(deletion_path)

        # Log shadow path information for debugging
        logging.info(f"Created fresh masked shadow path: empty={path_shadow.isEmpty()}, bounds={path_shadow.boundingRect()}")
        return path_shadow
        
    def get_mask_path(self):
        """
        Get the path representing the masked area.
        This includes base intersection and also subtracts any deletion rectangles.
        """
        if not self.first_selected_strand or not self.second_selected_strand:
            return QPainterPath()

        # Get the base paths for both strands
        path1 = self.get_stroked_path_for_strand(self.first_selected_strand)
        path2 = self.get_stroked_path_for_strand(self.second_selected_strand)
        
        # Create the final mask by intersecting the path1 shadow with path2
        result_path = path1.intersected(path2)

        # If we have a custom mask path, use that instead
        if self.custom_mask_path is not None:
            result_path = self.custom_mask_path

        # Apply any saved deletion rectangles
        if hasattr(self, 'deletion_rectangles'):
            for rect in self.deletion_rectangles:
                # NEW code using corner-based data:
                top_left = QPointF(*rect['top_left'])
                top_right = QPointF(*rect['top_right'])
                bottom_left = QPointF(*rect['bottom_left'])
                bottom_right = QPointF(*rect['bottom_right'])
                # Create a polygonal path from the four corners
                deletion_path = QPainterPath()

                deletion_path.moveTo(top_left)
                deletion_path.lineTo(top_right)
                deletion_path.lineTo(bottom_right)
                deletion_path.lineTo(bottom_left)
                deletion_path.closeSubpath()

                result_path = result_path.subtracted(deletion_path)

        return result_path

    def get_stroked_path_for_strand(self, strand):
        """Helper method to get the stroked path for a strand."""
        path = strand.get_path()
        stroker = QPainterPathStroker()
        stroker.setWidth(strand.width + strand.stroke_width * 2 + 2)
        stroker.setJoinStyle(Qt.MiterJoin)
        stroker.setCapStyle(Qt.FlatCap)
        return stroker.createStroke(path)

    def draw(self, painter):
        """Draw the masked strand and apply corner-based deletion rectangles."""
        logging.info(f"Drawing MaskedStrand - Has deletion rectangles: {hasattr(self, 'deletion_rectangles')}")
        if hasattr(self, 'deletion_rectangles'):
            logging.info(f"Current deletion rectangles: {self.deletion_rectangles}")

        if not self.first_selected_strand and not self.second_selected_strand:
            return

        painter.save()
        # Enable high-quality antialiasing for the entire drawing process
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

        # Create temporary image for masking with premultiplied alpha for better blending
        temp_image = QImage(
            painter.device().size(),
            QImage.Format_ARGB32_Premultiplied
        )
        temp_image.fill(Qt.transparent)
        temp_painter = QPainter(temp_image)
        # Enable high-quality antialiasing for the temporary painter too
        temp_painter.setRenderHint(QPainter.Antialiasing, True)
        temp_painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        temp_painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        
        # do not Draw the strands FIRST

            
        try:
            # Try different import approaches for robustness
            try:
                from shader_utils import draw_mask_strand_shadow
            except ImportError:
                from src.shader_utils import draw_mask_strand_shadow
            
            # Only draw shadows if shadow rendering is enabled in the canvas
            if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'shadow_enabled') and self.canvas.shadow_enabled:
                logging.info(f"Drawing shadow for MaskedStrand {self.layer_name}")
                
                # Get the shadow color directly from the canvas if available
                shadow_color = None
                if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'default_shadow_color'):
                    shadow_color = self.canvas.default_shadow_color
                    # Also update the strand's shadow color for future reference
                    self.shadow_color = QColor(shadow_color)
                
                # Always get fresh paths for both strands to ensure consistent refresh
                strand1_path = self.get_stroked_path_for_strand(self.first_selected_strand)
                strand2_path = self.get_stroked_path_for_strand(self.second_selected_strand)
                combined_strand_area = QPainterPath(strand1_path)
                combined_strand_area.addPath(strand2_path)
                
                # Always calculate fresh shadow paths - no caching at all
                # IMPORTANT: Get a new shadow path directly without reusing any cached values
                masked_shadow_path = self.get_masked_shadow_path()
                
                if masked_shadow_path and not masked_shadow_path.isEmpty():
                    # Limit shadow only to areas where strands exist
                    limited_shadow_path = masked_shadow_path.intersected(combined_strand_area)
                    
                    # Draw shadow on top of strands with proper composition mode
                    temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                    draw_mask_strand_shadow(temp_painter, limited_shadow_path, self, shadow_color)

 
        except Exception as e:
            logging.error(f"Error applying masked strand shadow: {e}")
            # Attempt to refresh even if there was an error
            try:
                self.force_shadow_refresh()
            except Exception as refresh_error:
                logging.error(f"Error during error recovery refresh: {refresh_error}")

        # Get the mask path - use edited mask if it exists, otherwise use base mask
        if hasattr(self, 'deletion_rectangles') and self.deletion_rectangles:
            logging.info("Using edited mask with deletion rectangles")
            
            # Get the base intersection mask
            path1 = self.get_stroked_path_for_strand(self.first_selected_strand)
            path2 = self.get_stroked_path_for_strand(self.second_selected_strand)
            mask_path = path1.intersected(path2)
            
            # Calculate new center point and update if needed
            new_center = self._calculate_center_from_path(mask_path)
            if new_center and self.base_center_point and (
                abs(new_center.x() - self.base_center_point.x()) > 0.01 or 
                abs(new_center.y() - self.base_center_point.y()) > 0.01
            ):
                logging.info(f"Detected center point movement from ({self.base_center_point.x():.2f}, {self.base_center_point.y():.2f}) to ({new_center.x():.2f}, {new_center.y():.2f})")
                self.update(new_center)
            
            # Apply deletion rectangles
            for rect in self.deletion_rectangles:
                # Build a bounding rect from corner data.
                top_left = QPointF(*rect['top_left'])
                top_right = QPointF(*rect['top_right'])
                bottom_left = QPointF(*rect['bottom_left'])
                bottom_right = QPointF(*rect['bottom_right'])
                deletion_path = QPainterPath()

                deletion_path.moveTo(top_left)
                deletion_path.lineTo(top_right)
                deletion_path.lineTo(bottom_right)
                deletion_path.lineTo(bottom_left)
                deletion_path.closeSubpath()

                mask_path = mask_path.subtracted(deletion_path)
                logging.info(
                    f"✂️ Applied corner-based deletion rect with corners: "
                    f"{rect['top_left']} {rect['top_right']} {rect['bottom_left']} {rect['bottom_right']}"
                )
            
            # Use the temp_painter to clip out the parts outside our mask
            temp_painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            temp_painter.setPen(Qt.NoPen)
            temp_painter.setBrush(Qt.black)
            temp_painter.drawPath(mask_path)
        else:
            # Get the base intersection mask
            logging.info("Using default intersection mask")
            path1 = self.get_stroked_path_for_strand(self.first_selected_strand)
            path2 = self.get_stroked_path_for_strand(self.second_selected_strand)
            mask_path = path1.intersected(path2)
            
            # Use the temp_painter to clip out the parts outside our mask
            temp_painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            temp_painter.setPen(Qt.NoPen)
            temp_painter.setBrush(Qt.black)
            temp_painter.drawPath(mask_path)

        # End painting on the temporary image
        temp_painter.end()
        
        # Make sure we're using the correct composition mode to transfer the temp image
        # to the main painter - this is critical for shadow visibility
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        
        # Draw the temp image onto the main painter
        painter.drawImage(0, 0, temp_image)
        
        # FINAL LAYER: Only draw the first strand on top if it should be above according to layer order
        try:
            if hasattr(self, 'first_selected_strand') and self.first_selected_strand:


                    # Get the base paths for both strands
                    # Use moderate shadow size for realistic effect
                    shadow_width_offset = 11  # Adjusted from 20 for more realistic effect

                    path1 = self.first_selected_strand.get_path()  # Get actual path instead of the strand object
                    shadow_stroker = QPainterPathStroker()
                    shadow_stroker.setWidth(self.first_selected_strand.width + self.first_selected_strand.stroke_width * 2 + shadow_width_offset)
                    shadow_stroker.setJoinStyle(Qt.MiterJoin)
                    shadow_stroker.setCapStyle(Qt.RoundCap)  # Use RoundCap for smoother edges
                    shadow_path1 = shadow_stroker.createStroke(path1)
                    
                    # Rest of the shadow drawing code remains the same
                    path2 = self.second_selected_strand.get_path()
                    shadow_stroker = QPainterPathStroker()
                    shadow_stroker.setWidth(self.second_selected_strand.width + self.second_selected_strand.stroke_width * 2 + shadow_width_offset)
                    shadow_stroker.setJoinStyle(Qt.MiterJoin)
                    shadow_stroker.setCapStyle(Qt.RoundCap)
                    shadow_path2 = shadow_stroker.createStroke(path2)

                    # First get the basic intersection of the two strands
                    intersection_path = shadow_path1.intersected(shadow_path2)
                    
                    # Create the shadow path by stroking the intersection
                    path_shadow = intersection_path
                    
                    # Log information about the shadow path
                    logging.info(f"Created masked shadow path: empty={path_shadow.isEmpty()}, bounds={path_shadow.boundingRect()}")
                    
                    # Apply any saved deletion rectangles to the shadow path
                    if hasattr(self, 'deletion_rectangles') and self.deletion_rectangles:
                        for rect in self.deletion_rectangles:
                            # Use corner-based data:
                            top_left = QPointF(*rect['top_left'])
                            top_right = QPointF(*rect['top_right'])
                            bottom_left = QPointF(*rect['bottom_left'])
                            bottom_right = QPointF(*rect['bottom_right'])
                            # Create a polygonal path from the four corners
                            deletion_path = QPainterPath()

                            deletion_path.moveTo(top_left)
                            deletion_path.lineTo(top_right)
                            deletion_path.lineTo(bottom_right)
                            deletion_path.lineTo(bottom_left)
                            deletion_path.closeSubpath()

                            path_shadow = path_shadow.subtracted(deletion_path)
                    
                    # Log information about the final shadow path
                    logging.info(f"Final shadow path for clipping: empty={path_shadow.isEmpty()}, bounds={path_shadow.boundingRect()}")
                    
                    # COMPLETELY NEW APPROACH: Use multiple buffers with soft-edge feathering to eliminate all aliasing
                    
                    # Create a dedicated high-quality buffer for the final strand layer
                    final_buffer = QImage(
                        painter.device().size(),
                        QImage.Format_ARGB32_Premultiplied
                    )
                    final_buffer.fill(Qt.transparent)
                    final_painter = QPainter(final_buffer)
                    
                    # Enable maximum quality rendering
                    final_painter.setRenderHint(QPainter.Antialiasing, True)
                    final_painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
                    final_painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
                    
                    if not path_shadow.isEmpty():
                            # Get the base paths for both strands
                        # Use moderate shadow size for realistic effect
                        shadow_width_offset = 20  # Adjusted from 20 for more realistic effect

                        path1 = self.first_selected_strand.get_path()  # Get actual path instead of the strand object
                        shadow_stroker = QPainterPathStroker()
                        shadow_stroker.setWidth(self.first_selected_strand.width + self.first_selected_strand.stroke_width * 2 + shadow_width_offset)
                        shadow_stroker.setJoinStyle(Qt.MiterJoin)
                        shadow_stroker.setCapStyle(Qt.RoundCap)  # Use RoundCap for smoother edges
                        shadow_path1 = shadow_stroker.createStroke(path1)
                        
                        # Rest of the shadow drawing code remains the same
                        path2 = self.second_selected_strand.get_path()
                        shadow_stroker = QPainterPathStroker()
                        shadow_stroker.setWidth(self.second_selected_strand.width + self.second_selected_strand.stroke_width * 2 + shadow_width_offset)
                        shadow_stroker.setJoinStyle(Qt.MiterJoin)
                        shadow_stroker.setCapStyle(Qt.RoundCap)
                        shadow_path2 = shadow_stroker.createStroke(path2)

                        # First get the basic intersection of the two strands
                        intersection_path = shadow_path1.intersected(shadow_path2)
                        
                        # Create the shadow path by stroking the intersection
                        path_shadow = intersection_path
                        
                        # Log information about the shadow path
                        logging.info(f"Created masked shadow path: empty={path_shadow.isEmpty()}, bounds={path_shadow.boundingRect()}")
                        
                        # Apply any saved deletion rectangles to the shadow path
                        if hasattr(self, 'deletion_rectangles') and self.deletion_rectangles:
                            for rect in self.deletion_rectangles:
                                # Use corner-based data:
                                top_left = QPointF(*rect['top_left'])
                                top_right = QPointF(*rect['top_right'])
                                bottom_left = QPointF(*rect['bottom_left'])
                                bottom_right = QPointF(*rect['bottom_right'])
                                # Create a polygonal path from the four corners
                                deletion_path = QPainterPath()

                                deletion_path.moveTo(top_left)
                                deletion_path.lineTo(top_right)
                                deletion_path.lineTo(bottom_right)
                                deletion_path.lineTo(bottom_left)
                                deletion_path.closeSubpath()

                                path_shadow = path_shadow.subtracted(deletion_path)
                        # Only draw the intersection area, not the entire first strand
                        # Set clip path to the intersection area first
                        
                        # Create a more aggressive inset path to eliminate edge artifacts
                        shadow_inset_stroker = QPainterPathStroker()
                        shadow_inset_stroker.setWidth(10)  # Increased inset value
                        shadow_inset_path = path_shadow.subtracted(shadow_inset_stroker.createStroke(path_shadow))
                        
                        # Create a separate buffer for the strand drawing to avoid artifacts
                        strand_buffer = QImage(
                            painter.device().size(),
                            QImage.Format_ARGB32_Premultiplied
                        )
                        strand_buffer.fill(Qt.transparent)
                        
                        # Draw strand to buffer first
                        strand_painter = QPainter(strand_buffer)
                        strand_painter.setRenderHint(QPainter.Antialiasing, True)
                        strand_painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
                        strand_painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
                        
                        # Completely disable any stroke drawing
                        strand_painter.setPen(Qt.NoPen)
                        
                        # Draw the strand without stroke
                        self.first_selected_strand.draw(strand_painter)
                        strand_painter.end()
                        
                        # Now draw the clipped strand to the final painter
                        final_painter.save()
                        final_painter.setClipPath(shadow_inset_path)
                        final_painter.setCompositionMode(QPainter.CompositionMode_Source)
                        final_painter.drawImage(0, 0, strand_buffer)
                        final_painter.restore()
                    else:
                        # When mask is empty, don't draw the first strand at all
                        pass
                    # Create a soft mask buffer for the intersection with feathered edges
                    mask_buffer = QImage(
                        painter.device().size(),
                        QImage.Format_ARGB32_Premultiplied
                    )
                    mask_buffer.fill(Qt.transparent)
                    mask_painter = QPainter(mask_buffer)
                    mask_painter.setRenderHint(QPainter.Antialiasing, True)
                    mask_painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
                    mask_painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
                    

                    
                    # Create a soft feathered mask from the intersection region
                    # Draw the core mask with solid opacity
                    mask_painter.setPen(Qt.NoPen)
                    mask_painter.setBrush(QBrush(Qt.black))
                    mask_painter.drawPath(path_shadow)
                    
                    # Create and draw the feathered edge for smooth transitions
                    feather_width = 4.0  # Use a wider feather for smoother edges
                    feather_stroker = QPainterPathStroker()
                    feather_stroker.setWidth(feather_width)
                    feather_stroker.setJoinStyle(Qt.RoundJoin)
                    feather_stroker.setCapStyle(Qt.RoundCap)
                    feathered_edge = feather_stroker.createStroke(path_shadow)
                    
                    # Draw feathered edge with gradient opacity
                    feather_path = QPainterPath(feathered_edge)
                    feather_path = feather_path.subtracted(path_shadow)
                    if not feather_path.isEmpty():
                        mask_painter.setBrush(QBrush(QColor(0, 0, 0, 128)))  # Half-transparent for feathering
                        mask_painter.drawPath(feather_path)
                    
                    mask_painter.end()
                    
                    # Apply the soft mask to the final buffer
                    final_painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
                    final_painter.drawImage(0, 0, mask_buffer)
                    final_painter.end()
                    

                    # Draw the result with perfect antialiasing to the main painter
                    painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                    painter.drawImage(0, 0, final_buffer)                        
                    # Skip drawing additional shadows for nested masked strands to prevent double-shadowing
                    logging.info(f"Skipping additional shadow for nested masked strand {self.layer_name}")
  
        except Exception as e:
            logging.error(f"Error drawing first strand on top: {str(e)}")
        
        # Debug output
        logging.info(f"Transferred masked strand image to main painter for {self.layer_name}")
        
        # Restore the painter state
        painter.restore()

        # Now handle the highlight or debug drawing
        if self.is_selected:
            logging.info("Drawing selected strand highlights")
            # Draw the mask outline and fill with a semi-transparent red
            highlight_pen = QPen(QColor(255, 0, 0, 128), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(highlight_pen)
            painter.setBrush(QBrush(QColor(255, 0, 0, 128)))

            # Acquire the mask path and set a winding fill rule so the region gets filled.
            mask_path = self.get_mask_path()
            
            # Only draw if the mask path is not empty (strands actually intersect)
            if not mask_path.isEmpty():
                mask_path.setFillRule(Qt.WindingFill)
                painter.drawPath(mask_path)

                # Always recalculate and draw center points based on current masks
                self.calculate_center_point()

                # Always show base center point in blue
                if self.base_center_point:
                    logging.info(f"Drawing base center point at: {self.base_center_point.x():.2f}, {self.base_center_point.y():.2f}")
                    temp_painter = QPainter(painter.device())  # a new painter for the crosshair
                    temp_painter.setCompositionMode(QPainter.CompositionMode_Source)
                    temp_painter.setPen(QPen(QColor('transparent'), 0))
                    temp_painter.setBrush(QBrush(QColor('transparent')))
                    center_radius = 0
                    temp_painter.drawEllipse(self.base_center_point, center_radius, center_radius)

                    # Draw blue crosshair
                    temp_painter.setPen(QPen(QColor('transparent'), 0))
                    crosshair_size = 0
                    temp_painter.drawLine(
                        QPointF(self.base_center_point.x() - crosshair_size, self.base_center_point.y()),
                        QPointF(self.base_center_point.x() + crosshair_size, self.base_center_point.y())
                    )
                    temp_painter.drawLine(
                        QPointF(self.base_center_point.x(), self.base_center_point.y() - crosshair_size),
                        QPointF(self.base_center_point.x(), self.base_center_point.y() + crosshair_size)
                    )
                    temp_painter.end()

                # Only show edited center point if there are deletion rectangles
                if self.edited_center_point and hasattr(self, 'deletion_rectangles') and self.deletion_rectangles:
                    logging.info(f"Drawing edited center point at: {self.edited_center_point.x():.2f}, {self.edited_center_point.y():.2f}")
                    temp_painter = QPainter(painter.device())  # a new painter for the crosshair
                    temp_painter.setCompositionMode(QPainter.CompositionMode_Source)
                    temp_painter.setPen(QPen(QColor('transparent'), 0))
                    temp_painter.setBrush(QBrush(QColor('transparent')))
                    center_radius = 0
                    temp_painter.drawEllipse(self.edited_center_point, center_radius, center_radius)

                    # Draw red crosshair
                    temp_painter.setPen(QPen(QColor('transparent'), 0))
                    crosshair_size = 0
                    temp_painter.drawLine(
                        QPointF(self.edited_center_point.x() - crosshair_size, self.edited_center_point.y()),
                        QPointF(self.edited_center_point.x() + crosshair_size, self.edited_center_point.y())
                    )
                    temp_painter.drawLine(
                        QPointF(self.edited_center_point.x(), self.edited_center_point.y() - crosshair_size),
                        QPointF(self.edited_center_point.x(), self.edited_center_point.y() + crosshair_size)
                    )
                    temp_painter.end()
            else:
                logging.info("Skipping highlight drawing: no intersection between strands")

        logging.info("Completed drawing masked strand")

    def update(self, new_position):
        """Update deletion rectangles position while maintaining strand positions."""
        # Check if we're using absolute coordinates (from JSON)
        if hasattr(self, 'using_absolute_coords') and self.using_absolute_coords:
            logging.info(f"Using absolute coordinates for {self.layer_name}, skipping transformation")
            return

        if not hasattr(self, 'base_center_point') or not self.base_center_point:
            logging.warning("No base center point set, cannot update")
            # Try to calculate center points if they don't exist
            self.calculate_center_point()
            # If still no base_center_point, we can't proceed
            if not hasattr(self, 'base_center_point') or not self.base_center_point:
                return

        # If no new position is provided, use the current edited_center_point if available
        if not new_position:
            if hasattr(self, 'edited_center_point') and self.edited_center_point:
                new_position = self.edited_center_point
                logging.info(f"Using current edited_center_point as new position")
            else:
                logging.warning("No new position provided and no edited_center_point available")
                return

        # Calculate the movement delta
        delta_x = new_position.x() - self.base_center_point.x()
        delta_y = new_position.y() - self.base_center_point.y()

        # Only proceed if there's actual movement
        if abs(delta_x) > 0.01 or abs(delta_y) > 0.01:
            logging.info(f"➡️ Movement delta: dx={delta_x:.2f}, dy={delta_y:.2f}")

            # Shift each deletion rectangle's corners by (delta_x, delta_y)
            for rect in self.deletion_rectangles:
                top_left = QPointF(*rect['top_left'])
                top_right = QPointF(*rect['top_right'])
                bottom_left = QPointF(*rect['bottom_left'])
                bottom_right = QPointF(*rect['bottom_right'])

                # Update corner positions
                rect['top_left'] = (top_left.x() + delta_x, top_left.y() + delta_y)
                rect['top_right'] = (top_right.x() + delta_x, top_right.y() + delta_y)
                rect['bottom_left'] = (bottom_left.x() + delta_x, bottom_left.y() + delta_y)
                rect['bottom_right'] = (bottom_right.x() + delta_x, bottom_right.y() + delta_y)

            # Update the base_center_point
            self.base_center_point = QPointF(new_position)
            
            # Also update edited_center_point to match
            if hasattr(self, 'edited_center_point'):
                self.edited_center_point = QPointF(new_position)

            # Force a complete shadow and mask update
            self.force_shadow_update()

            # Update the shape of both selected strands
            if hasattr(self, 'first_selected_strand') and self.first_selected_strand:
                if hasattr(self.first_selected_strand, 'update_shape'):
                    self.first_selected_strand.update_shape()
                    if hasattr(self.first_selected_strand, 'update_side_line'):
                        self.first_selected_strand.update_side_line()
            
            if hasattr(self, 'second_selected_strand') and self.second_selected_strand:
                if hasattr(self.second_selected_strand, 'update_shape'):
                    self.second_selected_strand.update_shape()
                    if hasattr(self.second_selected_strand, 'update_side_line'):
                        self.second_selected_strand.update_side_line()

            # Update canvas if available
            if hasattr(self, 'canvas') and self.canvas:
                self.canvas.update()

        else:
            logging.info("ℹ️ No movement detected, skipping updates")

        logging.info(f"=== Completed MaskedStrand update for {self.layer_name} ===\n")
        self.force_shadow_update()
    
    # Add this as a separate method
    def force_shadow_update(self):
        """Force recalculation of all shadow paths and cached data."""
        # Clear all cached paths and positions
        cached_attrs = [
            '_shadow_path', '_last_shadow_positions', '_cached_path', '_cached_mask',
            '_stroke_path', '_fill_path', '_mask_path', '_base_mask_path',
            'custom_mask_path', '_highlight_path', '_selection_path'
        ]
        
        # Clear all possible caches
        for attr in cached_attrs:
            if hasattr(self, attr):
                delattr(self, attr)
                logging.info(f"Cleared cache for {attr}")
        
        # Update all related shapes and components
        if hasattr(self.first_selected_strand, 'update_shape'):
            self.first_selected_strand.update_shape()
            if hasattr(self.first_selected_strand, 'update_side_line'):
                self.first_selected_strand.update_side_line()
        
        if hasattr(self.second_selected_strand, 'update_shape'):
            self.second_selected_strand.update_shape()
            if hasattr(self.second_selected_strand, 'update_side_line'):
                self.second_selected_strand.update_side_line()
        
        # Update the mask path
        self.update_mask_path()
        
        # Force recalculation of center points
        self.calculate_center_point()
        
        # Update canvas if available
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.update()
            
        logging.info(f"Forced complete shadow update for masked strand {self.layer_name}")
    
    # Add a more lightweight refresh method that doesn't recalculate everything
    def force_shadow_refresh(self):
        """Refresh the strand with minimal recalculation - for consistent UI updates."""
        # Update the shapes of component strands
        if hasattr(self.first_selected_strand, 'update_shape'):
            self.first_selected_strand.update_shape()
        
        if hasattr(self.second_selected_strand, 'update_shape'):
            self.second_selected_strand.update_shape()
        
        # Update canvas if available
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.update()
            
        logging.info(f"Refreshed masked strand {self.layer_name} for consistent UI updates")

    def add_deletion_rectangle(self, rect):
        """Initialize or add a new deletion rectangle with proper offset tracking."""
        if not hasattr(self, 'deletion_rectangles'):
            self.deletion_rectangles = []
            logging.info("📦 Initializing deletion rectangles array")
        
        # Ensure base center point exists
        if not hasattr(self, 'base_center_point') or self.base_center_point is None:
            self.calculate_center_point()
            if self.base_center_point:
                logging.info(f"📍 Calculated initial base center point: ({self.base_center_point.x():.2f}, {self.base_center_point.y():.2f})")
            else:
                logging.error("❌ Failed to calculate base center point")
                return
        
        # Deep copy the rectangle to avoid reference issues
        new_rect = rect.copy()
        
        # Calculate and store offsets from base center
        new_rect['offset_x'] = rect['x'] - self.base_center_point.x()
        new_rect['offset_y'] = rect['y'] - self.base_center_point.y()
        
        # Store original position
        new_rect['x'] = rect['x']
        new_rect['y'] = rect['y']
        new_rect['width'] = rect['width']
        new_rect['height'] = rect['height']
        
        logging.info(f"📐 New rectangle position: ({new_rect['x']:.2f}, {new_rect['y']:.2f})")
        logging.info(f"📏 Calculated offsets from base center: dx={new_rect['offset_x']:.2f}, dy={new_rect['offset_y']:.2f}")
        
        self.deletion_rectangles.append(new_rect)
        
        # Update the mask path with the new rectangle
        self.update_mask_path()
        
        logging.info(f"✅ Added deletion rectangle #{len(self.deletion_rectangles)} with dimensions: {new_rect['width']}x{new_rect['height']}")
        logging.info(f"📊 Total deletion rectangles: {len(self.deletion_rectangles)}")

    def update_mask_path(self):
        """Update the custom mask path based on current strand and rectangle positions."""
        # Check if we should skip center recalculation (used during loading)
        skip_recalculation = hasattr(self, 'skip_center_recalculation') and self.skip_center_recalculation
        
        # Check if this strand uses absolute coordinates for deletion rectangles
        using_absolute_coords = hasattr(self, 'using_absolute_coords') and self.using_absolute_coords
        
        if using_absolute_coords:
            logging.info(f"Using absolute coordinates for deletion rectangles in {self.layer_name}, preserving exact JSON positions")
        elif skip_recalculation:
            logging.info(f"Skipping center recalculation for {self.layer_name} to preserve deletion rectangle positions")
        
        # Get fresh paths from both strands
        path1 = self.get_stroked_path_for_strand(self.first_selected_strand)
        path2 = self.get_stroked_path_for_strand(self.second_selected_strand)
        
        # Create the final mask by directly intersecting path1 with path2
        # without applying any shadow stroker to path1
        self.custom_mask_path = path1.intersected(path2)
        
        # Check if the resulting path is empty (strands don't intersect)
        if self.custom_mask_path.isEmpty():
            logging.info(f"No intersection between strands for {self.layer_name}")
            # Even if there's no intersection, we still keep the custom_mask_path
            # (empty) and preserve any deletion rectangles for when they intersect again
        else:
            # Apply deletion rectangles if they exist
            if hasattr(self, 'deletion_rectangles'):
                for rect in self.deletion_rectangles:
                    # Build a bounding rect from corner data
                    top_left = QPointF(*rect['top_left'])
                    top_right = QPointF(*rect['top_right'])
                    bottom_left = QPointF(*rect['bottom_left'])
                    bottom_right = QPointF(*rect['bottom_right'])

                    # Create deletion path using exact corners for precision
                    deletion_path = QPainterPath()

                    min_x = min(top_left.x(), top_right.x(), bottom_left.x(), bottom_right.x())
                    max_x = max(top_left.x(), top_right.x(), bottom_left.x(), bottom_right.x())
                    min_y = min(top_left.y(), top_right.y(), bottom_left.y(), bottom_right.y())
                    max_y = max(top_left.y(), top_right.y(), bottom_left.y(), bottom_right.y())

                    width = max_x - min_x
                    height = max_y - min_y

                    deletion_path = QPainterPath()
                    deletion_path.addRect(QRectF(min_x, min_y, width, height))
                    self.custom_mask_path = self.custom_mask_path.subtracted(deletion_path)
                    logging.info(
                        f"✂️ Applied corner-based deletion rect with corners: "
                        f"{rect['top_left']} {rect['top_right']} {rect['bottom_left']} {rect['bottom_right']}"
                    )
            
            logging.info(f"Updated mask path for {self.layer_name}")
        
        # Clear any cached paths that depend on the mask
        cached_attrs = ['_shadow_path', '_cached_path', '_cached_mask', '_base_mask_path']
        for attr in cached_attrs:
            if hasattr(self, attr):
                delattr(self, attr)
                logging.info(f"Cleared cache for {attr} after mask update")

        # Skip center point recalculation for absolute coordinates
        if using_absolute_coords:
            # Do nothing with center point, keep deletion rectangles exactly as loaded
            logging.info(f"Preserved absolute coordinates for {self.layer_name}")
        # Skip center point recalculation if requested (during loading)
        elif not skip_recalculation:
            # Always update center points after mask path changes
            old_base_center = self.base_center_point if hasattr(self, 'base_center_point') else None
            old_edited_center = self.edited_center_point if hasattr(self, 'edited_center_point') else None
            
            # Calculate new center points
            self.calculate_center_point()
            
            # Log center point changes for debugging
            if hasattr(self, 'base_center_point') and old_base_center:
                dx = self.base_center_point.x() - old_base_center.x() if self.base_center_point else 0
                dy = self.base_center_point.y() - old_base_center.y() if self.base_center_point else 0
                if abs(dx) > 0.01 or abs(dy) > 0.01:
                    logging.info(f"Base center point moved: dx={dx:.2f}, dy={dy:.2f}")
                    
            if hasattr(self, 'edited_center_point') and old_edited_center:
                dx = self.edited_center_point.x() - old_edited_center.x() if self.edited_center_point else 0
                dy = self.edited_center_point.y() - old_edited_center.y() if self.edited_center_point else 0
                if abs(dx) > 0.01 or abs(dy) > 0.01:
                    logging.info(f"Edited center point moved: dx={dx:.2f}, dy={dy:.2f}")
        else:
            # Use control_point_center from JSON if available
            if hasattr(self, 'control_point_center'):
                self.base_center_point = QPointF(self.control_point_center)
                self.edited_center_point = QPointF(self.control_point_center)
                logging.info(f"Using center point from JSON: {self.base_center_point.x():.2f}, {self.base_center_point.y():.2f}")
        
        logging.info(f"Updated mask path for {self.layer_name}")

    def set_color(self, color):
        """Set the color of the masked strand while preserving second strand's color."""
        self.color = color
        # Don't propagate the color change to the second selected strand
        # The second strand should keep its own set's color
        logging.info(f"Set color for masked strand {self.layer_name} to {color.name()}, preserving second strand color")

    def remove_attached_strands(self):
        """Recursively remove all attached strands from both selected strands."""
        self._attached_strands.clear()
        if self.first_selected_strand:
            self.first_selected_strand.remove_attached_strands()
        if self.second_selected_strand:
            self.second_selected_strand.remove_attached_strands()

    def __getattr__(self, name):
        """
        Custom attribute getter to handle certain attributes.
        This is called when an attribute is not found in the normal places.
        """
        if name in ['attached_strands', 'has_circles', 'set_number', 'layer_name']:
            return getattr(self, name)
        if self.first_selected_strand and hasattr(self.first_selected_strand, name):
            return getattr(self.first_selected_strand, name)
        elif self.second_selected_strand and hasattr(self.second_selected_strand, name):
            return getattr(self.second_selected_strand, name)
        else:
            raise AttributeError(f"'MaskedStrand' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        """
        Custom attribute setter to handle specific attributes.
        """
        if name in ['attached_strands', 'has_circles', 'set_number', 'layer_name', '_attached_strands']:
            object.__setattr__(self, name, value)
        else:
            super().__setattr__(name, value)

    def update_control_points_from_geometry(self):
        """Override to do nothing since masked strands don't have control points."""
        pass

    def get_end_selection_path(self):
        """Override to create a simpler selection path for masked strands."""
        end_path = QPainterPath()
        # Use the width of the strand for the selection circle
        radius = self.width / 2
        end_path.addEllipse(self.end, radius, radius)
        return end_path

    def point_at(self, t):
        """Override to return point along straight line instead of bezier curve."""
        return QPointF(
            self.start.x() + t * (self.end.x() - self.start.x()),
            self.start.y() + t * (self.end.y() - self.start.y())
        )


    def update_masked_color(self, set_number, color):
        """Update the color of the masked strand if it involves the given set."""
        # Only update colors for the parts of the mask that match the set number
        if self.first_selected_strand and self.first_selected_strand.set_number == set_number:
            self.first_selected_strand.color = color
        
        if self.second_selected_strand and self.second_selected_strand.set_number == set_number:
            self.second_selected_strand.color = color
            
        # Update the mask's display color only if the first strand is from this set
        # (since the mask inherits its primary color from the first strand)
        if self.first_selected_strand and self.first_selected_strand.set_number == set_number:
            self.color = color

    def calculate_center_point(self):
        """Calculate both base and edited center points."""
        # Calculate base center point from unedited mask
        base_path = self.get_base_mask_path()
        self.base_center_point = self._calculate_center_from_path(base_path)
        
        # Calculate edited center point including deletion rectangles
        edited_path = self.get_mask_path()  # This includes deletion rectangles
        self.edited_center_point = self._calculate_center_from_path(edited_path)
        
        # If edited_center_point is None, try to fall back to base_center_point
        if self.edited_center_point is None and self.base_center_point is not None:
            logging.warning(f"Using base center point as fallback for {self.layer_name}")
            self.edited_center_point = QPointF(self.base_center_point)
        
        # If still None, use the midpoint between the strands as fallback
        if self.edited_center_point is None:
            # Try to use the midpoint of the strands' endpoints
            if hasattr(self, 'first_selected_strand') and hasattr(self, 'second_selected_strand'):
                if self.first_selected_strand and self.second_selected_strand:
                    # Calculate midpoint of all four endpoints for better stability
                    points = [
                        self.first_selected_strand.start,
                        self.first_selected_strand.end,
                        self.second_selected_strand.start,
                        self.second_selected_strand.end
                    ]
                    
                    # Filter out None values
                    valid_points = [p for p in points if p is not None]
                    
                    if valid_points:
                        # Calculate average position
                        sum_x = sum(p.x() for p in valid_points)
                        sum_y = sum(p.y() for p in valid_points)
                        mid_x = sum_x / len(valid_points)
                        mid_y = sum_y / len(valid_points)
                        
                        self.edited_center_point = QPointF(mid_x, mid_y)
                        logging.warning(f"Using fallback midpoint for {self.layer_name}: {mid_x:.2f}, {mid_y:.2f}")
            
            # If still None, use our own endpoints as last resort
            if self.edited_center_point is None and hasattr(self, 'start') and hasattr(self, 'end'):
                if self.start and self.end:
                    mid_x = (self.start.x() + self.end.x()) / 2
                    mid_y = (self.start.y() + self.end.y()) / 2
                    self.edited_center_point = QPointF(mid_x, mid_y)
                    logging.warning(f"Using own endpoints midpoint for {self.layer_name}: {mid_x:.2f}, {mid_y:.2f}")
        
        # Last resort - create a default point if everything else failed
        if self.edited_center_point is None:
            logging.error(f"Failed to calculate any center point for {self.layer_name}, using default")
            self.edited_center_point = QPointF(0, 0)
            self.base_center_point = QPointF(0, 0)
            
        return self.edited_center_point  # Return edited center point for display
        
    def _calculate_center_from_path(self, path):
        """Helper method to calculate center point from a given path."""
        if path.isEmpty():
            logging.warning(f"Empty path for strand {self.layer_name}, cannot calculate center")
            return None
            
        bounds = path.boundingRect()
        samples_x = 50
        samples_y = 50
        
        total_points = 0
        sum_x = 0
        sum_y = 0
        
        for i in range(samples_x):
            for j in range(samples_y):
                x = bounds.x() + (i + 0.5) * bounds.width() / samples_x
                y = bounds.y() + (j + 0.5) * bounds.height() / samples_y
                point = QPointF(x, y)
                
                if path.contains(point):
                    sum_x += x
                    sum_y += y
                    total_points += 1
        
        if total_points > 0:
            center = QPointF(sum_x / total_points, sum_y / total_points)
            logging.info(f"Calculated center point for {self.layer_name}: {center.x():.2f}, {center.y():.2f} from {total_points} points")
            return center
        return None

    def get_base_mask_path(self):
        """Get the mask path without any deletion rectangles."""
        if not self.first_selected_strand or not self.second_selected_strand:
            return QPainterPath()
            
        path1 = self.get_stroked_path_for_strand(self.first_selected_strand)
        path2 = self.get_stroked_path_for_strand(self.second_selected_strand)
        return path1.intersected(path2)

    def get_center_point(self):
        """Return the cached center point or recalculate if needed."""
        if self.edited_center_point is None:
            self.calculate_center_point()
        return self.edited_center_point
        
    def draw_highlight(self, painter):
        """
        Draw a thicker and red stroke around this masked strand's mask path
        to highlight it similarly to other strands.
        """
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Use a semi-transparent highlight color
        if hasattr(self, 'canvas') and hasattr(self.canvas, 'highlight_color'):
            highlight_color = QColor(self.canvas.highlight_color)
            highlight_color.setAlpha(128)  # Set 50% transparency
            highlight_pen = QPen(highlight_color, 6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        else:
            highlight_pen = QPen(QColor(255, 0, 0, 128), 6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            
        painter.setPen(highlight_pen)
        painter.setBrush(Qt.NoBrush)

        # Draw the mask path with our highlight pen, but only if it's not empty
        if hasattr(self, 'get_mask_path'):
            mask_path = self.get_mask_path()
            # Only draw if the path is not empty (strands actually intersect)
            if not mask_path.isEmpty():
                painter.drawPath(mask_path)

        painter.restore()

    def force_complete_update(self):
        """Force a complete update of the MaskedStrand and all its components."""
        # Check if we should skip repositioning of deletion rectangles (during loading)
        skip_recalculation = hasattr(self, 'skip_center_recalculation') and self.skip_center_recalculation
        
        # Check if this strand uses absolute coordinates for deletion rectangles
        using_absolute_coords = hasattr(self, 'using_absolute_coords') and self.using_absolute_coords
        
        if using_absolute_coords:
            logging.info(f"Using absolute coordinates for deletion rectangles in {self.layer_name}, preserving exact JSON positions")
            
            # Just update the mask path without moving deletion rectangles
            path1 = self.get_stroked_path_for_strand(self.first_selected_strand)
            path2 = self.get_stroked_path_for_strand(self.second_selected_strand)
            self.custom_mask_path = path1.intersected(path2)
            
            # Update the component strands but not the deletion rectangles
            if hasattr(self, 'first_selected_strand') and self.first_selected_strand:
                self.first_selected_strand.update_shape()
                if hasattr(self.first_selected_strand, 'update_side_line'):
                    self.first_selected_strand.update_side_line()
            
            if hasattr(self, 'second_selected_strand') and self.second_selected_strand:
                self.second_selected_strand.update_shape()
                if hasattr(self.second_selected_strand, 'update_side_line'):
                    self.second_selected_strand.update_side_line()
                
            # Update canvas if available
            if hasattr(self, 'canvas') and self.canvas:
                if hasattr(self.canvas, 'background_cache_valid'):
                    self.canvas.background_cache_valid = False
                self.canvas.update()
                
            # Don't clear the flag for absolute coordinate strands
            return
        elif skip_recalculation:
            logging.info(f"Skipping full recalculation for {self.layer_name} to preserve original deletion rectangle positions")
            
            # Ensure we have base_center_point and edited_center_point from JSON's control_point_center
            if hasattr(self, 'control_point_center'):
                self.base_center_point = QPointF(self.control_point_center)
                self.edited_center_point = QPointF(self.control_point_center)
                logging.info(f"Using center point from JSON for both base and edited centers: {self.base_center_point.x():.2f}, {self.base_center_point.y():.2f}")
            
            # Only update the mask path without recalculating center points
            path1 = self.get_stroked_path_for_strand(self.first_selected_strand)
            path2 = self.get_stroked_path_for_strand(self.second_selected_strand)
            self.custom_mask_path = path1.intersected(path2)
            
            # Clear the flag after loading is complete
            self.skip_center_recalculation = False
            return
        
        # Normal update path for non-loading scenarios
        # Update mask path
        self.update_mask_path()
        
        # Recalculate center points
        self.calculate_center_point()
        
        # Update shapes of constituent strands
        if hasattr(self, 'first_selected_strand') and self.first_selected_strand:
            self.first_selected_strand.update_shape()
            if hasattr(self.first_selected_strand, 'update_side_line'):
                self.first_selected_strand.update_side_line()
        
        if hasattr(self, 'second_selected_strand') and self.second_selected_strand:
            self.second_selected_strand.update_shape()
            if hasattr(self.second_selected_strand, 'update_side_line'):
                self.second_selected_strand.update_side_line()
        
        # Force shadow update
        self.force_shadow_update()
        
        # Update with center point if available
        if hasattr(self, 'edited_center_point') and self.edited_center_point:
            self.update(self.edited_center_point)
        elif hasattr(self, 'base_center_point') and self.base_center_point:
            self.update(self.base_center_point)
            
        # Update canvas if available
        if hasattr(self, 'canvas') and self.canvas:
            if hasattr(self.canvas, 'background_cache_valid'):
                self.canvas.background_cache_valid = False
            self.canvas.update()
            
        logging.info(f"Completed force_complete_update for {self.layer_name}")