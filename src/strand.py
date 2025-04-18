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
        self.is_hidden = False # Indicates if the strand is hidden

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

        # Add line visibility flags
        self.start_line_visible = True
        self.end_line_visible = True

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

        # --- START: Handle hidden state --- 
        if self.is_hidden:
            painter.restore()
            return # Don't draw anything else if hidden
        # --- END: Handle hidden state ---

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
        # Conditionally draw start line
        if self.start_line_visible:
            painter.drawLine(self.start_line_start, self.start_line_end)
        # Conditionally draw end line
        if self.end_line_visible:
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
            # Check if an attached strand starts at the end point
            skip_end_circle = any(
                isinstance(child, AttachedStrand) and child.start == self.end
                for child in self.attached_strands
            )

            if not skip_end_circle: # Only draw if no child is attached here
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
        if self.has_circles == [True, True]:
            # Check for attached children at start and end
            # Note: Assuming AttachedStrand only connects child.start to parent.end or parent.start
            skip_start_circle = any(
                isinstance(child, AttachedStrand) and child.start == self.start
                for child in self.attached_strands
            )
            skip_end_circle = any(
                isinstance(child, AttachedStrand) and child.start == self.end
                for child in self.attached_strands
            )

            # Re-create a temp image for drawing the circles
            temp_image = QImage(painter.device().size(), QImage.Format_ARGB32_Premultiplied)
            temp_image.fill(Qt.transparent)
            temp_painter = QPainter(temp_image)
            temp_painter.setRenderHint(QPainter.Antialiasing)

            # Common drawing setup
            total_diameter = self.width + self.stroke_width * 2
            circle_radius = total_diameter / 2
            temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            temp_painter.setPen(Qt.NoPen)

            # --- Draw Start Circle (if not skipped) ---
            if not skip_start_circle:
                tangent_start = self.calculate_cubic_tangent(0.0)
                angle_start = math.atan2(tangent_start.y(), tangent_start.x())

                mask_rect_start = QPainterPath()
                rect_width_start = total_diameter * 2
                rect_height_start = total_diameter * 2
                rect_x_start = self.start.x() - rect_width_start / 2
                rect_y_start = self.start.y()
                mask_rect_start.addRect(rect_x_start + 1, rect_y_start + 1, rect_width_start + 1, rect_height_start + 1)

                transform_start = QTransform()
                transform_start.translate(self.start.x(), self.start.y())
                transform_start.rotate(math.degrees(angle_start - math.pi / 2))
                transform_start.translate(-self.start.x(), -self.start.y())
                mask_rect_start = transform_start.map(mask_rect_start)

                outer_circle_start = QPainterPath()
                outer_circle_start.addEllipse(self.start, circle_radius, circle_radius)
                outer_mask_start = outer_circle_start.subtracted(mask_rect_start)

                # Draw stroke
                temp_painter.setBrush(self.stroke_color)
                temp_painter.drawPath(outer_mask_start)

                # Draw fill
                inner_circle_start = QPainterPath()
                inner_circle_start.addEllipse(self.start, self.width / 2, self.width / 2)
                inner_mask_start = inner_circle_start.subtracted(mask_rect_start)
                temp_painter.setBrush(self.color)
                temp_painter.drawPath(inner_mask_start)

                # Avoid clipping look
                just_inner_start = QPainterPath()
                just_inner_start.addEllipse(self.start, self.width / 2, self.width / 2)
                temp_painter.drawPath(just_inner_start)

            # --- Draw End Circle (if not skipped) ---
            if not skip_end_circle:
                tangent_end = self.calculate_cubic_tangent(1.0)
                angle_end = math.atan2(tangent_end.y(), tangent_end.x())

                mask_rect_end = QPainterPath()
                rect_width_end = total_diameter * 2
                rect_height_end = total_diameter * 2
                rect_x_end = self.end.x() - rect_width_end / 2
                rect_y_end = self.end.y()
                mask_rect_end.addRect(rect_x_end + 1, rect_y_end + 1, rect_width_end + 1, rect_height_end + 1)

                transform_end = QTransform()
                transform_end.translate(self.end.x(), self.end.y())
                transform_end.rotate(math.degrees(angle_end - math.pi / 2) + 180)
                transform_end.translate(-self.end.x(), -self.end.y())
                mask_rect_end = transform_end.map(mask_rect_end)

                outer_circle_end = QPainterPath()
                outer_circle_end.addEllipse(self.end, circle_radius, circle_radius)
                outer_mask_end = outer_circle_end.subtracted(mask_rect_end)

                # Draw stroke
                temp_painter.setBrush(self.stroke_color)
                temp_painter.drawPath(outer_mask_end)

                # Draw fill
                inner_circle_end = QPainterPath()
                inner_circle_end.addEllipse(self.end, self.width / 2, self.width / 2)
                inner_mask_end = inner_circle_end.subtracted(mask_rect_end)
                temp_painter.setBrush(self.color)
                temp_painter.drawPath(inner_mask_end)

                # Avoid clipping look
                just_inner_end = QPainterPath()
                just_inner_end.addEllipse(self.end, self.width / 2, self.width / 2)
                temp_painter.drawPath(just_inner_end)

            # --- Finalize drawing for this case ---
            painter.drawImage(0, 0, temp_image)
            temp_painter.end()

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